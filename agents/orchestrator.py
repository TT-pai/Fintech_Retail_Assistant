"""
编排Agent
负责意图识别、任务规划、Agent调度、结果聚合
"""
from typing import Dict, Any, List, Optional, Literal
from enum import Enum
from loguru import logger
import json

from agents.base import BaseAgent
from config.prompts import get_prompt, get_intent_classification_prompt


class IntentType(str, Enum):
    """意图类型"""
    STOCK_ANALYSIS = "stock_analysis"
    QUICK_QA = "quick_qa"
    REPORT_SEARCH = "report_search"
    BACKTEST = "backtest"
    UNKNOWN = "unknown"


class TaskStep:
    """任务步骤"""
    
    def __init__(
        self,
        step_id: str,
        agent_name: str,
        description: str,
        input_mapping: Dict[str, str],
        output_key: str
    ):
        self.step_id = step_id
        self.agent_name = agent_name
        self.description = description
        self.input_mapping = input_mapping
        self.output_key = output_key


class TaskPlan:
    """任务计划"""
    
    def __init__(self, intent: IntentType, steps: List[TaskStep]):
        self.intent = intent
        self.steps = steps


class OrchestratorAgent(BaseAgent):
    """编排Agent"""
    
    def __init__(self, llm=None):
        super().__init__(
            name="编排助手",
            role="理解用户意图，调度专业分析师团队",
            system_prompt=get_prompt("orchestrator"),
            llm=llm
        )
        
        # 注册可用的Agent
        self.agent_registry: Dict[str, Any] = {}
        
    def register_agent(self, name: str, agent: Any) -> None:
        """注册Agent"""
        self.agent_registry[name] = agent
        logger.info(f"注册Agent: {name}")
    
    def classify_intent(self, user_input: str) -> IntentType:
        """
        意图分类
        
        Args:
            user_input: 用户输入
            
        Returns:
            意图类型
        """
        # 简单规则匹配（可替换为LLM分类）
        input_lower = user_input.lower()
        
        # 股票分析意图检测
        stock_keywords = ["分析", "评估", "看看", "怎么样", "如何"]
        has_stock_code = self._contains_stock_code(user_input)
        has_stock_keyword = any(kw in input_lower for kw in stock_keywords)
        
        if has_stock_code and has_stock_keyword:
            return IntentType.STOCK_ANALYSIS
        
        # 研报检索
        if "研报" in input_lower or "报告" in input_lower or "券商观点" in input_lower:
            return IntentType.REPORT_SEARCH
        
        # 策略回测
        if "回测" in input_lower or "策略" in input_lower:
            return IntentType.BACKTEST
        
        # 快速问答
        if len(user_input) < 30 or "?" in user_input or "？" in user_input:
            return IntentType.QUICK_QA
        
        return IntentType.UNKNOWN
    
    def _contains_stock_code(self, text: str) -> bool:
        """检测是否包含股票代码"""
        import re
        # 6位数字股票代码
        if re.search(r'\b[036]\d{5}\b', text):
            return True
        # 常见股票名称
        common_stocks = [
            "茅台", "五粮液", "宁德时代", "比亚迪", "腾讯", "阿里",
            "平安", "招商银行", "美的", "格力", "中芯国际"
        ]
        return any(stock in text for stock in common_stocks)
    
    def create_plan(self, intent: IntentType, context: Dict[str, Any]) -> TaskPlan:
        """
        创建任务计划
        
        Args:
            intent: 意图类型
            context: 上下文
            
        Returns:
            任务计划
        """
        if intent == IntentType.STOCK_ANALYSIS:
            return TaskPlan(
                intent=intent,
                steps=[
                    TaskStep("1", "data_fetcher", "获取股票数据", {}, "stock_data"),
                    TaskStep("2", "fundamental_analyst", "基本面分析", {"stock_data": "stock_data"}, "fundamental"),
                    TaskStep("3", "technical_analyst", "技术面分析", {"stock_data": "stock_data"}, "technical"),
                    TaskStep("4", "capital_flow_analyst", "资金面分析", {"stock_data": "stock_data"}, "capital_flow"),
                    TaskStep("5", "sentiment_analyst", "情绪面分析", {"stock_data": "stock_data"}, "sentiment"),
                    TaskStep("6", "report_retriever", "研报观点汇总", {"stock_data": "stock_data"}, "report_view"),
                    TaskStep("7", "debate", "多空辩论", {}, "debate_result"),
                    TaskStep("8", "portfolio_manager", "投资决策", {}, "decision"),
                    TaskStep("9", "risk_controller", "风险评估", {}, "risk_assessment"),
                    TaskStep("10", "report_generator", "生成报告", {}, "final_report"),
                ]
            )
        
        elif intent == IntentType.QUICK_QA:
            return TaskPlan(
                intent=intent,
                steps=[
                    TaskStep("1", "qa_assistant", "快速问答", {}, "answer"),
                ]
            )
        
        elif intent == IntentType.REPORT_SEARCH:
            return TaskPlan(
                intent=intent,
                steps=[
                    TaskStep("1", "report_retriever", "研报检索", {}, "reports"),
                ]
            )
        
        elif intent == IntentType.BACKTEST:
            return TaskPlan(
                intent=intent,
                steps=[
                    TaskStep("1", "backtest_engine", "策略回测", {}, "backtest_result"),
                ]
            )
        
        else:
            return TaskPlan(
                intent=intent,
                steps=[
                    TaskStep("1", "qa_assistant", "通用问答", {}, "answer"),
                ]
            )
    
    def execute_plan(self, plan: TaskPlan, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务计划
        
        Args:
            plan: 任务计划
            context: 上下文
            
        Returns:
            执行结果
        """
        results = context.copy()
        execution_log = []
        
        for step in plan.steps:
            logger.info(f"执行步骤: {step.step_id} - {step.description}")
            
            # 获取Agent
            agent = self.agent_registry.get(step.agent_name)
            if not agent:
                logger.warning(f"Agent未注册: {step.agent_name}")
                continue
            
            # 准备输入
            step_input = {}
            for src_key, dst_key in step.input_mapping.items():
                step_input[dst_key] = results.get(src_key)
            
            # 执行
            try:
                if hasattr(agent, 'analyze'):
                    result = agent.analyze(step_input)
                elif hasattr(agent, 'execute'):
                    result = agent.execute(step_input)
                else:
                    result = {"error": f"Agent {step.agent_name} 没有可执行的方法"}
                
                results[step.output_key] = result
                execution_log.append({
                    "step_id": step.step_id,
                    "agent": step.agent_name,
                    "status": "success"
                })
                
            except Exception as e:
                logger.error(f"执行步骤失败: {step.step_id}, {e}")
                results[step.output_key] = {"error": str(e)}
                execution_log.append({
                    "step_id": step.step_id,
                    "agent": step.agent_name,
                    "status": "failed",
                    "error": str(e)
                })
        
        results["execution_log"] = execution_log
        return results
    
    def process(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入
            context: 上下文
            
        Returns:
            处理结果
        """
        context = context or {}
        context["user_input"] = user_input
        
        # 1. 意图识别
        intent = self.classify_intent(user_input)
        logger.info(f"识别意图: {intent.value}")
        context["intent"] = intent.value
        
        # 2. 创建任务计划
        plan = self.create_plan(intent, context)
        logger.info(f"任务计划: {len(plan.steps)} 个步骤")
        
        # 3. 执行任务
        results = self.execute_plan(plan, context)
        
        return results
    
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """实现抽象方法"""
        user_input = data.get("user_input", "")
        return self.process(user_input, data)


class IntentClassifier:
    """意图分类器（基于LLM）"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def classify(self, user_input: str) -> IntentType:
        """使用LLM进行意图分类"""
        prompt = get_intent_classification_prompt()
        
        try:
            response = self.llm.invoke([
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input}
            ])
            
            intent_str = response.content.strip().lower()
            
            # 映射到IntentType
            mapping = {
                "stock_analysis": IntentType.STOCK_ANALYSIS,
                "quick_qa": IntentType.QUICK_QA,
                "report_search": IntentType.REPORT_SEARCH,
                "backtest": IntentType.BACKTEST,
            }
            
            return mapping.get(intent_str, IntentType.UNKNOWN)
            
        except Exception as e:
            logger.error(f"意图分类失败: {e}")
            return IntentType.UNKNOWN
