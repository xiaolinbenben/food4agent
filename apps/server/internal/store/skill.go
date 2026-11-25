package store

import (
	"context"
	"errors"
	"strings"
	"time"
	"unicode/utf8"

	"food4agent/apps/server/internal/model"
	"food4agent/apps/server/internal/skillfs"
	"gorm.io/gorm"
)

type SkillStore struct {
	db    *gorm.DB
	files skillfs.Dir
}

func NewSkillStore(db *gorm.DB, root string) SkillStore {
	return SkillStore{db: db, files: skillfs.Dir{Root: root}}
}

type SkillSummary struct {
	Name               string    `json:"name"`
	DisplayName        string    `json:"display_name"`
	Description        string    `json:"description"`
	Visibility         string    `json:"visibility"`
	CurrentContentHash string    `json:"current_content_hash"`
	Version            string    `json:"version"`
	Dirty              bool      `json:"dirty"`
	UpdatedAt          time.Time `json:"updated_at"`
}

type SkillFileView struct {
	Path    string `json:"path"`
	SHA256  string `json:"sha256"`
	Size    int    `json:"size"`
	Content string `json:"content,omitempty"`
	Binary  bool   `json:"binary,omitempty"`
}

type SkillChange struct {
	Path   string `json:"path"`
	Status string `json:"status"`
}

type SkillDetail struct {
	Skill   SkillSummary    `json:"skill"`
	Files   []SkillFileView `json:"files"`
	Changes []SkillChange   `json:"changes"`
}

type DraftInput struct {
	Path    string `json:"path"`
	Content string `json:"content"`
	Binary  bool   `json:"binary"`
}

type VersionView struct {
	ContentHash string    `json:"content_hash"`
	Version     string    `json:"version"`
	Changelog   string    `json:"changelog"`
	PublishedAt time.Time `json:"published_at"`
}

func (s SkillStore) Create(ctx context.Context, owner model.Account, name, displayName, description, visibility string, zip []byte) (SkillDetail, error) {
	name = skillfs.NormalizeSlug(name)
	if !skillfs.ValidSlug(name) || skillfs.ReservedSkillName(name) {
		return SkillDetail{}, invalid("技能标识需要 2 到 32 位小写字母、数字或短横线")
	}
	displayName = cleanLine(displayName, 80)
	if displayName == "" {
		displayName = name
	}
	description = cleanLine(description, 280)
	visibility, err := normalizeVisibility(visibility)
	if err != nil {
		return SkillDetail{}, err
	}
	var files []skillfs.File
	if len(zip) > 0 {
		files, err = skillfs.ReadZip(zip)
		if err != nil {
			return SkillDetail{}, invalid(err.Error())
		}
		if err := skillfs.RequireSkillMarkdown(name, files); err != nil {
			return SkillDetail{}, invalid(err.Error())
		}
	} else {
		if description == "" {
			description = displayName
		}
		files = []skillfs.File{{Path: "SKILL.md", Data: []byte(blankSkill(name, description, displayName)), Mode: 0o644}}
	}
	skill := model.Skill{
		OwnerID: owner.ID, Name: name, DisplayName: displayName,
		Description: description, Visibility: visibility,
	}
	err = s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if err := tx.Create(&skill).Error; err != nil {
			return err
		}
		draft := model.SkillDraft{SkillID: skill.ID, Files: "[]", Manifest: "{}", UpdatedBy: owner.ID}
		return tx.Create(&draft).Error
	})
	if isConflict(err) {
		return SkillDetail{}, ErrConflict
	}
	if err != nil {
		return SkillDetail{}, err
	}
	if err := s.saveDraftFiles(ctx, owner.ID, skill, files); err != nil {
		_ = s.db.WithContext(ctx).Delete(&model.SkillDraft{}, "skill_id = ?", skill.ID).Error
		_ = s.db.WithContext(ctx).Delete(&model.Skill{}, skill.ID).Error
		return SkillDetail{}, err
	}
	return s.Detail(ctx, owner.ID, name)
}

func (s SkillStore) List(ctx context.Context, ownerID uint) ([]SkillSummary, error) {
	var rows []model.Skill
	if err := s.db.WithContext(ctx).Where("owner_id = ?", ownerID).Order("updated_at desc").Find(&rows).Error; err != nil {
		return nil, err
	}
	out := make([]SkillSummary, 0, len(rows))
	for _, row := range rows {
		item, err := s.summary(ctx, row)
		if err != nil {
			return nil, err
		}
		out = append(out, item)
	}
	return out, nil
}

func (s SkillStore) Detail(ctx context.Context, ownerID uint, name string) (SkillDetail, error) {
	skill, err := s.owned(ctx, ownerID, name)
	if err != nil {
		return SkillDetail{}, err
	}
	files, err := s.files.Read(s.files.Draft(skill.OwnerID, skill.ID))
	if err != nil {
		return SkillDetail{}, err
	}
	summary, err := s.summary(ctx, skill)
	if err != nil {
		return SkillDetail{}, err
	}
	published, err := s.publishedFiles(ctx, skill)
	if err != nil {
		return SkillDetail{}, err
	}
	return SkillDetail{Skill: summary, Files: views(files), Changes: changes(published, files)}, nil
}

func (s SkillStore) SaveDraft(ctx context.Context, ownerID uint, name string, inputs []DraftInput) (SkillDetail, error) {
	skill, err := s.owned(ctx, ownerID, name)
	if err != nil {
		return SkillDetail{}, err
	}
	existing, err := s.files.Read(s.files.Draft(skill.OwnerID, skill.ID))
	if err != nil {
		return SkillDetail{}, err
	}
	byPath := map[string]skillfs.File{}
	for _, file := range existing {
		byPath[file.Path] = file
	}
	if len(inputs) > skillfs.MaxFiles {
		return SkillDetail{}, invalid("文件数量过多")
	}
	files := make([]skillfs.File, 0, len(inputs))
	seen := map[string]struct{}{}
	for _, input := range inputs {
		if err := skillfs.ValidateRelPath(input.Path); err != nil {
			return SkillDetail{}, invalid(err.Error())
		}
		if _, ok := seen[input.Path]; ok {
			return SkillDetail{}, invalid("文件路径重复")
		}
		seen[input.Path] = struct{}{}
		if input.Binary {
			file, ok := byPath[input.Path]
			if !ok {
				return SkillDetail{}, invalid("草稿里没有这个二进制文件")
			}
			files = append(files, file)
			continue
		}
		if len(input.Content) > skillfs.MaxTextBytes || !utf8.ValidString(input.Content) {
			return SkillDetail{}, invalid("文本文件过大或不是 UTF-8")
		}
		files = append(files, skillfs.File{Path: input.Path, Data: []byte(input.Content), Mode: 0o644})
	}
	if body, ok := skillfs.SkillMarkdown(files); ok {
		if got, present := skillfs.FrontmatterValue(body, "name"); present && got != skill.Name {
			return SkillDetail{}, invalid("SKILL.md 的 name 必须等于技能标识")
		}
	}
	if err := s.saveDraftFiles(ctx, ownerID, skill, files); err != nil {
		if _, ok := err.(*InvalidError); ok {
			return SkillDetail{}, err
		}
		return SkillDetail{}, err
	}
	return s.Detail(ctx, ownerID, skill.Name)
}

func (s SkillStore) Upload(ctx context.Context, ownerID uint, name string, zip []byte) (SkillDetail, error) {
	skill, err := s.owned(ctx, ownerID, name)
	if err != nil {
		return SkillDetail{}, err
	}
	files, err := skillfs.ReadZip(zip)
	if err != nil {
		return SkillDetail{}, invalid(err.Error())
	}
	if err := skillfs.RequireSkillMarkdown(skill.Name, files); err != nil {
		return SkillDetail{}, invalid(err.Error())
	}
	if err := s.saveDraftFiles(ctx, ownerID, skill, files); err != nil {
		return SkillDetail{}, err
	}
	return s.Detail(ctx, ownerID, skill.Name)
}

func (s SkillStore) Publish(ctx context.Context, ownerID uint, name, changelog string) (VersionView, error) {
	skill, err := s.owned(ctx, ownerID, name)
	if err != nil {
		return VersionView{}, err
	}
	files, err := s.files.Read(s.files.Draft(skill.OwnerID, skill.ID))
	if err != nil {
		return VersionView{}, err
	}
	if err := skillfs.RequireSkillMarkdown(skill.Name, files); err != nil {
		return VersionView{}, invalid(err.Error())
	}
	hash, manifestFiles, err := skillfs.ContentHash(files)
	if err != nil {
		return VersionView{}, invalid(err.Error())
	}
	changelog = cleanBlock(changelog, 500)
	description := skill.Description
	if body, ok := skillfs.SkillMarkdown(files); ok {
		if value, present := skillfs.FrontmatterValue(body, "description"); present {
			if value = cleanLine(value, 280); value != "" {
				description = value
			}
		}
	}
	if err := s.files.WriteNew(s.files.Version(skill.OwnerID, skill.ID, hash), files); err != nil {
		return VersionView{}, err
	}
	manifest, err := skillfs.EncodeManifest(skillfs.NewManifest(skill.Name, hash, manifestFiles))
	if err != nil {
		return VersionView{}, err
	}
	publishedAt := time.Now()
	err = s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		var existing model.SkillVersion
		findErr := tx.Where("skill_id = ? AND content_hash = ?", skill.ID, hash).First(&existing).Error
		if errors.Is(findErr, gorm.ErrRecordNotFound) {
			row := model.SkillVersion{
				SkillID: skill.ID, ContentHash: hash, Manifest: manifest,
				Changelog: changelog, PublishedBy: ownerID, PublishedAt: publishedAt,
			}
			if err := tx.Create(&row).Error; err != nil {
				return err
			}
		} else if findErr != nil {
			return findErr
		} else {
			publishedAt = existing.PublishedAt
		}
		return tx.Model(&model.Skill{}).Where("id = ?", skill.ID).Updates(map[string]any{
			"current_content_hash": hash,
			"description":          description,
		}).Error
	})
	if err != nil {
		return VersionView{}, err
	}
	skill.CurrentContentHash = hash
	if err := s.pruneVersions(ctx, skill); err != nil {
		return VersionView{}, err
	}
	return VersionView{ContentHash: hash, Version: "sha256:" + hash, Changelog: changelog, PublishedAt: publishedAt}, nil
}

const keptVersions = 10

func (s SkillStore) pruneVersions(ctx context.Context, skill model.Skill) error {
	var rows []model.SkillVersion
	if err := s.db.WithContext(ctx).Where("skill_id = ?", skill.ID).Order("published_at desc, id desc").Find(&rows).Error; err != nil {
		return err
	}
	if len(rows) <= keptVersions {
		return nil
	}
	for _, row := range rows[keptVersions:] {
		if row.ContentHash == skill.CurrentContentHash {
			continue
		}
		if err := s.db.WithContext(ctx).Delete(&model.SkillVersion{}, row.ID).Error; err != nil {
			return err
		}
		if err := s.files.Remove(s.files.Version(skill.OwnerID, skill.ID, row.ContentHash)); err != nil {
			return err
		}
	}
	return nil
}

func (s SkillStore) Versions(ctx context.Context, ownerID uint, name string) ([]VersionView, error) {
	skill, err := s.owned(ctx, ownerID, name)
	if err != nil {
		return nil, err
	}
	var rows []model.SkillVersion
	if err := s.db.WithContext(ctx).Where("skill_id = ?", skill.ID).Order("published_at desc, id desc").Find(&rows).Error; err != nil {
		return nil, err
	}
	out := make([]VersionView, 0, len(rows))
	for _, row := range rows {
		out = append(out, VersionView{
			ContentHash: row.ContentHash,
			Version:     "sha256:" + row.ContentHash,
			Changelog:   row.Changelog,
			PublishedAt: row.PublishedAt,
		})
	}
	return out, nil
}

func (s SkillStore) Rollback(ctx context.Context, ownerID uint, name, hash string) error {
	skill, err := s.owned(ctx, ownerID, name)
	if err != nil {
		return err
	}
	hash = strings.TrimPrefix(strings.TrimSpace(hash), "sha256:")
	var version model.SkillVersion
	err = s.db.WithContext(ctx).Where("skill_id = ? AND content_hash = ?", skill.ID, hash).First(&version).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return ErrNotFound
	}
	if err != nil {
		return err
	}
	return s.db.WithContext(ctx).Model(&model.Skill{}).Where("id = ?", skill.ID).Update("current_content_hash", version.ContentHash).Error
}

func (s SkillStore) FindPublished(ctx context.Context, handle, name string) (model.Skill, error) {
	var skill model.Skill
	err := s.db.WithContext(ctx).
		Joins("join accounts on accounts.id = skills.owner_id").
		Where("accounts.user_id = ? AND skills.name = ?", handle, name).
		First(&skill).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return model.Skill{}, ErrNotFound
	}
	return skill, err
}

func (s SkillStore) ReadPublished(ctx context.Context, skill model.Skill) ([]skillfs.File, error) {
	if skill.CurrentContentHash == "" {
		return nil, ErrNotFound
	}
	files, err := s.files.Read(s.files.Version(skill.OwnerID, skill.ID, skill.CurrentContentHash))
	if err != nil {
		return nil, err
	}
	if len(files) == 0 {
		return nil, ErrNotFound
	}
	return files, nil
}

func (s SkillStore) Open(ctx context.Context, skill model.Skill, hash, rel string) ([]byte, error) {
	hash = strings.TrimPrefix(hash, "sha256:")
	if hash == "" {
		hash = skill.CurrentContentHash
	}
	if hash == "" || !skillfs.ContentHashPath(hash) {
		return nil, ErrNotFound
	}
	var version model.SkillVersion
	err := s.db.WithContext(ctx).Where("skill_id = ? AND content_hash = ?", skill.ID, hash).First(&version).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, ErrNotFound
	}
	if err != nil {
		return nil, err
	}
	if rel == "manifest.json" {
		return []byte(version.Manifest), nil
	}
	if err := skillfs.ValidateRelPath(rel); err != nil {
		return nil, ErrNotFound
	}
	data, err := s.files.ReadFile(s.files.Version(skill.OwnerID, skill.ID, hash), rel)
	if err != nil {
		return nil, ErrNotFound
	}
	return data, nil
}

type InstallationInput struct {
	SkillName        string
	Source           string
	InstalledVersion string
	LocalPath        string
	AutoUpdate       bool
}

type InstallationView struct {
	SkillName        string     `json:"skill_name"`
	Source           string     `json:"source"`
	InstalledVersion string     `json:"installed_version"`
	LocalPath        string     `json:"local_path"`
	AutoUpdate       bool       `json:"auto_update"`
	LastCheckedAt    *time.Time `json:"last_checked_at"`
}

func (s SkillStore) SaveInstallation(ctx context.Context, ownerID uint, input InstallationInput) (InstallationView, error) {
	if input.Source != model.SourcePrivate && input.Source != model.SourcePublic {
		return InstallationView{}, invalid("安装来源无效")
	}
	input.LocalPath = strings.TrimSpace(input.LocalPath)
	input.InstalledVersion = strings.TrimSpace(input.InstalledVersion)
	if input.LocalPath == "" || len(input.LocalPath) > 500 || strings.ContainsRune(input.LocalPath, 0) {
		return InstallationView{}, invalid("本地路径无效")
	}
	if input.InstalledVersion == "" || len(input.InstalledVersion) > 80 {
		return InstallationView{}, invalid("安装版本无效")
	}
	skill, err := s.owned(ctx, ownerID, skillfs.NormalizeSlug(input.SkillName))
	if err != nil {
		return InstallationView{}, err
	}
	now := time.Now()
	var row model.SkillInstallation
	err = s.db.WithContext(ctx).Where("owner_id = ? AND skill_id = ? AND local_path = ?", ownerID, skill.ID, input.LocalPath).First(&row).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		row = model.SkillInstallation{
			OwnerID: ownerID, SkillID: skill.ID, Source: input.Source,
			InstalledVersion: input.InstalledVersion, LocalPath: input.LocalPath,
			AutoUpdate: input.AutoUpdate, LastCheckedAt: &now,
		}
		if err := s.db.WithContext(ctx).Create(&row).Error; err != nil {
			return InstallationView{}, err
		}
	} else if err != nil {
		return InstallationView{}, err
	} else {
		row.Source = input.Source
		row.InstalledVersion = input.InstalledVersion
		row.AutoUpdate = input.AutoUpdate
		row.LastCheckedAt = &now
		if err := s.db.WithContext(ctx).Save(&row).Error; err != nil {
			return InstallationView{}, err
		}
	}
	return InstallationView{
		SkillName: skill.Name, Source: row.Source, InstalledVersion: row.InstalledVersion,
		LocalPath: row.LocalPath, AutoUpdate: row.AutoUpdate, LastCheckedAt: row.LastCheckedAt,
	}, nil
}

func (s SkillStore) Installations(ctx context.Context, ownerID uint) ([]InstallationView, error) {
	var rows []model.SkillInstallation
	if err := s.db.WithContext(ctx).Where("owner_id = ?", ownerID).Order("updated_at desc").Find(&rows).Error; err != nil {
		return nil, err
	}
	out := make([]InstallationView, 0, len(rows))
	for _, row := range rows {
		var skill model.Skill
		if err := s.db.WithContext(ctx).First(&skill, row.SkillID).Error; err != nil {
			return nil, err
		}
		out = append(out, InstallationView{
			SkillName: skill.Name, Source: row.Source, InstalledVersion: row.InstalledVersion,
			LocalPath: row.LocalPath, AutoUpdate: row.AutoUpdate, LastCheckedAt: row.LastCheckedAt,
		})
	}
	return out, nil
}

func (s SkillStore) saveDraftFiles(ctx context.Context, ownerID uint, skill model.Skill, files []skillfs.File) error {
	hash, manifestFiles, err := skillfs.ContentHash(files)
	if err != nil {
		return invalid(err.Error())
	}
	manifest, err := skillfs.EncodeManifest(skillfs.NewManifest(skill.Name, hash, manifestFiles))
	if err != nil {
		return err
	}
	encoded, err := skillfs.EncodeFiles(manifestFiles)
	if err != nil {
		return err
	}
	if err := s.files.Write(s.files.Draft(skill.OwnerID, skill.ID), files); err != nil {
		return err
	}
	return s.db.WithContext(ctx).Model(&model.SkillDraft{}).Where("skill_id = ?", skill.ID).Updates(map[string]any{
		"files":      encoded,
		"manifest":   manifest,
		"updated_by": ownerID,
	}).Error
}

func (s SkillStore) owned(ctx context.Context, ownerID uint, name string) (model.Skill, error) {
	name = skillfs.NormalizeSlug(name)
	var skill model.Skill
	err := s.db.WithContext(ctx).Where("owner_id = ? AND name = ?", ownerID, name).First(&skill).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return model.Skill{}, ErrNotFound
	}
	return skill, err
}

func (s SkillStore) summary(ctx context.Context, skill model.Skill) (SkillSummary, error) {
	files, err := s.files.Read(s.files.Draft(skill.OwnerID, skill.ID))
	if err != nil {
		return SkillSummary{}, err
	}
	hash, _, err := skillfs.ContentHash(files)
	if err != nil {
		return SkillSummary{}, err
	}
	version := ""
	if skill.CurrentContentHash != "" {
		version = "sha256:" + skill.CurrentContentHash
	}
	return SkillSummary{
		Name: skill.Name, DisplayName: skill.DisplayName, Description: skill.Description,
		Visibility: skill.Visibility, CurrentContentHash: skill.CurrentContentHash,
		Version: version, Dirty: hash != skill.CurrentContentHash, UpdatedAt: skill.UpdatedAt,
	}, nil
}

func (s SkillStore) publishedFiles(ctx context.Context, skill model.Skill) ([]skillfs.File, error) {
	if skill.CurrentContentHash == "" {
		return nil, nil
	}
	var version model.SkillVersion
	err := s.db.WithContext(ctx).Where("skill_id = ? AND content_hash = ?", skill.ID, skill.CurrentContentHash).First(&version).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	manifest, err := skillfs.DecodeManifest(version.Manifest)
	if err != nil {
		return nil, err
	}
	files := make([]skillfs.File, 0, len(manifest.Files))
	for _, file := range manifest.Files {
		files = append(files, skillfs.File{Path: file.Path})
		files[len(files)-1].Data = []byte(file.SHA256)
	}
	return files, nil
}

func changes(published, draft []skillfs.File) []SkillChange {
	old := map[string]string{}
	for _, file := range published {
		old[file.Path] = string(file.Data)
	}
	_, manifestFiles, err := skillfs.ContentHash(draft)
	next := map[string]string{}
	if err == nil {
		for _, file := range manifestFiles {
			next[file.Path] = file.SHA256
		}
	}
	paths := map[string]struct{}{}
	for path := range old {
		paths[path] = struct{}{}
	}
	for path := range next {
		paths[path] = struct{}{}
	}
	out := []SkillChange{}
	names := make([]string, 0, len(paths))
	for path := range paths {
		names = append(names, path)
	}
	sortStrings(names)
	for _, path := range names {
		oldHash, inOld := old[path]
		newHash, inNew := next[path]
		switch {
		case inOld && !inNew:
			out = append(out, SkillChange{Path: path, Status: "removed"})
		case !inOld && inNew:
			out = append(out, SkillChange{Path: path, Status: "added"})
		case oldHash != newHash:
			out = append(out, SkillChange{Path: path, Status: "modified"})
		}
	}
	return out
}

func views(files []skillfs.File) []SkillFileView {
	_, manifestFiles, err := skillfs.ContentHash(files)
	if err != nil {
		manifestFiles = nil
	}
	meta := map[string]skillfs.ManifestFile{}
	for _, file := range manifestFiles {
		meta[file.Path] = file
	}
	out := make([]SkillFileView, 0, len(files))
	for _, file := range files {
		item := SkillFileView{Path: file.Path, SHA256: meta[file.Path].SHA256, Size: len(file.Data)}
		if isText(file.Data) {
			item.Content = string(file.Data)
		} else {
			item.Binary = true
		}
		out = append(out, item)
	}
	return out
}

func isText(body []byte) bool {
	if len(body) > skillfs.MaxTextBytes {
		return false
	}
	for _, b := range body {
		if b == 0 {
			return false
		}
	}
	return utf8.Valid(body)
}

func normalizeVisibility(value string) (string, error) {
	value = strings.ToLower(strings.TrimSpace(value))
	if value == "" {
		return model.VisibilityPrivate, nil
	}
	if value != model.VisibilityPublic && value != model.VisibilityPrivate {
		return "", invalid("可见性只能是 public 或 private")
	}
	return value, nil
}

func blankSkill(name, description, display string) string {
	return "---\nname: " + name + "\ndescription: " + description + "\n---\n\n# " + display + "\n"
}

func sortStrings(values []string) {
	for i := 1; i < len(values); i++ {
		for j := i; j > 0 && values[j] < values[j-1]; j-- {
			values[j], values[j-1] = values[j-1], values[j]
		}
	}
}

func cleanBlock(value string, max int) string {
	value = strings.ReplaceAll(value, "\r\n", "\n")
	lines := strings.Split(value, "\n")
	for i, line := range lines {
		lines[i] = strings.Join(strings.Fields(line), " ")
	}
	value = strings.TrimSpace(strings.Join(lines, "\n"))
	runes := []rune(value)
	if len(runes) > max {
		return string(runes[:max])
	}
	return value
}
