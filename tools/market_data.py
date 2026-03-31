"""
全A股市场数据获取工具
使用 AkShare 作为主要数据源，Yahoo Finance 作为备选
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
import pandas as pd

# 尝试导入 akshare
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    logger.warning("AkShare 未安装，将使用备选数据源")


class MarketDataTool:
    """全A股市场数据获取工具"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or os.path.join(
            os.path.dirname(__file__), "..", "data", "market_cache"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.stock_list_cache_path = os.path.join(self.cache_dir, "stock_list.json")
        self.industry_cache_path = os.path.join(self.cache_dir, "industry_data.json")
        self.concept_cache_path = os.path.join(self.cache_dir, "concept_data.json")
        
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
        
        stocks = []
        
        if AKSHARE_AVAILABLE:
            try:
                stocks = self._get_stocks_from_akshare()
            except Exception as e:
                logger.error(f"AkShare 获取股票列表失败: {e}")
        
        if not stocks:
            logger.warning("主数据源失败，使用备选数据")
            stocks = self._get_stocks_from_backup()
        
        if stocks:
            # 保存缓存
            self._save_cache(self.stock_list_cache_path, stocks)
            logger.info(f"成功获取 {len(stocks)} 只A股股票")
        
        return stocks
    
    def _get_stocks_from_akshare(self) -> List[Dict[str, Any]]:
        """使用 AkShare 获取股票列表"""
        stocks = []
        
        # 获取A股股票列表
        try:
            # 沪市主板
            sh_df = ak.stock_info_sh_name_code(symbol="主板A股")
            for _, row in sh_df.iterrows():
                stocks.append({
                    "code": str(row.get("证券代码", "")),
                    "name": str(row.get("证券简称", "")),
                    "market": "SH",
                    "list_date": str(row.get("上市日期", ""))
                })
            logger.info(f"沪市主板: {len(sh_df)} 只")
        except Exception as e:
            logger.warning(f"获取沪市主板失败: {e}")
        
        # 深市主板
        try:
            sz_df = ak.stock_info_sz_name_code(symbol="A股列表")
            for _, row in sz_df.iterrows():
                stocks.append({
                    "code": str(row.get("A股代码", "")),
                    "name": str(row.get("A股简称", "")),
                    "market": "SZ",
                    "list_date": str(row.get("A股上市日期", ""))
                })
            logger.info(f"深市主板: {len(sz_df)} 只")
        except Exception as e:
            logger.warning(f"获取深市主板失败: {e}")
        
        # 创业板
        try:
            cyb_df = ak.stock_info_sz_name_code(symbol="创业板列表")
            for _, row in cyb_df.iterrows():
                stocks.append({
                    "code": str(row.get("A股代码", "")),
                    "name": str(row.get("A股简称", "")),
                    "market": "CYB",
                    "list_date": str(row.get("A股上市日期", ""))
                })
            logger.info(f"创业板: {len(cyb_df)} 只")
        except Exception as e:
            logger.warning(f"获取创业板失败: {e}")
        
        # 科创板
        try:
            kcb_df = ak.stock_info_sh_name_code(symbol="科创板")
            for _, row in kcb_df.iterrows():
                stocks.append({
                    "code": str(row.get("证券代码", "")),
                    "name": str(row.get("证券简称", "")),
                    "market": "KCB",
                    "list_date": str(row.get("上市日期", ""))
                })
            logger.info(f"科创板: {len(kcb_df)} 只")
        except Exception as e:
            logger.warning(f"获取科创板失败: {e}")
        
        # 过滤无效数据
        stocks = [s for s in stocks if s["code"] and len(s["code"]) == 6 and s["name"]]
        
        return stocks
    
    def _get_stocks_from_backup(self) -> List[Dict[str, Any]]:
        """备选方案：从现有缓存或硬编码数据获取"""
        cache_file = os.path.join(os.path.dirname(__file__), "stock_list_cache.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("data", [])
        return []
    
    def get_industry_classification(self, force_refresh: bool = False) -> Dict[str, List[str]]:
        """
        获取行业分类数据
        
        Returns:
            {行业名称: [股票代码列表]}
        """
        if not force_refresh:
            cached = self._load_cache(self.industry_cache_path)
            if cached and not self._is_cache_expired(cached):
                return cached['data']
        
        industry_data = {}
        
        if AKSHARE_AVAILABLE:
            try:
                # 获取行业分类
                df = ak.stock_board_industry_name_em()
                for _, row in df.iterrows():
                    industry_name = row.get("板块名称", "")
                    if industry_name:
                        try:
                            # 获取该行业的成分股
                            stocks_df = ak.stock_board_industry_cons_em(symbol=industry_name)
                            codes = stocks_df["代码"].tolist() if "代码" in stocks_df.columns else []
                            industry_data[industry_name] = codes
                        except:
                            pass
                
                self._save_cache(self.industry_cache_path, industry_data)
                logger.info(f"获取 {len(industry_data)} 个行业分类")
                
            except Exception as e:
                logger.error(f"获取行业分类失败: {e}")
        
        return industry_data
    
    def get_concept_classification(self, force_refresh: bool = False) -> Dict[str, List[str]]:
        """
        获取概念板块数据
        
        Returns:
            {概念名称: [股票代码列表]}
        """
        if not force_refresh:
            cached = self._load_cache(self.concept_cache_path)
            if cached and not self._is_cache_expired(cached):
                return cached['data']
        
        concept_data = {}
        
        if AKSHARE_AVAILABLE:
            try:
                # 获取概念板块列表
                df = ak.stock_board_concept_name_em()
                # 限制获取前100个主要概念（数据量太大）
                for _, row in df.head(100).iterrows():
                    concept_name = row.get("板块名称", "")
                    if concept_name:
                        try:
                            stocks_df = ak.stock_board_concept_cons_em(symbol=concept_name)
                            codes = stocks_df["代码"].tolist() if "代码" in stocks_df.columns else []
                            concept_data[concept_name] = codes
                        except:
                            pass
                
                self._save_cache(self.concept_cache_path, concept_data)
                logger.info(f"获取 {len(concept_data)} 个概念板块")
                
            except Exception as e:
                logger.error(f"获取概念板块失败: {e}")
        
        return concept_data
    
    def get_stock_realtime_data(self, stock_codes: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        获取股票实时行情数据
        
        Args:
            stock_codes: 股票代码列表，如果为None则获取全部
        
        Returns:
            {股票代码: {价格、市值、PE等}}
        """
        realtime_data = {}
        
        if AKSHARE_AVAILABLE:
            try:
                # 获取全市场实时行情
                df = ak.stock_zh_a_spot_em()
                
                for _, row in df.iterrows():
                    code = str(row.get("代码", ""))
                    if stock_codes and code not in stock_codes:
                        continue
                    
                    realtime_data[code] = {
                        "name": str(row.get("名称", "")),
                        "price": float(row.get("最新价", 0) or 0),
                        "change_percent": float(row.get("涨跌幅", 0) or 0),
                        "change_amount": float(row.get("涨跌额", 0) or 0),
                        "volume": float(row.get("成交量", 0) or 0),
                        "amount": float(row.get("成交额", 0) or 0),
                        "high": float(row.get("最高", 0) or 0),
                        "low": float(row.get("最低", 0) or 0),
                        "open": float(row.get("今开", 0) or 0),
                        "prev_close": float(row.get("昨收", 0) or 0),
                        "market_cap": float(row.get("总市值", 0) or 0),
                        "circulating_market_cap": float(row.get("流通市值", 0) or 0),
                        "pe_ratio": float(row.get("市盈率-动态", 0) or 0),
                        "pb_ratio": float(row.get("市净率", 0) or 0),
                    }
                
                logger.info(f"获取 {len(realtime_data)} 只股票实时数据")
                
            except Exception as e:
                logger.error(f"获取实时行情失败: {e}")
        
        return realtime_data
    
    def get_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """获取单只股票详细信息"""
        info = {"code": stock_code}
        
        if AKSHARE_AVAILABLE:
            try:
                # 获取个股信息
                df = ak.stock_individual_info_em(symbol=stock_code)
                for _, row in df.iterrows():
                    key = row.get("item", "")
                    value = row.get("value", "")
                    info[key] = value
            except Exception as e:
                logger.warning(f"获取股票 {stock_code} 信息失败: {e}")
        
        return info
    
    def build_knowledge_graph_data(self, force_refresh: bool = False, include_realtime: bool = True, limit: int = None) -> Dict[str, Any]:
        """
        构建知识图谱所需的全部数据
        
        Args:
            force_refresh: 是否强制刷新数据
            include_realtime: 是否包含实时行情数据（获取较慢）
            limit: 限制股票数量（用于测试，None表示不限制）
            
        Returns:
            包含股票、行业、概念等完整数据
        """
        logger.info("开始构建知识图谱数据...")
        
        # 获取股票列表
        stocks = self.get_all_stocks(force_refresh)
        
        # 限制数量（用于测试）
        if limit:
            stocks = stocks[:limit]
            logger.info(f"限制获取 {limit} 只股票用于测试")
        
        # 获取实时行情（可选，分批获取避免超时）
        realtime_data = {}
        if include_realtime:
            realtime_data = self.get_stock_realtime_data()
        else:
            logger.info("跳过实时行情数据获取")
        
        # 合并实时数据到股票列表
        stock_data = []
        for stock in stocks:
            code = stock["code"]
            rt = realtime_data.get(code, {})
            
            stock_data.append({
                "code": code,
                "name": rt.get("name") or stock.get("name", ""),
                "market": stock.get("market", ""),
                "market_cap": rt.get("market_cap", 0),
                "circulating_market_cap": rt.get("circulating_market_cap", 0),
                "pe_ratio": rt.get("pe_ratio", 0),
                "pb_ratio": rt.get("pb_ratio", 0),
                "price": rt.get("price", 0),
                "change_percent": rt.get("change_percent", 0),
                "list_date": stock.get("list_date", "")
            })
        
        # 获取行业分类
        industry_data = self.get_industry_classification(force_refresh)
        
        # 获取概念板块
        concept_data = self.get_concept_classification(force_refresh)
        
        result = {
            "stocks": stock_data,
            "industries": industry_data,
            "concepts": concept_data,
            "updated_at": datetime.now().isoformat(),
            "total_stocks": len(stock_data),
            "total_industries": len(industry_data),
            "total_concepts": len(concept_data)
        }
        
        logger.info(f"知识图谱数据构建完成: {len(stock_data)} 只股票, {len(industry_data)} 个行业, {len(concept_data)} 个概念")
        
        return result
    
    def quick_build(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        快速构建知识图谱数据（仅获取股票列表，不含行业和概念）
        适用于首次初始化或快速测试
        
        Args:
            force_refresh: 是否强制刷新数据
            
        Returns:
            包含股票基本数据的字典
        """
        logger.info("快速构建知识图谱数据...")
        
        # 获取股票列表
        stocks = self.get_all_stocks(force_refresh)
        
        # 构建简单的行业映射（从股票代码推断）
        industry_data = {}
        concept_data = {}
        
        # 定义简单的行业映射规则
        industry_map = {
            "601": "银行",  # 银行股通常以601开头
            "600": "主板",
            "000": "深市主板",
            "002": "中小板",
            "300": "创业板",
            "688": "科创板",
        }
        
        # 简单分类
        for stock in stocks:
            code = stock["code"]
            prefix = code[:3]
            if prefix in industry_map:
                industry = industry_map[prefix]
                if industry not in industry_data:
                    industry_data[industry] = []
                industry_data[industry].append(code)
        
        stock_data = [{
            "code": s["code"],
            "name": s.get("name", ""),
            "market": s.get("market", ""),
            "market_cap": 0,
            "pe_ratio": 0,
            "list_date": s.get("list_date", "")
        } for s in stocks]
        
        result = {
            "stocks": stock_data,
            "industries": industry_data,
            "concepts": concept_data,
            "updated_at": datetime.now().isoformat(),
            "total_stocks": len(stock_data),
            "total_industries": len(industry_data),
            "total_concepts": len(concept_data)
        }
        
        logger.info(f"快速构建完成: {len(stock_data)} 只股票")
        
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
def get_market_data(force_refresh: bool = False) -> Dict[str, Any]:
    """获取市场数据"""
    tool = MarketDataTool()
    return tool.build_knowledge_graph_data(force_refresh)


def get_all_a_stocks(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """获取全部A股列表"""
    tool = MarketDataTool()
    return tool.get_all_stocks(force_refresh)
