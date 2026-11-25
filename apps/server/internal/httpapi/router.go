package httpapi

import (
	"io/fs"
	"mime"
	"net/http"
	"path"
	"strings"

	"food4agent/apps/server/internal/config"
	"food4agent/apps/server/internal/middleware"
	"food4agent/apps/server/internal/response"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

func New(cfg config.Config, db *gorm.DB, webFS fs.FS) *gin.Engine {
	engine := gin.New()
	engine.Use(
		gin.CustomRecovery(func(c *gin.Context, _ any) {
			response.Error(c, http.StatusInternalServerError, "服务器内部错误")
			c.Abort()
		}),
		middleware.RequestLog(),
	)
	engine.HandleMethodNotAllowed = true

	engine.GET("/healthz", func(c *gin.Context) {
		response.OK(c, gin.H{"status": "ok"})
	})
	registerWoodfishRoutes(engine, db)
	registerAdminRoutes(engine, cfg.EncryptionKey)
	api := newAPI(cfg, db)
	registerAccountRoutes(engine, api)
	engine.GET("/skill/:name", func(c *gin.Context) {
		name := strings.ToLower(strings.TrimSpace(c.Param("name")))
		if !skillSlug(name) {
			writeSkillNotFound(c)
			return
		}
		c.Redirect(http.StatusMovedPermanently, "/skills/"+name)
	})
	engine.NoMethod(func(c *gin.Context) {
		response.Error(c, http.StatusMethodNotAllowed, "请求方法不支持")
	})
	engine.NoRoute(func(c *gin.Context) {
		if strings.HasPrefix(c.Request.URL.Path, "/api") {
			response.Error(c, http.StatusNotFound, "接口不存在")
			return
		}
		if api.handleAccountSkill(c) {
			return
		}
		serveFrontend(c, webFS)
	})

	return engine
}

func serveFrontend(c *gin.Context, webFS fs.FS) {
	fsPrefix, urlPrefix := frontendTarget(c.Request.URL.Path)
	relative := strings.TrimPrefix(c.Request.URL.Path, urlPrefix)
	name := strings.TrimPrefix(relative, "/")
	if name == "" || (strings.HasPrefix(name, ".") && !strings.HasPrefix(name, ".well-known/")) {
		name = "index.html"
	}

	assetName := path.Join(fsPrefix, name)
	info, err := fs.Stat(webFS, assetName)
	registry := strings.HasPrefix(name, "registry/")
	wellKnown := strings.HasPrefix(name, ".well-known/") || strings.Contains(name, "/.well-known/")
	if err != nil || info.IsDir() {
		if registry || wellKnown {
			c.String(http.StatusNotFound, "not found")
			return
		}
		name = "index.html"
		assetName = path.Join(fsPrefix, name)
	}

	content, err := fs.ReadFile(webFS, assetName)
	if err != nil {
		response.Error(c, http.StatusServiceUnavailable, "前端构建产物不存在，请先执行前端构建")
		return
	}

	// registry 地址不带内容哈希，必须每次校验，避免客户端拿到旧版本。
	if name == "index.html" || registry || wellKnown {
		c.Header("Cache-Control", "no-cache")
	} else {
		c.Header("Cache-Control", "public, max-age=31536000, immutable")
	}
	if contentType := mime.TypeByExtension(path.Ext(name)); contentType != "" {
		c.Header("Content-Type", contentType)
	}
	c.Data(http.StatusOK, contentType(name), content)
}

func frontendTarget(requestPath string) (string, string) {
	if requestPath == "/admin" || strings.HasPrefix(requestPath, "/admin/") {
		return "admin", "/admin"
	}
	return "public", ""
}

func contentType(name string) string {
	if value := mime.TypeByExtension(path.Ext(name)); value != "" {
		return value
	}
	if path.Ext(name) == ".md" {
		return "text/markdown; charset=utf-8"
	}
	return "application/octet-stream"
}

func skillSlug(value string) bool {
	if len(value) < 2 || len(value) > 32 || value[0] == '-' || value[len(value)-1] == '-' {
		return false
	}
	for i := 0; i < len(value); i++ {
		c := value[i]
		if c >= 'a' && c <= 'z' || c >= '0' && c <= '9' || c == '-' {
			continue
		}
		return false
	}
	return true
}
