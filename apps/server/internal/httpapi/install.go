package httpapi

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"net/url"
	"strings"

	"food4agent/apps/server/internal/model"
	"food4agent/apps/server/internal/skillfs"
	"food4agent/apps/server/internal/store"
	"github.com/gin-gonic/gin"
)

const discoverySchema = "https://schemas.agentskills.io/discovery/0.2.0/schema.json"

type installLocation struct {
	Handle string
	Name   string
	Grant  string
	Kind   string
	File   string
}

type discoverySkill struct {
	Name        string `json:"name"`
	Type        string `json:"type"`
	Description string `json:"description"`
	URL         string `json:"url"`
	Digest      string `json:"digest"`
}

type discoveryDocument struct {
	Schema string           `json:"$schema"`
	Skills []discoverySkill `json:"skills"`
}

func (a *API) serveInstall(c *gin.Context, loc installLocation) {
	skill, err := a.skills.FindPublished(c.Request.Context(), loc.Handle, loc.Name)
	if err != nil {
		writeSkillNotFound(c)
		return
	}
	if !a.installAllowed(c, skill, loc.Grant) {
		writeSkillNotFound(c)
		return
	}
	switch loc.Kind {
	case "index":
		files, readErr := a.publishedFiles(c, skill)
		if readErr != nil {
			writeSkillNotFound(c)
			return
		}
		archive, digest, zipErr := archiveSkill(files)
		if zipErr != nil {
			writeSkillNotFound(c)
			return
		}
		_ = archive
		description := strings.TrimSpace(skill.Description)
		if description == "" {
			description = skill.Name
		}
		body, err := json.Marshal(discoveryDocument{
			Schema: discoverySchema,
			Skills: []discoverySkill{{
				Name:        skill.Name,
				Type:        "archive",
				Description: description,
				URL:         installArchiveURL(loc),
				Digest:      digest,
			}},
		})
		if err != nil {
			writeSkillNotFound(c)
			return
		}
		c.Header("Cache-Control", installCache(skill))
		c.Data(http.StatusOK, "application/json; charset=utf-8", body)
	case "zip":
		files, readErr := a.publishedFiles(c, skill)
		if readErr != nil {
			writeSkillNotFound(c)
			return
		}
		archive, _, zipErr := archiveSkill(files)
		if zipErr != nil {
			writeSkillNotFound(c)
			return
		}
		c.Header("Cache-Control", installCache(skill))
		c.Header("X-Content-Type-Options", "nosniff")
		c.Data(http.StatusOK, "application/zip", archive)
	case "file":
		data, openErr := a.skills.Open(c.Request.Context(), skill, "", loc.File)
		if openErr != nil {
			writeSkillNotFound(c)
			return
		}
		c.Header("Cache-Control", installCache(skill))
		c.Header("X-Content-Type-Options", "nosniff")
		c.Data(http.StatusOK, contentType(loc.File), data)
	default:
		writeSkillNotFound(c)
	}
}

func (a *API) installAllowed(c *gin.Context, skill model.Skill, token string) bool {
	if token != "" {
		row, err := a.tokens.Lookup(c.Request.Context(), token)
		if err != nil || row.OwnerID != skill.OwnerID {
			return false
		}
		_ = a.tokens.Touch(c.Request.Context(), row.ID)
		return true
	}
	return skill.Visibility == model.VisibilityPublic
}

func (a *API) publishedFiles(c *gin.Context, skill model.Skill) ([]skillfs.File, error) {
	if skill.CurrentContentHash == "" {
		return nil, store.ErrNotFound
	}
	files, err := a.skills.ReadPublished(c.Request.Context(), skill)
	if err != nil || len(files) == 0 {
		return nil, store.ErrNotFound
	}
	return files, nil
}

func archiveSkill(files []skillfs.File) ([]byte, string, error) {
	archive, err := skillfs.Zip(files)
	if err != nil {
		return nil, "", err
	}
	sum := sha256.Sum256(archive)
	return archive, "sha256:" + hex.EncodeToString(sum[:]), nil
}

func installArchiveURL(loc installLocation) string {
	return url.PathEscape(loc.Name) + ".zip"
}

func installCache(skill model.Skill) string {
	if skill.Visibility == model.VisibilityPrivate {
		return "private, no-store"
	}
	return "no-cache"
}

func requestOrigin(c *gin.Context) string {
	scheme := "http"
	if c.Request.TLS != nil || strings.EqualFold(c.GetHeader("X-Forwarded-Proto"), "https") {
		scheme = "https"
	}
	return scheme + "://" + c.Request.Host
}

func classifyInstall(requestPath string) (installLocation, bool) {
	parts := strings.Split(strings.Trim(requestPath, "/"), "/")
	if len(parts) < 3 || parts[1] != "skills" {
		return installLocation{}, false
	}
	handle := skillfs.NormalizeUserID(parts[0])
	if !skillfs.ValidUserID(handle) || skillfs.ReservedHandle(handle) || !skillfs.ValidSlug(parts[2]) || skillfs.ReservedSkillName(parts[2]) {
		return installLocation{}, false
	}
	loc := installLocation{Handle: handle, Name: parts[2]}
	rest := parts[3:]
	if len(rest) >= 2 && rest[0] == "g" && validTokenPath(rest[1]) {
		loc.Grant = rest[1]
		rest = rest[2:]
	}
	if loc.Grant != "" && len(rest) == 0 {
		loc.Kind = "page"
		return loc, true
	}
	if len(rest) == 3 && rest[0] == ".well-known" && rest[1] == "agent-skills" && rest[2] == "index.json" {
		loc.Kind = "index"
		return loc, true
	}
	if len(rest) == 3 && rest[0] == ".well-known" && rest[1] == "agent-skills" && rest[2] == loc.Name+".zip" {
		loc.Kind = "zip"
		return loc, true
	}
	if loc.Grant != "" && len(rest) > 0 {
		loc.Kind = "file"
		loc.File = strings.Join(rest, "/")
		return loc, true
	}
	return installLocation{}, false
}

func validTokenPath(value string) bool {
	if !strings.HasPrefix(value, "f4a_") || len(value) != len("f4a_")+22 {
		return false
	}
	for _, r := range value[len("f4a_"):] {
		if r >= 'a' && r <= 'z' || r >= 'A' && r <= 'Z' || r >= '0' && r <= '9' || r == '-' || r == '_' {
			continue
		}
		return false
	}
	return true
}
