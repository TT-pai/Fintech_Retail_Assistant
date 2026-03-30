"""
智汇投研 - 配置管理模块
支持多LLM提供商配置
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal, Dict, Any
from functools import lru_cache


class LLMConfig(BaseSettings):
    """LLM配置"""
    provider: Literal["openai", "zhipuai", "deepseek", "qwen", "ollama"] = "openai"
    
    # OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    
    # 智谱AI
    zhipuai_api_key: str = ""
    
    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    
    # 通义千问
    dashscope_api_key: str = ""
    
    # Ollama本地
    ollama_base_url: str = "http://localhost:11434"
    
    # 模型选择（可在 .env 中配置覆盖）
    # 可选模型: qwen3-max, qwen3-coder-plus, qwen3-vl-plus, qwen3-235b-a22b-thinking-2507,
    #          deepseek-v3.2, kimi-k2, kimi-k2-0905, iflow-rome-30ba3b
    deep_think_model: str = "qwen3-max"      # 用于复杂推理的模型
    quick_think_model: str = "qwen3-32b"  # 用于快速任务的模型
    
    class Config:
        env_file = ".env"
        env_prefix = ""


class AgentConfig(BaseSettings):
    """Agent配置"""
    # 辩论轮数
    max_debate_rounds: int = 2
    
    # 分析师并行处理
    parallel_analysis: bool = True
    
    # 记忆系统
    enable_memory: bool = True
    memory_db_path: str = "./data/memory"
    
    # 日志级别
    log_level: str = "INFO"


class AppConfig(BaseSettings):
    """应用总配置"""
    app_name: str = "智汇投研"
    app_version: str = "0.1.0"
    debug: bool = True
    
    llm: LLMConfig = Field(default_factory=LLMConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)


@lru_cache()
def get_config() -> AppConfig:
    """获取配置单例"""
    return AppConfig()


# iFlow 可用模型列表
IFLOW_AVAILABLE_MODELS = [
    "qwen3-max",                        # 通义千问旗舰模型
    "qwen3-coder-plus",                 # 通义千问代码模型
    "qwen3-vl-plus",                    # 通义千问视觉模型
    "qwen3-235b-a22b-thinking-2507",    # 通义千问思维链模型
    "deepseek-v3.2",                    # DeepSeek 模型
    "kimi-k2",                          # Kimi K2 模型
    "kimi-k2-0905",                     # Kimi K2 特定版本
    "iflow-rome-30ba3b",                # iFlow 自研模型
]

# 各提供商的模型映射
PROVIDER_MODELS: Dict[str, Dict[str, str]] = {
    "openai": {
        "deep_think": "qwen3-max",      # iFlow - 复杂推理任务
        "quick_think": "qwen3-32b"  # iFlow - 快速任务
    },
    "zhipuai": {
        "deep_think": "glm-4-flash",
        "quick_think": "glm-4-flash"
    },
    "deepseek": {
        "deep_think": "deepseek-chat",
        "quick_think": "deepseek-chat"
    },
    "qwen": {
        "deep_think": "qwen-turbo",
        "quick_think": "qwen-turbo"
    },
    "ollama": {
        "deep_think": "llama3:8b",
        "quick_think": "llama3:8b"
    }
}


def get_model_for_task(task_type: Literal["deep_think", "quick_think"]) -> str:
    """
    根据任务类型获取对应模型
    优先使用用户在 .env 中配置的模型，否则使用默认映射
    """
    config = get_config()
    
    # 优先使用用户配置的模型
    if task_type == "deep_think" and config.llm.deep_think_model:
        return config.llm.deep_think_model
    elif task_type == "quick_think" and config.llm.quick_think_model:
        return config.llm.quick_think_model
    
    # 否则使用默认映射
    provider = config.llm.provider
    return PROVIDER_MODELS.get(provider, {}).get(task_type, "qwen3-max")
