#!/usr/bin/env python
"""
检查知识图谱状态的简单脚本
"""
import sys
import os

# 添加应用路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.services.graph_store import get_graph_store
    
    print("=" * 60)
    print("知识图谱状态检查")
    print("=" * 60)
    
    # 获取图存储实例
    print("\n正在加载图存储...")
    store = get_graph_store()
    print("✓ 图存储加载成功")
    
    # 获取统计信息
    print("\n正在获取统计信息...")
    stats = store.stats()
    print(f"✓ 获取统计信息: {stats}")
    
    print("\n" + "=" * 60)
    print("知识图谱统计")
    print("=" * 60)
    print(f"  总节点数: {stats.get('node_count', 0)}")
    print(f"  总边数: {stats.get('edge_count', 0)}")
    print(f"  文档数: {stats.get('doc_count', 0)}")
    print(f"  数据库大小: {stats.get('db_size_kb', 0)} KB")
    
    if stats.get('node_types'):
        print(f"\n  节点类型统计:")
        for node_type, count in stats.get('node_types', {}).items():
            print(f"    - {node_type}: {count}")
    
    # 获取所有文档节点
    print(f"\n  已索引的文档:")
    doc_ids = store.get_all_document_node_ids()
    print(f"    共 {len(doc_ids)} 个文档节点")
    
    # 检查 metadata 表
    print(f"\n  检查提取器版本...")
    extractor_version = store.get_extractor_version()
    print(f"    当前版本: {extractor_version}")
    
    print("\n" + "=" * 60)
    print("检查完成! ✓")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
