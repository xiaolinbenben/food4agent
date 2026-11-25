package store

import (
	"errors"
	"strings"
)

var (
	ErrUnauthorized = errors.New("unauthorized")
	ErrConflict     = errors.New("conflict")
	ErrNotFound     = errors.New("not found")
)

type InvalidError struct{ Message string }

func (e *InvalidError) Error() string { return e.Message }

func invalid(message string) error { return &InvalidError{Message: message} }

func isConflict(err error) bool {
	return err != nil && strings.Contains(strings.ToLower(err.Error()), "unique")
}
