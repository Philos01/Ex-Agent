#!/usr/bin/env python3
"""
检查向量库中的文档
"""
import sys
sys.path.append('backend')

from app.services.vector_store import init_collection

print("=== 检查向量库中的文档 ===")

collection = init_collection()

# 获取所有文档
print("获取所有文档...")
try:
    # 获取所有文档的元数据
    all_docs = collection.get(include=["metadatas"])
    
    if all_docs and all_docs.get("metadatas"):
        print(f"向量库中共有 {len(all_docs['metadatas'])} 个文档块")
        
        # 统计不同的source
        sources = {}
        for metadata in all_docs['metadatas']:
            source = metadata.get('source', 'unknown')
            if source in sources:
                sources[source] += 1
            else:
                sources[source] = 1
        
        print("\n来源统计:")
        for source, count in sources.items():
            print(f"  {source}: {count} 个文档块")
    else:
        print("向量库中没有文档")
except Exception as e:
    print(f"检查向量库失败: {e}")

print("\n=== 检查完成 ===")
