package httpapi

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"food4agent/apps/server/internal/model"
	"food4agent/apps/server/internal/response"
	"github.com/gin-gonic/gin"
)

const accountCookie = "account_session"

func registerAccountRoutes(engine *gin.Engine, api *API) {
	engine.POST("/api/accounts/register", api.register)
	engine.POST("/api/accounts/login", api.login)
	engine.POST("/api/accounts/logout", api.logout)
	engine.GET("/api/accounts/session", api.session)
	engine.GET("/api/skills", api.listSkills)
	engine.POST("/api/skills", api.createSkill)
	engine.GET("/api/skills/:name", api.skillDetail)
	engine.PATCH("/api/skills/:name", api.updateSkill)
	engine.DELETE("/api/skills/:name", api.deleteSkill)
	engine.POST("/api/skills/:name/draft", api.saveDraft)
	engine.POST("/api/skills/:name/upload", api.uploadSkill)
	engine.POST("/api/skills/:name/publish", api.publishSkill)
	engine.GET("/api/skills/:name/versions", api.skillVersions)
	engine.POST("/api/skills/:name/rollback", api.rollbackSkill)
	engine.GET("/api/token", api.token)
	engine.POST("/api/token/reset", api.resetToken)
	engine.GET("/api/installations", api.listInstallations)
	engine.POST("/api/installations", api.saveInstallation)
}

func (a *API) register(c *gin.Context) {
	var req struct {
		UserID   string `json:"user_id"`
		Nickname string `json:"nickname"`
		Password string `json:"password"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusBadRequest, "请求格式错误")
		return
	}
	account, err := a.accounts.Create(c.Request.Context(), req.UserID, req.Nickname, req.Password)
	if err != nil {
		a.fail(c, err)
		return
	}
	if _, err := a.tokens.Ensure(c.Request.Context(), account.ID); err != nil {
		a.fail(c, err)
		return
	}
	writeAccountSession(c, a.key, account.ID)
	response.OK(c, accountView(account))
}

func (a *API) login(c *gin.Context) {
	var req struct {
		UserID   string `json:"user_id"`
		Password string `json:"password"`
	}
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, http.StatusBadRequest, "请求格式错误")
		return
	}
	account, err := a.accounts.Authenticate(c.Request.Context(), req.UserID, req.Password)
	if err != nil {
		a.fail(c, err)
		return
	}
	writeAccountSession(c, a.key, account.ID)
	response.OK(c, accountView(account))
}

func (a *API) logout(c *gin.Context) {
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie(accountCookie, "", -1, "/", "", false, true)
	response.OK(c, gin.H{})
}

func (a *API) session(c *gin.Context) {
	account, ok := a.currentAccount(c)
	if !ok {
		response.Error(c, http.StatusUnauthorized, "未登录")
		return
	}
	response.OK(c, accountView(account))
}

func accountView(account model.Account) gin.H {
	return gin.H{"user_id": account.UserID, "nickname": account.Nickname, "email": account.Email}
}

func writeAccountSession(c *gin.Context, key string, id uint) {
	payload := fmt.Sprintf("%d|%d", id, time.Now().Add(sessionTTL).Unix())
	c.SetSameSite(http.SameSiteLaxMode)
	c.SetCookie(accountCookie, signSession(key, payload), int(sessionTTL.Seconds()), "/", "", false, true)
}

func currentAccountID(c *gin.Context, key string) (uint, bool) {
	raw, err := c.Cookie(accountCookie)
	if err != nil {
		return 0, false
	}
	payload, ok := openSession(key, raw)
	if !ok {
		return 0, false
	}
	idText, expiryText, found := strings.Cut(payload, "|")
	if !found {
		return 0, false
	}
	id, err := strconv.ParseUint(idText, 10, 64)
	if err != nil || id == 0 {
		return 0, false
	}
	expiry, err := strconv.ParseInt(expiryText, 10, 64)
	if err != nil || time.Now().Unix() > expiry {
		return 0, false
	}
	return uint(id), true
}

func (a *API) currentAccount(c *gin.Context) (model.Account, bool) {
	id, ok := currentAccountID(c, a.key)
	if !ok {
		return model.Account{}, false
	}
	account, err := a.accounts.ByID(c.Request.Context(), id)
	if err != nil {
		return model.Account{}, false
	}
	return account, true
}

func (a *API) requireAccount(c *gin.Context) (model.Account, bool) {
	account, ok := a.currentAccount(c)
	if !ok {
		response.Error(c, http.StatusUnauthorized, "未登录")
		return model.Account{}, false
	}
	return account, true
}
