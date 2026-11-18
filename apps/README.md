# food4agent apps

全栈站点，架构与 [fullstack-app-template](https://github.com/xiaolinbenben/fullstack-app-template) 相同。命令在 `apps/` 目录里执行。

公共首页是 food4agent 的落地页：BoldKit neobrutalism 组件，介绍框架对齐「一句话价值、接入入口、三步、能力、使用方式、常见问题」。管理端仍是 `admin` / `admin123`，账号写在首页上。

本地地址：

- 公共前端：<http://localhost:3000/>
- 管理端：<http://localhost:5173/admin/>
- Go 服务：<http://localhost:8888/>

## 技术栈

- 公共前端：React + Vite + TypeScript + Tailwind CSS v4 + BoldKit
- 管理端：React + Vite + Ant Design + `@ant-design/pro-components`
- 后端：Go + Gin + GORM + SQLite
- 部署：一个 Linux 二进制，SSH 上传后由 systemd 启动

开发时前后端分开运行。部署时 `go:embed` 把两套前端打进同一个二进制。数据库是进程旁边的 SQLite 文件。

## 项目结构

```text
web/                    # 公共前端，访问 /
admin/                  # 管理端，访问 /admin/
server/cmd/server/      # Go 程序入口
server/internal/config/ # 环境变量配置
server/internal/database/ # GORM 连接和迁移
server/internal/model/  # GORM 模型
server/internal/store/  # 查询
server/internal/httpapi/ # Gin 路由和静态资源
server/internal/middleware/
server/internal/response/
server/web/dist/        # 两套前端的构建产物
deploy/                 # 环境变量模板和 SSH 部署脚本
```

## 本地开发

安装依赖（需要 pnpm 11）：

```bash
corepack enable
make install
```

启动 Go 服务。不需要数据库服务。未设置 `SQLITE_PATH` 时，库文件是 `server/data/app.db`。

```bash
make server-dev
```

在另外两个终端启动前端：

```bash
make web-dev
make admin-dev
```

开发地址：

- 公共前端：`http://localhost:3000/`
- 管理端：`http://localhost:5173/admin/`
- Go 服务：`http://localhost:8888/`
- 健康检查：`http://localhost:8888/healthz`

两个 Vite 开发服务器都会将 `/api` 和 `/healthz` 通过同源代理转发到 `http://127.0.0.1:8888`，因此本地开发不需要给 Gin 添加 CORS 白名单，也不需要额外的前端 `.env` 文件。启动 Go 服务后，再分别运行 `make web-dev` 和 `make admin-dev` 即可。

## API 规范

当前提供：

```text
GET  /healthz
GET  /api/woodfish
POST /api/woodfish
POST /api/admin/login
GET  /api/admin/session
POST /api/admin/logout
```

`GET /api/woodfish` 返回木鱼被敲过的总次数，`POST /api/woodfish` 把次数加一。次数存在 SQLite 里。参观管理端的账号和密码写死为 `admin` / `admin123`，首页上能看到，不能在页面里修改。

响应统一为：

```json
{
  "success": true,
  "message": "",
  "data": {
    "status": "ok"
  }
}
```

后续业务接口统一放在 `/api/*` 或 `/api/admin/*` 下，只允许使用 `GET` 和 `POST`。不得未经说明加入 `PATCH`、`PUT` 或 `DELETE`。业务接口必须通过后端的统一响应封装返回数据。

## 环境变量

模板是 `deploy/.env.example`。本地可以复制为 `deploy/.env`，`make server-dev` 会读取它。文件不存在时使用默认值。

```dotenv
SQLITE_PATH=data/app.db
ENCRYPTION_KEY=replace-with-a-long-random-key
```

`SQLITE_PATH` 相对进程工作目录。本机 `make server-dev` 的工作目录是 `server/`。监听地址固定为 `:8888`。`ENCRYPTION_KEY` 用来给管理端会话签名。

## 部署

在 `apps/` 目录执行。脚本会构建前端，交叉编译 Linux 二进制，再用 SSH 上传。默认目标是 amd64，ARM 服务器加 `GOARCH=arm64`。

```bash
make deploy HOST=user@host
```

等价命令：

```bash
deploy/deploy.sh user@host
```

默认目录是 `/opt/food4agent`。换目录时设置 `DEPLOY_DIR`，只允许字母、数字、斜线和短横线。SSH 用户是 root，或者能 `sudo`。

服务器上第一次部署会生成 `/opt/food4agent/env` 和空的 SQLite 文件，之后更新只替换二进制，不覆盖数据库和 `env`。systemd 服务名是 `food4agent`。进程监听 `:8888`。反向代理指向服务器的 `127.0.0.1:8888`。
