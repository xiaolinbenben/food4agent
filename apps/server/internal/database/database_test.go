package database

import (
	"path/filepath"
	"testing"

	"food4agent/apps/server/internal/model"
	"gorm.io/gorm"
)

func openTest(t *testing.T) *gorm.DB {
	t.Helper()
	db, cleanup, err := OpenIsolated()
	if err != nil {
		t.Fatalf("打开测试库失败: %v", err)
	}
	t.Cleanup(func() {
		if err := cleanup(); err != nil {
			t.Errorf("清理测试库失败: %v", err)
		}
	})
	return db
}

func TestOpenRejectsInvalidPath(t *testing.T) {
	if _, err := Open(""); err == nil {
		t.Fatal("empty path returned a database")
	}
	if _, err := Open(t.TempDir()); err == nil {
		t.Fatal("directory path returned a database")
	}
}

func TestMigrateAndReadBack(t *testing.T) {
	db := openTest(t)
	if err := Migrate(db); err != nil {
		t.Fatalf("migrate again: %v", err)
	}
	sqlDB, err := db.DB()
	if err != nil {
		t.Fatal(err)
	}
	if sqlDB.Stats().MaxOpenConnections != 1 {
		t.Fatalf("max open connections = %d, want 1", sqlDB.Stats().MaxOpenConnections)
	}

	var row model.Counter
	if err := db.Where("name = ?", model.WoodfishName).First(&row).Error; err != nil {
		t.Fatal(err)
	}
	if row.Count != 0 {
		t.Fatalf("count = %d, want 0", row.Count)
	}
	if err := db.Model(&row).Update("count", int64(3)).Error; err != nil {
		t.Fatal(err)
	}
	var got model.Counter
	if err := db.First(&got, row.ID).Error; err != nil {
		t.Fatal(err)
	}
	if got.Count != 3 {
		t.Fatalf("count = %d, want 3", got.Count)
	}
}

func TestRenameAccountColumns(t *testing.T) {
	db, err := Open(filepath.Join(t.TempDir(), "test.db"))
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = Close(db) })
	if err := db.Exec(`CREATE TABLE accounts (
		id integer primary key,
		handle text not null,
		display_name text not null,
		avatar_url text not null default '',
		password_hash text not null,
		created_at datetime,
		updated_at datetime
	)`).Error; err != nil {
		t.Fatal(err)
	}
	if err := db.Exec(`INSERT INTO accounts (handle, display_name, avatar_url, password_hash) VALUES ('lzq', '林', '', 'hash')`).Error; err != nil {
		t.Fatal(err)
	}
	if err := Migrate(db); err != nil {
		t.Fatal(err)
	}
	var account model.Account
	if err := db.Where("user_id = ?", "lzq").First(&account).Error; err != nil {
		t.Fatal(err)
	}
	if account.Nickname != "林" || account.Email != "" {
		t.Fatalf("account = %+v", account)
	}
}
