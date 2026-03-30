"""
知识图谱模块
基于JSON实现轻量级知识图谱（无外部依赖）
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import os
import json
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
    BELONGS_TO = "BELONGS_TO"
    COMPETES = "COMPETES"
    SUPPLIES = "SUPPLIES"
    HAS_INDICATOR = "HAS_INDICATOR"
    AFFECTS = "AFFECTS"
    WORKS_AT = "WORKS_AT"
    RELATED_TO = "RELATED_TO"


class KnowledgeGraph:
    """知识图谱（简化版，基于字典实现）"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            os.path.dirname(__file__), "..", "data", "knowledge_graph"
        )
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[Dict[str, Any]] = []
        self._entity_index: Dict[str, str] = {}
        
        self._load()
        
        logger.info(f"知识图谱初始化完成，节点数: {len(self._nodes)}, 边数: {len(self._edges)}")
    
    @property
    def graph(self):
        """兼容性属性"""
        return self
    
    def number_of_nodes(self) -> int:
        return len(self._nodes)
    
    def number_of_edges(self) -> int:
        return len(self._edges)
    
    def add_entity(
        self,
        entity_type: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> str:
        node_id = f"{entity_type}_{name}"
        
        self._nodes[node_id] = {
            "entity_type": entity_type,
            "name": name,
            "properties": properties or {},
            "created_at": datetime.now().isoformat()
        }
        
        self._entity_index[name] = node_id
        return node_id
    
    def add_relation(
        self,
        source_name: str,
        relation_type: str,
        target_name: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        source_id = self._entity_index.get(source_name)
        target_id = self._entity_index.get(target_name)
        
        if not source_id or not target_id:
            logger.warning(f"实体不存在: {source_name} -> {target_name}")
            return False
        
        self._edges.append({
            "source": source_id,
            "target": target_id,
            "relation_type": relation_type,
            "properties": properties or {},
            "created_at": datetime.now().isoformat()
        })
        
        return True
    
    def add_company(
        self,
        code: str,
        name: str,
        industry: Optional[str] = None,
        market_cap: Optional[float] = None,
        pe_ratio: Optional[float] = None
    ) -> str:
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
        return self.add_entity(
            EntityType.CONCEPT,
            name,
            {"description": description}
        )
    
    def link_company_to_concept(self, company_name: str, concept_name: str) -> bool:
        return self.add_relation(company_name, RelationType.BELONGS_TO, concept_name)
    
    def add_competition(self, company1: str, company2: str) -> bool:
        return self.add_relation(company1, RelationType.COMPETES, company2)
    
    def add_supply_chain(self, supplier: str, customer: str) -> bool:
        return self.add_relation(supplier, RelationType.SUPPLIES, customer)
    
    def query_entity(self, name: str) -> Optional[Dict[str, Any]]:
        node_id = self._entity_index.get(name)
        if not node_id or node_id not in self._nodes:
            return None
        
        node_data = self._nodes[node_id]
        
        relations = []
        for edge in self._edges:
            if edge["source"] == node_id:
                target_data = self._nodes.get(edge["target"], {})
                relations.append({
                    "direction": "out",
                    "relation": edge.get("relation_type"),
                    "target": target_data.get("name"),
                    "target_type": target_data.get("entity_type")
                })
            elif edge["target"] == node_id:
                source_data = self._nodes.get(edge["source"], {})
                relations.append({
                    "direction": "in",
                    "relation": edge.get("relation_type"),
                    "source": source_data.get("name"),
                    "source_type": source_data.get("entity_type")
                })
        
        return {
            "id": node_id,
            "name": name,
            "type": node_data.get("entity_type"),
            "properties": node_data.get("properties", {}),
            "relations": relations
        }
    
    def query_entities(self, names: List[str]) -> List[Dict[str, Any]]:
        results = []
        for name in names:
            entity_info = self.query_entity(name)
            if entity_info:
                results.append(entity_info)
        return results
    
    def get_concept_stocks(self, concept_name: str) -> List[Dict[str, Any]]:
        concept_id = self._entity_index.get(concept_name)
        if not concept_id:
            return []
        
        stocks = []
        for edge in self._edges:
            if edge["target"] == concept_id and edge["relation_type"] == RelationType.BELONGS_TO:
                node_data = self._nodes.get(edge["source"], {})
                if node_data.get("entity_type") == EntityType.COMPANY:
                    stocks.append({
                        "name": node_data.get("name"),
                        "code": node_data.get("properties", {}).get("code"),
                        "market_cap": node_data.get("properties", {}).get("market_cap")
                    })
        
        stocks.sort(key=lambda x: x.get("market_cap") or 0, reverse=True)
        return stocks
    
    def get_competitors(self, company_name: str) -> List[str]:
        company_id = self._entity_index.get(company_name)
        if not company_id:
            return []
        
        competitors = []
        for edge in self._edges:
            if edge["relation_type"] == RelationType.COMPETES:
                if edge["source"] == company_id:
                    competitors.append(self._nodes.get(edge["target"], {}).get("name"))
                elif edge["target"] == company_id:
                    competitors.append(self._nodes.get(edge["source"], {}).get("name"))
        
        return list(set(competitors))
    
    def multi_hop_query(
        self,
        start_entity: str,
        relation_types: List[str],
        max_hops: int = 2
    ) -> List[Dict[str, Any]]:
        start_id = self._entity_index.get(start_entity)
        if not start_id:
            return []
        
        results = []
        visited = {start_id}
        current_level = [start_id]
        
        for hop in range(max_hops):
            next_level = []
            for node_id in current_level:
                for edge in self._edges:
                    if edge["source"] == node_id:
                        neighbor = edge["target"]
                        if neighbor in visited:
                            continue
                        
                        relation = edge.get("relation_type")
                        if not relation_types or relation in relation_types:
                            visited.add(neighbor)
                            next_level.append(neighbor)
                            
                            node_data = self._nodes.get(neighbor, {})
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
        results = []
        keyword_lower = keyword.lower()
        
        for node_id, node_data in self._nodes.items():
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
        type_counts = {}
        for node_data in self._nodes.values():
            entity_type = node_data.get("entity_type", "Unknown")
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
        
        relation_counts = {}
        for edge in self._edges:
            relation = edge.get("relation_type", "Unknown")
            relation_counts[relation] = relation_counts.get(relation, 0) + 1
        
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "entity_types": type_counts,
            "relation_types": relation_counts
        }
    
    def save(self) -> None:
        os.makedirs(self.storage_path, exist_ok=True)
        
        nodes_data = [{"id": k, **v} for k, v in self._nodes.items()]
        
        with open(os.path.join(self.storage_path, "nodes.json"), "w", encoding="utf-8") as f:
            json.dump(nodes_data, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(self.storage_path, "edges.json"), "w", encoding="utf-8") as f:
            json.dump(self._edges, f, ensure_ascii=False, indent=2)
        
        with open(os.path.join(self.storage_path, "index.json"), "w", encoding="utf-8") as f:
            json.dump(self._entity_index, f, ensure_ascii=False, indent=2)
        
        logger.info(f"知识图谱已保存到 {self.storage_path}")
    
    def _load(self) -> None:
        try:
            nodes_path = os.path.join(self.storage_path, "nodes.json")
            if os.path.exists(nodes_path):
                with open(nodes_path, "r", encoding="utf-8") as f:
                    nodes_data = json.load(f)
                
                for node in nodes_data:
                    node_id = node.pop("id")
                    self._nodes[node_id] = node
                    self._entity_index[node.get("name")] = node_id
            
            edges_path = os.path.join(self.storage_path, "edges.json")
            if os.path.exists(edges_path):
                with open(edges_path, "r", encoding="utf-8") as f:
                    self._edges = json.load(f)
            
            index_path = os.path.join(self.storage_path, "index.json")
            if os.path.exists(index_path):
                with open(index_path, "r", encoding="utf-8") as f:
                    self._entity_index = json.load(f)
            
            logger.info(f"知识图谱加载完成，节点数: {len(self._nodes)}")
            
        except Exception as e:
            logger.warning(f"加载知识图谱失败: {e}，将创建新图谱")


def build_default_knowledge_graph() -> KnowledgeGraph:
    """构建默认知识图谱"""
    kg = KnowledgeGraph()
    
    kg.add_concept("白酒", "白酒行业概念板块")
    kg.add_concept("新能源", "新能源行业概念板块")
    kg.add_concept("半导体", "半导体芯片概念板块")
    kg.add_concept("医药", "医药生物概念板块")
    kg.add_concept("银行", "银行金融概念板块")
    
    kg.add_company("600519", "茅台", "白酒", market_cap=2.2e12, pe_ratio=25)
    kg.add_company("000858", "五粮液", "白酒", market_cap=0.6e12, pe_ratio=20)
    kg.add_company("000568", "泸州老窖", "白酒", market_cap=0.3e12, pe_ratio=22)
    kg.add_company("002304", "洋河股份", "白酒", market_cap=0.15e12, pe_ratio=18)
    kg.add_company("300750", "宁德时代", "新能源", market_cap=0.9e12, pe_ratio=30)
    kg.add_company("002594", "比亚迪", "新能源", market_cap=0.7e12, pe_ratio=35)
    kg.add_company("688981", "中芯国际", "半导体", market_cap=0.4e12, pe_ratio=40)
    
    kg.link_company_to_concept("茅台", "白酒")
    kg.link_company_to_concept("五粮液", "白酒")
    kg.link_company_to_concept("泸州老窖", "白酒")
    kg.link_company_to_concept("洋河股份", "白酒")
    kg.link_company_to_concept("宁德时代", "新能源")
    kg.link_company_to_concept("比亚迪", "新能源")
    kg.link_company_to_concept("中芯国际", "半导体")
    
    kg.add_competition("茅台", "五粮液")
    kg.add_competition("茅台", "泸州老窖")
    kg.add_competition("五粮液", "泸州老窖")
    kg.add_competition("宁德时代", "比亚迪")
    
    kg.save()
    
    logger.info("默认知识图谱构建完成")
    
    return kg