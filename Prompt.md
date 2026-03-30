# 智汇投研Pro - AI智能投研平台产品规划文档

> 版本：v2.0  
> 日期：2026年3月30日  
> 定位：面向面试官展示的AI全栈能力作品集

---

## 一、项目背景与目标

### 1.1 项目定位

本项目是一个**金融智能投研平台**，旨在帮助个人投资者进行股票分析和投资决策。核心卖点：

1. **RAG知识增强**：构建研报/财报/新闻知识库，支持语义检索与知识溯源
2. **多Agent协作**：LangGraph编排的多智能体分析系统
3. **GraphRAG创新**：知识图谱+向量检索融合，支持多跳推理
4. **完整产品闭环**：从数据获取→分析→决策→回测→监控的全链路

### 1.2 技术栈要求

| 技术领域 | 选型 | 说明 |
|---------|------|------|
| **Agent框架** | LangGraph + LangChain | 状态图编排，支持复杂工作流 |
| **RAG引擎** | Chroma + LangChain Retriever | 轻量级向量库，易于部署 |
| **Embedding** | text2vec-base / BGE-small | 中文金融文本嵌入 |
| **LLM** | glm5 | 通过iFlow接口调用 |
| **知识图谱** | NetworkX (轻量) | 实体关系存储与推理 |
| **后端框架** | FastAPI | 异步高性能API |
| **前端框架** | Streamlit | 快速原型展示 |
| **数据存储** | SQLite + JSON | 轻量级存储方案 |

### 1.3 面试亮点对标

| 岗位要求 | 本项目覆盖 | 具体体现 |
|---------|-----------|---------|
| LLM技术理解 | ✅ | 多Agent编排、Prompt工程、思维链推理 |
| RAG技术栈 | ✅ | 向量检索、知识库构建、多路召回、引用溯源 |
| Agent框架 | ✅ | LangGraph状态图、多Agent协作、工具调用 |
| Function Calling | ✅ | 股票数据API、新闻API、技术指标计算 |
| 金融领域知识 | ✅ | 投研全流程、风控评估、合规审查 |
| 工程化能力 | ✅ | 模块化架构、配置管理、异常处理 |

---

## 二、系统架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      用户交互层 (Streamlit UI)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │  智能问答   │ │  深度分析   │ │  策略回测   │ │  知识溯源   │    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                      Agent编排层 (LangGraph)                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Orchestrator Agent                        │    │
│  │         (意图识别 → 任务拆解 → Agent调度 → 结果聚合)          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│       │              │              │              │                │
│  ┌────▼────┐    ┌────▼────┐    ┌────▼────┐    ┌────▼────┐         │
│  │ 分析师  │    │ 研究员  │    │ 决策者  │    │ 风控官  │         │
│  │ Agent池 │    │ Agent池 │    │ Agent池 │    │ Agent池 │         │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                      RAG知识增强层                                   │
│  ┌───────────────────┐  ┌───────────────────┐  ┌────────────────┐  │
│  │   向量检索引擎    │  │   知识图谱引擎    │  │  多路召回融合  │  │
│  │   (Chroma)        │  │   (NetworkX)      │  │   (RRF重排)    │  │
│  └───────────────────┘  └───────────────────┘  └────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    知识库内容                                │   │
│  │  研报摘要 | 财报要点 | 新闻舆情 | 行业知识 | 监管法规       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                      工具调用层 (Function Calling)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 行情数据 │ │ 财务数据 │ │ 新闻舆情 │ │ 技术指标 │ │ 知识检索 │  │
│  │ Tool     │ │ Tool     │ │ Tool     │ │ Tool     │ │ Tool     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────────────┐
│                      数据存储层                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ 向量库   │ │ 图数据库 │ │ 关系库   │ │ 文件存储 │               │
│  │ Chroma   │ │ NetworkX │ │ SQLite   │ │ JSON     │               │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
Proj2_fintech_retail_assistant/
├── main.py                      # 主入口
├── requirements.txt             # 依赖管理
├── .env.example                 # 环境变量模板
│
├── config/                      # 配置模块
│   ├── settings.py              # 配置管理
│   └── prompts.py               # Prompt模板库
│
├── agents/                      # Agent模块
│   ├── base.py                  # Agent基类
│   ├── orchestrator.py          # 编排Agent (新增)
│   ├── analysts/                # 分析师Agent池
│   │   ├── fundamental.py       # 基本面分析
│   │   ├── technical.py         # 技术面分析
│   │   ├── sentiment.py         # 情绪面分析
│   │   ├── news.py              # 新闻面分析
│   │   └── capital_flow.py      # 资金流分析 (新增)
│   ├── researchers/             # 研究员Agent池
│   │   ├── debate.py            # 红蓝军辩论
│   │   └── report_retriever.py  # 研报检索Agent (新增)
│   └── decision/                # 决策Agent池
│       ├── portfolio_manager.py # 投资组合经理
│       ├── risk_controller.py   # 风控官 (新增)
│       └── compliance.py        # 合规官 (新增)
│
├── rag/                         # RAG模块 (新增)
│   ├── __init__.py
│   ├── embeddings.py            # 向量嵌入
│   ├── vector_store.py          # 向量存储
│   ├── retriever.py             # 检索器
│   ├── reranker.py              # 重排序器
│   └── knowledge_graph.py       # 知识图谱
│
├── knowledge_base/              # 知识库数据 (新增)
│   ├── reports/                 # 研报数据
│   ├── financials/              # 财报数据
│   ├── news/                    # 新闻数据
│   ├── regulations/             # 监管法规
│   └── industry/                # 行业知识
│
├── tools/                       # 工具模块
│   ├── stock_data.py            # 股票数据工具
│   ├── news_api.py              # 新闻API工具 (新增)
│   ├── technical_indicators.py  # 技术指标工具
│   └── backtest.py              # 回测工具 (新增)
│
├── graph/                       # 工作流模块
│   └── workflow.py              # LangGraph工作流
│
├── ui/                          # 前端模块
│   ├── app.py                   # Streamlit主应用
│   ├── pages/                   # 多页面
│   │   ├── 1_📈_深度分析.py
│   │   ├── 2_💬_智能问答.py
│   │   ├── 3_🧪_策略回测.py
│   │   └── 4_📚_知识溯源.py
│   └── components/              # UI组件
│       ├── charts.py            # 图表组件
│       ├── cards.py             # 卡片组件
│       └── chat.py              # 聊天组件
│
├── memory/                      # 记忆模块
│   ├── conversation.py          # 对话记忆
│   └── user_profile.py          # 用户画像
│
└── data/                        # 数据存储
    ├── chroma/                  # 向量数据库
    ├── cache/                   # 缓存数据
    └── logs/                    # 日志文件
```

---

## 三、核心功能模块详细设计

### 3.1 RAG知识库系统

#### 3.1.1 知识库内容规划

| 知识库类型 | 数据来源 | 文档数量 | 更新频率 |
|-----------|---------|---------|---------|
| 研报摘要库 | 公开券商研报 | 500+ | 每周更新 |
| 财报要点库 | 上市公司财报 | 1000+ | 每季度更新 |
| 新闻舆情库 | 财经新闻网站 | 实时 | 每日更新 |
| 行业知识库 | 行业研究报告 | 100+ | 每月更新 |
| 监管法规库 | 证监会/交易所 | 50+ | 按需更新 |

#### 3.1.2 向量检索流程

```
用户查询
    │
    ▼
┌─────────────────┐
│  查询预处理      │  去除噪声、实体识别
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  查询向量化      │  text2vec-base embedding
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  向量相似检索    │  Chroma similarity_search
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  多路召回融合    │  向量检索 + 关键词检索
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  重排序         │  基于相关性、时效性重排
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  返回Top-K结果   │  包含原文、来源、时间
└─────────────────┘
```

#### 3.1.3 检索结果展示格式

```json
{
  "query": "茅台最近有什么利好吗",
  "results": [
    {
      "content": "贵州茅台2024年一季度营收同比增长18%，净利润同比增长20%...",
      "source": "研报-中信证券-2024-04-28",
      "score": 0.89,
      "metadata": {
        "stock_code": "600519",
        "report_type": "季报点评",
        "date": "2024-04-28",
        "author": "中信证券食品饮料团队"
      }
    }
  ],
  "answer": "根据研报分析，茅台近期利好包括：1) Q1营收净利双增长...",
  "citations": [
    {"text": "营收同比增长18%", "doc_id": "doc_001"},
    {"text": "净利润同比增长20%", "doc_id": "doc_001"}
  ]
}
```

### 3.2 知识图谱模块

#### 3.2.1 图谱Schema设计

```
实体类型:
  - Company(公司)
    属性: code, name, industry, market_cap, pe_ratio
    
  - Concept(概念/板块)
    属性: name, description, stocks_count
    
  - Person(人物)
    属性: name, position, company
    
  - Event(事件)
    属性: title, date, impact_level, type
    
  - Indicator(指标)
    属性: name, value, period, unit

关系类型:
  - (Company)-[:BELONGS_TO]->(Concept)      # 概念板块
  - (Company)-[:COMPETES]->(Company)        # 竞争关系
  - (Company)-[:SUPPLIES]->(Company)        # 供应链关系
  - (Company)-[:HAS_INDICATOR]->(Indicator) # 财务指标
  - (Event)-[:AFFECTS]->(Company)           # 事件影响
  - (Person)-[:WORKS_AT]->(Company)         # 任职关系
```

#### 3.2.2 GraphRAG查询示例

```
用户问题: "白酒板块龙头有哪些？茅台的主要竞争对手是谁？"

执行流程:
1. 实体识别: ["白酒板块", "茅台"]
2. 图谱查询:
   - MATCH (c:Concept {name: "白酒"})<-[:BELONGS_TO]-(company)
     RETURN company ORDER BY company.market_cap DESC
   - MATCH (m:Company {name: "茅台"})-[:COMPETES]->(competitor)
     RETURN competitor
3. 结果融合: 结合图谱结果与RAG检索内容
4. 生成回答: "白酒板块龙头包括贵州茅台、五粮液、泸州老窖..."
```

### 3.3 Agent系统升级

#### 3.3.1 Orchestrator Agent（新增）

**职责**：意图识别、任务拆解、Agent调度、结果聚合

```python
class OrchestratorAgent:
    """编排Agent - 负责整体任务调度"""
    
    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.task_planner = TaskPlanner()
        self.agent_registry = AgentRegistry()
    
    def process(self, user_input: str, context: dict) -> dict:
        # 1. 意图识别
        intent = self.intent_classifier.classify(user_input)
        # 意图类型: stock_analysis / quick_qa / report_search / backtest / unknown
        
        # 2. 任务规划
        plan = self.task_planner.create_plan(intent, context)
        
        # 3. Agent调度
        results = {}
        for step in plan.steps:
            agent = self.agent_registry.get(step.agent_name)
            results[step.output_key] = agent.execute(step.input)
        
        # 4. 结果聚合
        return self.aggregate(results)
```

#### 3.3.2 研报检索Agent（新增）

**职责**：基于RAG检索相关研报，提取关键观点

```python
class ReportRetrieverAgent(BaseAgent):
    """研报检索Agent"""
    
    def __init__(self, retriever: RAGRetriever):
        super().__init__(
            name="研报检索员",
            role="检索与分析券商研报"
        )
        self.retriever = retriever
    
    def analyze(self, query: str, stock_code: str = None) -> dict:
        # 1. 构建检索query
        search_query = f"{stock_code} {query}" if stock_code else query
        
        # 2. RAG检索
        docs = self.retriever.retrieve(
            query=search_query,
            filters={"doc_type": "report"},
            top_k=5
        )
        
        # 3. LLM提取关键观点
        prompt = f"""
        基于以下研报内容，提取关于"{query}"的关键观点：
        
        研报内容：
        {self._format_docs(docs)}
        
        请输出：
        1. 核心观点摘要
        2. 机构评级汇总
        3. 风险提示
        4. 信息来源标注
        """
        
        return self.invoke_llm(prompt)
```

#### 3.3.3 风控官Agent（新增）

**职责**：多维度风险评估、预警提示

```python
class RiskControllerAgent(BaseAgent):
    """风控官Agent"""
    
    RISK_DIMENSIONS = [
        "market_risk",      # 市场风险
        "liquidity_risk",   # 流动性风险
        "concentration_risk", # 集中度风险
        "valuation_risk",   # 估值风险
        "sentiment_risk",   # 情绪风险
    ]
    
    def analyze(self, analysis_results: dict) -> dict:
        # 1. 汇总各维度风险信号
        risk_signals = self._collect_risk_signals(analysis_results)
        
        # 2. 风险评分计算
        risk_scores = self._calculate_risk_scores(risk_signals)
        
        # 3. 生成风险报告
        risk_report = self._generate_risk_report(risk_scores)
        
        return {
            "overall_risk_level": self._get_overall_level(risk_scores),
            "risk_scores": risk_scores,
            "warnings": risk_report["warnings"],
            "suggestions": risk_report["suggestions"],
        }
```

### 3.4 工作流升级

#### 3.4.1 新版工作流设计

```python
class InvestmentWorkflowV2:
    """投资分析工作流 v2.0"""
    
    def _build_graph(self):
        workflow = StateGraph(InvestmentState)
        
        # 节点定义
        workflow.add_node("intent_recognition", self._intent_node)
        workflow.add_node("rag_retrieval", self._rag_retrieval_node)
        workflow.add_node("graph_query", self._graph_query_node)
        workflow.add_node("multi_analysis", self._multi_analysis_node)
        workflow.add_node("debate", self._debate_node)
        workflow.add_node("decision", self._decision_node)
        workflow.add_node("risk_control", self._risk_control_node)
        workflow.add_node("generate_report", self._report_node)
        
        # 条件路由
        workflow.add_conditional_edges(
            "intent_recognition",
            self._route_by_intent,
            {
                "quick_qa": "rag_retrieval",
                "deep_analysis": "graph_query",
                "backtest": "backtest_node",
            }
        )
        
        # 主流程边
        workflow.add_edge("rag_retrieval", "generate_report")
        workflow.add_edge("graph_query", "multi_analysis")
        workflow.add_edge("multi_analysis", "debate")
        workflow.add_edge("debate", "decision")
        workflow.add_edge("decision", "risk_control")
        workflow.add_edge("risk_control", "generate_report")
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
```

---

## 四、UI界面设计

### 4.1 页面导航结构

```
🏠 首页仪表盘
├── 自选股监控卡片
├── 今日市场热点词云
├── 最新研报推荐
└── 快速提问入口

💬 智能问答
├── 对话界面（ChatGPT风格）
├── 知识来源引用（可点击查看原文）
├── 相关问题推荐
└── 对话历史记录

📈 深度分析
├── 股票搜索输入框
├── 分析进度展示（Agent执行状态）
├── 多维度分析结果Tab页
│   ├── 基本面分析
│   ├── 技术面分析
│   ├── 资金面分析
│   ├── 舆情面分析
│   └── 研报观点汇总
├── 投资建议卡片
└── 风险评估仪表盘

🧪 策略回测
├── 策略选择/自定义
├── 参数配置面板
├── 回测结果图表
│   ├── 收益曲线
│   ├── 回撤曲线
│   └── 持仓分布
└── AI回测报告解读

📚 知识溯源
├── 搜索框
├── 知识图谱可视化
├── 检索结果列表
└── 文档详情查看
```

### 4.2 视觉风格规范

```css
/* 主色调 */
--primary-color: #0A84FF;      /* 科技蓝 */
--accent-color: #FFB800;       /* 财富金 */
--success-color: #00C853;      /* 涨/正面 */
--danger-color: #FF5252;       /* 跌/负面 */
--warning-color: #FF9800;      /* 警告 */

/* 背景色 */
--bg-primary: #0D1117;         /* 深色背景 */
--bg-secondary: #161B22;       /* 卡片背景 */
--bg-tertiary: #21262D;        /* 次级背景 */

/* 文字色 */
--text-primary: #F0F6FC;       /* 主要文字 */
--text-secondary: #8B949E;     /* 次要文字 */

/* 卡片样式 */
card {
    background: rgba(22, 27, 34, 0.8);
    border: 1px solid rgba(48, 54, 61, 0.5);
    border-radius: 12px;
    backdrop-filter: blur(10px);
}
```

### 4.3 交互设计要点

1. **流式输出**：Agent分析过程实时展示，让用户看到"思考过程"
2. **进度可视化**：工作流执行时显示当前节点和进度条
3. **知识溯源**：AI回答中引用的来源可点击跳转查看原文
4. **图表交互**：K线图、资金流向图支持缩放、悬停查看详情

---

## 五、实现路线规划

### Phase 1: RAG基础能力（优先级：高）

**目标**：搭建向量检索基础能力

**任务清单**：
- [ ] 安装依赖：chromadb, sentence-transformers
- [ ] 实现 `rag/embeddings.py`：文本向量化
- [ ] 实现 `rag/vector_store.py`：向量存储与检索
- [ ] 实现 `rag/retriever.py`：检索器封装
- [ ] 准备示例知识库数据（研报摘要、财报要点）
- [ ] 实现知识库导入脚本

**验收标准**：
- 能够对"茅台最新研报观点"进行语义检索
- 返回Top-5相关文档，包含来源信息

### Phase 2: Agent能力增强（优先级：高）

**目标**：扩展Agent能力，支持RAG调用

**任务清单**：
- [ ] 实现 `agents/orchestrator.py`：编排Agent
- [ ] 实现 `agents/researchers/report_retriever.py`：研报检索Agent
- [ ] 实现 `agents/analysts/capital_flow.py`：资金流分析Agent
- [ ] 实现 `agents/decision/risk_controller.py`：风控官Agent
- [ ] 升级 `graph/workflow.py`：集成新Agent

**验收标准**：
- 深度分析流程包含研报观点汇总
- 输出包含风险评估报告

### Phase 3: 知识图谱（优先级：中）

**目标**：实现GraphRAG能力

**任务清单**：
- [ ] 实现 `rag/knowledge_graph.py`：知识图谱管理
- [ ] 设计图谱Schema（公司、概念、事件等实体）
- [ ] 构建示例图谱数据（白酒板块、新能源板块）
- [ ] 实现多跳查询（如"茅台的竞争对手有哪些"）
- [ ] 融合向量检索与图谱查询

**验收标准**：
- 支持"白酒板块龙头"类概念查询
- 支持"茅台竞争对手"类关系查询

### Phase 4: UI产品化（优先级：高）

**目标**：打造可展示的Web界面

**任务清单**：
- [ ] 搭建Streamlit多页面应用结构
- [ ] 实现首页仪表盘
- [ ] 实现智能问答页面（对话+引用）
- [ ] 实现深度分析页面（Agent流程可视化）
- [ ] 实现知识溯源页面
- [ ] 优化UI样式（深色主题、玻璃态效果）

**验收标准**：
- 完整可运行的Web应用
- 支持股票分析完整流程

### Phase 5: 优化与文档（优先级：中）

**目标**：完善项目质量

**任务清单**：
- [ ] 性能优化：缓存、并发
- [ ] 异常处理：网络超时、API限流
- [ ] 代码注释与类型标注
- [ ] README更新：项目介绍、部署指南
- [ ] 准备面试演示Demo

---

## 六、技术实现要点

### 6.1 RAG检索优化策略

```python
# 混合检索：向量 + 关键词
class HybridRetriever:
    def retrieve(self, query: str, top_k: int = 5):
        # 1. 向量检索
        vector_results = self.vector_store.similarity_search(query, k=top_k * 2)
        
        # 2. 关键词检索 (BM25风格)
        keyword_results = self.keyword_search(query, k=top_k * 2)
        
        # 3. RRF融合重排
        return self.rrf_fusion(vector_results, keyword_results, top_k)

# 时效性加权
def rerank_by_freshness(results: List[Document]) -> List[Document]:
    """对检索结果按时效性重新排序"""
    for doc in results:
        days_old = (datetime.now() - doc.metadata["date"]).days
        freshness_score = 1.0 / (1 + days_old / 30)  # 月衰减
        doc.score = doc.score * 0.7 + freshness_score * 0.3
    return sorted(results, key=lambda x: x.score, reverse=True)
```

### 6.2 Prompt模板管理

```python
# config/prompts.py

SYSTEM_PROMPTS = {
    "orchestrator": """你是智汇投研的智能助手，负责理解用户需求并调度专业分析师。
    
    你的职责：
    1. 准确识别用户意图（股票分析/快速问答/研报检索/策略回测）
    2. 规划分析任务，决定需要调用哪些Agent
    3. 聚合各Agent结果，生成连贯的回答
    
    回答原则：
    - 专业但易懂，避免过度术语
    - 引用信息来源，保证可追溯
    - 明确区分事实与观点
    """,
    
    "fundamental_analyst": """你是一位资深基本面分析师...
    (保留原有prompt)
    """,
    
    "risk_controller": """你是一位严谨的风险控制官...
    
    你的职责：
    1. 从多个维度评估投资风险
    2. 识别潜在风险信号并预警
    3. 提供风险缓释建议
    
    风险维度：
    - 市场风险：整体市场环境、系统性风险
    - 流动性风险：成交量、换手率
    - 估值风险：PE/PB分位数、估值合理性
    - 情绪风险：舆情热度、市场情绪
    """,
}

def get_prompt(agent_name: str, context: dict = None) -> str:
    """获取Agent的System Prompt"""
    base_prompt = SYSTEM_PROMPTS.get(agent_name, "")
    if context:
        return base_prompt.format(**context)
    return base_prompt
```

### 6.3 流式输出实现

```python
# ui/components/chat.py

import streamlit as st
from typing import Generator

def stream_response(generator: Generator) -> None:
    """流式展示AI回复"""
    placeholder = st.empty()
    full_response = ""
    
    for chunk in generator:
        full_response += chunk
        placeholder.markdown(full_response + "▌")
    
    placeholder.markdown(full_response)

# Agent调用端
def analyze_stream(self, data: dict) -> Generator[str, None, None]:
    """流式分析"""
    prompt = self._build_prompt(data)
    
    for chunk in self.llm.stream(prompt):
        yield chunk.content
```

---

## 七、验收标准

### 7.1 功能验收清单

| 功能模块 | 验收标准 | 状态 |
|---------|---------|------|
| RAG检索 | 输入问题返回相关文档，支持来源引用 | ⬜ |
| 知识图谱 | 支持概念查询、关系查询 | ⬜ |
| 多Agent协作 | 分析流程包含5+个Agent协作 | ⬜ |
| 风险评估 | 输出包含多维度风险评分 | ⬜ |
| 智能问答 | 支持对话式交互，知识溯源 | ⬜ |
| 深度分析 | 完整分析报告，可复制下载 | ⬜ |
| UI界面 | 美观可交互，响应式布局 | ⬜ |

### 7.2 面试演示流程

1. **开场（30秒）**：项目背景介绍，解决什么问题
2. **架构讲解（1分钟）**：技术架构图，核心亮点
3. **功能演示（3分钟）**：
   - 智能问答：问一个复杂问题，展示知识溯源
   - 深度分析：输入股票代码，展示多Agent协作过程
   - 风险评估：展示风险报告
4. **技术深挖（2分钟）**：选一个技术点深入讲解（如RAG优化、Agent编排）
5. **总结（30秒）**：项目收获、后续规划

---

## 八、风险与应对

| 风险项 | 影响 | 应对措施 |
|-------|------|---------|
| LLM API限流 | 响应延迟 | 本地缓存、降级策略、异步处理 |
| 知识库数据不足 | 检索质量差 | 多数据源、数据增强 |
| 前端性能 | 用户体验差 | 懒加载、虚拟滚动 |
| 部署环境限制 | 无法演示 | Docker容器化、云端部署备选 |

---

**文档结束**

> 请审阅此文档，确认后我将开始实现。如有修改意见，请直接在文档中标注。
