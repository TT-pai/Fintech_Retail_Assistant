# 智汇投研Pro - 基于RAG+多智能体的AI投研平台

## 项目简介

智汇投研Pro是一个创新的AI投研平台，通过**多智能体协作**、**RAG知识增强**和**红蓝军辩论机制**，为个人投资者提供专业的股票分析服务。

### 核心创新点

1. **五维分析师团队**: 基本面、技术面、情绪面、新闻面、资金流五位分析师并行分析
2. **红蓝军辩论室**: 看多vs看空研究员的结构化辩论，让用户看到观点碰撞
3. **RAG知识增强**: 向量检索+知识图谱，支持研报/财报/新闻检索与溯源
4. **多层级风控**: 交易员→风控官→投资组合经理的完整风控流程
5. **白盒化设计**: 将Agent协作过程透明展示，增强可解释性
6. **知识沉淀体系**: Prompt模式沉淀、记忆分层管理、自动化脚本

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                     用户输入 (股票代码/名称/拼音)              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     数据获取层 (Yahoo Finance)                │
│         股票行情 / 财务数据 / 新闻 / 行业信息                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     RAG知识增强层                            │
│    向量检索 + 知识图谱 + 研报检索 (基础检索/混合检索/GraphRAG) │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     分析师团队 (顺序执行，避免限流)            │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│  │基本面分析│ │技术面分析│ │情绪面分析│ │新闻面分析│ │资金流分析││
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘│
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     研报检索 & 红蓝军辩论室                    │
│         📚 研报检索员 → 🐂 看多研究员 ←→ 🐻 看空研究员         │
│                   (多轮结构化辩论)                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     决策与风控团队                            │
│     🎯 交易员  →  🛡️ 风控官  →  📊 投资组合经理              │
│       (决策建议)   (风险评估)    (最终审核)                   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     输出报告                                 │
│        完整的投资分析研报 + 风险评估摘要 (Markdown)           │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/TT-pai/Fintech_Retail_Assistant.git
cd Fintech_Retail_Assistant

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的API密钥
```

### 3. 运行

**命令行模式:**
```bash
python main.py
```

**Streamlit Web界面:**
```bash
streamlit run ui/app.py
```

**知识库初始化:**
```bash
python -m knowledge_base
```

## 项目结构

```
fintech_retail_assistant/
├── agents/                    # Agent模块
│   ├── base.py               # Agent基类
│   ├── analysts/             # 分析师团队
│   │   ├── fundamental.py    # 基本面分析师
│   │   ├── technical.py      # 技术分析师
│   │   ├── sentiment.py      # 情绪分析师
│   │   ├── news.py           # 新闻分析师
│   │   └── capital_flow.py   # 资金流分析师
│   ├── researchers/          # 研究员团队
│   │   ├── debate.py         # 红蓝军辩论室
│   │   └── report_retriever.py # 研报检索Agent
│   └── decision/             # 决策团队
│       ├── portfolio_manager.py  # 交易员+投资组合经理
│       └── risk_controller.py    # 风控官
├── rag/                      # RAG检索模块
│   ├── embeddings.py         # 向量嵌入
│   ├── vector_store.py       # 向量存储
│   ├── retriever.py          # 检索器(基础/混合/GraphRAG)
│   ├── reranker.py           # 重排序
│   └── knowledge_graph.py    # 知识图谱（NetworkX）
├── knowledge_base/           # 知识库数据
│   ├── __init__.py           # 知识库管理器
│   ├── reports.json          # 研报数据
│   ├── news.json             # 新闻数据
│   ├── industry.json         # 行业信息
│   ├── regulations.json      # 法规数据
│   └── financials.json       # 财务数据
├── scripts/                  # 自动化脚本
│   ├── generate_reports.py   # 研报数据生成脚本
│   ├── update_kg.py          # 知识图谱更新脚本
│   └── README.md             # 脚本使用说明
├── prompts/                  # Prompt沉淀目录
│   ├── daily/                # 每日Prompt整理
│   ├── patterns/             # 表达模式
│   └── README.md             # Prompt沉淀规范
├── memory/                   # 记忆系统
│   ├── MEMORY.md             # 记忆索引
│   └── conversation.py       # 对话管理
├── tools/                    # 工具模块
│   ├── stock_data.py         # A股数据获取
│   ├── market_data.py        # 市场数据工具
│   └── cli/                  # CLI工具目录
├── mcp/                      # MCP服务配置
│   └── README.md             # MCP使用说明
├── graph/                    # LangGraph工作流
│   └── workflow.py           # 主工作流定义
├── ui/                       # 前端界面
│   ├── app.py               # Streamlit主应用
│   ├── components/          # UI组件
│   │   ├── cards.py         # 卡片组件
│   │   ├── charts.py        # 图表组件
│   │   └── chat.py          # 聊天组件
│   └── pages/               # 多页面
│       └── 📈_深度分析.py   # 深度分析页
├── config/                   # 配置
│   ├── settings.py          # 多LLM提供商配置
│   └── prompts.py           # Prompt模板库
├── data/                     # 数据存储
│   ├── chroma/              # 向量数据库
│   └── knowledge_graph/     # 知识图谱数据
├── .claude/                  # Claude Code配置
├── main.py                   # 命令行入口
├── requirements.txt          # 依赖清单
└── README.md                 # 项目说明
```

## 核心功能

### 1. 多维度分析看板
- **基本面分析**: ROE/ROA、毛利率、负债率、现金流、红旗警告
- **技术面分析**: MA均线、RSI、MACD、布林带、支撑压力位
- **情绪面分析**: 市场情绪评分、逆向信号识别、舆情热度
- **新闻面分析**: 重大事件、政策影响、催化剂识别
- **资金流分析**: 主力资金、北向资金、机构持仓变化、融资融券

### 2. RAG知识增强
- **向量检索**: 基于语义相似度的文档检索（ChromaDB）
- **混合检索**: 向量+关键词检索，RRF融合算法
- **GraphRAG**: 知识图谱+向量检索，实体关联查询（NetworkX）
- **重排序**: 基于相关性的二次排序

### 3. 红蓝军辩论室
- 看多研究员挖掘上涨催化剂
- 看空研究员警示风险隐患
- 多轮结构化辩论（可配置轮数）
- 辩论摘要与共识提取

### 4. 智能风控系统
- **五维风险评估**: 市场/流动性/估值/情绪/信用风险
- **动态仓位限制**: 根据风险评分自动调整仓位上限
  - 低风险(0-30): 最大50%
  - 中等风险(30-60): 最大30%
  - 高风险(60-80): 最大15%
  - 极高风险(80-100): 最大5%
- **止损建议**: 智能止损线计算
- **风险预警**: 多维度风险信号提示

### 5. 多页面UI
- **首页**: 快速搜索、热点股票、市场概览
- **深度分析**: 完整的投资分析流程（12节点）
- **智能问答**: RAG增强的问答系统
- **知识溯源**: 来源追溯与知识图谱可视化

### 6. 知识沉淀体系
- **Prompt沉淀**: 高效表达模式提取与复用
- **记忆分层**: 短期记忆→长期记忆归档
- **自动化脚本**: 研报生成、图谱更新

## 工作流节点

```
fetch_data → analyze_fundamental → analyze_technical → analyze_sentiment 
           → analyze_news → analyze_capital_flow → retrieve_reports 
           → debate → make_decision → assess_risk → review_decision 
           → generate_report → END
```

**执行顺序说明**：
- 分析师团队顺序执行（避免API限流）
- 研报检索在辩论前执行（为辩论提供参考）
- 辩论结果传入交易决策

## 配置说明

### 模型配置
```bash
# .env 文件配置
provider=openai                    # 提供商选择
OPENAI_API_KEY=your_key            # API密钥
OPENAI_BASE_URL=  # API地址

deep_think_model=qwen3-max         # 复杂推理任务
quick_think_model=deepseek-v3.2    # 快速任务
```

### Embedding配置
```bash
EMBEDDING_MODEL=shibing624/text2vec-base-chinese  # 向量模型
VECTOR_STORE_PATH=./data/chroma                   # 存储路径
```

## 技术栈

- **Agent框架**: LangGraph（工作流编排）+ LangChain
- **RAG**: ChromaDB（向量存储）+ NetworkX（知识图谱）+ jieba（分词）
- **数据源**: Yahoo Finance（A股数据）
- **前端**: Streamlit（多页面应用）
- **记忆**: 文件系统（MD/YAML/JSON）+ Git

## 自动化脚本

### 研报数据生成
```bash
python scripts/generate_reports.py
```
自动生成覆盖全A股的行业研报数据。

### 知识图谱更新
```bash
python scripts/update_kg.py
```
更新知识图谱实体关系。

## 项目亮点

1. **产品设计创新**: Agent黑盒流程白盒化，辩论机制增强可解释性
2. **RAG深度集成**: 三种检索策略（基础/混合/GraphRAG），知识可溯源
3. **风控体系完善**: 五维风险评估，动态仓位管理，风险评分驱动
4. **技术深度**: Multi-Agent协作、LangGraph工作流、TypedDict状态管理
5. **工程能力**: 模块化设计、多LLM支持、指数退避重试、Mock数据降级
6. **知识沉淀**: Prompt模式沉淀、记忆分层、自动化脚本

## 免责声明

本系统仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。

## License

MIT License