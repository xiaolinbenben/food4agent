package skillsync

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

const MarkerName = ".terln-skill.json"

var ErrDirty = errors.New("本地技能有未同步修改")

type File struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
	Size   int    `json:"size"`
}

type Manifest struct {
	Name    string `json:"name"`
	Version string `json:"version"`
	Files   []File `json:"files"`
}

// Marker 写在技能目录里。Files 用来判断本地文件是否被改过。
type Marker struct {
	Source     string `json:"source"`
	Owner      string `json:"owner,omitempty"`
	Name       string `json:"name"`
	SourceURL  string `json:"source_url"`
	Version    string `json:"version"`
	AutoUpdate bool   `json:"auto_update"`
	Files      []File `json:"files"`
}

type Getter func(rel string) ([]byte, error)

// Sync 下载到临时目录，逐文件校验后原子替换。本地有修改且未确认时不会覆盖。
func Sync(dest string, marker Marker, manifest Manifest, get Getter, force bool) error {
	if manifest.Name == "" || marker.Name == "" {
		return errors.New("技能名称缺失")
	}
	dirty, err := localDirty(dest)
	if err != nil {
		return err
	}
	if dirty && !force {
		return ErrDirty
	}
	existing, ok, err := readMarker(dest)
	if err != nil {
		return err
	}
	if ok && !dirty && existing.Version == manifest.Version {
		return nil
	}
	files, err := download(manifest, get)
	if err != nil {
		return err
	}
	marker.Version = manifest.Version
	marker.Files = manifest.Files
	return swap(dest, files, marker, dirty && force)
}

func download(manifest Manifest, get Getter) (map[string][]byte, error) {
	if len(manifest.Files) == 0 {
		return nil, errors.New("清单里没有文件")
	}
	out := make(map[string][]byte, len(manifest.Files))
	for _, file := range manifest.Files {
		if file.Path == "" || strings.Contains(file.Path, "..") || strings.HasPrefix(file.Path, "/") {
			return nil, errors.New("清单路径无效")
		}
		body, err := get(file.Path)
		if err != nil {
			return nil, err
		}
		if len(body) != file.Size {
			return nil, errors.New(file.Path + " 的大小和清单不一致")
		}
		sum := sha256.Sum256(body)
		if hex.EncodeToString(sum[:]) != file.SHA256 {
			return nil, errors.New(file.Path + " 的 sha256 和清单不一致")
		}
		out[file.Path] = body
	}
	return out, nil
}

func localDirty(dest string) (bool, error) {
	info, err := os.Stat(dest)
	if errors.Is(err, os.ErrNotExist) {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if !info.IsDir() {
		return false, errors.New("安装位置不是目录")
	}
	marker, ok, err := readMarker(dest)
	if err != nil {
		return false, err
	}
	files, err := localFiles(dest)
	if err != nil {
		return false, err
	}
	if !ok {
		return len(files) > 0, nil
	}
	return !sameFiles(files, marker.Files), nil
}

func localFiles(dest string) ([]File, error) {
	files := []File{}
	err := filepath.WalkDir(dest, func(target string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(dest, target)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		if rel == MarkerName {
			return nil
		}
		data, err := os.ReadFile(target)
		if err != nil {
			return err
		}
		sum := sha256.Sum256(data)
		files = append(files, File{Path: rel, SHA256: hex.EncodeToString(sum[:]), Size: len(data)})
		return nil
	})
	if err != nil {
		return nil, err
	}
	sort.Slice(files, func(i, j int) bool { return files[i].Path < files[j].Path })
	return files, nil
}

func sameFiles(got, want []File) bool {
	if len(got) != len(want) {
		return false
	}
	wantSorted := append([]File(nil), want...)
	sort.Slice(wantSorted, func(i, j int) bool { return wantSorted[i].Path < wantSorted[j].Path })
	for i := range got {
		if got[i] != wantSorted[i] {
			return false
		}
	}
	return true
}

func readMarker(dest string) (Marker, bool, error) {
	body, err := os.ReadFile(filepath.Join(dest, MarkerName))
	if errors.Is(err, os.ErrNotExist) {
		return Marker{}, false, nil
	}
	if err != nil {
		return Marker{}, false, err
	}
	var marker Marker
	if err := json.Unmarshal(body, &marker); err != nil {
		return Marker{}, false, errors.New(".terln-skill.json 无法读取")
	}
	return marker, true, nil
}

func swap(dest string, files map[string][]byte, marker Marker, backup bool) error {
	parent := filepath.Dir(dest)
	if parent == "" {
		parent = "."
	}
	if err := os.MkdirAll(parent, 0o755); err != nil {
		return err
	}
	tmp, err := os.MkdirTemp(parent, "skill-sync-")
	if err != nil {
		return err
	}
	defer func() { _ = os.RemoveAll(tmp) }()
	for rel, body := range files {
		target := filepath.Join(tmp, filepath.FromSlash(rel))
		if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(target, body, 0o644); err != nil {
			return err
		}
	}
	body, err := json.MarshalIndent(marker, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(filepath.Join(tmp, MarkerName), append(body, '\n'), 0o644); err != nil {
		return err
	}
	backupPath := ""
	if _, err := os.Stat(dest); err == nil {
		if backup {
			backupPath = dest + ".backup-" + time.Now().Format("20060102150405")
		} else {
			backupPath = dest + ".old"
		}
		_ = os.RemoveAll(backupPath)
		if err := os.Rename(dest, backupPath); err != nil {
			return err
		}
	} else if !errors.Is(err, os.ErrNotExist) {
		return err
	}
	if err := os.Rename(tmp, dest); err != nil {
		if backupPath != "" {
			_ = os.Rename(backupPath, dest)
		}
		return err
	}
	if !backup {
		_ = os.RemoveAll(backupPath)
	}
	return nil
}
