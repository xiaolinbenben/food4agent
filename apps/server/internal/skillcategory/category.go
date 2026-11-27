package skillcategory

import (
	"errors"
	"strings"
	"unicode/utf8"
)

type Category struct {
	ID    string
	Label string
}

// Presets 与 skills/categories.json 的 id、label 顺序一致。账号可以另建分类，但不会改这份清单。
var Presets = []Category{
	{ID: "office", Label: "办公协作"},
	{ID: "documents", Label: "文档表格"},
	{ID: "presentations", Label: "演示汇报"},
	{ID: "writing", Label: "内容写作"},
	{ID: "images", Label: "图像设计"},
	{ID: "media", Label: "视频音频"},
	{ID: "social", Label: "社媒运营"},
	{ID: "marketing", Label: "营销销售"},
	{ID: "ecommerce", Label: "电商运营"},
	{ID: "research", Label: "学术科研"},
	{ID: "education", Label: "教育学习"},
	{ID: "product", Label: "产品与体验"},
	{ID: "development", Label: "软件开发"},
	{ID: "data", Label: "数据分析"},
	{ID: "search", Label: "搜索采集"},
	{ID: "agents", Label: "Agent 与自动化"},
	{ID: "finance", Label: "金融财税"},
	{ID: "legal", Label: "法律合规"},
	{ID: "health", Label: "医疗健康"},
	{ID: "lifestyle", Label: "生活休闲"},
	{ID: "system", Label: "系统工具"},
}

func Label(id string) string {
	if id == "" {
		return ""
	}
	for _, preset := range Presets {
		if preset.ID == id {
			return preset.Label
		}
	}
	return id
}

// Resolve 把用户输入收成分类 id。与预置分类同名或同 id 时复用预置 id。
// 合法 id 原样保留；其他名称去掉首尾空白后同时作为 id。
func Resolve(raw string) (string, error) {
	raw = strings.Join(strings.Fields(raw), " ")
	if raw == "" || raw == "未分类" {
		return "", nil
	}
	if utf8.RuneCountInString(raw) > 40 {
		return "", errors.New("分类名称过长")
	}
	for _, r := range raw {
		if r < 0x20 || r == 0x7f || r == '/' || r == '\\' {
			return "", errors.New("分类名称无效")
		}
	}
	for _, preset := range Presets {
		if raw == preset.Label || strings.EqualFold(raw, preset.ID) {
			return preset.ID, nil
		}
	}
	if validID(raw) {
		return raw, nil
	}
	return raw, nil
}

func validID(value string) bool {
	if value == "" {
		return false
	}
	for i, r := range value {
		switch {
		case r >= 'a' && r <= 'z':
		case r >= '0' && r <= '9' || r == '-':
			if i == 0 {
				return false
			}
		default:
			return false
		}
	}
	return true
}
