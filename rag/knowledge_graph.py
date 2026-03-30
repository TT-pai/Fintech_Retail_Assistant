"""
知识图谱模块
基于NetworkX实现轻量级知识图谱
"""
from typing import List, Dict, Any, Optional, Tuple, Set
from loguru import logger
import os
import json
import networkx as nx
from datetime import datetime


class EntityType:
    """实体类型"""
    COMPANY = "Company"
    CONCEPT = "Concept"
    PERSON = "Person"
    EVENT = "Event"
    INDICATOR = "Indicator"


class RelationType:
    """关系类型"""
    BELONGS_TO = "BELONGS_TO"       # 公司属于概念
    COMPETES = "COMPETES"           # 竞争关系
    SUPPLIES = "SUPPLIES"           # 供应链关系
    HAS_INDICATOR = "HAS_INDICATOR" # 财务指标
    AFFECTS = "AFFECTS"             # 事件影响
    WORKS_AT = "WORKS_AT"           # 任职关系
    RELATED_TO = "RELATED_TO"       # 相关关系


class KnowledgeGraph:
    """知识图谱"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化知识图谱
        
        Args:
            storage_path: 存储路径
        """
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "knowledge_graph"
        )
        self.graph = nx.DiGraph()
        self._entity_index: Dict[str, str] = {}  # name -> node_id
        
        # 加载已有数据
        self._load()
        
        logger.info(f"知识图谱初始化完成，节点数: {self.graph.number_of_nodes()}, 边数: {self.graph.number_of_edges()}")
    
    def add_entity(
        self,
        entity_type: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        添加实体
        
        Args:
            entity_type: 实体类型
            name: 实体名称
            properties: 属性字典
            
        Returns:
            实体ID
        """
        node_id = f"{entity_type}_{name}"
        
        self.graph.add_node(
            node_id,
            entity_type=entity_type,
            name=name,
            properties=properties or {},
            created_at=datetime.now().isoformat()
        )
        
        # 更新索引
        self._entity_index[name] = node_id
        
        return node_id
    
    def add_relation(
        self,
        source_name: str,
        relation_type: str,
        target_name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加关系
        
        Args:
            source_name: 源实体名称
            relation_type: 关系类型
            target_name: 目标实体名称
            properties: 关系属性
            
        Returns:
            是否成功
        """
        source_id = self._entity_index.get(source_name)
        target_id = self._entity_index.get(target_name)
        
        if not source_id or not target_id:
            logger.warning(f"实体不存在: {source_name} -> {target_name}")
            return False
        
        self.graph.add_edge(
            source_id,
            target_id,
            relation_type=relation_type,
            properties=properties or {},
            created_at=datetime.now().isoformat()
        )
        
        return True
    
    def add_company(
        self,
        code: str,
        name: str,
        industry: Optional[str] = None,
        market_cap: Optional[float] = None,
        pe_ratio: Optional[float] = None
    ) -> str:
        """添加公司实体"""
        return self.add_entity(
            EntityType.COMPANY,
            name,
            {
                "code": code,
                "industry": industry,
                "market_cap": market_cap,
                "pe_ratio": pe_ratio
            }
        )
    
    def add_concept(
        self,
        name: str,
        description: Optional[str] = None
    ) -> str:
        """添加概念实体"""
        return self.add_entity(
            EntityType.CONCEPT,
            name,
            {"description": description}
        )
    
    def link_company_to_concept(self, company_name: str, concept_name: str) -> bool:
        """关联公司和概念"""
        return self.add_relation(company_name, RelationType.BELONGS_TO, concept_name)
    
    def add_competition(self, company1: str, company2: str) -> bool:
        """添加竞争关系"""
        return self.add_relation(company1, RelationType.COMPETES, company2)
    
    def add_supply_chain(self, supplier: str, customer: str) -> bool:
        """添加供应链关系"""
        return self.add_relation(supplier, RelationType.SUPPLIES, customer)
    
    def query_entity(self, name: str) -> Optional[Dict[str, Any]]:
        """
        查询实体信息
        
        Args:
            name: 实体名称
            
        Returns:
            实体信息
        """
        node_id = self._entity_index.get(name)
        if not node_id or node_id not in self.graph:
            return None
        
        node_data = self.graph.nodes[node_id]
        
        # 获取关联节点
        neighbors = list(self.graph.neighbors(node_id))
        predecessors = list(self.graph.predecessors(node_id))
        
        relations = []
        
        # 出边关系
        for neighbor in neighbors:
            edge_data = self.graph.get_edge_data(node_id, neighbor)
            neighbor_data = self.graph.nodes[neighbor]
            relations.append({
                "direction": "out",
                "relation": edge_data.get("relation_type"),
                "target": neighbor_data.get("name"),
                "target_type": neighbor_data.get("entity_type")
            })
        
        # 入边关系
        for pred in predecessors:
            edge_data = self.graph.get_edge_data(pred, node_id)
            pred_data = self.graph.nodes[pred]
            relations.append({
                "direction": "in",
                "relation": edge_data.get("relation_type"),
                "source": pred_data.get("name"),
                "source_type": pred_data.get("entity_type")
            })
        
        return {
            "id": node_id,
            "name": name,
            "type": node_data.get("entity_type"),
            "properties": node_data.get("properties", {}),
            "relations": relations
        }
    
    def query_entities(self, names: List[str]) -> List[Dict[str, Any]]:
        """
        批量查询实体
        
        Args:
            names: 实体名称列表
            
        Returns:
            实体信息列表
        """
        results = []
        for name in names:
            entity_info = self.query_entity(name)
            if entity_info:
                results.append(entity_info)
        return results
    
    def get_concept_stocks(self, concept_name: str) -> List[Dict[str, Any]]:
        """
        获取概念下的股票
        
        Args:
            concept_name: 概念名称
            
        Returns:
            股票列表
        """
        concept_id = self._entity_index.get(concept_name)
        if not concept_id:
            return []
        
        # 找到所有指向该概念的公司节点
        stocks = []
        for pred in self.graph.predecessors(concept_id):
            node_data = self.graph.nodes[pred]
            if node_data.get("entity_type") == EntityType.COMPANY:
                stocks.append({
                    "name": node_data.get("name"),
                    "code": node_data.get("properties", {}).get("code"),
                    "market_cap": node_data.get("properties", {}).get("market_cap")
                })
        
        # 按市值排序
        stocks.sort(key=lambda x: x.get("market_cap") or 0, reverse=True)
        
        return stocks
    
    def get_competitors(self, company_name: str) -> List[str]:
        """
        获取竞争对手
        
        Args:
            company_name: 公司名称
            
        Returns:
            竞争对手列表
        """
        company_id = self._entity_index.get(company_name)
        if not company_id:
            return []
        
        competitors = []
        
        # 出边
        for neighbor in self.graph.neighbors(company_id):
            edge_data = self.graph.get_edge_data(company_id, neighbor)
            if edge_data.get("relation_type") == RelationType.COMPETES:
                competitors.append(self.graph.nodes[neighbor].get("name"))
        
        # 入边
        for pred in self.graph.predecessors(company_id):
            edge_data = self.graph.get_edge_data(pred, company_id)
            if edge_data.get("relation_type") == RelationType.COMPETES:
                competitors.append(self.graph.nodes[pred].get("name"))
        
        return list(set(competitors))
    
    def multi_hop_query(
        self,
        start_entity: str,
        relation_types: List[str],
        max_hops: int = 2
    ) -> List[Dict[str, Any]]:
        """
        多跳查询
        
        Args:
            start_entity: 起始实体
            relation_types: 关系类型列表
            max_hops: 最大跳数
            
        Returns:
            查询结果
        """
        start_id = self._entity_index.get(start_entity)
        if not start_id:
            return []
        
        results = []
        visited = {start_id}
        current_level = [start_id]
        
        for hop in range(max_hops):
            next_level = []
            for node_id in current_level:
                for neighbor in self.graph.neighbors(node_id):
                    if neighbor in visited:
                        continue
                    
                    edge_data = self.graph.get_edge_data(node_id, neighbor)
                    relation = edge_data.get("relation_type")
                    
                    if not relation_types or relation in relation_types:
                        visited.add(neighbor)
                        next_level.append(neighbor)
                        
                        node_data = self.graph.nodes[neighbor]
                        results.append({
                            "hop": hop + 1,
                            "name": node_data.get("name"),
                            "type": node_data.get("entity_type"),
                            "relation": relation,
                            "properties": node_data.get("properties", {})
                        })
            
            current_level = next_level
        
        return results
    
    def search_entities(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索实体
        
        Args:
            keyword: 关键词
            limit: 返回数量
            
        Returns:
            匹配的实体列表
        """
        results = []
        keyword_lower = keyword.lower()
        
        for node_id, node_data in self.graph.nodes(data=True):
            name = node_data.get("name", "").lower()
            if keyword_lower in name:
                results.append({
                    "id": node_id,
                    "name": node_data.get("name"),
                    "type": node_data.get("entity_type"),
                    "properties": node_data.get("properties", {})
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        type_counts = {}
        for _, node_data in self.graph.nodes(data=True):
            entity_type = node_data.get("entity_type", "Unknown")
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        
        relation_counts = {}
        for _, _, edge_data in self.graph.edges(data=True):
            relation = edge_data.get("relation_type", "Unknown")
            relation_counts[relation] = relation_counts.get(relation, 0) + 1
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "entity_types": type_counts,
            "relation_types": relation_counts
        }
    
    def save(self) -> None:
        """保存图谱到文件"""
        os.makedirs(self.storage_path, exist_ok=True)
        
        # 保存节点
        nodes_data = []
        for node_id, node_data in self.graph.nodes(data=True):
            nodes_data.append({
                "id": node_id,
                **node_data
            })
        
        # 保存边
        edges_data = []
        for source, target, edge_data in self.graph.edges(data=True):
            edges_data.append({
                "source": source,
                "target": target,
                **edge_data
            })
        
        # 保存索引
        index_data = self._entity_index
        
        # 写入文件
        with open(os.path.join(self.storage_path, "nodes.json"), "w", encoding="utf-8") as f:
            json.dump(nodes_data, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(self.storage_path, "edges.json"), "w", encoding="utf-8") as f:
            json.dump(edges_data, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(self.storage_path, "index.json"), "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"知识图谱已保存到 {self.storage_path}")
    
    def _load(self) -> None:
        """从文件加载图谱"""
        try:
            # 加载节点
            nodes_path = os.path.join(self.storage_path, "nodes.json")
            if os.path.exists(nodes_path):
                with open(nodes_path, "r", encoding="utf-8") as f:
                    nodes_data = json.load(f)
                
                for node in nodes_data:
                    node_id = node.pop("id")
                    self.graph.add_node(node_id, **node)
                    self._entity_index[node.get("name")] = node_id
            
            # 加载边
            edges_path = os.path.join(self.storage_path, "edges.json")
            if os.path.exists(edges_path):
                with open(edges_path, "r", encoding="utf-8") as f:
                    edges_data = json.load(f)
                
                for edge in edges_data:
                    source = edge.pop("source")
                    target = edge.pop("target")
                    self.graph.add_edge(source, target, **edge)
            
            # 加载索引
            index_path = os.path.join(self.storage_path, "index.json")
            if os.path.exists(index_path):
                with open(index_path, "r", encoding="utf-8") as f:
                    self._entity_index = json.load(f)
            
            logger.info(f"知识图谱加载完成，节点数: {self.graph.number_of_nodes()}")
            
        except Exception as e:
            logger.warning(f"加载知识图谱失败: {e}，将创建新图谱")


def build_default_knowledge_graph() -> KnowledgeGraph:
    """
    构建默认知识图谱（示例数据）
    
    Returns:
        初始化好的知识图谱
    """
    kg = KnowledgeGraph()
    
    # 添加概念
    kg.add_concept("白酒", "白酒行业概念板块")
    kg.add_concept("新能源", "新能源行业概念板块")
    kg.add_concept("半导体", "半导体芯片概念板块")
    kg.add_concept("医药", "医药生物概念板块")
    kg.add_concept("银行", "银行金融概念板块")
    
    # 添加公司（白酒）
    kg.add_company("600519", "茅台", "白酒", market_cap=2.2e12, pe_ratio=25)
    kg.add_company("000858", "五粮液", "白酒", market_cap=0.6e12, pe_ratio=20)
    kg.add_company("000568", "泸州老窖", "白酒", market_cap=0.3e12, pe_ratio=22)
    kg.add_company("002304", "洋河股份", "白酒", market_cap=0.15e12, pe_ratio=18)
    
    # 添加公司（新能源）
    kg.add_company("300750", "宁德时代", "新能源", market_cap=0.9e12, pe_ratio=30)
    kg.add_company("002594", "比亚迪", "新能源", market_cap=0.7e12, pe_ratio=35)
    
    # 添加公司（半导体）
    kg.add_company("688981", "中芯国际", "半导体", market_cap=0.4e12, pe_ratio=40)
    
    # 关联概念
    kg.link_company_to_concept("茅台", "白酒")
    kg.link_company_to_concept("五粮液", "白酒")
    kg.link_company_to_concept("泸州老窖", "白酒")
    kg.link_company_to_concept("洋河股份", "白酒")
    kg.link_company_to_concept("宁德时代", "新能源")
    kg.link_company_to_concept("比亚迪", "新能源")
    kg.link_company_to_concept("中芯国际", "半导体")
    
    # 添加竞争关系
    kg.add_competition("茅台", "五粮液")
    kg.add_competition("茅台", "泸州老窖")
    kg.add_competition("五粮液", "泸州老窖")
    kg.add_competition("宁德时代", "比亚迪")
    
    # 保存
    kg.save()
    
    logger.info("默认知识图谱构建完成")
    
    return kg
