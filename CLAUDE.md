# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 核心原则

### 设计哲学
- **克制**：不引入复杂依赖，保持目录干净
- **本地优先**：数据存本地，用 MD 格式，关键附件单独管理
- **CLI 优先**：能用 CLI 的不用 MCP，能用脚本的不用框架
- **可演进**：所有内容用 Git 管理，可回溯、可迭代

### 语言偏好
- 所有对话用中文，除非涉及代码/命令等技术内容
- Prompt 整理保留原始表达，标注来源和演化路径

---

## Commands

### 运行应用
```bash
# 命令行交互模式
python main.py

# Streamlit Web 界面
streamlit run ui/app.py
```

### 环境配置
```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# 或 source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置 API 密钥
cp .env.example .env
# 编辑 .env 填入 LLM provider credentials
```

### 知识库初始化
```bash
python -m knowledge_base
```

---

## Architecture

### Multi-Agent Workflow (LangGraph)

核心工作流在 `graph/workflow.py` 中定义，顺序执行以避免 API 限流：

```
fetch_data → analyze_fundamental → analyze_technical → analyze_sentiment
           → analyze_news → analyze_capital_flow → retrieve_reports
           → debate → make_decision → assess_risk → review_decision
           → generate_report → END
```

**Workflow State**: `InvestmentState` TypedDict，包含每个 Agent 的分析结果。

### Agent 类型

| 目录 | Agents | 用途 |
|------|--------|------|
| `agents/analysts/` | Fundamental, Technical, Sentiment, News, CapitalFlow | 五维分析师团队 |
| `agents/researchers/` | DebateRoom, ReportRetrieverAgent | 红蓝军辩论室、研报检索 |
| `agents/decision/` | Trader, PortfolioManager, RiskControllerAgent | 交易决策、投资组合管理、风控 |
| `agents/orchestrator.py` | Orchestrator | 意图分类和任务规划 |

### RAG 系统 (`rag/`)

- **Vector Store**: `vector_store.py` - ChromaDB 文档存储
- **Retrievers**: `RAGRetriever`, `HybridRetriever`, `GraphRAGRetriever`（三种检索策略）
- **Knowledge Graph**: `knowledge_graph.py` - NetworkX 实体关系图

### Configuration

**`config/settings.py`**: 多 LLM 提供商配置

- Provider: `openai`, `zhipuai`, `deepseek`, `qwen`, `ollama`
- 模型映射: `deep_think_model`（复杂推理）/ `quick_think_model`（快速任务）
- iFlow 可用模型: `qwen3-max`, `deepseek-v3.2`, `kimi-k2` 等

**`config/prompts.py`**: 所有 Agent 的 system prompts

---

## Important Files

| 文件 | 用途 |
|------|------|
| `graph/workflow.py` | LangGraph 主工作流定义 |
| `config/settings.py` | LLM 和应用配置 |
| `config/prompts.py` | Agent system prompts |
| `agents/base.py` | Agent 基类（`BaseAgent`），包含 LLM 初始化和重试逻辑 |
| `tools/stock_data.py` | A股数据获取（Yahoo Finance 数据源） |
| `main.py` | CLI 入口 |
| `ui/app.py` | Streamlit 主应用 |

---

## 技术细节

### LLM 调用模式

`BaseAgent` 在 `agents/base.py` 中实现了 LLM 调用的统一模式：

1. 通过 `get_model_for_task()` 从配置获取模型名
2. `invoke_llm()` 方法包含指数退避重试机制
3. 支持 OpenAI 兼容接口（iFlow、Anthropic、Ollama）

### 数据获取

`tools/stock_data.py` 使用 Yahoo Finance：
- A股代码转换: `.SS`（上海）、`.SZ`（深圳）
- 支持股票代码、名称、拼音首字母搜索
- News/Sentiment/CapitalFlow 使用 Mock 数据（演示用）

### UI 多页面

`ui/pages/` 目录结构：
- `1_📈_深度分析.py` - 完整投资分析流程
- `2_💬_智能问答.py` - RAG 问答系统
- `4_📚_知识溯源.py` - 来源追溯与知识图谱可视化

---

## Notes

- 所有 prompts 和输出均为中文
- Yahoo Finance symbols: `.SS` 上海, `.SZ` 深圳
- Rate limit handling 使用指数退避（2^n + 1 秒）
- News/Sentiment/CapitalFlow 数据当前为 Mock（演示）