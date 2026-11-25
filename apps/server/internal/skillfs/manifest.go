package skillfs

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"sort"
	"strings"
)

// File 是一个技能文件。Path 使用斜杠，相对技能根目录。
type File struct {
	Path string
	Data []byte
	Mode uint32
}

type ManifestFile struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
	Size   int    `json:"size"`
}

// Manifest 是发给客户端的文件清单。Version 使用 sha256: 前缀的完整内容哈希。
type Manifest struct {
	Name    string         `json:"name"`
	Version string         `json:"version"`
	Files   []ManifestFile `json:"files"`
}

// ContentHash 对按路径排序后的「路径 + 文件 sha256」做 sha256。
// 算法和公共 registry 相同，这里保留完整 64 位，不截成 12 位。
func ContentHash(files []File) (string, []ManifestFile, error) {
	if len(files) > MaxFiles {
		return "", nil, errors.New("文件数量过多")
	}
	sorted := append([]File(nil), files...)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i].Path < sorted[j].Path })
	seen := make(map[string]struct{}, len(sorted))
	manifestFiles := make([]ManifestFile, 0, len(sorted))
	var total int
	for _, file := range sorted {
		if err := ValidateRelPath(file.Path); err != nil {
			return "", nil, err
		}
		if _, ok := seen[file.Path]; ok {
			return "", nil, errors.New("文件路径重复")
		}
		seen[file.Path] = struct{}{}
		if len(file.Data) > MaxFileBytes {
			return "", nil, errors.New("文件过大")
		}
		total += len(file.Data)
		if total > MaxTreeBytes {
			return "", nil, errors.New("技能文件总大小过大")
		}
		sum := sha256.Sum256(file.Data)
		manifestFiles = append(manifestFiles, ManifestFile{
			Path:   file.Path,
			SHA256: hex.EncodeToString(sum[:]),
			Size:   len(file.Data),
		})
	}
	hash := sha256.New()
	for _, file := range manifestFiles {
		_, _ = hash.Write([]byte(file.Path))
		_, _ = hash.Write([]byte{0})
		_, _ = hash.Write([]byte(file.SHA256))
		_, _ = hash.Write([]byte{'\n'})
	}
	return hex.EncodeToString(hash.Sum(nil)), manifestFiles, nil
}

func NewManifest(name, contentHash string, files []ManifestFile) Manifest {
	version := ""
	if contentHash != "" {
		version = "sha256:" + contentHash
	}
	if files == nil {
		files = []ManifestFile{}
	}
	return Manifest{Name: name, Version: version, Files: files}
}

func EncodeManifest(manifest Manifest) (string, error) {
	body, err := json.Marshal(manifest)
	if err != nil {
		return "", err
	}
	return string(body), nil
}

func DecodeManifest(body string) (Manifest, error) {
	var manifest Manifest
	if strings.TrimSpace(body) == "" {
		return Manifest{Files: []ManifestFile{}}, nil
	}
	if err := json.Unmarshal([]byte(body), &manifest); err != nil {
		return Manifest{}, err
	}
	if manifest.Files == nil {
		manifest.Files = []ManifestFile{}
	}
	return manifest, nil
}

func EncodeFiles(files []ManifestFile) (string, error) {
	if files == nil {
		files = []ManifestFile{}
	}
	body, err := json.Marshal(files)
	if err != nil {
		return "", err
	}
	return string(body), nil
}

// FrontmatterValue 只读取 SKILL.md 顶部单行的 name 或 description。
func FrontmatterValue(content, key string) (string, bool) {
	text := strings.ReplaceAll(content, "\r\n", "\n")
	if !strings.HasPrefix(text, "---\n") {
		return "", false
	}
	rest := strings.TrimPrefix(text, "---\n")
	end := strings.Index(rest, "\n---")
	if end < 0 {
		return "", false
	}
	prefix := key + ":"
	for _, line := range strings.Split(rest[:end], "\n") {
		if !strings.HasPrefix(line, prefix) {
			continue
		}
		value := strings.TrimSpace(strings.TrimPrefix(line, prefix))
		value = strings.Trim(value, `"'`)
		return value, true
	}
	return "", false
}

func SkillMarkdown(files []File) (string, bool) {
	for _, file := range files {
		if file.Path == "SKILL.md" {
			return string(file.Data), true
		}
	}
	return "", false
}

func RequireSkillMarkdown(name string, files []File) error {
	body, ok := SkillMarkdown(files)
	if !ok || strings.TrimSpace(body) == "" {
		return errors.New("缺少 SKILL.md")
	}
	got, present := FrontmatterValue(body, "name")
	if present && got != name {
		return errors.New("SKILL.md 的 name 必须等于技能标识")
	}
	return nil
}
