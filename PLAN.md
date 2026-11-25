# Food4Agent Skill 托管与私有分发实现计划

> 本文件用于指导 VS Code 中的 AI 编程工具实现 Food4Agent 的公共与私有 Skill 托管能力。

## 1. 目标

在现有 Food4Agent 公共 Skill 静态目录的基础上，增加账号级的私有 Skill 托管能力。

产品模型参考 GitHub：

```text
一个账号
  ├── 多个 Skill
  ├── 每个 Skill 独立管理文件和版本
  └── 每个 Skill 可以公开或私有
```

一个 Skill 在产品概念上对应一个 GitHub 风格的仓库，但实现中不增加单独的 `repositories` 实体，也不在 URL 中增加 `repo` 层级。

本次实现需要完成：

1. 账号拥有多个 Skill。
2. 每个 Skill 有唯一的账号路径和名称。
3. 公共 Skill 继续使用静态文件分发。
4. 私有 Skill 继续使用 Food4Agent 主域名分发。
5. 私有 Skill 需要登录会话或 Skill Key 才能访问。
6. 没有权限访问私有 Skill 时返回 404。
7. 支持 Skill 上传、在线编辑、草稿、发布、版本查看和回滚。
8. 继续使用目录内容哈希作为真实版本。
9. 继续使用 `manifest.json` 记录文件 SHA256 和大小。
10. 客户端下载后逐文件校验，并使用原子替换更新本地 Skill。

## 2. 已确定的边界

### 2.1 不增加的层级

第一版不引入以下概念：

```text
workspace
organization
enterprise
personal account type
repository entity
registry subdomain
Skill URL 的版本前缀
```

账号本身就是 Skill 的所有者。每个 Skill 直接归属于一个账号。

### 2.2 不做的功能

第一版暂不实现：

1. 多人协作权限。
2. 团队和组织层级。
3. Git clone、push 等完整 Git 协议。
4. Pull Request 和代码合并。
5. dev、staging、prod 多级发布渠道。
6. 分支管理。
7. SSO、SAML、SCIM。
8. 第三方 Skill 市场。
9. 任意上传脚本的自动执行。
10. 私有 Skill 的公开索引。

GitHub 或 Gitea 导入可以保留为后续扩展，第一版以 ZIP 上传和在线编辑为主。

## 3. URL 设计

所有路径统一使用 `skills`，不要使用单数 `skill`。

### 3.1 公共 Skill 页面

```text
https://food4agent.com/skills/{skillName}
```

示例：

```text
https://food4agent.com/skills/product-search
```

旧地址可以做兼容跳转：

```text
/skill/{skillName}  →  /skills/{skillName}
```

### 3.2 公共 Skill 静态文件

继续保留现有公共静态目录：

```text
https://food4agent.com/registry/skills/{skillName}/manifest.json
https://food4agent.com/registry/skills/{skillName}/SKILL.md
```

公共目录可以继续使用对象存储和 CDN。

### 3.3 私有 Skill 页面与文件

私有 Skill 直接使用 Food4Agent 主域名，并通过账号 handle 区分所有者：

```text
https://food4agent.com/{handle}/skills/{skillName}
```

示例：

```text
https://food4agent.com/acme/skills/product-search
https://food4agent.com/terln/skills/product-search
```

两个账号可以拥有同名 Skill，因为唯一标识是：

```text
{handle}/{skillName}
```

私有 Skill 文件地址：

```text
https://food4agent.com/acme/skills/product-search/manifest.json
https://food4agent.com/acme/skills/product-search/SKILL.md
https://food4agent.com/acme/skills/product-search/references/api.md
```

固定内容版本地址：

```text
https://food4agent.com/acme/skills/product-search/{contentHash}/manifest.json
https://food4agent.com/acme/skills/product-search/{contentHash}/SKILL.md
```

不要增加 `registry` 子域名，也不要给私有 Skill 路径增加版本前缀。

### 3.4 管理页面

`console.food4agent.com` 只承担登录和管理，不出现在 Skill 的实际分发地址中。

```text
登录：
https://console.food4agent.com/login

账号的 Skills：
https://console.food4agent.com/{handle}/skills

新建 Skill：
https://console.food4agent.com/{handle}/skills/new

Skill 编辑：
https://console.food4agent.com/{handle}/skills/{skillName}/edit

版本列表：
https://console.food4agent.com/{handle}/skills/{skillName}/versions

创建发布：
https://console.food4agent.com/{handle}/skills/{skillName}/releases/new
```

## 4. 路由解析规则

主域名需要根据路径进行分流：

```text
/skills/{skillName}
公共 Skill 页面

/registry/skills/{skillName}/*
公共静态 Skill 文件

/{handle}/skills/{skillName}/*
账号下的私有或公开 Skill
```

私有路径先进行权限校验，再读取对象存储中的文件。

账号 handle 使用全局唯一规则，建议约束为：

```text
2 至 32 个字符
小写字母、数字和短横线
不能以短横线开头或结尾
```

需要保留以下系统路径，禁止注册为账号 handle：

```text
skills
registry
console
api
docs
assets
static
login
settings
```

Skill 名称在同一账号下唯一。建议沿用相同的 slug 规则。

## 5. 私有访问控制

### 5.1 浏览器访问

用户在 `console.food4agent.com` 登录后获得登录会话，再访问主域名下的私有 Skill 地址。

```text
登录：
console.food4agent.com/login

访问：
food4agent.com/acme/skills/product-search
```

服务端根据登录会话判断当前账号是否有权限。

### 5.2 客户端访问

客户端使用从控制台获取的 Skill Key：

```http
Authorization: Bearer FOOD4AGENT_SKILL_KEY
```

请求示例：

```http
GET https://food4agent.com/acme/skills/product-search/manifest.json
Authorization: Bearer s4a_skill_xxxxxxxxx
```

Skill Key 只用于读取私有 Skill，和付费能力 API 的 `FOOD4AGENT_API_KEY` 分开。

```text
FOOD4AGENT_SKILL_KEY
私有 Skill 下载和同步

FOOD4AGENT_API_KEY
商品查询、图片处理等付费能力 API
```

两个 Key 在同一个控制台中管理，但权限和生命周期分开。

### 5.3 无权限响应

对于私有 Skill：

```text
没有登录会话：404
没有有效 Skill Key：404
Skill 不属于当前账号：404
Skill 不存在：404
```

授权成功后正常返回文件。

私有响应禁止被公共 CDN 缓存：

```http
Cache-Control: private, no-store
```

内容哈希版本可以使用长缓存，因为它们不可修改。

## 6. 数据模型

第一版只需要以下核心表：

```text
accounts
skills
skill_drafts
skill_versions
skill_tokens
skill_installations
```

### 6.1 accounts

```text
id
handle
display_name
avatar_url
created_at
updated_at
```

`handle` 全局唯一，创建后尽量保持稳定。显示名称可以修改。

### 6.2 skills

```text
id
owner_id
name
display_name
description
visibility
current_content_hash
created_at
updated_at
```

唯一约束：

```text
owner_id + name
```

`visibility` 支持：

```text
public
private
```

### 6.3 skill_drafts

```text
id
skill_id
files
manifest
updated_by
created_at
updated_at
```

草稿可以修改，发布以后生成不可变版本。

### 6.4 skill_versions

```text
id
skill_id
content_hash
manifest
changelog
published_by
published_at
```

`content_hash` 是版本的真实身份。页面可以显示内容哈希的短版本，但 URL 不使用固定版本前缀。

### 6.5 skill_tokens

```text
id
owner_id
token_hash
name
scope
last_used_at
expires_at
revoked_at
created_at
```

Token 只保存哈希，完整 Token 只在创建成功后显示一次。

### 6.6 skill_installations

```text
id
owner_id
skill_id
source
installed_version
local_path
auto_update
last_checked_at
```

本地安装位置：

```text
~/.codex/skills/{skillName}
<workdir>/.codex/skills/{skillName}
```

## 7. Skill 上传与编辑

### 7.1 Skill 列表页

访问：

```text
console.food4agent.com/{handle}/skills
```

页面展示：

```text
Skill 名称
公开或私有
当前版本
最近更新时间
草稿状态
最近同步状态
```

顶部按钮：

```text
新建 Skill
创建 Skill Key
```

### 7.2 新建 Skill

访问：

```text
console.food4agent.com/{handle}/skills/new
```

创建表单：

```text
名称
标识
简介
公开或私有
创建方式
```

创建方式：

```text
上传 ZIP
在线创建
从 Git 导入
```

第一版优先支持上传 ZIP 和在线创建。

### 7.3 上传 ZIP

ZIP 内部结构示例：

```text
product-search/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

上传后执行：

1. 解压到临时目录。
2. 检查 `SKILL.md` 是否存在。
3. 检查文件路径和文件大小。
4. 检查是否包含禁止文件。
5. 读取 Skill 元信息和能力依赖。
6. 计算目录内容哈希。
7. 为每个文件计算 SHA256 和大小。
8. 生成 `manifest.json`。
9. 保存为当前草稿。
10. 展示文件变化。

### 7.4 在线编辑

编辑页：

```text
console.food4agent.com/{handle}/skills/{skillName}/edit
```

采用三栏布局：

```text
左侧：文件树
中间：编辑器
右侧：Skill 信息和校验结果
```

顶部操作：

```text
保存草稿
预览变化
发布版本
```

已经发布的版本不允许直接编辑。所有修改先进入草稿，发布后创建新的内容哈希版本。

## 8. 版本与同步

第一版只保留两个状态：

```text
draft
published
```

不实现多级发布渠道和分支。

### 8.1 发布流程

```text
编辑文件或上传 ZIP
  ↓
保存草稿
  ↓
检查文件变化
  ↓
生成 manifest.json
  ↓
计算 content_hash
  ↓
预览 Diff
  ↓
发布不可变版本
```

### 8.2 客户端安装

公共 Skill：

```text
https://food4agent.com/registry/skills/{skillName}/manifest.json
```

私有 Skill：

```text
https://food4agent.com/{handle}/skills/{skillName}/manifest.json
```

客户端将来源和版本写入 `.terln-skill.json`：

```json
{
  "source": "food4agent_private",
  "owner": "acme",
  "name": "product-search",
  "source_url": "https://food4agent.com/acme/skills/product-search",
  "version": "sha256:abc123...",
  "auto_update": true
}
```

### 8.3 客户端更新

```text
请求最新 manifest
  ↓
对比本地 content_hash
  ↓
下载到临时目录
  ↓
逐文件校验 SHA256
  ↓
检查本地是否存在未同步修改
  ↓
用户确认或自动更新
  ↓
原子替换 Skill 目录
  ↓
更新 .terln-skill.json
```

如果本地 Skill 被用户修改，需要先提示并保存备份，不能直接覆盖。

## 9. 主域名实现方式

公共路径可以继续使用纯静态部署：

```text
/skills/*
/registry/skills/*
```

账号路径需要经过鉴权服务：

```text
/{handle}/skills/*
```

建议由 Caddy、Nginx 或边缘服务按路径分流：

```text
/skills/*
读取公共页面或静态资源

/registry/skills/*
读取公共 Skill 对象

/{handle}/skills/*
进入私有 Skill 鉴权服务
```

私有 Skill 的对象可以存放在现有 S3 或 MinIO 中，例如：

```text
private/{ownerId}/skills/{skillId}/{contentHash}/...
```

对象存储路径不要直接暴露给客户端，客户端只访问 Food4Agent 主域名。

## 10. 实现顺序

### 阶段一：账号与 URL

1. 增加账号 `handle`。
2. 增加 `skills` 数据表。
3. 实现账号下的 Skill 唯一约束。
4. 将公共页面路径统一为 `/skills/{name}`。
5. 保留旧 `/skill/{name}` 到新地址的跳转。
6. 实现 `/{handle}/skills/{name}` 路由。
7. 预留系统路径和账号 handle 校验。

### 阶段二：私有 Skill 存储

1. 增加私有对象存储路径。
2. 实现 Skill 草稿。
3. 实现 ZIP 上传。
4. 实现 Skill 目录校验。
5. 实现 `manifest.json` 生成。
6. 实现内容哈希和文件 SHA256。
7. 实现草稿发布。

### 阶段三：鉴权与私有分发

1. 实现 `console.food4agent.com` 登录会话。
2. 实现 Skill Key 创建、撤销和哈希存储。
3. 实现主域名私有路径鉴权。
4. 无权限时统一返回 404。
5. 有效会话或 Key 可以读取私有 Skill。
6. 为私有响应设置禁止公共缓存的 Header。

### 阶段四：在线编辑

1. 实现账号的 Skill 列表页。
2. 实现新建 Skill 页面。
3. 实现文件树。
4. 实现 `SKILL.md` 编辑。
5. 实现参考文件和资源文件上传。
6. 实现草稿保存。
7. 实现文件 Diff 预览。
8. 实现发布操作。

### 阶段五：客户端同步

1. 兼容公共 Skill 的现有安装逻辑。
2. 增加私有 Skill Key 配置。
3. 支持私有 Manifest 请求。
4. 支持逐文件 SHA256 校验。
5. 支持临时目录下载。
6. 支持原子替换。
7. 更新 `.terln-skill.json`。
8. 处理本地修改冲突。

## 11. 验收标准

### URL

1. 公共页面使用 `/skills/{name}`。
2. 旧 `/skill/{name}` 可以跳转。
3. 私有地址使用 `/{handle}/skills/{name}`。
4. 所有路径统一使用 `skills`。
5. 私有路径不包含 `workspace`、`enterprise`、`repository`、`registry` 或版本前缀。
6. 不同账号可以拥有相同名称的 Skill。
7. 私有页面和私有文件都使用 `food4agent.com` 主域名。

### 权限

1. 公共 Skill 无 Key 可以访问。
2. 私有 Skill 没有登录会话时返回 404。
3. 私有 Skill 没有有效 Key 时返回 404。
4. 有效登录会话可以在浏览器中查看私有 Skill。
5. 有效 Skill Key 可以下载私有 Skill 文件。
6. 私有响应不会进入公共缓存。
7. 私有资源的 404 与资源不存在时的 404 行为一致。

### 版本

1. 草稿可以修改。
2. 已发布版本不可修改。
3. 每个发布版本都有唯一 content hash。
4. `manifest.json` 包含所有文件的 SHA256 和大小。
5. 客户端逐文件验证后才能替换本地目录。
6. 客户端保存 `.terln-skill.json`。
7. 客户端发现本地修改时不会静默覆盖。

### 多账号

下面两个地址必须可以同时存在：

```text
https://food4agent.com/acme/skills/product-search
https://food4agent.com/terln/skills/product-search
```

两者的文件、权限、版本和 Key 互相隔离。

## 12. 实现风险

1. 使用稳定的账号 handle，不要把可随时修改的显示名称当作 URL 标识。
2. 私有文件不能直接挂在公共静态 CDN 下。
3. 不要使用 URL 本身代替鉴权 Key。
4. 不要直接覆盖已经发布的版本。
5. 防止路径穿越和非法文件名。
6. 处理私有响应缓存，不能让一个账号的 200 响应被其他用户命中。
7. 无权限响应的 404 不能被公共缓存长期缓存。
8. 账号 handle 需要保留系统路径。
9. 不要重新引入 workspace、organization、repository、registry 子域名或版本前缀。
10. 不要把付费能力 API 的业务逻辑写入 Skill 文件分发模块。
11. Skill 中的脚本和资源需要经过路径、大小和类型校验。
12. 上传内容不能自动获得任意代码执行权限。

## 13. 给 VS Code AI 的执行要求

开始实现前，先检查现有项目的目录结构、路由、Skill 清单、对象存储适配和客户端安装逻辑。

执行时遵循以下规则：

1. 先复用已有的 Skill Manifest 和内容哈希逻辑。
2. 先复用现有对象存储，不重复实现存储抽象。
3. 先复用现有登录和账号体系。
4. 不新增 workspace、organization、repository 数据模型。
5. 不新增 registry 子域名。
6. 不在私有 Skill URL 中添加版本前缀。
7. 不把付费能力 API 的业务逻辑写进 Skill 托管模块。
8. 不让 API Key 出现在 Skill 文件、前端静态资源或 URL 查询参数中。
9. 不直接覆盖已发布版本。
10. 不为了实现本计划重写无关模块。
11. 每完成一个阶段，先运行相关检查，再继续下一阶段。
12. 最后补充路由、权限、Manifest、版本更新和本地同步测试。

实现完成后，需要输出：

```text
修改的文件
新增的数据表或字段
新增的路由
鉴权流程
上传和发布流程
客户端同步流程
验证命令
仍未实现的内容
```
