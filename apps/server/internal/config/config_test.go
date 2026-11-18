package config

import "testing"

func TestDatabasePathDefaults(t *testing.T) {
	t.Setenv("SQLITE_PATH", "")
	got, err := DatabasePath()
	if err != nil {
		t.Fatal(err)
	}
	if got != "data/app.db" {
		t.Fatalf("DatabasePath() = %q, want data/app.db", got)
	}
}

func TestDatabasePathUsesEnv(t *testing.T) {
	t.Setenv("SQLITE_PATH", "  /var/lib/food4agent/app.db  ")
	got, err := DatabasePath()
	if err != nil {
		t.Fatal(err)
	}
	if got != "/var/lib/food4agent/app.db" {
		t.Fatalf("DatabasePath() = %q", got)
	}
}

func TestDatabasePathRejectsNewlines(t *testing.T) {
	t.Setenv("SQLITE_PATH", "data/app.db\nENCRYPTION_KEY=nope")
	if _, err := DatabasePath(); err == nil {
		t.Fatal("newline path was accepted")
	}
}

func TestLoad(t *testing.T) {
	t.Setenv("SQLITE_PATH", "data/test.db")
	t.Setenv("ENCRYPTION_KEY", "test-key")

	cfg, err := Load(":8000")
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Addr != ":8000" {
		t.Fatalf("Addr = %q, want :8000", cfg.Addr)
	}
	if cfg.EncryptionKey != "test-key" {
		t.Fatalf("EncryptionKey = %q, want test-key", cfg.EncryptionKey)
	}
	if cfg.DatabasePath != "data/test.db" {
		t.Fatalf("DatabasePath = %q", cfg.DatabasePath)
	}
}
