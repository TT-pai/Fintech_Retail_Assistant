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


def search_stock_code(query: str) -> Tuple[str, str]:
    """
    根据股票代码搜索股票
    Args:
        query: 股票代码(如000001、600519)
    Returns:
        (股票代码, 股票名称) 元组
    """
    query = query.strip().upper()
    
    # 处理6位数字代码
    if re.match(r'^\d{6}$', query):
        return query, query
    
    raise ValueError(f"请输入6位股票代码，如：600519")


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
        """获取股票相关新闻（返回空列表，Yahoo Finance新闻API不稳定）"""
        return []
    
    def get_industry_info(self, stock_code: str) -> Dict[str, Any]:
        """获取行业信息（返回空字典）"""
        return {}


def get_stock_data(stock_code: str) -> Dict[str, Any]:
    """获取股票综合数据"""
    tool = AStockDataTool()
    
    return {
        "basic_info": tool.get_stock_info(stock_code),
        "financial": tool.get_financial_report(stock_code),
        "technical": tool.get_technical_indicators(stock_code),
        "news": tool.get_news(stock_code),
        "industry": tool.get_industry_info(stock_code)
    }
