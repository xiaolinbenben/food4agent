package skillfs

import (
	"bytes"
	"encoding/binary"
	"errors"
	"hash/crc32"
	"sort"
)

// Zip 把技能文件打成未压缩的 zip。文件按路径排序，时间戳固定，同一内容总是得到同一个包。
// SKILL.md 在压缩包根目录。
func Zip(files []File) ([]byte, error) {
	sorted := append([]File(nil), files...)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i].Path < sorted[j].Path })
	var body bytes.Buffer
	type entry struct {
		name   string
		crc    uint32
		size   uint32
		offset uint32
	}
	entries := make([]entry, 0, len(sorted))
	for _, file := range sorted {
		if err := ValidateRelPath(file.Path); err != nil {
			return nil, err
		}
		if len(file.Data) > int(^uint32(0)) {
			return nil, errors.New("文件过大")
		}
		size := uint32(len(file.Data))
		item := entry{
			name:   file.Path,
			crc:    crc32.ChecksumIEEE(file.Data),
			size:   size,
			offset: uint32(body.Len()),
		}
		writeLocal(&body, item.name, item.crc, item.size)
		body.Write(file.Data)
		entries = append(entries, item)
	}
	directory := uint32(body.Len())
	for _, item := range entries {
		writeCentral(&body, item.name, item.crc, item.size, item.offset)
	}
	writeEnd(&body, uint16(len(entries)), uint32(body.Len())-directory, directory)
	return body.Bytes(), nil
}

func writeLocal(body *bytes.Buffer, name string, sum, size uint32) {
	header := make([]byte, 30)
	binary.LittleEndian.PutUint32(header[0:], 0x04034b50)
	binary.LittleEndian.PutUint16(header[4:], 20)
	binary.LittleEndian.PutUint32(header[14:], sum)
	binary.LittleEndian.PutUint32(header[18:], size)
	binary.LittleEndian.PutUint32(header[22:], size)
	binary.LittleEndian.PutUint16(header[26:], uint16(len(name)))
	body.Write(header)
	body.WriteString(name)
}

func writeCentral(body *bytes.Buffer, name string, sum, size, offset uint32) {
	header := make([]byte, 46)
	binary.LittleEndian.PutUint32(header[0:], 0x02014b50)
	binary.LittleEndian.PutUint16(header[4:], 20)
	binary.LittleEndian.PutUint16(header[6:], 20)
	binary.LittleEndian.PutUint32(header[16:], sum)
	binary.LittleEndian.PutUint32(header[20:], size)
	binary.LittleEndian.PutUint32(header[24:], size)
	binary.LittleEndian.PutUint16(header[28:], uint16(len(name)))
	binary.LittleEndian.PutUint32(header[42:], offset)
	body.Write(header)
	body.WriteString(name)
}

func writeEnd(body *bytes.Buffer, count uint16, size, offset uint32) {
	header := make([]byte, 22)
	binary.LittleEndian.PutUint32(header[0:], 0x06054b50)
	binary.LittleEndian.PutUint16(header[8:], count)
	binary.LittleEndian.PutUint16(header[10:], count)
	binary.LittleEndian.PutUint32(header[12:], size)
	binary.LittleEndian.PutUint32(header[16:], offset)
	body.Write(header)
}
