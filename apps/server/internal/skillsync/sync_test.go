package skillsync

import (
	"crypto/sha256"
	"encoding/hex"
	"os"
	"path/filepath"
	"testing"
)

func TestSyncReplacesCleanDirectoryAndRefusesDirty(t *testing.T) {
	dest := filepath.Join(t.TempDir(), "product-search")
	manifest := Manifest{
		Name:    "product-search",
		Version: "sha256:abc",
		Files:   []File{{Path: "SKILL.md", SHA256: sha("hello"), Size: len("hello")}},
	}
	marker := Marker{Source: "food4agent_private", Owner: "acme", Name: "product-search", SourceURL: "https://food4agent.com/acme/skills/product-search", AutoUpdate: true}
	err := Sync(dest, marker, manifest, func(rel string) ([]byte, error) {
		if rel != "SKILL.md" {
			t.Fatalf("unexpected %s", rel)
		}
		return []byte("hello"), nil
	}, false)
	if err != nil {
		t.Fatal(err)
	}
	body, err := os.ReadFile(filepath.Join(dest, "SKILL.md"))
	if err != nil || string(body) != "hello" {
		t.Fatalf("file = %q, err = %v", body, err)
	}
	if _, err := os.Stat(filepath.Join(dest, MarkerName)); err != nil {
		t.Fatal(err)
	}

	if err := os.WriteFile(filepath.Join(dest, "SKILL.md"), []byte("changed"), 0o644); err != nil {
		t.Fatal(err)
	}
	err = Sync(dest, marker, manifest, func(string) ([]byte, error) {
		t.Fatal("dirty skill was downloaded")
		return nil, nil
	}, false)
	if err != ErrDirty {
		t.Fatalf("err = %v, want dirty", err)
	}
	body, _ = os.ReadFile(filepath.Join(dest, "SKILL.md"))
	if string(body) != "changed" {
		t.Fatalf("dirty file overwritten: %q", body)
	}
}

func TestSyncSkipsCurrentVersion(t *testing.T) {
	dest := filepath.Join(t.TempDir(), "product-search")
	manifest := Manifest{Name: "product-search", Version: "sha256:abc", Files: []File{{Path: "SKILL.md", SHA256: sha("hello"), Size: len("hello")}}}
	marker := Marker{Source: "food4agent_public", Name: "product-search", SourceURL: "https://food4agent.com/registry/skills/product-search", AutoUpdate: true}
	get := func(string) ([]byte, error) { return []byte("hello"), nil }
	if err := Sync(dest, marker, manifest, get, false); err != nil {
		t.Fatal(err)
	}
	if err := Sync(dest, marker, manifest, func(string) ([]byte, error) {
		t.Fatal("current version was downloaded again")
		return nil, nil
	}, false); err != nil {
		t.Fatal(err)
	}
}

func TestIndexURL(t *testing.T) {
	index, err := IndexURL("https://food4agent.com/acme/skills/product-search/g/g_abcdefghijklmnopqrstuv?token=ignored")
	if err != nil {
		t.Fatal(err)
	}
	if index != "https://food4agent.com/acme/skills/product-search/g/g_abcdefghijklmnopqrstuv/.well-known/agent-skills/index.json" {
		t.Fatal(index)
	}
	source, err := SourceURL("https://food4agent.com/skills/hello-world/?token=ignored")
	if err != nil || source != "https://food4agent.com/skills/hello-world" {
		t.Fatal(err, source)
	}
}

func sha(body string) string {
	sum := sha256.Sum256([]byte(body))
	return hex.EncodeToString(sum[:])
}
