package skillfs

import (
	"errors"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// Dir 把技能文件放在 SQLite 旁边的本地目录。这里没有单独的对象存储。
type Dir struct {
	Root string
}

func (d Dir) Draft(ownerID, skillID uint) string {
	return filepath.Join(d.Root, itoa(ownerID), itoa(skillID), "draft")
}

func (d Dir) Version(ownerID, skillID uint, hash string) string {
	return filepath.Join(d.Root, itoa(ownerID), itoa(skillID), "versions", hash)
}

func (d Dir) Write(dir string, files []File) error {
	if _, _, err := ContentHash(files); err != nil {
		return err
	}
	parent := filepath.Dir(dir)
	if err := os.MkdirAll(parent, 0o755); err != nil {
		return err
	}
	tmp, err := os.MkdirTemp(parent, "next-")
	if err != nil {
		return err
	}
	defer func() { _ = os.RemoveAll(tmp) }()
	for _, file := range files {
		target := filepath.Join(tmp, filepath.FromSlash(file.Path))
		if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
			return err
		}
		mode := os.FileMode(0o644)
		if file.Mode&0o111 != 0 {
			mode = 0o755
		}
		if err := os.WriteFile(target, file.Data, mode); err != nil {
			return err
		}
	}
	backup := dir + ".bak"
	_ = os.RemoveAll(backup)
	renamed := false
	if _, err := os.Stat(dir); err == nil {
		if err := os.Rename(dir, backup); err != nil {
			return err
		}
		renamed = true
	} else if !errors.Is(err, os.ErrNotExist) {
		return err
	}
	if err := os.Rename(tmp, dir); err != nil {
		if renamed {
			_ = os.Rename(backup, dir)
		}
		return err
	}
	_ = os.RemoveAll(backup)
	return nil
}

// WriteNew 只在目标不存在时写入。已发布目录不会被覆盖。
func (d Dir) WriteNew(dir string, files []File) error {
	if _, err := os.Stat(dir); err == nil {
		return nil
	} else if !errors.Is(err, os.ErrNotExist) {
		return err
	}
	return d.Write(dir, files)
}

func (d Dir) Read(dir string) ([]File, error) {
	info, err := os.Stat(dir)
	if errors.Is(err, os.ErrNotExist) {
		return []File{}, nil
	}
	if err != nil {
		return nil, err
	}
	if !info.IsDir() {
		return nil, errors.New("技能目录无效")
	}
	files := []File{}
	err = filepath.WalkDir(dir, func(target string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(dir, target)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		if err := ValidateRelPath(rel); err != nil {
			return err
		}
		data, err := os.ReadFile(target)
		if err != nil {
			return err
		}
		info, err := entry.Info()
		if err != nil {
			return err
		}
		mode := uint32(0o644)
		if info.Mode()&0o111 != 0 {
			mode = 0o755
		}
		files = append(files, File{Path: rel, Data: data, Mode: mode})
		return nil
	})
	if err != nil {
		return nil, err
	}
	sort.Slice(files, func(i, j int) bool { return files[i].Path < files[j].Path })
	return files, nil
}

func (d Dir) ReadFile(dir, rel string) ([]byte, error) {
	if err := ValidateRelPath(rel); err != nil {
		return nil, err
	}
	target := filepath.Join(dir, filepath.FromSlash(rel))
	root, err := filepath.Abs(dir)
	if err != nil {
		return nil, err
	}
	full, err := filepath.Abs(target)
	if err != nil {
		return nil, err
	}
	if full != root && !strings.HasPrefix(full, root+string(os.PathSeparator)) {
		return nil, errors.New("文件路径无效")
	}
	return os.ReadFile(full)
}

func itoa(value uint) string {
	if value == 0 {
		return "0"
	}
	var buf [20]byte
	i := len(buf)
	for value > 0 {
		i--
		buf[i] = byte('0' + value%10)
		value /= 10
	}
	return string(buf[i:])
}

func (d Dir) Remove(dir string) error {
	if dir == "" || dir == d.Root {
		return errors.New("路径无效")
	}
	root := filepath.Clean(d.Root)
	target := filepath.Clean(dir)
	rel, err := filepath.Rel(root, target)
	if err != nil || rel == "." || strings.HasPrefix(rel, "..") {
		return errors.New("路径无效")
	}
	return os.RemoveAll(target)
}
