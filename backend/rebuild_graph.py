#!/usr/bin/env python
"""
用最新版本的提取器重新构建知识图谱
"""
import sys
import os

# 添加应用路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.services.graph_store import get_graph_store
    from app.services.entity_extractor import EntityExtractor, EXTRACTOR_VERSION
    
    print("=" * 60)
    print("知识图谱重新构建")
    print("=" * 60)
    print(f"当前提取器版本: {EXTRACTOR_VERSION}")
    
    # 1. 获取图存储
    print("\n[1] 正在加载图存储...")
    store = get_graph_store()
    print("✓ 图存储加载成功")
    
    # 2. 检查当前版本
    print(f"\n[2] 检查版本...")
    current_stored_version = store.get_extractor_version()
    print(f"  数据库中的版本: {current_stored_version}")
    print(f"  代码中的版本: {EXTRACTOR_VERSION}")
    
    # 3. 获取所有文档
    print("\n[3] 获取已索引文档...")
    conn = store._get_conn()
    rows = conn.execute("SELECT filename FROM doc_versions").fetchall()
    
    if not rows:
        print("  没有找到已索引的文档")
        sys.exit(0)
    
    filenames = [row[0] for row in rows]
    print(f"  找到 {len(filenames)} 个文档")
    
    # 4. 更新版本号
    print("\n[4] 更新提取器版本...")
    store.set_extractor_version(EXTRACTOR_VERSION)
    print(f"✓ 版本已更新为: {EXTRACTOR_VERSION}")
    
    # 5. 获取文档内容并重新提取
    print("\n[5] 开始重新提取实体...")
    extractor = EntityExtractor()
    
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'uploads')
    
    success_count = 0
    fail_count = 0
    
    for filename in filenames:
        print(f"\n  处理: {filename}")
        
        file_path = os.path.join(uploads_dir, filename)
        if not os.path.exists(file_path):
            print(f"    ⚠️ 文件不存在: {file_path}")
            fail_count += 1
            continue
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            print(f"    ✓ 读取文件成功，长度: {len(text)} 字符")
            
            # 提取实体
            print(f"    正在提取实体...")
            extracted = extractor.extract(text, filename)
            entities = extracted.get("entities", [])
            relations = extracted.get("relations", [])
            print(f"    ✓ 提取: {len(entities)} 个实体, {len(relations)} 个关系")
            
            # 更新到图数据库
            print(f"    正在更新图数据库...")
            result = store.upsert_document(
                filename=filename,
                text=text,
                entities=entities,
                relations=relations
            )
            print(f"    ✓ 完成! 状态: {result.get('status')}")
            
            success_count += 1
            
        except Exception as e:
            print(f"    ✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1
    
    # 6. 完成
    print("\n" + "=" * 60)
    print("重新构建完成!")
    print("=" * 60)
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    
    # 7. 显示新的统计信息
    print("\n新的知识图谱统计:")
    stats = store.stats()
    print(f"  节点数: {stats.get('node_count', 0)}")
    print(f"  边数: {stats.get('edge_count', 0)}")
    print(f"  文档数: {stats.get('doc_count', 0)}")
    
    print("\n✓ 完成!")
    print("\n提示: 现在可以重新生成知识图谱可视化页面，")
    print("      访问 /api/graph/visualize 或点击前端的 '查看知识图谱' 按钮")
    
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
