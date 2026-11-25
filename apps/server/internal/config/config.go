package config

import (
	"errors"
	"os"
	"path/filepath"
	"strings"
)

type Config struct {
	Addr          string
	DatabasePath  string
	SkillRoot     string
	EncryptionKey string
}

func Load(addr string) (Config, error) {
	databasePath, err := DatabasePath()
	if err != nil {
		return Config{}, err
	}
	return Config{
		Addr:          addr,
		DatabasePath:  databasePath,
		SkillRoot:     SkillRoot(databasePath),
		EncryptionKey: os.Getenv("ENCRYPTION_KEY"),
	}, nil
}

// SkillRoot 和 SQLite 放在同一目录，避免再引入对象存储配置。
func SkillRoot(databasePath string) string {
	return filepath.Join(filepath.Dir(databasePath), "skills")
}

// DatabasePath 是 SQLite 文件路径。未设置 SQLITE_PATH 时用 data/app.db，相对进程工作目录。
func DatabasePath() (string, error) {
	path := strings.TrimSpace(os.Getenv("SQLITE_PATH"))
	if path == "" {
		return "data/app.db", nil
	}
	if strings.ContainsRune(path, 0) || strings.ContainsAny(path, "\r\n") {
		return "", errors.New("SQLITE_PATH 无效")
	}
	return path, nil
}
