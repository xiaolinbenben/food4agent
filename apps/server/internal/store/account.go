package store

import (
	"context"
	"errors"
	"strings"
	"unicode/utf8"

	"food4agent/apps/server/internal/model"
	"food4agent/apps/server/internal/skillfs"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"
)

type AccountStore struct{ db *gorm.DB }

func NewAccountStore(db *gorm.DB) AccountStore { return AccountStore{db: db} }

var dummyHash []byte

func init() {
	hash, err := bcrypt.GenerateFromPassword([]byte("food4agent-missing-account"), bcrypt.DefaultCost)
	if err != nil {
		panic(err)
	}
	dummyHash = hash
}

func (s AccountStore) Create(ctx context.Context, userID, nickname, password string) (model.Account, error) {
	userID = skillfs.NormalizeUserID(userID)
	if !skillfs.ValidUserID(userID) {
		return model.Account{}, invalid("用户 ID 需要 1 到 39 位字母、数字或单个短横线，不能连续，也不能开头或结尾")
	}
	if skillfs.ReservedHandle(userID) {
		return model.Account{}, invalid("这个用户 ID 不能使用")
	}
	if err := checkPassword(password); err != nil {
		return model.Account{}, err
	}
	nickname = cleanLine(nickname, 80)
	if nickname == "" {
		nickname = userID
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return model.Account{}, err
	}
	account := model.Account{UserID: userID, Nickname: nickname, PasswordHash: string(hash)}
	if err := s.db.WithContext(ctx).Create(&account).Error; err != nil {
		if isConflict(err) {
			return model.Account{}, ErrConflict
		}
		return model.Account{}, err
	}
	return account, nil
}

func (s AccountStore) Authenticate(ctx context.Context, userID, password string) (model.Account, error) {
	userID = skillfs.NormalizeUserID(userID)
	account, err := s.ByUserID(ctx, userID)
	if err != nil {
		_ = bcrypt.CompareHashAndPassword(dummyHash, []byte(password))
		if errors.Is(err, ErrNotFound) {
			return model.Account{}, ErrUnauthorized
		}
		return model.Account{}, err
	}
	if bcrypt.CompareHashAndPassword([]byte(account.PasswordHash), []byte(password)) != nil {
		return model.Account{}, ErrUnauthorized
	}
	return account, nil
}

func (s AccountStore) ByUserID(ctx context.Context, userID string) (model.Account, error) {
	var account model.Account
	err := s.db.WithContext(ctx).Where("user_id = ?", userID).First(&account).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return model.Account{}, ErrNotFound
	}
	return account, err
}

func (s AccountStore) ByID(ctx context.Context, id uint) (model.Account, error) {
	var account model.Account
	err := s.db.WithContext(ctx).First(&account, id).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return model.Account{}, ErrNotFound
	}
	return account, err
}

func checkPassword(password string) error {
	if utf8.RuneCountInString(password) < 8 {
		return invalid("密码至少 8 位")
	}
	if len(password) > 72 {
		return invalid("密码最长 72 字节")
	}
	return nil
}

func cleanLine(value string, max int) string {
	value = strings.Join(strings.Fields(value), " ")
	runes := []rune(value)
	if len(runes) > max {
		return string(runes[:max])
	}
	return value
}
