package main

import (
	"archive/zip"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"food4agent/apps/server/internal/skillsync"
)

type discoverySkill struct {
	Name        string `json:"name"`
	Type        string `json:"type"`
	Description string `json:"description"`
	URL         string `json:"url"`
	Digest      string `json:"digest"`
}

type discoveryIndex struct {
	Skills []discoverySkill `json:"skills"`
}

func main() {
	rawURL := flag.String("url", "", "技能地址")
	dest := flag.String("dest", "", "安装目录，例如 skills/product-search")
	force := flag.Bool("force", false, "本地有修改时先备份再覆盖")
	autoUpdate := flag.Bool("auto-update", true, "写入自动更新标记")
	flag.Parse()
	if strings.TrimSpace(*rawURL) == "" || strings.TrimSpace(*dest) == "" {
		fmt.Fprintln(os.Stderr, "用法: skill-sync -url https://food4agent.com/skills/name -dest skills/name")
		os.Exit(1)
	}
	indexURL, err := skillsync.IndexURL(*rawURL)
	if err != nil {
		fail(err)
	}
	sourceURL, err := skillsync.SourceURL(*rawURL)
	if err != nil {
		fail(err)
	}
	client := &http.Client{Timeout: 60 * time.Second}
	body, err := fetch(client, indexURL)
	if err != nil {
		fail(err)
	}
	var index discoveryIndex
	if err := json.Unmarshal(body, &index); err != nil || len(index.Skills) == 0 {
		fail(errors.New("技能索引无法读取"))
	}
	if len(index.Skills) != 1 {
		fail(errors.New("这个地址包含多个技能，请使用具体技能链接"))
	}
	entry := index.Skills[0]
	if entry.Type != "archive" || entry.Name == "" || !strings.HasPrefix(entry.Digest, "sha256:") {
		fail(errors.New("技能索引无效"))
	}
	archive, err := fetch(client, entry.URL)
	if err != nil {
		fail(err)
	}
	sum := sha256.Sum256(archive)
	if "sha256:"+hex.EncodeToString(sum[:]) != entry.Digest {
		fail(errors.New("技能压缩包摘要不一致"))
	}
	files, blobs, err := unzip(archive)
	if err != nil {
		fail(err)
	}
	marker := skillsync.Marker{
		Source:     "food4agent",
		Name:       entry.Name,
		SourceURL:  sourceURL,
		Version:    entry.Digest,
		AutoUpdate: *autoUpdate,
	}
	manifest := skillsync.Manifest{Name: entry.Name, Version: entry.Digest, Files: files}
	err = skillsync.Sync(*dest, marker, manifest, func(rel string) ([]byte, error) {
		body, ok := blobs[rel]
		if !ok {
			return nil, errors.New("压缩包缺少 " + rel)
		}
		return body, nil
	}, *force)
	if errors.Is(err, skillsync.ErrDirty) {
		fmt.Fprintln(os.Stderr, "本地技能有未同步修改，没有覆盖。确认后加 -force，原目录会备份。")
		os.Exit(2)
	}
	if err != nil {
		fail(err)
	}
	fmt.Printf("已同步 %s 到 %s\n", entry.Name, *dest)
}

func unzip(body []byte) ([]skillsync.File, map[string][]byte, error) {
	reader, err := zip.NewReader(bytes.NewReader(body), int64(len(body)))
	if err != nil {
		return nil, nil, errors.New("技能压缩包无法读取")
	}
	files := make([]skillsync.File, 0, len(reader.File))
	blobs := make(map[string][]byte, len(reader.File))
	for _, entry := range reader.File {
		if entry.FileInfo().IsDir() {
			continue
		}
		name := strings.TrimPrefix(strings.ReplaceAll(entry.Name, "\\", "/"), "/")
		if name == "" || strings.Contains(name, "..") {
			return nil, nil, errors.New("技能压缩包路径无效")
		}
		opened, err := entry.Open()
		if err != nil {
			return nil, nil, errors.New("技能压缩包无法读取")
		}
		data, err := io.ReadAll(io.LimitReader(opened, 32<<20))
		_ = opened.Close()
		if err != nil {
			return nil, nil, errors.New("技能压缩包无法读取")
		}
		sum := sha256.Sum256(data)
		files = append(files, skillsync.File{Path: name, SHA256: hex.EncodeToString(sum[:]), Size: len(data)})
		blobs[name] = data
	}
	return files, blobs, nil
}

func fetch(client *http.Client, rawURL string) ([]byte, error) {
	request, err := http.NewRequest(http.MethodGet, rawURL, nil)
	if err != nil {
		return nil, err
	}
	response, err := client.Do(request)
	if err != nil {
		return nil, err
	}
	defer response.Body.Close()
	body, err := io.ReadAll(io.LimitReader(response.Body, 64<<20))
	if err != nil {
		return nil, err
	}
	if response.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("读取 %s 失败: %s", rawURL, response.Status)
	}
	return body, nil
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}
