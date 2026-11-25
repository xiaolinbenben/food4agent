package skillfs

import (
	"errors"
	"path"
	"strings"
	"unicode/utf8"
)

const (
	MaxSlugLen   = 32
	MaxPathLen   = 200
	MaxFiles     = 200
	MaxFileBytes = 8 << 20
	MaxTextBytes = 1 << 20
	MaxZipBytes  = 20 << 20
	MaxTreeBytes = 32 << 20
)

var reservedHandles = map[string]struct{}{
	"skills": {}, "registry": {}, "console": {}, "api": {}, "docs": {},
	"assets": {}, "static": {}, "login": {}, "settings": {},
	"admin": {}, "mcp": {}, "healthz": {}, "skill": {},
}

// ValidSlug 要求 2 到 32 位，小写字母、数字和短横线，且不能以短横线开头或结尾。
func ValidSlug(value string) bool {
	if len(value) < 2 || len(value) > MaxSlugLen {
		return false
	}
	if value[0] == '-' || value[len(value)-1] == '-' {
		return false
	}
	for i := 0; i < len(value); i++ {
		c := value[i]
		if c >= 'a' && c <= 'z' || c >= '0' && c <= '9' || c == '-' {
			continue
		}
		return false
	}
	return true
}

func NormalizeSlug(value string) string {
	return strings.ToLower(strings.TrimSpace(value))
}

// ValidUserID 对齐 GitHub 用户名：1 到 39 位字母、数字或单个短横线，不能连续，也不能开头或结尾。
func ValidUserID(value string) bool {
	if len(value) < 1 || len(value) > 39 {
		return false
	}
	if value[0] == '-' || value[len(value)-1] == '-' {
		return false
	}
	hyphen := false
	for i := 0; i < len(value); i++ {
		c := value[i]
		if c >= 'a' && c <= 'z' || c >= '0' && c <= '9' {
			hyphen = false
			continue
		}
		if c == '-' && !hyphen {
			hyphen = true
			continue
		}
		return false
	}
	return true
}

func NormalizeUserID(value string) string {
	return strings.ToLower(strings.TrimSpace(value))
}

func ReservedHandle(value string) bool {
	_, ok := reservedHandles[value]
	return ok
}

func ReservedSkillName(value string) bool {
	return value == "new"
}

// ValidateRelPath 拒绝路径穿越、点文件和会占用页面地址的路径。
func ValidateRelPath(value string) error {
	if value == "" || len(value) > MaxPathLen || !utf8.ValidString(value) {
		return errors.New("文件路径无效")
	}
	if strings.Contains(value, "\\") || strings.ContainsRune(value, 0) || path.IsAbs(value) {
		return errors.New("文件路径无效")
	}
	if path.Clean(value) != value {
		return errors.New("文件路径无效")
	}
	parts := strings.Split(value, "/")
	for _, part := range parts {
		if part == "" || part == "." || part == ".." || strings.HasPrefix(part, ".") {
			return errors.New("文件路径无效")
		}
		if part == "__MACOSX" || part == "node_modules" || part == ".git" {
			return errors.New("文件路径无效")
		}
		for _, r := range part {
			if r < 0x20 || r == 0x7f {
				return errors.New("文件路径无效")
			}
		}
	}
	if value == "manifest.json" || value == "edit" || value == "versions" || strings.HasPrefix(value, "releases/") {
		return errors.New("这个文件路径已被页面占用")
	}
	if len(parts) == 1 && len(parts[0]) == 64 && isHex(parts[0]) {
		return errors.New("这个文件路径已被版本地址占用")
	}
	return nil
}

func isHex(value string) bool {
	for i := 0; i < len(value); i++ {
		c := value[i]
		if c >= '0' && c <= '9' || c >= 'a' && c <= 'f' {
			continue
		}
		return false
	}
	return true
}

func ContentHashPath(value string) bool {
	return len(value) == 64 && isHex(value)
}
