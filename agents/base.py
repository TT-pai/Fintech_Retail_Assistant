"""
Agent基类模块
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from loguru import logger

import sys
sys.path.append("..")
from config.settings import get_config, get_model_for_task


class AgentState(BaseModel):
    """Agent状态"""
    agent_name: str
    analysis_result: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    reasoning: str = ""


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        llm: Optional[BaseChatModel] = None
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = llm or self._get_default_llm()
        self.state = AgentState(agent_name=name)
    
    def _get_default_llm(self) -> BaseChatModel:
        """获取默认LLM"""
        config = get_config()
        model_name = get_model_for_task("deep_think")  # 从映射获取模型名
        
        if config.llm.provider == "openai":
            return ChatOpenAI(
                model=model_name,
                api_key=config.llm.openai_api_key,
                base_url=config.llm.openai_base_url,
                temperature=0.7
            )
        elif config.llm.provider == "anthropic":
            # Anthropic 通过 OpenAI 兼容接口（如阿里云 DashScope）
            return ChatOpenAI(
                model=model_name,
                api_key=config.llm.anthropic_api_key or config.llm.openai_api_key,
                base_url=config.llm.anthropic_base_url or config.llm.openai_base_url,
                temperature=0.7
            )
        elif config.llm.provider == "zhipuai":
            from langchain_community.chat_models import ChatZhipuAI
            return ChatZhipuAI(
                model=model_name,
                api_key=config.llm.zhipuai_api_key,
                temperature=0.7
            )
        elif config.llm.provider == "deepseek":
            return ChatOpenAI(
                model=model_name,
                api_key=config.llm.deepseek_api_key,
                base_url=config.llm.deepseek_base_url,
                temperature=0.7
            )
        elif config.llm.provider == "qwen":
            from langchain_community.chat_models import ChatTongyi
            return ChatTongyi(
                model=model_name,
                dashscope_api_key=config.llm.dashscope_api_key,
                temperature=0.7
            )
        else:
            # 默认使用OpenAI兼容接口（支持 ollama 或其他兼容接口）
            return ChatOpenAI(
                model=model_name,
                api_key=config.llm.openai_api_key or "sk-dummy",
                base_url=config.llm.ollama_base_url if config.llm.provider == "ollama" else config.llm.openai_base_url,
                temperature=0.7
            )
    
    @abstractmethod
    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析方法，由子类实现
        Args:
            data: 输入数据
        Returns:
            分析结果字典
        """
        pass
    
    def invoke_llm(
        self, 
        user_input: str, 
        system_message: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """调用LLM，带重试机制"""
        import time
        
        messages = [
            SystemMessage(content=system_message or self.system_prompt),
            HumanMessage(content=user_input)
        ]
        
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                if response.content:
                    return response.content
                else:
                    raise ValueError("LLM returned empty content")
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # 如果是限流错误，等待后重试
                if "rate" in error_msg.lower() or "limit" in error_msg.lower() or "null value" in error_msg.lower():
                    wait_time = 2 ** attempt + 1  # 指数退避
                    logger.warning(f"{self.name} LLM调用失败 (尝试 {attempt+1}/{max_retries}): {e}, 等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)
                else:
                    # 其他错误直接抛出
                    break
        
        logger.error(f"{self.name} LLM调用失败: {last_error}")
        return f"分析失败: {str(last_error)}"
    
    def update_state(self, result: Dict[str, Any], confidence: float, reasoning: str):
        """更新Agent状态"""
        self.state.analysis_result = result
        self.state.confidence = confidence
        self.state.reasoning = reasoning



