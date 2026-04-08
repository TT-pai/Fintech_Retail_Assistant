"""增量更新知识图谱脚本"""
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.knowledge_graph import KnowledgeGraph


def main():
    # 加载知识图谱
    kg = KnowledgeGraph()
    
    # 加载新的股票列表
    cache_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "market_cache", "stock_list.json"
    )
    
    with open(cache_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        stocks = data.get('data', [])
    
    # 添加缺失的股票
    added = 0
    for stock in stocks:
        result = kg.query_entity(stock['name'])
        if result is None:
            kg.add_company(
                code=stock['code'],
                name=stock['name'],
                industry=None,
                market_cap=0,
                pe_ratio=0
            )
            added += 1
    
    # 保存
    kg.save()
    
    stats = kg.get_graph_stats()
    print(f"新增节点: {added}")
    print(f"总节点数: {stats['total_nodes']}")
    print(f"总边数: {stats['total_edges']}")


if __name__ == "__main__":
    main()
