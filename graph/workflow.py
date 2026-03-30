"""
LangGraph工作流定义 v2.0
集成RAG、知识图谱、多Agent协作
"""
from typing import TypedDict, Annotated, Sequence, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from loguru import logger
import operator

import sys
sys.path.append("..")
from tools.stock_data import AStockDataTool, get_stock_data, resolve_stock_input
from agents.analysts import FundamentalAnalyst, TechnicalAnalyst, SentimentAnalyst, NewsAnalyst
from agents.analysts.capital_flow import CapitalFlowAnalyst
from agents.researchers.debate import DebateRoom
from agents.researchers.report_retriever import ReportRetrieverAgent
from agents.decision import Trader, PortfolioManager
from agents.decision.risk_controller import RiskControllerAgent
from config.settings import get_config


class InvestmentState(TypedDict):
    """投资分析状态 v2.0"""
    # 输入
    stock_code: str
    risk_profile: str  # conservative/moderate/aggressive
    
    # 数据层
    stock_data: Dict[str, Any]
    
    # 分析师层
    fundamental_analysis: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    news_analysis: Dict[str, Any]
    capital_flow_analysis: Dict[str, Any]  # 新增
    
    # 研究员层
    report_view: Dict[str, Any]  # 新增：研报观点
    debate_result: Dict[str, Any]
    
    # 决策层
    trader_decision: Dict[str, Any]
    risk_assessment: Dict[str, Any]  # 新增
    pm_review: Dict[str, Any]
    
    # 输出
    final_report: str
    
    # 消息历史
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # 错误信息
    errors: list
    
    # 执行日志
    execution_log: list


class InvestmentWorkflow:
    """投资分析工作流 v2.0"""
    
    def __init__(self, llm=None, config: Dict[str, Any] = None, retriever=None):
        self.llm = llm
        self.config = config or get_config().agent.model_dump()
        self.stock_tool = AStockDataTool()
        self.retriever = retriever
        
        # 初始化各Agent
        self.fundamental_analyst = FundamentalAnalyst(llm=llm)
        self.technical_analyst = TechnicalAnalyst(llm=llm)
        self.sentiment_analyst = SentimentAnalyst(llm=llm)
        self.news_analyst = NewsAnalyst(llm=llm)
        self.capital_flow_analyst = CapitalFlowAnalyst(llm=llm)  # 新增
        
        # 研报检索Agent
        self.report_retriever = ReportRetrieverAgent(llm=llm, retriever=retriever)
        
        self.debate_room = DebateRoom(
            llm=llm,
            max_rounds=self.config.get("max_debate_rounds", 2)
        )
        
        self.trader = Trader(llm=llm)
        self.portfolio_manager = PortfolioManager(llm=llm)
        self.risk_controller = RiskControllerAgent(llm=llm)  # 新增
        
        # 构建工作流图
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建工作流图 v2.0"""
        workflow = StateGraph(InvestmentState)
        
        # 添加节点
        workflow.add_node("fetch_data", self._fetch_data_node)
        workflow.add_node("analyze_fundamental", self._analyze_fundamental_node)
        workflow.add_node("analyze_technical", self._analyze_technical_node)
        workflow.add_node("analyze_sentiment", self._analyze_sentiment_node)
        workflow.add_node("analyze_news", self._analyze_news_node)
        workflow.add_node("analyze_capital_flow", self._analyze_capital_flow_node)  # 新增
        workflow.add_node("retrieve_reports", self._retrieve_reports_node)  # 新增
        workflow.add_node("debate", self._debate_node)
        workflow.add_node("make_decision", self._make_decision_node)
        workflow.add_node("assess_risk", self._assess_risk_node)  # 新增
        workflow.add_node("review_decision", self._review_decision_node)
        workflow.add_node("generate_report", self._generate_report_node)
        
        # 设置入口
        workflow.set_entry_point("fetch_data")
        
        # 定义边：顺序执行分析师，避免 API 限流
        workflow.add_edge("fetch_data", "analyze_fundamental")
        workflow.add_edge("analyze_fundamental", "analyze_technical")
        workflow.add_edge("analyze_technical", "analyze_sentiment")
        workflow.add_edge("analyze_sentiment", "analyze_news")
        workflow.add_edge("analyze_news", "analyze_capital_flow")
        workflow.add_edge("analyze_capital_flow", "retrieve_reports")
        
        # 研报检索后进入辩论
        workflow.add_edge("retrieve_reports", "debate")
        
        # 辩论后决策
        workflow.add_edge("debate", "make_decision")
        
        # 决策后风险评估
        workflow.add_edge("make_decision", "assess_risk")
        
        # 风险评估后审核
        workflow.add_edge("assess_risk", "review_decision")
        
        # 审核后生成报告
        workflow.add_edge("review_decision", "generate_report")
        
        # 报告生成后结束
        workflow.add_edge("generate_report", END)
        
        return workflow.compile()
    
    # ========== 节点函数 ==========
    
    def _fetch_data_node(self, state: InvestmentState) -> dict:
        """数据获取节点"""
        user_input = state["stock_code"]
        logger.info(f"解析股票输入: {user_input}")
        
        try:
            # 解析用户输入（支持代码、名称、拼音首字母）
            stock_code, stock_name = resolve_stock_input(user_input)
            logger.info(f"解析结果: {stock_code} ({stock_name})")
            
            data = get_stock_data(stock_code)
            
            # 确保名称正确显示
            if data.get("basic_info"):
                data["basic_info"]["user_input"] = user_input  # 保存用户原始输入
            
            return {
                "stock_data": data,
                "messages": [AIMessage(content=f"已获取 {stock_code} ({stock_name}) 的股票数据")]
            }
        except Exception as e:
            logger.error(f"数据获取失败: {e}")
            return {
                "stock_data": {},
                "errors": [f"数据获取失败: {str(e)}"],
                "messages": [AIMessage(content=f"数据获取失败: {str(e)}")]
            }
    
    def _analyze_fundamental_node(self, state: InvestmentState) -> dict:
        """基本面分析节点"""
        logger.info("执行基本面分析...")
        stock_data = state.get("stock_data", {})
        
        try:
            result = self.fundamental_analyst.analyze(stock_data)
            return {
                "fundamental_analysis": result,
                "messages": [AIMessage(content=f"[基本面分析师] 分析完成")]
            }
        except Exception as e:
            logger.error(f"基本面分析失败: {e}")
            return {
                "fundamental_analysis": {"error": str(e)},
                "errors": [f"基本面分析失败: {str(e)}"]
            }
    
    def _analyze_technical_node(self, state: InvestmentState) -> dict:
        """技术面分析节点"""
        logger.info("执行技术面分析...")
        stock_data = state.get("stock_data", {})
        
        try:
            result = self.technical_analyst.analyze(stock_data)
            return {
                "technical_analysis": result,
                "messages": [AIMessage(content=f"[技术分析师] 分析完成")]
            }
        except Exception as e:
            logger.error(f"技术面分析失败: {e}")
            return {
                "technical_analysis": {"error": str(e)},
                "errors": [f"技术面分析失败: {str(e)}"]
            }
    
    def _analyze_sentiment_node(self, state: InvestmentState) -> dict:
        """情绪面分析节点"""
        logger.info("执行情绪面分析...")
        stock_data = state.get("stock_data", {})
        
        try:
            result = self.sentiment_analyst.analyze(stock_data)
            return {
                "sentiment_analysis": result,
                "messages": [AIMessage(content=f"[情绪分析师] 分析完成")]
            }
        except Exception as e:
            logger.error(f"情绪面分析失败: {e}")
            return {
                "sentiment_analysis": {"error": str(e)},
                "errors": [f"情绪面分析失败: {str(e)}"]
            }
    
    def _analyze_news_node(self, state: InvestmentState) -> dict:
        """新闻面分析节点"""
        logger.info("执行新闻面分析...")
        stock_data = state.get("stock_data", {})
        
        try:
            result = self.news_analyst.analyze(stock_data)
            return {
                "news_analysis": result,
                "messages": [AIMessage(content=f"[新闻分析师] 分析完成")]
            }
        except Exception as e:
            logger.error(f"新闻面分析失败: {e}")
            return {
                "news_analysis": {"error": str(e)},
                "errors": [f"新闻面分析失败: {str(e)}"]
            }
    
    def _analyze_capital_flow_node(self, state: InvestmentState) -> dict:
        """资金流分析节点（新增）"""
        logger.info("执行资金流分析...")
        stock_data = state.get("stock_data", {})
        
        try:
            result = self.capital_flow_analyst.analyze(stock_data)
            return {
                "capital_flow_analysis": result,
                "messages": [AIMessage(content=f"[资金流分析师] 分析完成")]
            }
        except Exception as e:
            logger.error(f"资金流分析失败: {e}")
            return {
                "capital_flow_analysis": {"error": str(e)},
                "errors": [f"资金流分析失败: {str(e)}"]
            }
    
    def _retrieve_reports_node(self, state: InvestmentState) -> dict:
        """研报检索节点（新增）"""
        logger.info("执行研报检索...")
        stock_data = state.get("stock_data", {})
        
        try:
            result = self.report_retriever.analyze({"stock_data": stock_data})
            return {
                "report_view": result,
                "messages": [AIMessage(content=f"[研报检索员] 检索完成，找到 {result.get('retrieved_reports', 0)} 份研报")]
            }
        except Exception as e:
            logger.error(f"研报检索失败: {e}")
            return {
                "report_view": {"error": str(e)},
                "errors": [f"研报检索失败: {str(e)}"]
            }
    
    def _debate_node(self, state: InvestmentState) -> dict:
        """辩论节点"""
        logger.info("执行红蓝军辩论...")
        
        analysis_results = {
            "fundamental": state.get("fundamental_analysis", {}),
            "technical": state.get("technical_analysis", {}),
            "sentiment": state.get("sentiment_analysis", {}),
            "news": state.get("news_analysis", {}),
            "capital_flow": state.get("capital_flow_analysis", {}),
            "report_view": state.get("report_view", {})
        }
        
        try:
            result = self.debate_room.conduct_debate(analysis_results)
            debate_summary = self.debate_room.get_debate_summary()
            
            return {
                "debate_result": result,
                "messages": [AIMessage(content=f"[辩论室] 完成{result.get('total_rounds', 0)}轮辩论")]
            }
        except Exception as e:
            logger.error(f"辩论失败: {e}")
            return {
                "debate_result": {"error": str(e)},
                "errors": [f"辩论失败: {str(e)}"]
            }
    
    def _make_decision_node(self, state: InvestmentState) -> dict:
        """决策节点"""
        logger.info("交易员做出决策...")
        
        analysis_results = {
            "basic_info": state.get("stock_data", {}).get("basic_info", {}),
            "fundamental": state.get("fundamental_analysis", {}),
            "technical": state.get("technical_analysis", {}),
            "sentiment": state.get("sentiment_analysis", {}),
            "news": state.get("news_analysis", {}),
            "capital_flow": state.get("capital_flow_analysis", {}),
            "report_view": state.get("report_view", {})
        }
        
        debate_result = state.get("debate_result", {})
        
        try:
            result = self.trader.make_decision(analysis_results, debate_result)
            return {
                "trader_decision": result,
                "messages": [AIMessage(content=f"[交易员] 决策: {result.get('decision', 'N/A')}")]
            }
        except Exception as e:
            logger.error(f"决策失败: {e}")
            return {
                "trader_decision": {"error": str(e), "decision": "持有"},
                "errors": [f"决策失败: {str(e)}"]
            }
    
    def _assess_risk_node(self, state: InvestmentState) -> dict:
        """风险评估节点（新增）"""
        logger.info("执行风险评估...")
        
        risk_input = {
            "fundamental": state.get("fundamental_analysis", {}),
            "technical": state.get("technical_analysis", {}),
            "sentiment": state.get("sentiment_analysis", {}),
            "capital_flow": state.get("capital_flow_analysis", {}),
            "stock_data": state.get("stock_data", {})
        }
        
        try:
            result = self.risk_controller.analyze(risk_input)
            return {
                "risk_assessment": result,
                "messages": [AIMessage(content=f"[风控官] 风险等级: {result.get('overall_risk_level', 'N/A')}")]
            }
        except Exception as e:
            logger.error(f"风险评估失败: {e}")
            return {
                "risk_assessment": {"error": str(e), "overall_risk_level": "未知"},
                "errors": [f"风险评估失败: {str(e)}"]
            }
    
    def _review_decision_node(self, state: InvestmentState) -> dict:
        """审核节点"""
        logger.info("投资组合经理审核决策...")
        
        trader_decision = state.get("trader_decision", {})
        risk_assessment = state.get("risk_assessment", {})
        risk_profile = state.get("risk_profile", "moderate")
        
        try:
            result = self.portfolio_manager.review_decision(
                trader_decision,
                risk_profile=risk_profile
            )
            
            # 考虑风险评估调整建议
            if risk_assessment.get("overall_risk_score", 50) > 70:
                result["approval_status"] = "有条件批准"
                result["risk_adjustment"] = "根据风险评估结果，建议降低仓位"
            
            return {
                "pm_review": result,
                "messages": [AIMessage(content=f"[投资组合经理] 审批状态: {result.get('approval_status', 'N/A')}")]
            }
        except Exception as e:
            logger.error(f"审核失败: {e}")
            return {
                "pm_review": {"error": str(e), "approval_status": "有条件批准"},
                "errors": [f"审核失败: {str(e)}"]
            }
    
    def _generate_report_node(self, state: InvestmentState) -> dict:
        """报告生成节点"""
        logger.info("生成最终报告...")
        
        stock_data = state.get("stock_data", {})
        stock_info = stock_data.get("basic_info", {})
        
        analysis_results = {
            "fundamental": state.get("fundamental_analysis", {}),
            "technical": state.get("technical_analysis", {}),
            "sentiment": state.get("sentiment_analysis", {}),
            "news": state.get("news_analysis", {}),
            "capital_flow": state.get("capital_flow_analysis", {}),
            "report_view": state.get("report_view", {})
        }
        
        debate_result = state.get("debate_result", {})
        trader_decision = state.get("trader_decision", {})
        pm_review = state.get("pm_review", {})
        risk_assessment = state.get("risk_assessment", {})
        
        try:
            report = self.portfolio_manager.generate_final_report(
                stock_info=stock_info,
                analysis_results=analysis_results,
                debate_result=debate_result,
                trader_decision=trader_decision,
                pm_review=pm_review
            )
            
            # 添加风险评估摘要
            if risk_assessment:
                risk_summary = f"""

## 风险评估摘要

- **整体风险等级**: {risk_assessment.get('overall_risk_level', '未知')}
- **风险评分**: {risk_assessment.get('overall_risk_score', 'N/A')}/100
- **建议仓位上限**: {risk_assessment.get('position_limit', 'N/A')*100:.0f}%
- **建议止损线**: {risk_assessment.get('stop_loss_suggestion', 'N/A')*100:.1f}%

**风险提示**:
"""
                warnings = risk_assessment.get("warnings", [])
                for warning in warnings[:3]:
                    risk_summary += f"- {warning}\n"
                
                report += risk_summary
            
            return {
                "final_report": report,
                "messages": [AIMessage(content="[系统] 报告生成完成")]
            }
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            return {
                "final_report": f"报告生成失败: {str(e)}",
                "errors": [f"报告生成失败: {str(e)}"]
            }
    
    # ========== 执行接口 ==========
    
    def run(self, stock_code: str, risk_profile: str = "moderate") -> Dict[str, Any]:
        """
        执行完整的投资分析流程
        Args:
            stock_code: 股票代码
            risk_profile: 风险偏好 conservative/moderate/aggressive
        Returns:
            完整的分析结果
        """
        initial_state: InvestmentState = {
            "stock_code": stock_code,
            "risk_profile": risk_profile,
            "stock_data": {},
            "fundamental_analysis": {},
            "technical_analysis": {},
            "sentiment_analysis": {},
            "news_analysis": {},
            "capital_flow_analysis": {},
            "report_view": {},
            "debate_result": {},
            "trader_decision": {},
            "risk_assessment": {},
            "pm_review": {},
            "final_report": "",
            "messages": [],
            "errors": [],
            "execution_log": []
        }
        
        # 执行工作流
        final_state = self.graph.invoke(initial_state)
        
        return final_state
    
    def stream(self, stock_code: str, risk_profile: str = "moderate"):
        """
        流式执行，返回每一步的结果
        用于前端实时展示进度
        """
        initial_state: InvestmentState = {
            "stock_code": stock_code,
            "risk_profile": risk_profile,
            "stock_data": {},
            "fundamental_analysis": {},
            "technical_analysis": {},
            "sentiment_analysis": {},
            "news_analysis": {},
            "capital_flow_analysis": {},
            "report_view": {},
            "debate_result": {},
            "trader_decision": {},
            "risk_assessment": {},
            "pm_review": {},
            "final_report": "",
            "messages": [],
            "errors": [],
            "execution_log": []
        }
        
        for event in self.graph.stream(initial_state):
            yield event