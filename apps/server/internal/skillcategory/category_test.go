package skillcategory

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestResolvePresetAndCustomNames(t *testing.T) {
	id, err := Resolve("  电商运营 ")
	if err != nil || id != "ecommerce" || Label(id) != "电商运营" {
		t.Fatalf("label id = %s err = %v", id, err)
	}
	id, err = Resolve("Ecommerce")
	if err != nil || id != "ecommerce" {
		t.Fatalf("id match = %s err = %v", id, err)
	}
	id, err = Resolve("my-tools")
	if err != nil || id != "my-tools" || Label(id) != "my-tools" {
		t.Fatalf("slug = %s label = %s err = %v", id, Label(id), err)
	}
	id, err = Resolve("  内部资料  ")
	if err != nil || id != "内部资料" || Label(id) != "内部资料" {
		t.Fatalf("custom = %s err = %v", id, err)
	}
	id, err = Resolve(" 未分类 ")
	if err != nil || id != "" || Label(id) != "" {
		t.Fatalf("uncategorized = %q err = %v", id, err)
	}
}

func TestPresetsMatchCategoriesFile(t *testing.T) {
	body, err := os.ReadFile(filepath.Join("..", "..", "..", "..", "skills", "categories.json"))
	if err != nil {
		t.Fatal(err)
	}
	var rows []struct {
		ID    string `json:"id"`
		Label string `json:"label"`
	}
	if err := json.Unmarshal(body, &rows); err != nil {
		t.Fatal(err)
	}
	if len(rows) != len(Presets) {
		t.Fatalf("presets = %d, categories = %d", len(Presets), len(rows))
	}
	for i, row := range rows {
		if Presets[i].ID != row.ID || Presets[i].Label != row.Label {
			t.Fatalf("preset %d = %+v, category = %+v", i, Presets[i], row)
		}
	}
}
