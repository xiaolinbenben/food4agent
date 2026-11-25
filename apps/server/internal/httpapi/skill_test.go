package httpapi

import (
	"archive/zip"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestAccountSkillsAreIsolated(t *testing.T) {
	handler := testHandler(t)
	acme := registerAccount(t, handler, "acme", "password-acme")
	terln := registerAccount(t, handler, "terln", "password-terln")
	createSkill(t, handler, acme, "product-search", "private")
	createSkill(t, handler, terln, "product-search", "public")

	publishSkill(t, handler, acme, "product-search")
	publishSkill(t, handler, terln, "product-search")

	privateBody := getSkillFile(t, handler, "/acme/skills/product-search/SKILL.md", "")
	if privateBody.Code != http.StatusNotFound || privateBody.Body.String() != "not found" {
		t.Fatalf("anonymous private status = %d body = %q", privateBody.Code, privateBody.Body.String())
	}
	if privateBody.Header().Get("Cache-Control") != "private, no-store" {
		t.Fatalf("cache = %q", privateBody.Header().Get("Cache-Control"))
	}

	ownerBody := getSkillFile(t, handler, "/acme/skills/product-search/SKILL.md", acme)
	if ownerBody.Code != http.StatusOK || !strings.Contains(ownerBody.Body.String(), "name: product-search") {
		t.Fatalf("owner status = %d body = %q", ownerBody.Code, ownerBody.Body.String())
	}
	if ownerBody.Header().Get("Cache-Control") != "private, no-store" {
		t.Fatalf("owner cache = %q", ownerBody.Header().Get("Cache-Control"))
	}

	otherBody := getSkillFile(t, handler, "/acme/skills/product-search/SKILL.md", terln)
	if otherBody.Code != http.StatusNotFound || otherBody.Body.String() != "not found" {
		t.Fatalf("other account status = %d body = %q", otherBody.Code, otherBody.Body.String())
	}

	publicBody := getSkillFile(t, handler, "/terln/skills/product-search/manifest.json", "")
	if publicBody.Code != http.StatusOK {
		t.Fatalf("public status = %d body = %q", publicBody.Code, publicBody.Body.String())
	}
	if publicBody.Header().Get("Cache-Control") != "no-cache" {
		t.Fatalf("public cache = %q", publicBody.Header().Get("Cache-Control"))
	}
	var manifest struct {
		Version string `json:"version"`
		Files   []struct {
			Path   string `json:"path"`
			SHA256 string `json:"sha256"`
			Size   int    `json:"size"`
		} `json:"files"`
	}
	if err := json.Unmarshal(publicBody.Body.Bytes(), &manifest); err != nil {
		t.Fatal(err)
	}
	if len(manifest.Files) != 1 || manifest.Files[0].SHA256 == "" || manifest.Files[0].Size == 0 {
		t.Fatalf("manifest = %+v", manifest)
	}
	if !strings.HasPrefix(manifest.Version, "sha256:") || len(manifest.Version) != len("sha256:")+64 {
		t.Fatalf("version = %s", manifest.Version)
	}

	key := createSkillKey(t, handler, acme)
	keyed := getSkillFile(t, handler, "/acme/skills/product-search/SKILL.md", "Bearer "+key)
	if keyed.Code != http.StatusOK {
		t.Fatalf("key status = %d", keyed.Code)
	}
	query := getSkillFile(t, handler, "/acme/skills/product-search/SKILL.md?token="+key, "")
	if query.Code != http.StatusOK || !strings.Contains(query.Body.String(), "name: product-search") {
		t.Fatalf("query token status = %d body = %q", query.Code, query.Body.String())
	}
	tokenManifest := getSkillFile(t, handler, "/acme/skills/product-search/manifest.json?token="+key, "")
	if tokenManifest.Code != http.StatusOK || !strings.Contains(tokenManifest.Body.String(), "SKILL.md") {
		t.Fatalf("manifest status = %d body = %q", tokenManifest.Code, tokenManifest.Body.String())
	}
	detail := getSkillFile(t, handler, "/api/skills/product-search", "Bearer "+key)
	if detail.Code != http.StatusOK || !strings.Contains(detail.Body.String(), "product-search") {
		t.Fatalf("token detail status = %d body = %q", detail.Code, detail.Body.String())
	}
	revokeSkillKey(t, handler, acme)
	revoked := getSkillFile(t, handler, "/acme/skills/product-search/SKILL.md", "Bearer "+key)
	if revoked.Code != http.StatusNotFound {
		t.Fatalf("revoked status = %d", revoked.Code)
	}

	hash := strings.TrimPrefix(manifest.Version, "sha256:")
	// terln manifest hash is its own. Fetch acme hash from owner manifest.
	ownerManifest := getSkillFile(t, handler, "/acme/skills/product-search/manifest.json", acme)
	var acmeManifest struct {
		Version string `json:"version"`
	}
	if err := json.Unmarshal(ownerManifest.Body.Bytes(), &acmeManifest); err != nil {
		t.Fatal(err)
	}
	oldHash := strings.TrimPrefix(acmeManifest.Version, "sha256:")
	oldFile := getSkillFile(t, handler, "/acme/skills/product-search/"+oldHash+"/SKILL.md", acme)
	if oldFile.Code != http.StatusOK || oldFile.Header().Get("Cache-Control") != "private, max-age=31536000, immutable" {
		t.Fatalf("hash file status = %d cache = %q", oldFile.Code, oldFile.Header().Get("Cache-Control"))
	}
	saveDraft(t, handler, acme, "product-search", "---\nname: product-search\ndescription: next\n---\n\n# next\n")
	unchanged := getSkillFile(t, handler, "/acme/skills/product-search/"+oldHash+"/SKILL.md", acme)
	if unchanged.Body.String() != oldFile.Body.String() {
		t.Fatal("published hash changed after draft save")
	}
	latest := getSkillFile(t, handler, "/acme/skills/product-search/SKILL.md", acme)
	if strings.Contains(latest.Body.String(), "description: next") {
		t.Fatal("unpublished draft replaced the current file")
	}
	publishSkill(t, handler, acme, "product-search")
	published := getSkillFile(t, handler, "/acme/skills/product-search/SKILL.md", acme)
	if !strings.Contains(published.Body.String(), "description: next") {
		t.Fatalf("publish did not update current file: %s", published.Body.String())
	}
	stillOld := getSkillFile(t, handler, "/acme/skills/product-search/"+oldHash+"/SKILL.md", acme)
	if stillOld.Body.String() != oldFile.Body.String() {
		t.Fatal("old version was overwritten")
	}
	rollback(t, handler, acme, "product-search", oldHash)
	rolled := getSkillFile(t, handler, "/acme/skills/product-search/SKILL.md", acme)
	if rolled.Body.String() != oldFile.Body.String() {
		t.Fatal("rollback did not restore the current file")
	}
	_ = hash
}

func TestSkillUploadRejectsPathTraversal(t *testing.T) {
	handler := testHandler(t)
	cookie := registerAccount(t, handler, "acme", "password-acme")
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)
	_ = writer.WriteField("name", "product-search")
	_ = writer.WriteField("visibility", "private")
	file, err := writer.CreateFormFile("file", "skill.zip")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := file.Write(zipBytes(t, map[string]string{"../SKILL.md": "nope"})); err != nil {
		t.Fatal(err)
	}
	_ = writer.Close()
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodPost, "/api/skills", body)
	request.Header.Set("Content-Type", writer.FormDataContentType())
	request.Header.Set("Cookie", cookie)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("status = %d body = %s", recorder.Code, recorder.Body.String())
	}
}

func TestReservedHandleAndLegacySkillRedirect(t *testing.T) {
	handler := testHandler(t)
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodPost, "/api/accounts/register", strings.NewReader(`{"user_id":"skills","password":"password-ok"}`))
	request.Header.Set("Content-Type", "application/json")
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("reserved status = %d body = %s", recorder.Code, recorder.Body.String())
	}

	recorder = httptest.NewRecorder()
	request = httptest.NewRequest(http.MethodGet, "/skill/hello-world", nil)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusMovedPermanently || recorder.Header().Get("Location") != "/skills/hello-world" {
		t.Fatalf("redirect status = %d location = %q", recorder.Code, recorder.Header().Get("Location"))
	}
}

func registerAccount(t *testing.T, handler http.Handler, handle, password string) string {
	t.Helper()
	recorder := httptest.NewRecorder()
	body := `{"user_id":"` + handle + `","nickname":"` + handle + `","password":"` + password + `"}`
	request := httptest.NewRequest(http.MethodPost, "/api/accounts/register", strings.NewReader(body))
	request.Header.Set("Content-Type", "application/json")
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("register %s status = %d body = %s", handle, recorder.Code, recorder.Body.String())
	}
	cookie := recorder.Result().Cookies()
	if len(cookie) == 0 {
		t.Fatal("missing session cookie")
	}
	return cookie[0].Name + "=" + cookie[0].Value
}

func createSkill(t *testing.T, handler http.Handler, cookie, name, visibility string) {
	t.Helper()
	recorder := postJSON(handler, "/api/skills", `{"name":"`+name+`","nickname":"`+name+`","description":"demo","visibility":"`+visibility+`"}`, cookie)
	if recorder.Code != http.StatusOK {
		t.Fatalf("create status = %d body = %s", recorder.Code, recorder.Body.String())
	}
}

func publishSkill(t *testing.T, handler http.Handler, cookie, name string) {
	t.Helper()
	recorder := postJSON(handler, "/api/skills/"+name+"/publish", `{"changelog":"first"}`, cookie)
	if recorder.Code != http.StatusOK {
		t.Fatalf("publish status = %d body = %s", recorder.Code, recorder.Body.String())
	}
}

func saveDraft(t *testing.T, handler http.Handler, cookie, name, content string) {
	t.Helper()
	payload, err := json.Marshal(map[string]any{"files": []map[string]string{{"path": "SKILL.md", "content": content}}})
	if err != nil {
		t.Fatal(err)
	}
	recorder := postJSON(handler, "/api/skills/"+name+"/draft", string(payload), cookie)
	if recorder.Code != http.StatusOK {
		t.Fatalf("draft status = %d body = %s", recorder.Code, recorder.Body.String())
	}
}

func rollback(t *testing.T, handler http.Handler, cookie, name, hash string) {
	t.Helper()
	recorder := postJSON(handler, "/api/skills/"+name+"/rollback", `{"content_hash":"`+hash+`"}`, cookie)
	if recorder.Code != http.StatusOK {
		t.Fatalf("rollback status = %d body = %s", recorder.Code, recorder.Body.String())
	}
}

func createSkillKey(t *testing.T, handler http.Handler, cookie string) string {
	t.Helper()
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodGet, "/api/token", nil)
	request.Header.Set("Cookie", cookie)
	handler.ServeHTTP(recorder, request)
	if recorder.Code != http.StatusOK {
		t.Fatalf("token status = %d body = %s", recorder.Code, recorder.Body.String())
	}
	var payload struct {
		Data struct {
			Token string `json:"token"`
		} `json:"data"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &payload); err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(payload.Data.Token, "f4a_") {
		t.Fatalf("token = %q", payload.Data.Token)
	}
	if len(payload.Data.Token) != len("f4a_")+22 {
		t.Fatalf("token length = %d, want %d", len(payload.Data.Token), len("f4a_")+22)
	}
	return payload.Data.Token
}

func revokeSkillKey(t *testing.T, handler http.Handler, cookie string) {
	t.Helper()
	recorder := postJSON(handler, "/api/token/reset", `{}`, cookie)
	if recorder.Code != http.StatusOK {
		t.Fatalf("reset status = %d body = %s", recorder.Code, recorder.Body.String())
	}
}

func uintString(value uint) string {
	return strings.TrimPrefix(strings.ReplaceAll(jsonNumber(value), " ", ""), "")
}

func jsonNumber(value uint) string {
	body, _ := json.Marshal(value)
	return string(body)
}

func postJSON(handler http.Handler, path, body, cookie string) *httptest.ResponseRecorder {
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodPost, path, strings.NewReader(body))
	request.Header.Set("Content-Type", "application/json")
	if strings.HasPrefix(cookie, "Bearer ") {
		request.Header.Set("Authorization", cookie)
	} else if cookie != "" {
		request.Header.Set("Cookie", cookie)
	}
	handler.ServeHTTP(recorder, request)
	return recorder
}

func getSkillFile(t *testing.T, handler http.Handler, path, auth string) *httptest.ResponseRecorder {
	t.Helper()
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodGet, path, nil)
	if strings.HasPrefix(auth, "Bearer ") {
		request.Header.Set("Authorization", auth)
	} else if auth != "" {
		request.Header.Set("Cookie", auth)
	}
	handler.ServeHTTP(recorder, request)
	return recorder
}

func zipBytes(t *testing.T, files map[string]string) []byte {
	t.Helper()
	var buf bytes.Buffer
	writer := zip.NewWriter(&buf)
	for name, content := range files {
		file, err := writer.Create(name)
		if err != nil {
			t.Fatal(err)
		}
		if _, err := io.WriteString(file, content); err != nil {
			t.Fatal(err)
		}
	}
	if err := writer.Close(); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}

func TestProfilePageAndUserIDRules(t *testing.T) {
	handler := testHandler(t)
	missing := httptest.NewRecorder()
	handler.ServeHTTP(missing, httptest.NewRequest(http.MethodGet, "/acme", nil))
	if missing.Code != http.StatusNotFound {
		t.Fatalf("missing profile status = %d", missing.Code)
	}
	registerAccount(t, handler, "acme", "password-acme")
	page := httptest.NewRecorder()
	handler.ServeHTTP(page, httptest.NewRequest(http.MethodGet, "/acme", nil))
	if page.Code != http.StatusOK || !strings.Contains(page.Body.String(), "public") {
		t.Fatalf("profile status = %d body = %q", page.Code, page.Body.String())
	}
	bad := postJSON(handler, "/api/accounts/register", `{"user_id":"a--b","password":"password-ok"}`, "")
	if bad.Code != http.StatusBadRequest {
		t.Fatalf("bad user id status = %d body = %s", bad.Code, bad.Body.String())
	}
}

func TestKeepsLatestTenVersions(t *testing.T) {
	handler := testHandler(t)
	cookie := registerAccount(t, handler, "acme", "password-acme")
	createSkill(t, handler, cookie, "product-search", "private")
	var oldest string
	for i := 0; i < 11; i++ {
		content := fmt.Sprintf("---\nname: product-search\ndescription: v%d\n---\n\n# v%d\n", i, i)
		saveDraft(t, handler, cookie, "product-search", content)
		recorder := postJSON(handler, "/api/skills/product-search/publish", fmt.Sprintf(`{"changelog":"v%d"}`, i), cookie)
		if recorder.Code != http.StatusOK {
			t.Fatalf("publish %d status = %d body = %s", i, recorder.Code, recorder.Body.String())
		}
		if i == 0 {
			var payload struct {
				Data struct {
					ContentHash string `json:"content_hash"`
				} `json:"data"`
			}
			if err := json.Unmarshal(recorder.Body.Bytes(), &payload); err != nil {
				t.Fatal(err)
			}
			oldest = payload.Data.ContentHash
		}
	}
	recorder := httptest.NewRecorder()
	request := httptest.NewRequest(http.MethodGet, "/api/skills/product-search/versions", nil)
	request.Header.Set("Cookie", cookie)
	handler.ServeHTTP(recorder, request)
	var payload struct {
		Data struct {
			Versions []struct {
				ContentHash string `json:"content_hash"`
			} `json:"versions"`
		} `json:"data"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &payload); err != nil {
		t.Fatal(err)
	}
	if len(payload.Data.Versions) != 10 {
		t.Fatalf("versions = %d", len(payload.Data.Versions))
	}
	for _, version := range payload.Data.Versions {
		if version.ContentHash == oldest {
			t.Fatal("oldest version was kept")
		}
	}
	gone := getSkillFile(t, handler, "/acme/skills/product-search/"+oldest+"/SKILL.md", cookie)
	if gone.Code != http.StatusNotFound {
		t.Fatalf("deleted version status = %d", gone.Code)
	}
}

func TestInstallProtocolUsesAccountToken(t *testing.T) {
	handler := testHandler(t)
	acme := registerAccount(t, handler, "acme", "password-acme")
	createSkill(t, handler, acme, "product-search", "private")
	publishSkill(t, handler, acme, "product-search")
	token := createSkillKey(t, handler, acme)

	hidden := getSkillFile(t, handler, "/acme/skills/product-search/.well-known/agent-skills/index.json", "")
	if hidden.Code != http.StatusNotFound {
		t.Fatalf("private index without token = %d", hidden.Code)
	}
	indexPath := "/acme/skills/product-search/g/" + token + "/.well-known/agent-skills/index.json"
	index := getSkillFile(t, handler, indexPath, "")
	if index.Code != http.StatusOK || index.Header().Get("Cache-Control") != "private, no-store" {
		t.Fatalf("index status = %d cache = %q body = %s", index.Code, index.Header().Get("Cache-Control"), index.Body.String())
	}
	var discovery struct {
		Skills []struct {
			Type   string `json:"type"`
			URL    string `json:"url"`
			Digest string `json:"digest"`
		} `json:"skills"`
	}
	if err := json.Unmarshal(index.Body.Bytes(), &discovery); err != nil {
		t.Fatal(err)
	}
	if len(discovery.Skills) != 1 || discovery.Skills[0].Type != "archive" || discovery.Skills[0].URL != "product-search.zip" || !strings.HasPrefix(discovery.Skills[0].Digest, "sha256:") {
		t.Fatalf("discovery = %+v", discovery)
	}
	archive := getSkillFile(t, handler, "/acme/skills/product-search/g/"+token+"/.well-known/agent-skills/product-search.zip", "")
	if archive.Code != http.StatusOK {
		t.Fatalf("zip status = %d", archive.Code)
	}
	reader, err := zip.NewReader(bytes.NewReader(archive.Body.Bytes()), int64(archive.Body.Len()))
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, file := range reader.File {
		if file.Name == "SKILL.md" {
			found = true
		}
	}
	if !found {
		t.Fatal("zip missing SKILL.md at root")
	}
	revokeSkillKey(t, handler, acme)
	revoked := getSkillFile(t, handler, indexPath, "")
	if revoked.Code != http.StatusNotFound {
		t.Fatalf("revoked token status = %d", revoked.Code)
	}
}
