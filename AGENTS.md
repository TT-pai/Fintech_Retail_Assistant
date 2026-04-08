# AGENTS.md

本文件定义 Agent 的行为规则、协作模式和职责分工。

---

## Agent 分类

### 1. Vibe Learning Agent
负责资讯获取、内容过滤、知识沉淀。

**职责**：
- 执行定时拉取任务
- 过滤低质量内容
- 格式化存储到 `vibe/daily/` 或 `vibe/weekly/`
- 维护 `vibe/sources.yaml` 配置

**行为规则**：
- 只拉取配置中声明的源
- 遵循 `filter` 规则过滤
- 存储格式统一用 Markdown
- 不重复拉取已存在的内容

### 2. Prompt Agent
负责 Prompt 整理和模式沉淀。

**职责**：
- 每日提取对话中的 Prompt
- 整理到 `prompts/daily/{date}.md`
- 定期提取模式到 `prompts/patterns/`
- 维护模式库的可召回性

**行为规则**：
- 提取时保留原始表达
- 标注上下文和用途
- 模式提取要去重、合并相似
- 模式命名要语义化

### 3. Memory Agent
负责规则文件管理和记忆分层。

**职责**：
- 每周 review `memory/` 目录
- 短期记忆 → 长期记忆 归档
- 合并冗余规则
- 维护 MEMORY.md 索引

**行为规则**：
- 7天以上有价值的短期记忆归档为长期
- 相似规则合并，保留最精炼版本
- 过期记忆标记删除或归档
- 更新索引保持同步

### 4. 投研 Agent（原有）
保持原有行为，详见原 CLAUDE.md 投研部分。

---

## Agent 协作模式

### 任务分发
```
用户请求 → Orchestrator → 分类 → 调用对应 Agent
```

### Agent 间通信
- 通过共享文件系统（MD/YAML/JSON）
- 通过 Git 记录变更历史
- 不引入复杂的消息队列

### 触发条件

| Agent | 触发方式 |
|-------|---------|
| Vibe Learning | 定时 cron / 手动 `bun run fetch` |
| Prompt Agent | 每日定时 / 手动整理 |
| Memory Agent | 每周定时 / 手动 review |

---

## Agent 输出规范

### Markdown 格式
```markdown
# 标题

> 来源：xxx | 时间：xxx | 标签：xxx

## 正文

...

## 关键信息
- 点1
- 点2

## 相关内容
- [[链接1]]
- [[链接2]]
```

### YAML 配置格式
```yaml
# sources.yaml 示例
daily:
  - name: "源名称"
    url: "..."
    type: "rss"
    schedule: "0 8 * * *"
    filter:
      keywords: ["关键词1", "关键词2"]
      exclude: ["排除词"]
    store: "vibe/daily/{date}/{source}.md"
```

---

## 约束与限制

### 不做的事
- 不抓取未授权的私有内容
- 不存储低质量/重复内容
- 不引入不必要的依赖

### 必须做的事
- 每次变更记录 Git
- 定期 review 规则文件
- 保持目录结构清晰
- 用中文对话

---

## 工具使用优先级

```
CLI 工具 > 本地脚本 > MCP 服务 > 外部 API
```

优先用 `yt-dlp`、`gallery-dl`、`jq` 等成熟 CLI。
其次用 Bun/TS 脚本处理。
MCP 仅在 CLI 无法满足时引入。

---

## 记忆召回机制

### 启动时
1. 读取 MEMORY.md 索引
2. 加载 CLAUDE.md 和 AGENTS.md
3. 根据任务类型加载相关长期记忆

### 执行中
1. 根据关键词匹配短期记忆
2. 如需要，召回相关长期记忆
3. 执行完成后，更新相关记忆

### 优先级
```
CLAUDE.md > AGENTS.md > 长期记忆 > 短期记忆
```