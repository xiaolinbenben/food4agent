package skillfs

import (
	"archive/zip"
	"bytes"
	"errors"
	"io"
	"os"
	"strings"
)

// ReadZip 解压技能包。单层根目录会被去掉。不执行压缩包里的任何文件。
func ReadZip(body []byte) ([]File, error) {
	if len(body) == 0 || len(body) > MaxZipBytes {
		return nil, errors.New("压缩包大小无效")
	}
	reader, err := zip.NewReader(bytes.NewReader(body), int64(len(body)))
	if err != nil {
		return nil, errors.New("压缩包无法读取")
	}
	files := make([]File, 0, len(reader.File))
	total := 0
	for _, entry := range reader.File {
		if entry.Flags&0x1 != 0 {
			return nil, errors.New("不支持加密压缩包")
		}
		info := entry.FileInfo()
		if info.IsDir() {
			continue
		}
		if info.Mode()&os.ModeSymlink != 0 {
			return nil, errors.New("压缩包不能包含符号链接")
		}
		name := strings.TrimPrefix(strings.ReplaceAll(entry.Name, "\\", "/"), "/")
		if skipZipEntry(name) {
			continue
		}
		if err := validateZipName(name); err != nil {
			return nil, err
		}
		if len(files) >= MaxFiles {
			return nil, errors.New("文件数量过多")
		}
		reader, err := entry.Open()
		if err != nil {
			return nil, errors.New("压缩包无法读取")
		}
		data, err := io.ReadAll(io.LimitReader(reader, MaxFileBytes+1))
		_ = reader.Close()
		if err != nil {
			return nil, errors.New("压缩包无法读取")
		}
		if len(data) > MaxFileBytes {
			return nil, errors.New("文件过大")
		}
		total += len(data)
		if total > MaxTreeBytes {
			return nil, errors.New("技能文件总大小过大")
		}
		mode := uint32(0o644)
		if info.Mode()&0o111 != 0 {
			mode = 0o755
		}
		files = append(files, File{Path: name, Data: data, Mode: mode})
	}
	files = stripSharedRoot(files)
	for i := range files {
		if err := ValidateRelPath(files[i].Path); err != nil {
			return nil, err
		}
	}
	if _, _, err := ContentHash(files); err != nil {
		return nil, err
	}
	return files, nil
}

func skipZipEntry(name string) bool {
	for _, part := range strings.Split(name, "/") {
		if part == "__MACOSX" || part == ".DS_Store" {
			return true
		}
	}
	return false
}

func validateZipName(name string) error {
	if name == "" || strings.Contains(name, "\\") || strings.ContainsRune(name, 0) || strings.HasPrefix(name, "/") {
		return errors.New("文件路径无效")
	}
	for _, part := range strings.Split(name, "/") {
		if part == "" || part == "." || part == ".." || strings.HasPrefix(part, ".") {
			return errors.New("文件路径无效")
		}
		if part == "node_modules" || part == ".git" {
			return errors.New("文件路径无效")
		}
	}
	return nil
}

func stripSharedRoot(files []File) []File {
	if len(files) == 0 {
		return files
	}
	top := ""
	for _, file := range files {
		name, rest, ok := strings.Cut(file.Path, "/")
		if !ok || rest == "" {
			return files
		}
		if top == "" {
			top = name
		}
		if name != top {
			return files
		}
	}
	out := make([]File, len(files))
	for i, file := range files {
		_, rest, _ := strings.Cut(file.Path, "/")
		out[i] = File{Path: rest, Data: file.Data, Mode: file.Mode}
	}
	return out
}
