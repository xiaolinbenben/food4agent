package httpapi

import (
	"errors"
	"log"
	"net/http"

	"food4agent/apps/server/internal/config"
	"food4agent/apps/server/internal/response"
	"food4agent/apps/server/internal/store"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

type API struct {
	key      string
	accounts store.AccountStore
	skills   store.SkillStore
	tokens   store.TokenStore
}

func newAPI(cfg config.Config, db *gorm.DB) *API {
	root := cfg.SkillRoot
	if root == "" {
		root = config.SkillRoot(cfg.DatabasePath)
	}
	return &API{
		key:      cfg.EncryptionKey,
		accounts: store.NewAccountStore(db),
		skills:   store.NewSkillStore(db, root),
		tokens:   store.NewTokenStore(db, cfg.EncryptionKey),
	}
}

func (a *API) fail(c *gin.Context, err error) {
	var invalid *store.InvalidError
	switch {
	case errors.As(err, &invalid):
		response.Error(c, http.StatusBadRequest, invalid.Error())
	case errors.Is(err, store.ErrConflict):
		response.Error(c, http.StatusBadRequest, "名称已存在")
	case errors.Is(err, store.ErrNotFound):
		response.Error(c, http.StatusNotFound, "不存在")
	case errors.Is(err, store.ErrUnauthorized):
		response.Error(c, http.StatusUnauthorized, "账号或密码错误")
	default:
		log.Printf("请求失败 %s %s: %v", c.Request.Method, c.Request.URL.Path, err)
		response.Error(c, http.StatusInternalServerError, "服务器内部错误")
	}
}

func writeSkillNotFound(c *gin.Context) {
	c.Header("Cache-Control", "private, no-store")
	c.Header("X-Content-Type-Options", "nosniff")
	c.String(http.StatusNotFound, "not found")
}
