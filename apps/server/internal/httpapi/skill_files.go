package httpapi

import (
	"net/http"
	"strings"

	"food4agent/apps/server/internal/model"
	"food4agent/apps/server/internal/skillfs"
	"github.com/gin-gonic/gin"
)

type skillLocation struct {
	Handle string
	Name   string
	Kind   string
	File   string
	Hash   string
}

func (a *API) handleAccountSkill(c *gin.Context) bool {
	if userID, ok := classifyProfile(c.Request.URL.Path); ok {
		if c.Request.Method != http.MethodGet {
			writeSkillNotFound(c)
			return true
		}
		if _, err := a.accounts.ByUserID(c.Request.Context(), userID); err != nil {
			writeSkillNotFound(c)
			return true
		}
		return false
	}
	if install, ok := classifyInstall(c.Request.URL.Path); ok {
		if c.Request.Method != http.MethodGet {
			writeSkillNotFound(c)
			return true
		}
		if install.Kind == "page" {
			return false
		}
		a.serveInstall(c, install)
		return true
	}
	loc, ok := classifySkillPath(c.Request.URL.Path)
	if !ok {
		return false
	}
	if c.Request.Method != http.MethodGet {
		writeSkillNotFound(c)
		return true
	}
	if loc.Kind == "list" || loc.Kind == "new" {
		if _, err := a.accounts.ByUserID(c.Request.Context(), loc.Handle); err != nil {
			writeSkillNotFound(c)
			return true
		}
		return false
	}
	skill, err := a.skills.FindPublished(c.Request.Context(), loc.Handle, loc.Name)
	if err != nil {
		writeSkillNotFound(c)
		return true
	}
	tokenID, readable := a.canRead(c, skill)
	switch loc.Kind {
	case "detail":
		if !readable {
			writeSkillNotFound(c)
			return true
		}
		return false
	case "edit", "versions", "publish":
		if !a.canManage(c, skill.OwnerID) {
			writeSkillNotFound(c)
			return true
		}
		return false
	case "file":
		if !readable {
			writeSkillNotFound(c)
			return true
		}
		a.serveSkillFile(c, skill, loc, tokenID)
		return true
	default:
		writeSkillNotFound(c)
		return true
	}
}

func classifyProfile(requestPath string) (string, bool) {
	parts := strings.Split(strings.Trim(requestPath, "/"), "/")
	if len(parts) == 0 || parts[0] == "" {
		return "", false
	}
	if len(parts) != 1 && !(len(parts) == 2 && parts[1] == "token") {
		return "", false
	}
	userID := skillfs.NormalizeUserID(parts[0])
	if !skillfs.ValidUserID(userID) || skillfs.ReservedHandle(userID) {
		return "", false
	}
	return userID, true
}

func classifySkillPath(requestPath string) (skillLocation, bool) {
	parts := strings.Split(strings.Trim(requestPath, "/"), "/")
	if len(parts) < 2 || parts[1] != "skills" {
		return skillLocation{}, false
	}
	handle := skillfs.NormalizeUserID(parts[0])
	if !skillfs.ValidUserID(handle) || skillfs.ReservedHandle(handle) {
		return skillLocation{}, false
	}
	rest := parts[2:]
	if len(rest) == 0 {
		return skillLocation{Handle: handle, Kind: "list"}, true
	}
	if len(rest) == 1 && rest[0] == "new" {
		return skillLocation{Handle: handle, Kind: "new"}, true
	}
	if !skillfs.ValidSlug(rest[0]) || skillfs.ReservedSkillName(rest[0]) {
		return skillLocation{}, false
	}
	loc := skillLocation{Handle: handle, Name: rest[0]}
	if len(rest) == 1 {
		loc.Kind = "detail"
		return loc, true
	}
	if len(rest) == 2 && rest[1] == "edit" {
		loc.Kind = "edit"
		return loc, true
	}
	if len(rest) == 2 && rest[1] == "versions" {
		loc.Kind = "versions"
		return loc, true
	}
	if len(rest) == 3 && rest[1] == "releases" && rest[2] == "new" {
		loc.Kind = "publish"
		return loc, true
	}
	fileParts := rest[1:]
	if skillfs.ContentHashPath(fileParts[0]) {
		loc.Hash = fileParts[0]
		fileParts = fileParts[1:]
	}
	if len(fileParts) == 0 {
		return skillLocation{}, false
	}
	loc.Kind = "file"
	loc.File = strings.Join(fileParts, "/")
	return loc, true
}

func (a *API) canManage(c *gin.Context, ownerID uint) bool {
	account, ok := a.currentAccount(c)
	return ok && account.ID == ownerID
}

func (a *API) canRead(c *gin.Context, skill model.Skill) (uint, bool) {
	if skill.Visibility == model.VisibilityPublic || a.canManage(c, skill.OwnerID) {
		return 0, true
	}
	raw := presentedToken(c)
	if raw == "" {
		return 0, false
	}
	token, err := a.tokens.Lookup(c.Request.Context(), raw)
	if err != nil || token.OwnerID != skill.OwnerID {
		return 0, false
	}
	return token.ID, true
}

func (a *API) serveSkillFile(c *gin.Context, skill model.Skill, loc skillLocation, tokenID uint) {
	data, err := a.skills.Open(c.Request.Context(), skill, loc.Hash, loc.File)
	if err != nil {
		writeSkillNotFound(c)
		return
	}
	if tokenID != 0 {
		_ = a.tokens.Touch(c.Request.Context(), tokenID)
	}
	private := skill.Visibility == model.VisibilityPrivate
	switch {
	case loc.Hash != "" && private:
		c.Header("Cache-Control", "private, max-age=31536000, immutable")
	case loc.Hash != "":
		c.Header("Cache-Control", "public, max-age=31536000, immutable")
	case private:
		c.Header("Cache-Control", "private, no-store")
	default:
		c.Header("Cache-Control", "no-cache")
	}
	c.Header("X-Content-Type-Options", "nosniff")
	c.Data(http.StatusOK, contentType(loc.File), data)
}

func presentedToken(c *gin.Context) string {
	if raw, ok := strings.CutPrefix(c.GetHeader("Authorization"), "Bearer "); ok {
		return strings.TrimSpace(raw)
	}
	return strings.TrimSpace(c.Query("token"))
}
