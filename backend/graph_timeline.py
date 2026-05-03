#!/usr/bin/env python
"""
查看知识图谱的时间线信息
"""
import sys
import os
from datetime import datetime

# 添加应用路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.services.graph_store import get_graph_store
    
    print("=" * 60)
    print("知识图谱时间线信息")
    print("=" * 60)
    
    # 获取图存储实例
    store = get_graph_store()
    
    # 1. 检查数据库文件
    print("\n[1] 数据库文件信息")
    db_path = getattr(store, '_db_path', None)
    if db_path and os.path.exists(db_path):
        stat = os.stat(db_path)
        created_time = datetime.fromtimestamp(stat.st_ctime)
        modified_time = datetime.fromtimestamp(stat.st_mtime)
        print(f"  数据库文件: {db_path}")
        print(f"  创建时间: {created_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  修改时间: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  文件大小: {stat.st_size / 1024:.2f} KB")
    
    # 2. 检查 knowledge_graph.html
    print("\n[2] 可视化文件信息")
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'knowledge_graph.html')
    if os.path.exists(html_path):
        stat = os.stat(html_path)
        html_modified = datetime.fromtimestamp(stat.st_mtime)
        print(f"  文件路径: {html_path}")
        print(f"  生成时间: {html_modified.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 3. 检查文档版本信息
    print("\n[3] 已索引文档详情")
    conn = store._get_conn()
    rows = conn.execute("SELECT filename, content_hash, entity_count, last_indexed_at FROM doc_versions").fetchall()
    
    if rows:
        for idx, row in enumerate(rows, 1):
            filename = row[0]
            entity_count = row[2]
            last_indexed = row[3]
            
            try:
                indexed_time = datetime.fromisoformat(last_indexed)
                time_str = indexed_time.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_str = last_indexed
            
            print(f"\n  [{idx}] {filename}")
            print(f"      索引时间: {time_str}")
            print(f"      实体数量: {entity_count}")
    else:
        print("  没有找到文档索引记录")
    
    # 4. 提取器版本
    print("\n[4] 提取器信息")
    extractor_version = store.get_extractor_version()
    from app.services.entity_extractor import EXTRACTOR_VERSION as CURRENT_VERSION
    print(f"  数据库中存储的版本: {extractor_version}")
    print(f"  当前代码版本: {CURRENT_VERSION}")
    
    # 5. 统计信息
    print("\n[5] 当前知识图谱统计")
    stats = store.stats()
    print(f"  总节点数: {stats.get('node_count', 0)}")
    print(f"  总边数: {stats.get('edge_count', 0)}")
    print(f"  文档数: {stats.get('doc_count', 0)}")
    
    print("\n" + "=" * 60)
    print("时间线信息获取完成! ✓")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
