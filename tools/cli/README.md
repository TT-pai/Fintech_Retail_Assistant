# CLI 工具目录

本目录存放本地安装的 CLI 工具，用于内容拉取和处理。

---

## 推荐工具

### yt-dlp
视频/音频下载，支持 YouTube、Bilibili 等。

```bash
# 安装
pip install yt-dlp

# 埸用命令
yt-dlp "https://www.youtube.com/watch?v=xxx" --write-description --write-info-json
yt-dlp "https://www.bilibili.com/video/xxx" --write-description
```

### gallery-dl
图片/内容下载，支持多平台（Twitter、Pixiv、Reddit等）。

```bash
# 安装
pip install gallery-dl

# 常用命令
gallery-dl "https://twitter.com/user/status/xxx"
gallery-dl "https://www.pixiv.net/artworks/xxx"
```

### jq
JSON 处理。

```bash
# 安装 (Windows)
# 下载 https://stedolan.github.io/jq/download/

# 常用命令
cat data.json | jq '.[] | .title'
```

### newsboat
RSS 阅读器 CLI。

```bash
# 安装
brew install newsboat  # Mac
# 或 apt install newsboat  # Linux

# 配置
# 编辑 ~/.newsboat/config
```

---

## 本地安装策略

### 方案1：全局安装
直接 pip/brew 安装到系统，简单直接。

### 方案2：项目级安装
在 `tools/cli/` 下存放：
- 可执行文件（Windows .exe）
- 配置文件
- 缓存目录

```
tools/cli/
├── yt-dlp/
│   ├── yt-dlp.exe
│   ├── config.txt
│   └── cache/
│
├── gallery-dl/
│   ├── gallery-dl.exe
│   └── config.json
│
└── bin/
│   └── jq.exe
```

---

## 使用优先级

```
CLI 工具 > Bun 脚本 > MCP 服务
```

能用 CLI 直接处理的，优先用 CLI。
CLI 无法处理的，用 Bun/TS 脚本。
尽量不引入 MCP，保持克制。