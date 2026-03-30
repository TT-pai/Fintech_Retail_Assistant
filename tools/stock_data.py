"""
A股数据获取工具
支持多数据源：东方财富(主)、Yahoo Finance(备用)
支持股票代码、名称、拼音首字母查询（全A股覆盖）
"""
import akshare as ak
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from loguru import logger
import time
import random
import yfinance as yf
import re
from functools import lru_cache
import json
import os

# 获取当前文件目录，用于存储缓存
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_STOCK_CACHE_FILE = os.path.join(_CURRENT_DIR, "stock_list_cache.json")

# 全局股票列表缓存
_STOCK_LIST_CACHE: Optional[pd.DataFrame] = None
_STOCK_LIST_TIME: Optional[float] = None
_CACHE_EXPIRE_SECONDS = 3600  # 内存缓存1小时
_FILE_CACHE_EXPIRE_SECONDS = 86400 * 7  # 文件缓存7天


def _get_pinyin_initials(text: str) -> str:
    """
    获取中文文本的拼音首字母
    Args:
        text: 中文文本
    Returns:
        拼音首字母（大写）
    """
    try:
        from pypinyin import pinyin, Style
        result = pinyin(text, style=Style.FIRST_LETTER)
        return ''.join([item[0].upper() for item in result if item[0].isalpha()])
    except ImportError:
        # 如果没有安装 pypinyin，使用简化方法
        return _simple_pinyin_initials(text)
    except Exception:
        return ""


def _simple_pinyin_initials(text: str) -> str:
    """
    简化的拼音首字母提取（仅处理常见字）
    """
    # 常用字的拼音首字母映射（部分）
    common_initials = {
        '平': 'P', '安': 'A', '银': 'Y', '行': 'H', '浦': 'P', '发': 'F',
        '招': 'Z', '工': 'G', '商': 'S', '建': 'J', '设': 'S', '农': 'N', '业': 'Y',
        '中': 'Z', '国': 'G', '交': 'J', '通': 'T', '兴': 'X', '民': 'M', '生': 'S',
        '信': 'X', '证': 'Z', '券': 'Q', '华': 'H', '泰': 'T', '海': 'H',
        '东': 'D', '方': 'F', '财': 'C', '富': 'F', '比': 'B', '迪': 'D',
        '宁': 'N', '德': 'D', '时': 'S', '代': 'D', '茅': 'M', '台': 'T',
        '五': 'W', '粮': 'L', '液': 'Y', '泸': 'L', '州': 'Z', '老': 'L', '窖': 'J',
        '洋': 'Y', '河': 'H', '股': 'G', '份': 'F', '山': 'S', '西': 'X', '汾': 'F', '酒': 'J',
        '伊': 'Y', '利': 'L', '天': 'T', '味': 'W', '双': 'S', '汇': 'H',
        '恒': 'H', '瑞': 'R', '医': 'Y', '药': 'Y', '明': 'M', '康': 'K',
        '迈': 'M', '疗': 'L', '片': 'P', '仔': 'Z', '癀': 'H', '云': 'Y', '南': 'N', '白': 'B',
        '隆': 'L', '基': 'J', '绿': 'L', '能': 'N', '威': 'W', '三': 'S', '峡': 'X',
        '长': 'C', '江': 'J', '电': 'D', '万': 'W', '科': 'K', '保': 'B', '利': 'L',
        '人': 'R', '寿': 'S', '移': 'Y', '动': 'D', '联': 'L', '网': 'W',
        '工': 'G', '业': 'Y', '富': 'F', '联': 'L', '立': 'L', '讯': 'X', '精': 'J', '密': 'M',
        '歌': 'G', '尔': 'E', '京': 'J', '科': 'K', '技': 'J',
        '贵': 'G', '州': 'Z', '茅': 'M', '台': 'T', '阿': 'A', '里': 'L', '巴': 'B',
        '腾': 'T', '讯': 'X', '美': 'M', '团': 'T', '京': 'J', '小': 'X', '米': 'M',
        '百': 'B', '度': 'D', '网': 'W', '易': 'Y', '哔': 'B', '哩': 'L',
        '理': 'L', '想': 'X', '汽': 'Q', '车': 'C', '蔚': 'W', '小': 'X', '鹏': 'P',
        '龙': 'L', '阳': 'Y', '光': 'G', '比': 'B', '亚': 'Y', '迪': 'D',
        '深': 'S', '圳': 'Z', '上': 'S', '海': 'H', '北': 'B', '京': 'J',
    }
    
    result = []
    for char in text:
        if char.isalpha():
            result.append(char.upper())
        elif char in common_initials:
            result.append(common_initials[char])
    
    return ''.join(result)


@lru_cache(maxsize=10000)
def _get_cached_pinyin(name: str) -> str:
    """缓存拼音首字母结果"""
    return _get_pinyin_initials(name)


def _save_stock_list_to_file(df: pd.DataFrame) -> None:
    """保存股票列表到本地文件"""
    try:
        cache_data = {
            "timestamp": time.time(),
            "data": df.to_dict(orient="records")
        }
        with open(_STOCK_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False)
        logger.info(f"股票列表已缓存到本地文件，共 {len(df)} 只股票")
    except Exception as e:
        logger.warning(f"保存股票列表缓存失败: {e}")


def _load_stock_list_from_file() -> Optional[pd.DataFrame]:
    """从本地文件加载股票列表"""
    try:
        if not os.path.exists(_STOCK_CACHE_FILE):
            return None
        
        with open(_STOCK_CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 检查文件缓存是否过期（如果过期但网络不可用，仍然使用）
        file_time = cache_data.get("timestamp", 0)
        # 注释掉过期检查，允许使用任何可用的缓存
        # if time.time() - file_time > _FILE_CACHE_EXPIRE_SECONDS:
        #     logger.info("本地股票缓存已过期，将重新获取")
        #     return None
        
        data = cache_data.get("data", [])
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        # 处理字段名映射（兼容不同格式的缓存文件）
        if 'code' in df.columns and '代码' not in df.columns:
            df['代码'] = df['code']
        if 'name' in df.columns and '名称' not in df.columns:
            df['名称'] = df['name']
        if 'pinyin' in df.columns and '拼音首字母' not in df.columns:
            df['拼音首字母'] = df['pinyin'].str.upper()
        
        # 确保有拼音首字母列
        if '拼音首字母' not in df.columns and '名称' in df.columns:
            df['拼音首字母'] = df['名称'].apply(_get_cached_pinyin)
        
        if not df.empty:
            logger.info(f"从本地缓存加载股票列表，共 {len(df)} 只股票，缓存时间: {datetime.fromtimestamp(file_time)}")
            return df
        return None
    except Exception as e:
        logger.warning(f"加载股票列表缓存失败: {e}")
        return None


def get_all_stocks() -> pd.DataFrame:
    """
    获取所有A股股票列表（带缓存）
    优先级：内存缓存 -> 本地文件缓存 -> 网络获取
    Returns:
        包含代码、名称、拼音首字母的DataFrame
    """
    global _STOCK_LIST_CACHE, _STOCK_LIST_TIME
    
    current_time = time.time()
    
    # 1. 检查内存缓存是否有效
    if _STOCK_LIST_CACHE is not None and _STOCK_LIST_TIME is not None:
        if current_time - _STOCK_LIST_TIME < _CACHE_EXPIRE_SECONDS:
            return _STOCK_LIST_CACHE
    
    # 2. 尝试从网络获取
    try:
        logger.info("正在从网络获取A股股票列表...")
        df = ak.stock_zh_a_spot_em()
        
        # 只保留A股（排除北交所等）
        df = df[df['代码'].str.match(r'^[036]\d{5}$')]
        
        # 生成拼音首字母列
        df['拼音首字母'] = df['名称'].apply(_get_cached_pinyin)
        
        _STOCK_LIST_CACHE = df
        _STOCK_LIST_TIME = current_time
        
        # 保存到本地文件缓存
        _save_stock_list_to_file(df)
        
        logger.info(f"成功获取 {len(df)} 只A股股票")
        return df
        
    except Exception as e:
        logger.warning(f"网络获取股票列表失败: {e}")
        
        # 3. 尝试从本地文件缓存加载
        file_cache = _load_stock_list_from_file()
        if file_cache is not None:
            _STOCK_LIST_CACHE = file_cache
            _STOCK_LIST_TIME = current_time
            return file_cache
        
        # 4. 最后尝试使用过期的内存缓存
        if _STOCK_LIST_CACHE is not None:
            logger.warning("使用过期的内存缓存")
            return _STOCK_LIST_CACHE
        
        raise ValueError("无法获取股票列表，请检查网络连接后重试")


def search_stock_code(query: str) -> Tuple[str, str]:
    """
    根据股票代码、名称或拼音首字母搜索股票代码
    Args:
        query: 股票代码(如000001)、名称(如平安银行)或拼音首字母(如PAYH)
    Returns:
        (股票代码, 股票名称) 元组
    Raises:
        ValueError: 如果找不到匹配的股票
    """
    query = query.strip().upper()
    
    if not query:
        raise ValueError("请输入股票代码、名称或拼音首字母")
    
    # 1. 检查是否是纯数字代码（A股代码）
    if re.match(r'^\d{6}$', query):
        try:
            df = get_all_stocks()
            stock = df[df['代码'] == query]
            if not stock.empty:
                return query, stock.iloc[0]['名称']
        except Exception:
            pass
        return query, query  # 返回代码本身
    
    try:
        df = get_all_stocks()
        query_upper = query.upper()
        
        # 2. 精确匹配代码
        matches = df[df['代码'] == query]
        if not matches.empty:
            row = matches.iloc[0]
            return row['代码'], row['名称']
        
        # 3. 精确匹配名称
        matches = df[df['名称'].str.upper() == query_upper]
        if not matches.empty:
            row = matches.iloc[0]
            return row['代码'], row['名称']
        
        # 4. 精确匹配拼音首字母
        matches = df[df['拼音首字母'] == query_upper]
        if not matches.empty:
            row = matches.iloc[0]
            return row['代码'], row['名称']
        
        # 5. 模糊匹配名称
        matches = df[df['名称'].str.upper().str.contains(query_upper, na=False)]
        if not matches.empty:
            row = matches.iloc[0]
            return row['代码'], row['名称']
        
        # 6. 模糊匹配拼音首字母
        matches = df[df['拼音首字母'].str.contains(query_upper, na=False)]
        if not matches.empty:
            row = matches.iloc[0]
            return row['代码'], row['名称']
        
        # 7. 模糊匹配代码
        matches = df[df['代码'].str.contains(query, na=False)]
        if not matches.empty:
            row = matches.iloc[0]
            return row['代码'], row['名称']
            
    except Exception as e:
        logger.warning(f"搜索股票失败: {e}")
    
    raise ValueError(f"未找到匹配的股票: {query}，请检查输入是否正确")


def resolve_stock_input(user_input: str) -> Tuple[str, str]:
    """
    解析用户输入，返回股票代码和名称
    Args:
        user_input: 用户输入的股票代码、名称或拼音首字母
    Returns:
        (股票代码, 股票名称) 元组
    """
    return search_stock_code(user_input)


def retry_request(func, max_retries=3, delay=2, *args, **kwargs):
    """带重试的请求包装器"""
    last_error = None
    for i in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            wait_time = delay * (i + 1) + random.uniform(0, 1)
            logger.warning(f"请求失败 (尝试 {i+1}/{max_retries}): {e}, 等待 {wait_time:.1f}s 后重试...")
            time.sleep(wait_time)
    raise last_error


class YahooFinanceAPI:
    """Yahoo Finance 数据接口（备用数据源）"""
    
    @staticmethod
    def _get_yahoo_symbol(stock_code: str) -> str:
        """将A股代码转换为Yahoo Finance格式"""
        if stock_code.startswith('6'):
            return f"{stock_code}.SS"  # 上海交易所
        else:
            return f"{stock_code}.SZ"  # 深圳交易所
    
    def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """获取股票实时信息"""
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
            logger.error(f"Yahoo Finance获取股票信息失败: {e}")
            return {"error": str(e)}
    
    def get_stock_history(self, stock_code: str, period: str = "6mo") -> pd.DataFrame:
        """获取股票历史数据"""
        try:
            symbol = self._get_yahoo_symbol(stock_code)
            stock = yf.Ticker(symbol)
            df = stock.history(period=period)
            
            if df.empty:
                return pd.DataFrame()
            
            # 重命名列以匹配原有格式
            df = df.reset_index()
            df = df.rename(columns={
                'Date': '日期',
                'Open': '开盘',
                'Close': '收盘',
                'High': '最高',
                'Low': '最低',
                'Volume': '成交量'
            })
            
            # 转换日期格式
            if '日期' not in df.columns:
                df['日期'] = df.index
            
            # 确保日期是字符串格式
            if hasattr(df['日期'].iloc[0], 'strftime'):
                df['日期'] = df['日期'].dt.strftime('%Y-%m-%d')
            
            return df[['日期', '开盘', '收盘', '最高', '最低', '成交量']]
        except Exception as e:
            logger.error(f"Yahoo Finance获取历史数据失败: {e}")
            return pd.DataFrame()
    
    def get_financial_data(self, stock_code: str) -> Dict[str, Any]:
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
            logger.error(f"Yahoo Finance获取财务数据失败: {e}")
            return {"error": str(e)}


class AStockDataTool:
    """A股数据获取工具（支持多数据源）"""
    
    def __init__(self, use_yahoo: bool = True):
        self.cache: Dict[str, pd.DataFrame] = {}
        self.yahoo_api = YahooFinanceAPI()
        self._use_yahoo = use_yahoo  # 默认使用 Yahoo Finance，更稳定
    
    def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票基本信息
        Args:
            stock_code: 股票代码，如 '000001' 或 '600000'
        """
        if self._use_yahoo:
            logger.info("使用 Yahoo Finance 数据源获取股票信息")
            return self.yahoo_api.get_stock_info(stock_code)
        
        try:
            # 获取A股实时行情（带重试）
            df = retry_request(ak.stock_zh_a_spot_em, max_retries=2, delay=2)
            stock_data = df[df['代码'] == stock_code]
            
            if stock_data.empty:
                return {"error": f"未找到股票代码 {stock_code}"}
            
            row = stock_data.iloc[0]
            return {
                "code": row['代码'],
                "name": row['名称'],
                "price": float(row['最新价']),
                "change_percent": float(row['涨跌幅']),
                "change_amount": float(row['涨跌额']),
                "volume": float(row['成交量']),
                "turnover": float(row['成交额']),
                "high": float(row['最高']),
                "low": float(row['最低']),
                "open": float(row['今开']),
                "prev_close": float(row['昨收']),
            }
        except Exception as e:
            logger.warning(f"东方财富API失败，切换到 Yahoo Finance: {e}")
            self._use_yahoo = True
            return self.yahoo_api.get_stock_info(stock_code)
    
    def get_stock_history(
        self, 
        stock_code: str, 
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取股票历史K线数据
        """
        if self._use_yahoo:
            logger.info("使用 Yahoo Finance 数据源获取历史数据")
            return self.yahoo_api.get_stock_history(stock_code, period="6mo")
        
        try:
            df = retry_request(
                ak.stock_zh_a_hist,
                max_retries=2,
                delay=2,
                symbol=stock_code,
                period=period,
                start_date=start_date or "20200101",
                end_date=end_date or datetime.now().strftime("%Y%m%d"),
                adjust=adjust
            )
            return df
        except Exception as e:
            logger.warning(f"东方财富历史数据API失败，切换到 Yahoo Finance: {e}")
            self._use_yahoo = True
            return self.yahoo_api.get_stock_history(stock_code, period="6mo")
    
    def get_financial_report(self, stock_code: str) -> Dict[str, Any]:
        """获取财务报表关键指标"""
        if self._use_yahoo:
            return self.yahoo_api.get_financial_data(stock_code)
        
        try:
            df = retry_request(
                ak.stock_financial_analysis_indicator,
                max_retries=2,
                delay=2,
                symbol=stock_code
            )
            
            if df.empty:
                return self.yahoo_api.get_financial_data(stock_code)
            
            latest = df.iloc[0]
            
            return {
                "date": latest.get('日期', ''),
                "roe": float(latest.get('净资产收益率(%)', 0)),
                "roa": float(latest.get('总资产净利率(%)', 0)),
                "gross_margin": float(latest.get('销售毛利率(%)', 0)),
                "net_margin": float(latest.get('销售净利率(%)', 0)),
                "debt_ratio": float(latest.get('资产负债率(%)', 0)),
                "current_ratio": float(latest.get('流动比率', 0)),
                "quick_ratio": float(latest.get('速动比率', 0)),
                "eps": float(latest.get('每股收益(元)', 0)),
                "bvps": float(latest.get('每股净资产(元)', 0)),
            }
        except Exception as e:
            logger.warning(f"东方财富财务数据API失败，使用 Yahoo Finance: {e}")
            self._use_yahoo = True
            return self.yahoo_api.get_financial_data(stock_code)
    
    def get_technical_indicators(self, stock_code: str, days: int = 60) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            df = self.get_stock_history(stock_code)
            if df.empty:
                return {"error": "无法获取历史数据"}
            
            close = df['收盘'].astype(float)
            
            # 计算MA
            ma5 = close.rolling(5).mean().iloc[-1]
            ma10 = close.rolling(10).mean().iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]
            ma60 = close.rolling(60).mean().iloc[-1] if len(close) >= 60 else None
            
            # 计算RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            
            # 计算MACD
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            histogram = (macd - signal) * 2
            
            # 布林带
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
        """获取股票相关新闻"""
        try:
            df = retry_request(
                ak.stock_news_em,
                max_retries=2,
                delay=2,
                symbol=stock_code
            )
            
            news_list = []
            for _, row in df.head(10).iterrows():
                news_list.append({
                    "title": row['新闻标题'],
                    "content": row['新闻内容'][:500] if len(str(row['新闻内容'])) > 500 else row['新闻内容'],
                    "source": row['文章来源'],
                    "publish_time": row['发布时间'],
                    "url": row['新闻链接']
                })
            
            return news_list
        except Exception as e:
            logger.warning(f"获取新闻失败: {e}")
            return []
    
    def get_industry_info(self, stock_code: str) -> Dict[str, Any]:
        """获取行业板块信息"""
        try:
            df = retry_request(
                ak.stock_individual_info_em,
                max_retries=2,
                delay=2,
                symbol=stock_code
            )
            info = {}
            for _, row in df.iterrows():
                info[row['item']] = row['value']
            return info
        except Exception as e:
            logger.warning(f"获取行业信息失败: {e}")
            return {}


# 便捷函数
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