package httpapi

import (
	"errors"
	"io"
	"net/http"
	"strings"

	"food4agent/apps/server/internal/response"
	"food4agent/apps/server/internal/skillfs"
	"food4agent/apps/server/internal/store"
	"github.com/gin-gonic/gin"
)

func (a *API) listSkills(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	items, err := a.skills.List(c.Request.Context(), account.ID)
	if err != nil {
		a.fail(c, err)
		return
	}
	if items == nil {
		items = []store.SkillSummary{}
	}
	response.OK(c, gin.H{"skills": items})
}

func (a *API) createSkill(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	name, displayName, description, visibility, zip, ok := readSkillForm(c)
	if !ok {
		return
	}
	detail, err := a.skills.Create(c.Request.Context(), account, name, displayName, description, visibility, zip)
	if err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, detail)
}

func (a *API) updateSkill(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	var req struct {
		DisplayName string `json:"display_name"`
		Description string `json:"description"`
		Category    string `json:"category"`
		Visibility  string `json:"visibility"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusBadRequest, "请求格式错误")
		return
	}
	detail, err := a.skills.UpdateInfo(c.Request.Context(), account.ID, c.Param("name"), req.DisplayName, req.Description, req.Category, req.Visibility)
	if err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, detail)
}

func (a *API) deleteSkill(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	if err := a.skills.Delete(c.Request.Context(), account.ID, c.Param("name")); err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, gin.H{})
}

func (a *API) skillDetail(c *gin.Context) {
	ownerID, ok := a.readOwner(c)
	if !ok {
		return
	}
	detail, err := a.skills.Detail(c.Request.Context(), ownerID, c.Param("name"))
	if err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, detail)
}

func (a *API) readOwner(c *gin.Context) (uint, bool) {
	if account, ok := a.currentAccount(c); ok {
		return account.ID, true
	}
	raw := presentedToken(c)
	if raw == "" {
		response.Error(c, http.StatusUnauthorized, "未登录")
		return 0, false
	}
	token, err := a.tokens.Lookup(c.Request.Context(), raw)
	if err != nil {
		response.Error(c, http.StatusNotFound, "不存在")
		return 0, false
	}
	return token.OwnerID, true
}

func (a *API) saveDraft(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	c.Request.Body = http.MaxBytesReader(c.Writer, c.Request.Body, 8<<20)
	var req struct {
		Files []store.DraftInput `json:"files"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusBadRequest, "请求格式错误")
		return
	}
	detail, err := a.skills.SaveDraft(c.Request.Context(), account.ID, c.Param("name"), req.Files)
	if err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, detail)
}

func (a *API) uploadSkill(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	zip, ok := readRequiredZip(c)
	if !ok {
		return
	}
	detail, err := a.skills.Upload(c.Request.Context(), account.ID, c.Param("name"), zip)
	if err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, detail)
}

func (a *API) publishSkill(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	var req struct {
		Changelog string `json:"changelog"`
	}
	if err := c.ShouldBindJSON(&req); err != nil && !errors.Is(err, io.EOF) {
		response.Error(c, http.StatusBadRequest, "请求格式错误")
		return
	}
	version, err := a.skills.Publish(c.Request.Context(), account.ID, c.Param("name"), req.Changelog)
	if err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, version)
}

func (a *API) skillVersions(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	versions, err := a.skills.Versions(c.Request.Context(), account.ID, c.Param("name"))
	if err != nil {
		a.fail(c, err)
		return
	}
	if versions == nil {
		versions = []store.VersionView{}
	}
	response.OK(c, gin.H{"versions": versions})
}

func (a *API) rollbackSkill(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	var req struct {
		ContentHash string `json:"content_hash"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusBadRequest, "请求格式错误")
		return
	}
	if err := a.skills.Rollback(c.Request.Context(), account.ID, c.Param("name"), req.ContentHash); err != nil {
		a.fail(c, err)
		return
	}
	detail, err := a.skills.Detail(c.Request.Context(), account.ID, c.Param("name"))
	if err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, detail)
}

func (a *API) token(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	raw, err := a.tokens.Ensure(c.Request.Context(), account.ID)
	if err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, gin.H{"token": raw})
}

func (a *API) resetToken(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	raw, err := a.tokens.Reset(c.Request.Context(), account.ID)
	if err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, gin.H{"token": raw})
}

func (a *API) listInstallations(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	rows, err := a.skills.Installations(c.Request.Context(), account.ID)
	if err != nil {
		a.fail(c, err)
		return
	}
	if rows == nil {
		rows = []store.InstallationView{}
	}
	response.OK(c, gin.H{"installations": rows})
}

func (a *API) saveInstallation(c *gin.Context) {
	account, ok := a.requireAccount(c)
	if !ok {
		return
	}
	var req struct {
		SkillName        string `json:"skill_name"`
		Source           string `json:"source"`
		InstalledVersion string `json:"installed_version"`
		LocalPath        string `json:"local_path"`
		AutoUpdate       bool   `json:"auto_update"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusBadRequest, "请求格式错误")
		return
	}
	row, err := a.skills.SaveInstallation(c.Request.Context(), account.ID, store.InstallationInput{
		SkillName: req.SkillName, Source: req.Source, InstalledVersion: req.InstalledVersion,
		LocalPath: req.LocalPath, AutoUpdate: req.AutoUpdate,
	})
	if err != nil {
		a.fail(c, err)
		return
	}
	response.OK(c, row)
}

func readSkillForm(c *gin.Context) (string, string, string, string, []byte, bool) {
	if strings.HasPrefix(c.ContentType(), "multipart/") {
		if err := c.Request.ParseMultipartForm(skillfs.MaxZipBytes); err != nil {
			response.Error(c, http.StatusBadRequest, "请求格式错误")
			return "", "", "", "", nil, false
		}
		zip, _, ok := optionalZip(c)
		if !ok {
			return "", "", "", "", nil, false
		}
		return c.PostForm("name"), c.PostForm("display_name"), c.PostForm("description"), c.PostForm("visibility"), zip, true
	}
	var req struct {
		Name        string `json:"name"`
		DisplayName string `json:"display_name"`
		Description string `json:"description"`
		Visibility  string `json:"visibility"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusBadRequest, "请求格式错误")
		return "", "", "", "", nil, false
	}
	return req.Name, req.DisplayName, req.Description, req.Visibility, nil, true
}

func readRequiredZip(c *gin.Context) ([]byte, bool) {
	if err := c.Request.ParseMultipartForm(skillfs.MaxZipBytes); err != nil {
		response.Error(c, http.StatusBadRequest, "请求格式错误")
		return nil, false
	}
	body, ok, valid := optionalZip(c)
	if !valid {
		return nil, false
	}
	if !ok || len(body) == 0 {
		response.Error(c, http.StatusBadRequest, "请上传 ZIP")
		return nil, false
	}
	return body, true
}

func optionalZip(c *gin.Context) ([]byte, bool, bool) {
	file, header, err := c.Request.FormFile("file")
	if err != nil {
		return nil, false, true
	}
	defer file.Close()
	if header.Size > skillfs.MaxZipBytes {
		response.Error(c, http.StatusBadRequest, "压缩包过大")
		return nil, false, false
	}
	body, err := io.ReadAll(io.LimitReader(file, skillfs.MaxZipBytes+1))
	if err != nil || len(body) > skillfs.MaxZipBytes {
		response.Error(c, http.StatusBadRequest, "压缩包过大")
		return nil, false, false
	}
	return body, true, true
}
