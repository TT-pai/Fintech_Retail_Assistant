"""
A股数据获取工具
使用 Yahoo Finance 作为数据源
"""
import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from loguru import logger
import re
import os
import json


# 股票列表缓存（用于名称/拼音搜索）
_stock_list_cache: List[Dict[str, str]] = None


def _load_stock_list() -> List[Dict[str, str]]:
    """加载股票列表缓存"""
    global _stock_list_cache
    
    if _stock_list_cache is not None:
        return _stock_list_cache
    
    # 尝试从多个路径加载
    cache_paths = [
        os.path.join(os.path.dirname(__file__), "..", "data", "market_cache", "stock_list.json"),
        os.path.join(os.path.dirname(__file__), "stock_list_cache.json"),
    ]
    
    for cache_path in cache_paths:
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    _stock_list_cache = data.get("data", data) if isinstance(data, dict) else data
                    logger.info(f"加载股票列表缓存: {len(_stock_list_cache)} 只股票")
                    return _stock_list_cache
            except Exception as e:
                logger.warning(f"加载股票列表失败: {e}")
    
    # 尝试使用 MarketDataTool
    try:
        from tools.market_data import get_all_a_stocks
        _stock_list_cache = get_all_a_stocks()
        return _stock_list_cache
    except Exception as e:
        logger.warning(f"使用 MarketDataTool 加载股票列表失败: {e}")
    
    _stock_list_cache = []
    return _stock_list_cache


def search_stock_code(query: str) -> Tuple[str, str]:
    """
    根据股票代码、名称或拼音搜索股票
    
    Args:
        query: 股票代码(如000001)、名称(如平安银行)或拼音首字母
    
    Returns:
        (股票代码, 股票名称) 元组
    
    Raises:
        ValueError: 找不到匹配的股票
    """
    query = query.strip()
    query_upper = query.upper()
    
    # 1. 如果是6位数字代码，直接返回
    if re.match(r'^\d{6}$', query):
        # 尝试查找名称
        stock_list = _load_stock_list()
        for stock in stock_list:
            if stock.get("code") == query:
                return stock["code"], stock.get("name", query)
        return query, query
    
    # 2. 名称或拼音搜索
    stock_list = _load_stock_list()
    
    # 精确匹配名称
    for stock in stock_list:
        if stock.get("name", "") == query:
            return stock["code"], stock["name"]
    
    # 部分匹配名称
    partial_matches = []
    for stock in stock_list:
        name = stock.get("name", "")
        if query in name:
            partial_matches.append(stock)
    
    if len(partial_matches) == 1:
        return partial_matches[0]["code"], partial_matches[0]["name"]
    elif len(partial_matches) > 1:
        # 多个匹配，返回最短的（最精确的）
        partial_matches.sort(key=lambda x: len(x.get("name", "")))
        return partial_matches[0]["code"], partial_matches[0]["name"]
    
    # 拼音首字母匹配
    pinyin_matches = []
    for stock in stock_list:
        pinyin = stock.get("pinyin", "")
        if pinyin and query_upper in pinyin.upper():
            pinyin_matches.append(stock)
    
    if pinyin_matches:
        return pinyin_matches[0]["code"], pinyin_matches[0]["name"]
    
    raise ValueError(f"找不到匹配的股票: {query}")


def resolve_stock_input(user_input: str) -> Tuple[str, str]:
    """解析用户输入"""
    return search_stock_code(user_input)


class AStockDataTool:
    """A股数据获取工具（Yahoo Finance 数据源）"""
    
    def __init__(self):
        self.cache: Dict[str, pd.DataFrame] = {}
    
    def _get_yahoo_symbol(self, stock_code: str) -> str:
        """将A股代码转换为Yahoo Finance格式"""
        if stock_code.startswith('6'):
            return f"{stock_code}.SS"  # 上海交易所
        else:
            return f"{stock_code}.SZ"  # 深圳交易所
    
    def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        try:
            symbol = self._get_yahoo_symbol(stock_code)
            stock = yf.Ticker(symbol)
            info = stock.info
            
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            prev_close = info.get('previousClose', info.get('regularMarketPreviousClose', current_price))
            
            return {
                "code": stock_code,
                "name": info.get('shortName', info.get('longName', 'Unknown')),
                "price": float(current_price) if current_price else 0,
                "prev_close": float(prev_close) if prev_close else 0,
                "change_amount": round(float(current_price - prev_close), 2) if current_price and prev_close else 0,
                "change_percent": round((current_price - prev_close) / prev_close * 100, 2) if current_price and prev_close else 0,
                "volume": int(info.get('volume', info.get('regularMarketVolume', 0))),
                "turnover": float(info.get('marketCap', 0)),
                "high": float(info.get('dayHigh', info.get('regularMarketDayHigh', current_price))),
                "low": float(info.get('dayLow', info.get('regularMarketDayLow', current_price))),
                "open": float(info.get('open', info.get('regularMarketOpen', current_price))),
            }
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return {"error": str(e), "code": stock_code}
    
    def get_stock_history(self, stock_code: str, period: str = "6mo") -> pd.DataFrame:
        """获取股票历史数据"""
        try:
            symbol = self._get_yahoo_symbol(stock_code)
            stock = yf.Ticker(symbol)
            df = stock.history(period=period)
            
            if df.empty:
                return pd.DataFrame()
            
            df = df.reset_index()
            df = df.rename(columns={
                'Date': '日期',
                'Open': '开盘',
                'Close': '收盘',
                'High': '最高',
                'Low': '最低',
                'Volume': '成交量'
            })
            
            if hasattr(df['日期'].iloc[0], 'strftime'):
                df['日期'] = df['日期'].dt.strftime('%Y-%m-%d')
            
            return df[['日期', '开盘', '收盘', '最高', '最低', '成交量']]
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_financial_report(self, stock_code: str) -> Dict[str, Any]:
        """获取财务数据"""
        try:
            symbol = self._get_yahoo_symbol(stock_code)
            stock = yf.Ticker(symbol)
            info = stock.info
            
            return {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "roe": float(info.get('returnOnEquity', 0) * 100) if info.get('returnOnEquity') else 0,
                "roa": float(info.get('returnOnAssets', 0) * 100) if info.get('returnOnAssets') else 0,
                "gross_margin": float(info.get('grossMargins', 0) * 100) if info.get('grossMargins') else 0,
                "net_margin": float(info.get('profitMargins', 0) * 100) if info.get('profitMargins') else 0,
                "debt_ratio": float(info.get('debtToEquity', 0)) if info.get('debtToEquity') else 0,
                "current_ratio": float(info.get('currentRatio', 0)) if info.get('currentRatio') else 0,
                "quick_ratio": float(info.get('quickRatio', 0)) if info.get('quickRatio') else 0,
                "eps": float(info.get('trailingEps', 0)) if info.get('trailingEps') else 0,
                "bvps": float(info.get('bookValue', 0)) if info.get('bookValue') else 0,
                "pe_ratio": float(info.get('trailingPE', 0)) if info.get('trailingPE') else 0,
                "market_cap": float(info.get('marketCap', 0)) if info.get('marketCap') else 0,
            }
        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
            return {"error": str(e)}
    
    def get_technical_indicators(self, stock_code: str, days: int = 60) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            df = self.get_stock_history(stock_code)
            if df.empty:
                return {"error": "无法获取历史数据"}
            
            close = df['收盘'].astype(float)
            
            ma5 = close.rolling(5).mean().iloc[-1]
            ma10 = close.rolling(10).mean().iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]
            ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else None
            
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            histogram = (macd - signal) * 2
            
            bb_middle = close.rolling(20).mean().iloc[-1]
            bb_std = close.rolling(20).std().iloc[-1]
            bb_upper = bb_middle + 2 * bb_std
            bb_lower = bb_middle - 2 * bb_std
            
            current_price = close.iloc[-1]
            
            return {
                "current_price": float(current_price),
                "ma5": float(ma5),
                "ma10": float(ma10),
                "ma20": float(ma20),
                "ma60": float(ma60) if ma60 and not pd.isna(ma60) else None,
                "rsi": float(rsi) if not pd.isna(rsi) else 50,
                "macd": {
                    "dif": float(macd.iloc[-1]),
                    "dea": float(signal.iloc[-1]),
                    "histogram": float(histogram.iloc[-1])
                },
                "bollinger_bands": {
                    "upper": float(bb_upper),
                    "middle": float(bb_middle),
                    "lower": float(bb_lower),
                    "position": (float(current_price) - float(bb_lower)) / (float(bb_upper) - float(bb_lower)) if bb_upper != bb_lower else 0.5
                },
                "trend": self._determine_trend(close, ma5, ma10, ma20)
            }
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return {"error": str(e)}
    
    def _determine_trend(self, close: pd.Series, ma5: float, ma10: float, ma20: float) -> str:
        """判断趋势"""
        current = close.iloc[-1]
        
        if current > ma5 > ma10 > ma20:
            return "强势上涨"
        elif current > ma5 > ma10:
            return "上涨趋势"
        elif current < ma5 < ma10 < ma20:
            return "强势下跌"
        elif current < ma5 < ma10:
            return "下跌趋势"
        else:
            return "震荡整理"
    
    def get_news(self, stock_code: str, stock_name: str = None) -> List[Dict[str, Any]]:
        """获取股票相关新闻（使用Mock数据）"""
        return self._get_mock_news(stock_code, stock_name)
    
    def _get_mock_news(self, stock_code: str, stock_name: str = None) -> List[Dict[str, Any]]:
        """Mock新闻数据（用于演示）"""
        from datetime import timedelta
        import random
        
        stock_name = stock_name or stock_code
        
        # 生成模拟新闻列表
        news_templates = [
            {
                'title': f'{stock_name}发布季度财报，业绩超市场预期',
                'content': f'{stock_name}今日发布最新季度财报，营收同比增长15%，净利润同比增长12%，超出市场预期。分析师普遍看好公司未来发展前景。',
                'source': '财经日报',
                'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': f'{stock_name}获得重大订单，市场关注度提升',
                'content': f'据悉，{stock_name}近期获得一笔重大订单，合同金额超过10亿元。该订单将为公司未来业绩增长提供有力支撑。',
                'source': '证券时报',
                'publish_time': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': f'行业政策利好，{stock_name}受益明显',
                'content': f'国家相关部门发布行业支持政策，{stock_name}作为行业龙头企业，将直接受益于政策红利，未来发展前景向好。',
                'source': '上海证券报',
                'publish_time': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': f'{stock_name}股价异动，成交量放大',
                'content': f'{stock_name}今日股价出现明显异动，成交量较前一交易日放大2倍，市场关注度显著提升。分析师建议关注后续走势。',
                'source': '第一财经',
                'publish_time': (datetime.now() - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M')
            },
            {
                'title': f'机构调研频繁，{stock_name}受关注',
                'content': f'近期多家知名机构对{stock_name}进行调研，公司管理层对未来发展战略进行了详细阐述，机构投资者普遍持乐观态度。',
                'source': '中国证券报',
                'publish_time': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d %H:%M')
            }
        ]
        
        # 随机选择3-5条新闻
        selected_news = random.sample(news_templates, min(random.randint(3, 5), len(news_templates)))
        
        return selected_news
    
    def get_industry_info(self, stock_code: str) -> Dict[str, Any]:
        """获取行业信息（返回空字典）"""
        return {}
    
    def get_capital_flow(self, stock_code: str) -> Dict[str, Any]:
        """获取资金流向数据（使用Mock数据）"""
        return self._get_mock_capital_flow(stock_code)
    
    def _get_mock_capital_flow(self, stock_code: str) -> Dict[str, Any]:
        """Mock资金流数据（用于演示）"""
        import random
        
        # 生成随机资金流数据
        main_net_inflow = random.uniform(-50000000, 80000000)
        northbound_net_inflow = random.uniform(-20000000, 30000000)
        financing_balance = random.uniform(100000000, 800000000)
        
        # 判断趋势
        main_trend = "流入" if main_net_inflow > 0 else "流出"
        main_strength = "强" if abs(main_net_inflow) > 30000000 else ("中" if abs(main_net_inflow) > 10000000 else "弱")
        
        northbound_trend = "流入" if northbound_net_inflow > 0 else "流出"
        
        # 机构持仓变化
        institution_change = random.choice(["增持", "减持", "不变"])
        institution_confidence = "高" if institution_change == "增持" else ("中" if institution_change == "不变" else "低")
        
        # 融资融券趋势
        margin_trend = "上升" if financing_balance > 300000000 else "下降"
        
        # 综合判断
        if main_net_inflow > 20000000 and northbound_net_inflow > 0:
            overall_signal = "买入"
            conclusion = "主力资金和北向资金同步流入，市场情绪积极"
        elif main_net_inflow > 10000000:
            overall_signal = "买入"
            conclusion = "主力资金持续流入，值得关注"
        elif main_net_inflow < -20000000:
            overall_signal = "卖出"
            conclusion = "主力资金大幅流出，注意风险"
        else:
            overall_signal = "持有"
            conclusion = "资金流向平衡，建议观望"
        
        return {
            "main_force": {
                "net_inflow": round(main_net_inflow, 2),
                "trend": main_trend,
                "strength": main_strength,
                "buy_amount": round(abs(main_net_inflow) * random.uniform(1.1, 1.3), 2) if main_net_inflow > 0 else 0,
                "sell_amount": round(abs(main_net_inflow) * random.uniform(1.1, 1.3), 2) if main_net_inflow < 0 else 0
            },
            "northbound": {
                "net_inflow": round(northbound_net_inflow, 2),
                "trend": northbound_trend,
                "consecutive_days": random.randint(1, 5),
                "holdings": round(random.uniform(10000000, 500000000), 2)
            },
            "institution": {
                "holding_change": institution_change,
                "confidence": institution_confidence,
                "holdings_ratio": round(random.uniform(5, 30), 2)
            },
            "margin_trading": {
                "financing_balance": round(financing_balance, 2),
                "securities_balance": round(random.uniform(10000000, 50000000), 2),
                "trend": margin_trend
            },
            "conclusion": conclusion,
            "signal": overall_signal,
            "confidence": round(random.uniform(0.6, 0.85), 2)
        }
    
    def get_sentiment_data(self, stock_code: str, stock_name: str = None) -> Dict[str, Any]:
        """获取情绪数据（使用Mock数据）"""
        return self._get_mock_sentiment(stock_code, stock_name)
    
    def _get_mock_sentiment(self, stock_code: str, stock_name: str = None) -> Dict[str, Any]:
        """Mock情绪数据（用于演示）"""
        import random
        
        stock_name = stock_name or stock_code
        
        # 生成情绪分数（-100到100）
        sentiment_score = random.uniform(-60, 80)
        
        # 根据分数判断整体情绪
        if sentiment_score > 50:
            overall_sentiment = "极度贪婪"
            market_mood = "非常活跃"
            investor_sentiment = "非常乐观"
        elif sentiment_score > 20:
            overall_sentiment = "贪婪"
            market_mood = "活跃"
            investor_sentiment = "乐观"
        elif sentiment_score > -20:
            overall_sentiment = "中性"
            market_mood = "一般"
            investor_sentiment = "观望"
        elif sentiment_score > -50:
            overall_sentiment = "恐慌"
            market_mood = "低迷"
            investor_sentiment = "悲观"
        else:
            overall_sentiment = "极度恐慌"
            market_mood = "非常低迷"
            investor_sentiment = "非常悲观"
        
        # 新闻情绪
        news_sentiment = random.choice(["正面", "中性", "负面"])
        
        # 社交媒体热度（0-100）
        social_media_heat = random.randint(30, 90)
        
        # 散户情绪
        retail_sentiment = "买入" if sentiment_score > 10 else ("持有" if sentiment_score > -10 else "卖出")
        
        # 逆向信号（极端情绪时出现）
        contrarian_signal = "是" if abs(sentiment_score) > 50 else "否"
        contrarian_reason = ""
        if sentiment_score > 50:
            contrarian_reason = "市场过度贪婪，可能存在回调风险"
        elif sentiment_score < -50:
            contrarian_reason = "市场过度恐慌，可能出现反弹机会"
        
        # 情绪驱动因素
        key_drivers = []
        if sentiment_score > 20:
            key_drivers.append(f"{stock_name}近期利好消息频出，提振市场信心")
            key_drivers.append("成交量放大，市场参与度提升")
        elif sentiment_score < -20:
            key_drivers.append(f"{stock_name}面临短期压力，投资者情绪谨慎")
            key_drivers.append("市场波动加大，避险情绪上升")
        else:
            key_drivers.append("市场情绪相对稳定，多空因素平衡")
        
        # 短期影响预测
        if sentiment_score > 30:
            short_term_impact = "情绪积极，短期内可能继续上涨，但需警惕情绪过热"
        elif sentiment_score > 0:
            short_term_impact = "情绪偏暖，短期走势有望保持稳定"
        elif sentiment_score > -30:
            short_term_impact = "情绪偏弱，短期可能震荡整理"
        else:
            short_term_impact = "情绪悲观，短期存在下跌压力，但可能迎来反弹"
        
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": round(sentiment_score, 2),
            "news_sentiment": news_sentiment,
            "social_media_heat": social_media_heat,
            "market_mood": market_mood,
            "investor_sentiment": investor_sentiment,
            "retail_sentiment": retail_sentiment,
            "contrarian_signal": contrarian_signal,
            "contrarian_reason": contrarian_reason,
            "key_drivers": key_drivers,
            "short_term_impact": short_term_impact,
            "confidence": round(random.uniform(0.55, 0.80), 2),
            "recommendation": "关注情绪变化，把握逆向投资机会" if contrarian_signal == "是" else "根据情绪适度调整仓位"
        }


def get_stock_data(stock_code: str) -> Dict[str, Any]:
    """获取股票综合数据"""
    tool = AStockDataTool()
    basic_info = tool.get_stock_info(stock_code)
    
    return {
        "basic_info": basic_info,
        "financial": tool.get_financial_report(stock_code),
        "technical": tool.get_technical_indicators(stock_code),
        "news": tool.get_news(stock_code, basic_info.get('name')),
        "industry": tool.get_industry_info(stock_code),
        "capital_flow": tool.get_capital_flow(stock_code),  # 新增资金流数据
        "sentiment": tool.get_sentiment_data(stock_code, basic_info.get('name'))  # 新增情绪数据
    }
