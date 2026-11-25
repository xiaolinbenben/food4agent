package model

import "time"

const (
	VisibilityPublic  = "public"
	VisibilityPrivate = "private"
	TokenScopeRead    = "read"
	SourcePrivate     = "food4agent_private"
	SourcePublic      = "food4agent_public"
)

// Account 是 Skill 的所有者。UserID 是地址里的用户 ID，创建后保持稳定。Nickname 可以改。Email 先留空。
type Account struct {
	ID           uint   `gorm:"primaryKey"`
	UserID       string `gorm:"size:39;uniqueIndex;not null"`
	Nickname     string `gorm:"size:80;not null"`
	Email        string `gorm:"size:255;not null;default:''"`
	AvatarURL    string `gorm:"size:500;not null"`
	PasswordHash string `gorm:"size:100;not null"`
	CreatedAt    time.Time
	UpdatedAt    time.Time
}

func (Account) TableName() string { return "accounts" }

// Skill 直接归属于一个账号。同一账号下名称唯一，不同账号可以同名。
type Skill struct {
	ID                 uint   `gorm:"primaryKey"`
	OwnerID            uint   `gorm:"not null;uniqueIndex:owner_skill_name"`
	Name               string `gorm:"size:32;not null;uniqueIndex:owner_skill_name"`
	DisplayName        string `gorm:"size:80;not null"`
	Description        string `gorm:"size:280;not null"`
	Visibility         string `gorm:"size:16;not null"`
	CurrentContentHash string `gorm:"size:64;not null"`
	CreatedAt          time.Time
	UpdatedAt          time.Time
}

func (Skill) TableName() string { return "skills" }

// SkillDraft 是可修改的当前草稿。已发布版本不写回这里。
type SkillDraft struct {
	ID        uint   `gorm:"primaryKey"`
	SkillID   uint   `gorm:"uniqueIndex;not null"`
	Files     string `gorm:"not null"`
	Manifest  string `gorm:"not null"`
	UpdatedBy uint   `gorm:"not null"`
	CreatedAt time.Time
	UpdatedAt time.Time
}

func (SkillDraft) TableName() string { return "skill_drafts" }

// SkillVersion 是一次发布。ContentHash 相同的内容只保留一份，不能改写。
type SkillVersion struct {
	ID          uint   `gorm:"primaryKey"`
	SkillID     uint   `gorm:"not null;uniqueIndex:skill_content_hash"`
	ContentHash string `gorm:"size:64;not null;uniqueIndex:skill_content_hash"`
	Manifest    string `gorm:"not null"`
	Changelog   string `gorm:"size:500;not null"`
	PublishedBy uint   `gorm:"not null"`
	PublishedAt time.Time
}

func (SkillVersion) TableName() string { return "skill_versions" }

// SkillToken 只保存 Skill Key 的哈希。完整 Key 只在创建时返回一次。
type SkillToken struct {
	ID         uint   `gorm:"primaryKey"`
	OwnerID    uint   `gorm:"not null;index"`
	TokenHash  string `gorm:"size:64;uniqueIndex;not null"`
	Secret     string `gorm:"not null;default:''"`
	Name       string `gorm:"size:80;not null"`
	Scope      string `gorm:"size:32;not null"`
	LastUsedAt *time.Time
	ExpiresAt  *time.Time
	RevokedAt  *time.Time
	CreatedAt  time.Time
}

func (SkillToken) TableName() string { return "skill_tokens" }

// SkillInstallation 记录客户端上报的安装位置，不代替本地的 .terln-skill.json。
type SkillInstallation struct {
	ID               uint   `gorm:"primaryKey"`
	OwnerID          uint   `gorm:"not null;index"`
	SkillID          uint   `gorm:"not null;index"`
	Source           string `gorm:"size:32;not null"`
	InstalledVersion string `gorm:"size:80;not null"`
	LocalPath        string `gorm:"size:500;not null"`
	AutoUpdate       bool   `gorm:"not null"`
	LastCheckedAt    *time.Time
	CreatedAt        time.Time
	UpdatedAt        time.Time
}

func (SkillInstallation) TableName() string { return "skill_installations" }
