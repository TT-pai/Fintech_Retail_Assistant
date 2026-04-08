# Scripts 目录

本目录存放 Bun/TypeScript 脚本，用于自动化处理。

---

## 子目录

```
scripts/
├── fetch/      # 内容拉取脚本
└── analyze/    # 内容分析脚本
```

---

## 技术栈

- **运行时**：Bun
- **语言**：TypeScript
- **数据库**：SQLite（预留 MySQL adapter）

---

## 脚本示例

### fetch/daily.ts
每日内容拉取脚本。

```typescript
// 读取 vibe/sources.yaml
// 调用 CLI 或 API 拉取
// 过滤、格式化、存储
```

### analyze/style.ts
内容分析脚本。

```typescript
// 分析内容特征
// 更新相关配置
```

---

## 执行方式

```bash
# 每日拉取
bun run scripts/fetch/daily.ts

# 内容分析
bun run scripts/analyze/style.ts

# 定时任务（cron）
# 0 8 * * * bun run scripts/fetch/daily.ts
```