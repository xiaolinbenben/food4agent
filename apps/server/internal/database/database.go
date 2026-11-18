// Package database 打开 GORM 连接，并在启动时集中迁移。
// 数据库固定为 SQLite，驱动是纯 Go 的 github.com/glebarez/sqlite。
package database

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"time"

	"food4agent/apps/server/internal/model"
	"github.com/glebarez/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

func Open(path string) (*gorm.DB, error) {
	path = strings.TrimSpace(path)
	if path == "" {
		return nil, errors.New("未设置 SQLite 路径")
	}
	info, err := os.Stat(path)
	if err == nil && info.IsDir() {
		return nil, errors.New("SQLite 路径是目录")
	}
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		return nil, err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}

	db, err := gorm.Open(sqlite.Open(path), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Warn),
	})
	if err != nil {
		return nil, err
	}

	sqlDB, err := db.DB()
	if err != nil {
		return nil, err
	}
	sqlDB.SetMaxOpenConns(1)
	sqlDB.SetMaxIdleConns(1)
	sqlDB.SetConnMaxLifetime(0)

	if err := db.Exec("PRAGMA busy_timeout = 5000").Error; err != nil {
		_ = sqlDB.Close()
		return nil, err
	}
	if err := db.Exec("PRAGMA journal_mode = WAL").Error; err != nil {
		_ = sqlDB.Close()
		return nil, err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := sqlDB.PingContext(ctx); err != nil {
		_ = sqlDB.Close()
		return nil, err
	}
	return db, nil
}

func Migrate(db *gorm.DB) error {
	if db == nil {
		return errors.New("数据库未连接")
	}
	if err := db.AutoMigrate(&model.Counter{}); err != nil {
		return err
	}
	var row model.Counter
	return db.Where(model.Counter{Name: model.WoodfishName}).Attrs(model.Counter{Count: 0}).FirstOrCreate(&row).Error
}

func Close(db *gorm.DB) error {
	if db == nil {
		return nil
	}
	sqlDB, err := db.DB()
	if err != nil {
		return err
	}
	return sqlDB.Close()
}

// OpenIsolated 创建一个临时 SQLite 文件并完成迁移。
// cleanup 关闭连接并删除该目录。
func OpenIsolated() (*gorm.DB, func() error, error) {
	dir, err := os.MkdirTemp("", "food4agent-")
	if err != nil {
		return nil, nil, err
	}
	db, err := Open(filepath.Join(dir, "test.db"))
	if err != nil {
		_ = os.RemoveAll(dir)
		return nil, nil, err
	}
	if err := Migrate(db); err != nil {
		_ = Close(db)
		_ = os.RemoveAll(dir)
		return nil, nil, err
	}
	cleanup := func() error {
		return errors.Join(Close(db), os.RemoveAll(dir))
	}
	return db, cleanup, nil
}
