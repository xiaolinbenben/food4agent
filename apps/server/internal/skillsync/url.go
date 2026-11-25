package skillsync

import (
	"errors"
	"net/url"
	"strings"
)

// IndexURL 把页面地址换成外部 CLI 使用的发现索引。查询参数不保留。
func IndexURL(raw string) (string, error) {
	parsed, err := url.Parse(strings.TrimSpace(raw))
	if err != nil || parsed.Scheme == "" || parsed.Host == "" {
		return "", errors.New("技能地址无效")
	}
	if parsed.Scheme != "https" && parsed.Scheme != "http" {
		return "", errors.New("技能地址无效")
	}
	parsed.RawQuery = ""
	parsed.Fragment = ""
	parsed.Path = strings.TrimRight(parsed.Path, "/")
	const suffix = "/.well-known/agent-skills/index.json"
	if !strings.HasSuffix(parsed.Path, suffix) {
		parsed.Path += suffix
	}
	return parsed.String(), nil
}

// SourceURL 是写进本地标记的安装地址，不含查询参数。
func SourceURL(raw string) (string, error) {
	parsed, err := url.Parse(strings.TrimSpace(raw))
	if err != nil || parsed.Scheme == "" || parsed.Host == "" {
		return "", errors.New("技能地址无效")
	}
	if parsed.Scheme != "https" && parsed.Scheme != "http" {
		return "", errors.New("技能地址无效")
	}
	parsed.RawQuery = ""
	parsed.Fragment = ""
	parsed.Path = strings.TrimRight(parsed.Path, "/")
	return parsed.String(), nil
}
