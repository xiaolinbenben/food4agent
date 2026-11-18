.PHONY: install web-install admin-install web-dev admin-dev server-dev web-build admin-build server-build linux-build test build deploy

install: web-install admin-install

web-install:
	cd web && pnpm install --frozen-lockfile

admin-install:
	cd admin && pnpm install --frozen-lockfile

web-dev:
	cd web && pnpm run dev

admin-dev:
	cd admin && pnpm run dev

server-dev:
	@set -a; if [ -f deploy/.env ]; then . ./deploy/.env; fi; set +a; cd server && go run ./cmd/server

web-build:
	cd web && pnpm run typecheck && pnpm run build

admin-build:
	cd admin && pnpm run typecheck && pnpm run build

server-build:
	cd server && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o bin/server ./cmd/server

linux-build: web-build admin-build
	cd server && CGO_ENABLED=0 GOOS=linux GOARCH=$${GOARCH:-amd64} go build -trimpath -ldflags="-s -w" -o bin/food4agent-linux-$${GOARCH:-amd64} ./cmd/server

test:
	cd server && go test ./...

build: web-build admin-build server-build

deploy:
	@test -n "$(HOST)" || { echo "用法: make deploy HOST=user@host"; exit 1; }
	deploy/deploy.sh "$(HOST)"
