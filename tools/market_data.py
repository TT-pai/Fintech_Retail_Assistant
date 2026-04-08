"""
全A股市场数据获取工具
使用 Yahoo Finance 作为数据源
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger

import yfinance as yf
import pandas as pd


# 预定义的A股股票列表（包含主要股票，可定期更新）
# 数据来源：A股主要上市公司
DEFAULT_STOCK_LIST = [
    # 沪市主板
    {"code": "600000", "name": "浦发银行", "market": "SH"},
    {"code": "600004", "name": "白云机场", "market": "SH"},
    {"code": "600006", "name": "东风汽车", "market": "SH"},
    {"code": "600007", "name": "中国国贸", "market": "SH"},
    {"code": "600008", "name": "首创环保", "market": "SH"},
    {"code": "600009", "name": "上海机场", "market": "SH"},
    {"code": "600010", "name": "包钢股份", "market": "SH"},
    {"code": "600011", "name": "华能国际", "market": "SH"},
    {"code": "600012", "name": "皖通高速", "market": "SH"},
    {"code": "600015", "name": "华夏银行", "market": "SH"},
    {"code": "600016", "name": "民生银行", "market": "SH"},
    {"code": "600017", "name": "日照港", "market": "SH"},
    {"code": "600018", "name": "上港集团", "market": "SH"},
    {"code": "600019", "name": "宝钢股份", "market": "SH"},
    {"code": "600020", "name": "中原高速", "market": "SH"},
    {"code": "600021", "name": "上海电力", "market": "SH"},
    {"code": "600022", "name": "山东钢铁", "market": "SH"},
    {"code": "600023", "name": "浙能电力", "market": "SH"},
    {"code": "600025", "name": "华能水电", "market": "SH"},
    {"code": "600026", "name": "中远海能", "market": "SH"},
    {"code": "600027", "name": "华电国际", "market": "SH"},
    {"code": "600028", "name": "中国石化", "market": "SH"},
    {"code": "600029", "name": "南方航空", "market": "SH"},
    {"code": "600030", "name": "中信证券", "market": "SH"},
    {"code": "600031", "name": "三一重工", "market": "SH"},
    {"code": "600033", "name": "福建高速", "market": "SH"},
    {"code": "600035", "name": "楚天高速", "market": "SH"},
    {"code": "600036", "name": "招商银行", "market": "SH"},
    {"code": "600037", "name": "歌华有线", "market": "SH"},
    {"code": "600038", "name": "中直股份", "market": "SH"},
    {"code": "600039", "name": "四川路桥", "market": "SH"},
    {"code": "600048", "name": "保利发展", "market": "SH"},
    {"code": "600050", "name": "中国联通", "market": "SH"},
    {"code": "600104", "name": "上汽集团", "market": "SH"},
    {"code": "600109", "name": "国金证券", "market": "SH"},
    {"code": "600111", "name": "北方稀土", "market": "SH"},
    {"code": "600115", "name": "中国东航", "market": "SH"},
    {"code": "600118", "name": "中国卫星", "market": "SH"},
    {"code": "600150", "name": "中国船舶", "market": "SH"},
    {"code": "600176", "name": "中国巨石", "market": "SH"},
    {"code": "600183", "name": "生益科技", "market": "SH"},
    {"code": "600196", "name": "复星医药", "market": "SH"},
    {"code": "600276", "name": "恒瑞医药", "market": "SH"},
    {"code": "600309", "name": "万华化学", "market": "SH"},
    {"code": "600332", "name": "白云山", "market": "SH"},
    {"code": "600340", "name": "华夏幸福", "market": "SH"},
    {"code": "600346", "name": "恒力石化", "market": "SH"},
    {"code": "600352", "name": "浙江龙盛", "market": "SH"},
    {"code": "600438", "name": "通威股份", "market": "SH"},
    {"code": "600486", "name": "扬农化工", "market": "SH"},
    {"code": "600489", "name": "中金黄金", "market": "SH"},
    {"code": "600498", "name": "烽火通信", "market": "SH"},
    {"code": "600519", "name": "贵州茅台", "market": "SH"},
    {"code": "600547", "name": "山东黄金", "market": "SH"},
    {"code": "600570", "name": "恒生电子", "market": "SH"},
    {"code": "600588", "name": "用友网络", "market": "SH"},
    {"code": "600585", "name": "海螺水泥", "market": "SH"},
    {"code": "600588", "name": "用友网络", "market": "SH"},
    {"code": "600690", "name": "海尔智家", "market": "SH"},
    {"code": "600703", "name": "三安光电", "market": "SH"},
    {"code": "600809", "name": "山西汾酒", "market": "SH"},
    {"code": "600837", "name": "海通证券", "market": "SH"},
    {"code": "600887", "name": "伊利股份", "market": "SH"},
    {"code": "600893", "name": "航发动力", "market": "SH"},
    {"code": "600900", "name": "长江电力", "market": "SH"},
    {"code": "600919", "name": "江苏银行", "market": "SH"},
    {"code": "600926", "name": "杭州银行", "market": "SH"},
    {"code": "600941", "name": "中国移动", "market": "SH"},
    {"code": "600989", "name": "宝丰能源", "market": "SH"},
    {"code": "601012", "name": "隆基绿能", "market": "SH"},
    {"code": "601066", "name": "中信建投", "market": "SH"},
    {"code": "601088", "name": "中国神华", "market": "SH"},
    {"code": "601111", "name": "中国国航", "market": "SH"},
    {"code": "601138", "name": "工业富联", "market": "SH"},
    {"code": "601166", "name": "兴业银行", "market": "SH"},
    {"code": "601225", "name": "陕西煤业", "market": "SH"},
    {"code": "601236", "name": "红塔证券", "market": "SH"},
    {"code": "601238", "name": "广汽集团", "market": "SH"},
    {"code": "601288", "name": "农业银行", "market": "SH"},
    {"code": "601318", "name": "中国平安", "market": "SH"},
    {"code": "601319", "name": "中国人保", "market": "SH"},
    {"code": "601328", "name": "交通银行", "market": "SH"},
    {"code": "601336", "name": "新华保险", "market": "SH"},
    {"code": "601390", "name": "中国中铁", "market": "SH"},
    {"code": "601398", "name": "工商银行", "market": "SH"},
    {"code": "601601", "name": "中国太保", "market": "SH"},
    {"code": "601628", "name": "中国人寿", "market": "SH"},
    {"code": "601633", "name": "长城汽车", "market": "SH"},
    {"code": "601668", "name": "中国建筑", "market": "SH"},
    {"code": "601669", "name": "中国电建", "market": "SH"},
    {"code": "601688", "name": "华泰证券", "market": "SH"},
    {"code": "601728", "name": "中国电信", "market": "SH"},
    {"code": "601766", "name": "中国中车", "market": "SH"},
    {"code": "601816", "name": "京沪高铁", "market": "SH"},
    {"code": "601818", "name": "光大银行", "market": "SH"},
    {"code": "601857", "name": "中国石油", "market": "SH"},
    {"code": "601877", "name": "中国交建", "market": "SH"},
    {"code": "601899", "name": "紫金矿业", "market": "SH"},
    {"code": "601919", "name": "中远海控", "market": "SH"},
    {"code": "601939", "name": "建设银行", "market": "SH"},
    {"code": "601988", "name": "中国银行", "market": "SH"},
    {"code": "601998", "name": "中信银行", "market": "SH"},
    {"code": "603105", "name": "芯能科技", "market": "SH"},
    {"code": "603259", "name": "药明康德", "market": "SH"},
    {"code": "603288", "name": "海天味业", "market": "SH"},
    {"code": "603501", "name": "韦尔股份", "market": "SH"},
    {"code": "603986", "name": "兆易创新", "market": "SH"},
    
    # 深市主板
    {"code": "000001", "name": "平安银行", "market": "SZ"},
    {"code": "000002", "name": "万科A", "market": "SZ"},
    {"code": "000063", "name": "中兴通讯", "market": "SZ"},
    {"code": "000066", "name": "中国长城", "market": "SZ"},
    {"code": "000333", "name": "美的集团", "market": "SZ"},
    {"code": "000338", "name": "潍柴动力", "market": "SZ"},
    {"code": "000425", "name": "徐工机械", "market": "SZ"},
    {"code": "000538", "name": "云南白药", "market": "SZ"},
    {"code": "000568", "name": "泸州老窖", "market": "SZ"},
    {"code": "000596", "name": "古井贡酒", "market": "SZ"},
    {"code": "000625", "name": "长安汽车", "market": "SZ"},
    {"code": "000651", "name": "格力电器", "market": "SZ"},
    {"code": "000661", "name": "长春高新", "market": "SZ"},
    {"code": "000703", "name": "中兴通讯", "market": "SZ"},
    {"code": "000708", "name": "中信特钢", "market": "SZ"},
    {"code": "000725", "name": "京东方A", "market": "SZ"},
    {"code": "000768", "name": "中航西飞", "market": "SZ"},
    {"code": "000776", "name": "广发证券", "market": "SZ"},
    {"code": "000799", "name": "酒鬼酒", "market": "SZ"},
    {"code": "000858", "name": "五粮液", "market": "SZ"},
    {"code": "000876", "name": "新希望", "market": "SZ"},
    {"code": "000895", "name": "双汇发展", "market": "SZ"},
    {"code": "000938", "name": "紫光股份", "market": "SZ"},
    {"code": "001979", "name": "招商蛇口", "market": "SZ"},
    
    # 中小板
    {"code": "002007", "name": "华兰生物", "market": "SZ"},
    {"code": "002024", "name": "苏宁易购", "market": "SZ"},
    {"code": "002049", "name": "紫光国微", "market": "SZ"},
    {"code": "002050", "name": "三花智控", "market": "SZ"},
    {"code": "002120", "name": "韵达股份", "market": "SZ"},
    {"code": "002142", "name": "宁波银行", "market": "SZ"},
    {"code": "002230", "name": "科大讯飞", "market": "SZ"},
    {"code": "002236", "name": "大华股份", "market": "SZ"},
    {"code": "002241", "name": "歌尔股份", "market": "SZ"},
    {"code": "002271", "name": "东方雨虹", "market": "SZ"},
    {"code": "002304", "name": "洋河股份", "market": "SZ"},
    {"code": "002352", "name": "顺丰控股", "market": "SZ"},
    {"code": "002410", "name": "广联达", "market": "SZ"},
    {"code": "002415", "name": "海康威视", "market": "SZ"},
    {"code": "002460", "name": "赣锋锂业", "market": "SZ"},
    {"code": "002475", "name": "立讯精密", "market": "SZ"},
    {"code": "002594", "name": "比亚迪", "market": "SZ"},
    {"code": "002709", "name": "天赐材料", "market": "SZ"},
    {"code": "002714", "name": "牧原股份", "market": "SZ"},
    {"code": "002821", "name": "凯莱英", "market": "SZ"},
    
    # 创业板
    {"code": "300003", "name": "乐普医疗", "market": "CYB"},
    {"code": "300014", "name": "亿纬锂能", "market": "CYB"},
    {"code": "300015", "name": "爱尔眼科", "market": "CYB"},
    {"code": "300033", "name": "同花顺", "market": "CYB"},
    {"code": "300059", "name": "东方财富", "market": "CYB"},
    {"code": "300122", "name": "智飞生物", "market": "CYB"},
    {"code": "300124", "name": "汇川技术", "market": "CYB"},
    {"code": "300142", "name": "沃森生物", "market": "CYB"},
    {"code": "300144", "name": "宋城演艺", "market": "CYB"},
    {"code": "300274", "name": "阳光电源", "market": "CYB"},
    {"code": "300347", "name": "泰格医药", "market": "CYB"},
    {"code": "300408", "name": "三环集团", "market": "CYB"},
    {"code": "300413", "name": "芒果超媒", "market": "CYB"},
    {"code": "300433", "name": "蓝思科技", "market": "CYB"},
    {"code": "300450", "name": "先导智能", "market": "CYB"},
    {"code": "300454", "name": "深信服", "market": "CYB"},
    {"code": "300498", "name": "温氏股份", "market": "CYB"},
    {"code": "300628", "name": "亿联网络", "market": "CYB"},
    {"code": "300750", "name": "宁德时代", "market": "CYB"},
    {"code": "300760", "name": "迈瑞医疗", "market": "CYB"},
    {"code": "300782", "name": "卓胜微", "market": "CYB"},
    
    # 科创板
    {"code": "688001", "name": "华兴源创", "market": "KCB"},
    {"code": "688008", "name": "澜起科技", "market": "KCB"},
    {"code": "688012", "name": "中微公司", "market": "KCB"},
    {"code": "688036", "name": "传音控股", "market": "KCB"},
    {"code": "688041", "name": "海光信息", "market": "KCB"},
    {"code": "688065", "name": "凯盛新材", "market": "KCB"},
    {"code": "688111", "name": "金山办公", "market": "KCB"},
    {"code": "688126", "name": "沪硅产业", "market": "KCB"},
    {"code": "688180", "name": "君实生物", "market": "KCB"},
    {"code": "688185", "name": "康希诺", "market": "KCB"},
    {"code": "688223", "name": "晶科能源", "market": "KCB"},
    {"code": "688256", "name": "寒武纪", "market": "KCB"},
    {"code": "688303", "name": "大全能源", "market": "KCB"},
    {"code": "688369", "name": "致远互联", "market": "KCB"},
    {"code": "688567", "name": "孚能科技", "market": "KCB"},
    {"code": "688599", "name": "天合光能", "market": "KCB"},
    {"code": "688981", "name": "中芯国际", "market": "KCB"},
]


class MarketDataTool:
    """全A股市场数据获取工具（Yahoo Finance 数据源）"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(__file__), "..", "data", "market_cache"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.stock_list_cache_path = os.path.join(self.cache_dir, "stock_list.json")
        
        # 缓存有效期（秒）
        self.cache_expire_seconds = 24 * 60 * 60  # 24小时
    
    def get_all_stocks(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        获取全部A股上市公司列表
        
        Returns:
            包含股票代码、名称、市场等信息的列表
        """
        # 检查缓存
        if not force_refresh:
            cached = self._load_cache(self.stock_list_cache_path)
            if cached and not self._is_cache_expired(cached):
                logger.info(f"从缓存加载股票列表，共 {len(cached['data'])} 只股票")
                return cached['data']
        
        # 使用预定义列表
        stocks = DEFAULT_STOCK_LIST.copy()
        
        # 保存缓存
        self._save_cache(self.stock_list_cache_path, stocks)
        logger.info(f"使用预定义股票列表，共 {len(stocks)} 只股票")
        
        return stocks
    
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
    
    def build_knowledge_graph_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        构建知识图谱所需的全部数据
        
        Returns:
            包含股票基本数据的字典
        """
        logger.info("开始构建知识图谱数据...")
        
        # 获取股票列表
        stocks = self.get_all_stocks(force_refresh)
        
        stock_data = []
        for s in stocks:
            stock_data.append({
                "code": s["code"],
                "name": s.get("name", ""),
                "market": s.get("market", ""),
                "market_cap": 0,
                "pe_ratio": 0,
                "list_date": s.get("list_date", "")
            })
        
        # 简单的行业分类（根据股票代码前缀）
        industry_data = {
            "沪市主板": [s["code"] for s in stocks if s["code"].startswith("60") and not s["code"].startswith("688")],
            "科创板": [s["code"] for s in stocks if s["code"].startswith("688")],
            "深市主板": [s["code"] for s in stocks if s["code"].startswith("00") and not s["code"].startswith("002")],
            "中小板": [s["code"] for s in stocks if s["code"].startswith("002")],
            "创业板": [s["code"] for s in stocks if s["code"].startswith("300")],
        }
        
        result = {
            "stocks": stock_data,
            "industries": industry_data,
            "concepts": {},
            "updated_at": datetime.now().isoformat(),
            "total_stocks": len(stock_data),
            "total_industries": len(industry_data),
            "total_concepts": 0
        }
        
        logger.info(f"知识图谱数据构建完成: {len(stock_data)} 只股票")
        
        return result
    
    def _load_cache(self, path: str) -> Optional[Dict[str, Any]]:
        """加载缓存"""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def _save_cache(self, path: str, data: Any) -> None:
        """保存缓存"""
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    
    def _is_cache_expired(self, cached: Dict[str, Any]) -> bool:
        """检查缓存是否过期"""
        try:
            timestamp = datetime.fromisoformat(cached.get("timestamp", ""))
            age = (datetime.now() - timestamp).total_seconds()
            return age > self.cache_expire_seconds
        except:
            return True


# 便捷函数
def get_all_a_stocks(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """获取全部A股列表"""
    tool = MarketDataTool()
    return tool.get_all_stocks(force_refresh)