package httpapi

import (
	"net/http"
	"net/http/httptest"
	"path/filepath"
	"strings"
	"testing"
	"testing/fstest"

	"food4agent/apps/server/internal/config"
	"food4agent/apps/server/internal/database"
)

func testHandler(t *testing.T) http.Handler {
	t.Helper()
	dir := t.TempDir()
	db, err := database.Open(filepath.Join(dir, "test.db"))
	if err != nil {
		t.Fatalf("打开测试库失败: %v", err)
	}
	if err := database.Migrate(db); err != nil {
		t.Fatalf("迁移测试库失败: %v", err)
	}
	t.Cleanup(func() {
		if err := database.Close(db); err != nil {
			t.Errorf("关闭测试库失败: %v", err)
		}
	})
	webFS := fstest.MapFS{
		"public/index.html":                          &fstest.MapFile{Data: []byte("<html>public</html>")},
		"public/assets/app.js":                       &fstest.MapFile{Data: []byte("console.log('app')")},
		"public/registry/skills/demo/SKILL.md":       &fstest.MapFile{Data: []byte("---\nname: demo\n---\n")},
		"public/.well-known/agent-skills/index.json": &fstest.MapFile{Data: []byte("{\"skills\":[]}")},
		"admin/index.html":                           &fstest.MapFile{Data: []byte("<html>admin</html>")},
	}
	return New(config.Config{Addr: ":8000", DatabasePath: filepath.Join(dir, "test.db"), SkillRoot: filepath.Join(dir, "skills"), EncryptionKey: "test-key"}, db, webFS)
}

func TestHealthz(t *testing.T) {
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	testHandler(t).ServeHTTP(recorder, request)

	if recorder.Code != http.StatusOK {
		t.Fatalf("healthz status = %d, want %d", recorder.Code, http.StatusOK)
	}
	if got := recorder.Header().Get("Content-Type"); got != "application/json; charset=utf-8" {
		t.Fatalf("content type = %q", got)
	}
	if body := recorder.Body.String(); body != `{"success":true,"message":"","data":{"status":"ok"}}` {
		t.Fatalf("unexpected body: %s", body)
	}
}

func TestFrontendFallbacks(t *testing.T) {
	tests := []struct {
		path string
		want string
	}{
		{path: "/", want: "public"},
		{path: "/app/settings", want: "public"},
		{path: "/admin/", want: "admin"},
		{path: "/admin/users", want: "admin"},
		{path: "/assets/app.js", want: "console.log('app')"},
	}

	for _, test := range tests {
		t.Run(test.path, func(t *testing.T) {
			recorder := httptest.NewRecorder()
			request := httptest.NewRequest(http.MethodGet, test.path, nil)
			testHandler(t).ServeHTTP(recorder, request)
			if recorder.Code != http.StatusOK {
				t.Fatalf("status = %d", recorder.Code)
			}
			if body := recorder.Body.String(); body != test.want && !contains(body, test.want) {
				t.Fatalf("body %q does not contain %q", body, test.want)
			}
		})
	}
}

func TestUnknownAPI(t *testing.T) {
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodGet, "/api/unknown", nil)
	testHandler(t).ServeHTTP(recorder, request)

	if recorder.Code != http.StatusNotFound {
		t.Fatalf("status = %d, want %d", recorder.Code, http.StatusNotFound)
	}
	if body := recorder.Body.String(); body != `{"success":false,"message":"接口不存在","data":{}}` {
		t.Fatalf("unexpected body: %s", body)
	}
}

func TestHealthzRejectsUnsupportedMethod(t *testing.T) {
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodPost, "/healthz", nil)
	testHandler(t).ServeHTTP(recorder, request)

	if recorder.Code != http.StatusMethodNotAllowed {
		t.Fatalf("status = %d, want %d", recorder.Code, http.StatusMethodNotAllowed)
	}
	if body := recorder.Body.String(); body != `{"success":false,"message":"请求方法不支持","data":{}}` {
		t.Fatalf("unexpected body: %s", body)
	}
}

func contains(value, expected string) bool {
	for i := 0; i+len(expected) <= len(value); i++ {
		if value[i:i+len(expected)] == expected {
			return true
		}
	}
	return false
}

func TestRegistryFiles(t *testing.T) {
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodGet, "/registry/skills/demo/SKILL.md", nil)
	testHandler(t).ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK || !contains(recorder.Body.String(), "name: demo") {
		t.Fatalf("status = %d, body = %q", recorder.Code, recorder.Body.String())
	}
	if got := recorder.Header().Get("Cache-Control"); got != "no-cache" {
		t.Fatalf("cache control = %q", got)
	}
	if got := recorder.Header().Get("Content-Type"); got != "text/markdown; charset=utf-8" {
		t.Fatalf("content type = %q", got)
	}

	recorder = httptest.NewRecorder()
	request = httptest.NewRequest(http.MethodGet, "/registry/skills/missing/SKILL.md", nil)
	testHandler(t).ServeHTTP(recorder, request)
	if recorder.Code != http.StatusNotFound {
		t.Fatalf("missing registry status = %d", recorder.Code)
	}
}

func TestWellKnownIndexIsNotTheSitePage(t *testing.T) {
	handler := testHandler(t)
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodGet, "/.well-known/agent-skills/index.json", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK || recorder.Body.String() != `{"skills":[]}` {
		t.Fatalf("status = %d body = %q", recorder.Code, recorder.Body.String())
	}
	recorder = httptest.NewRecorder()
	request = httptest.NewRequest(http.MethodGet, "/.well-known/agent-skills/missing.json", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusNotFound || strings.Contains(recorder.Body.String(), "<html>") {
		t.Fatalf("missing status = %d body = %q", recorder.Code, recorder.Body.String())
	}
}
