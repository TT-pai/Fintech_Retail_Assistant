"""
智汇投研 - 主入口文件
"""
import os
import sys
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import get_config
from graph.workflow import InvestmentWorkflow


def setup_logging():
    """配置日志"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/fintech_assistant_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )


def main():
    """主函数 - 命令行入口"""
    # 加载环境变量
    load_dotenv()
    
    # 配置日志
    setup_logging()
    
    # 获取配置
    config = get_config()
    logger.info(f"启动 {config.app_name} v{config.app_version}")
    logger.info(f"LLM Provider: {config.llm.provider}")
    
    # 创建工作流
    workflow = InvestmentWorkflow()
    
    # 命令行交互
    print("\n" + "="*60)
    print("  智汇投研 - 基于多智能体的AI投研助手")
    print("="*60)
    
    while True:
        print("\n请输入股票代码（如 000001, 600000）或输入 'q' 退出:")
        user_input = input(">>> ").strip()
        
        if user_input.lower() == 'q':
            print("感谢使用，再见！")
            break
        
        if not user_input:
            continue
        
        # 询问风险偏好
        print("\n请选择您的风险偏好:")
        print("1. 保守型（低风险）")
        print("2. 稳健型（中风险）")
        print("3. 激进型（高风险）")
        
        risk_choice = input("请选择 (1/2/3, 默认2): ").strip() or "2"
        risk_map = {"1": "conservative", "2": "moderate", "3": "aggressive"}
        risk_profile = risk_map.get(risk_choice, "moderate")
        
        print(f"\n正在分析 {user_input}，请稍候...\n")
        
        try:
            # 执行分析
            result = workflow.run(user_input, risk_profile)
            
            # 输出报告
            print("\n" + "="*60)
            print(result.get("final_report", "报告生成失败"))
            print("="*60)
            
            # 显示错误（如有）
            errors = result.get("errors", [])
            if errors:
                print("\n⚠️  分析过程中的警告:")
                for err in errors:
                    print(f"  - {err}")
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            print(f"\n分析失败: {str(e)}")


if __name__ == "__main__":
    main()