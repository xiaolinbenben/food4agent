package store

import (
	"context"
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"io"
	"strings"

	"food4agent/apps/server/internal/model"
	"gorm.io/gorm"
)

const tokenPrefix = "f4a_"

// tokenBytes 是令牌的随机部分。128 bit 在线无法猜中；用 base64url 比十六进制短。
const tokenBytes = 16

type TokenStore struct {
	db  *gorm.DB
	key string
}

func NewTokenStore(db *gorm.DB, key string) TokenStore {
	return TokenStore{db: db, key: key}
}

// Ensure 返回账号唯一的令牌。没有可用令牌时生成一个。
func (s TokenStore) Ensure(ctx context.Context, ownerID uint) (string, error) {
	var row model.SkillToken
	err := s.db.WithContext(ctx).Where("owner_id = ? AND revoked_at IS NULL", ownerID).Order("id desc").First(&row).Error
	if err == nil && row.Secret != "" {
		plain, openErr := openSecret(s.key, row.Secret)
		if openErr == nil && hashToken(plain) == row.TokenHash {
			return plain, nil
		}
	} else if err != nil && !errors.Is(err, gorm.ErrRecordNotFound) {
		return "", err
	}
	return s.Reset(ctx, ownerID)
}

// Reset 作废旧令牌并生成新的。一个账号同时只有一个令牌。
func (s TokenStore) Reset(ctx context.Context, ownerID uint) (string, error) {
	if err := s.db.WithContext(ctx).Where("owner_id = ?", ownerID).Delete(&model.SkillToken{}).Error; err != nil {
		return "", err
	}
	buf := make([]byte, tokenBytes)
	if _, err := rand.Read(buf); err != nil {
		return "", err
	}
	raw := tokenPrefix + base64.RawURLEncoding.EncodeToString(buf)
	sealed, err := sealSecret(s.key, raw)
	if err != nil {
		return "", err
	}
	row := model.SkillToken{
		OwnerID:   ownerID,
		TokenHash: hashToken(raw),
		Secret:    sealed,
		Name:      "default",
		Scope:     model.TokenScopeRead,
	}
	if err := s.db.WithContext(ctx).Create(&row).Error; err != nil {
		return "", err
	}
	return raw, nil
}

func (s TokenStore) Lookup(ctx context.Context, raw string) (model.SkillToken, error) {
	raw = strings.TrimSpace(raw)
	if !strings.HasPrefix(raw, tokenPrefix) || len(raw) < len(tokenPrefix)+22 {
		return model.SkillToken{}, ErrNotFound
	}
	var row model.SkillToken
	err := s.db.WithContext(ctx).Where("token_hash = ? AND revoked_at IS NULL", hashToken(raw)).First(&row).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return model.SkillToken{}, ErrNotFound
	}
	if err != nil {
		return model.SkillToken{}, err
	}
	if row.Scope != model.TokenScopeRead {
		return model.SkillToken{}, ErrNotFound
	}
	return row, nil
}

func (s TokenStore) Touch(ctx context.Context, id uint) error {
	return s.db.WithContext(ctx).Model(&model.SkillToken{}).Where("id = ?", id).Update("last_used_at", gorm.Expr("CURRENT_TIMESTAMP")).Error
}

func hashToken(raw string) string {
	sum := sha256.Sum256([]byte(raw))
	return hex.EncodeToString(sum[:])
}

func sealSecret(key, plain string) (string, error) {
	block, err := aes.NewCipher(hashTokenKey(key))
	if err != nil {
		return "", err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", err
	}
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(gcm.Seal(nonce, nonce, []byte(plain), nil)), nil
}

func openSecret(key, sealed string) (string, error) {
	body, err := base64.RawURLEncoding.DecodeString(sealed)
	if err != nil {
		return "", err
	}
	block, err := aes.NewCipher(hashTokenKey(key))
	if err != nil {
		return "", err
	}
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return "", err
	}
	if len(body) < gcm.NonceSize() {
		return "", errors.New("令牌无法读取")
	}
	plain, err := gcm.Open(nil, body[:gcm.NonceSize()], body[gcm.NonceSize():], nil)
	if err != nil {
		return "", err
	}
	return string(plain), nil
}

func hashTokenKey(key string) []byte {
	sum := sha256.Sum256([]byte(key))
	return sum[:]
}
