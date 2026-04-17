#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全面检查数据库中是否存储了 API 密钥
"""
import sys
import os
import json
import pickle
from pathlib import Path

# 添加 backend 到路径
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

os.environ['PYTHONPATH'] = str(ROOT / "backend")


def check_database():
    """检查 SQLite 数据库"""
    print("=" * 60)
    print("检查 SQLite 数据库")
    print("=" * 60)
    
    from app.core.config import DB_PATH, engine, SessionLocal
    from sqlalchemy import inspect, text
    
    print(f"\n数据库路径: {DB_PATH}")
    
    # 检查所有表
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n找到的表: {tables}")
    
    found_key = False
    
    # 检查每个表的数据
    for table in tables:
        print(f"\n--- 检查表: {table} ---")
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {table}"))
                rows = result.fetchall()
                columns = result.keys()
                
                print(f"列名: {list(columns)}")
                print(f"行数: {len(rows)}")
                
                # 特别仔细检查 messages 表，因为有 453 条记录
                if table == 'messages':
                    print(f"\n[特别检查] 正在扫描 {len(rows)} 条消息...")
                
                # 检查每行数据
                for i, row in enumerate(rows):
                    row_dict = dict(zip(columns, row))
                    for key, value in row_dict.items():
                        if value and isinstance(value, str):
                            # 检查是否包含 API 密钥模式
                            if 'sk-' in value and len(value) > 20:
                                print(f"[WARNING] [表 {table}, 行 {i}] 字段 {key} 中发现疑似 API 密钥!")
                                print(f"   内容预览: {value[:50]}...")
                                found_key = True
        except Exception as e:
            print(f"检查表 {table} 时出错: {e}")
    
    return found_key


def check_json_files():
    """检查所有 JSON 文件"""
    print("\n" + "=" * 60)
    print("检查 JSON 文件")
    print("=" * 60)
    
    found_key = False
    json_files = list(ROOT.rglob("*.json"))
    
    print(f"\n找到 {len(json_files)} 个 JSON 文件")
    
    for json_file in json_files:
        # 跳过 node_modules 和其他不需要的目录
        if 'node_modules' in str(json_file) or '.git' in str(json_file):
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'sk-' in content and len(content) > 100:
                    print(f"\n⚠️  在 {json_file} 中发现 'sk-' 模式")
                    # 尝试解析 JSON
                    try:
                        data = json.loads(content)
                        # 检查所有值
                        def check_dict(d, path=""):
                            nonlocal found_key
                            if isinstance(d, dict):
                                for k, v in d.items():
                                    new_path = f"{path}.{k}" if path else k
                                    if isinstance(v, str) and 'sk-' in v and len(v) > 20:
                                        print(f"   字段 {new_path}: {v[:20]}...")
                                        found_key = True
                                    elif isinstance(v, (dict, list)):
                                        check_dict(v, new_path)
                            elif isinstance(d, list):
                                for i, item in enumerate(d):
                                    check_dict(item, f"{path}[{i}]")
                        
                        check_dict(data)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            pass
    
    return found_key


def check_pickle_files():
    """检查 pickle 文件"""
    print("\n" + "=" * 60)
    print("检查 Pickle 文件")
    print("=" * 60)
    
    found_key = False
    pickle_files = list(ROOT.rglob("*.pickle")) + list(ROOT.rglob("*.pkl"))
    
    print(f"\n找到 {len(pickle_files)} 个 Pickle 文件")
    
    for pickle_file in pickle_files:
        try:
            with open(pickle_file, 'rb') as f:
                # 尝试读取但不完全反序列化（安全起见）
                content = f.read()
                if b'sk-' in content:
                    print(f"⚠️  在 {pickle_file} 中发现 'sk-' 字节模式")
                    found_key = True
        except Exception as e:
            pass
    
    return found_key


def check_env_files():
    """检查环境变量文件"""
    print("\n" + "=" * 60)
    print("检查环境变量文件")
    print("=" * 60)
    
    found_key = False
    env_patterns = ['.env', '.env.local', '.env.*']
    
    for pattern in env_patterns:
        env_files = list(ROOT.glob(pattern))
        for env_file in env_files:
            print(f"\n找到环境变量文件: {env_file}")
            try:
                with open(env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if 'sk-' in line and len(line) > 20:
                            print(f"   第 {i+1} 行: {line.strip()[:30]}...")
                            found_key = True
            except Exception as e:
                print(f"   读取错误: {e}")
    
    return found_key


def check_summary_files():
    """检查摘要文件"""
    print("\n" + "=" * 60)
    print("检查摘要文件")
    print("=" * 60)
    
    found_key = False
    summary_dir = ROOT / "data" / "summaries"
    
    if summary_dir.exists():
        summary_files = list(summary_dir.glob("*.json"))
        print(f"\n找到 {len(summary_files)} 个摘要文件")
        
        for summary_file in summary_files:
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'sk-' in content:
                        print(f"⚠️  在 {summary_file} 中发现 'sk-' 模式")
                        found_key = True
            except Exception as e:
                pass
    
    return found_key


def main():
    print("\n" + "=" * 60)
    print("开始全面检查 API 密钥存储位置")
    print("=" * 60)
    
    all_found = []
    
    # 各项检查
    all_found.append(("数据库", check_database()))
    all_found.append(("JSON 文件", check_json_files()))
    all_found.append(("Pickle 文件", check_pickle_files()))
    all_found.append(("环境变量文件", check_env_files()))
    all_found.append(("摘要文件", check_summary_files()))
    
    # 总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    
    any_found = False
    for name, found in all_found:
        status = "[WARNING] 发现疑似密钥" if found else "[PASS] 安全"
        print(f"{name}: {status}")
        if found:
            any_found = True
    
    print("\n" + "=" * 60)
    if any_found:
        print("[WARNING] 发现疑似 API 密钥，请检查上述位置！")
    else:
        print("[SUCCESS] 所有检查位置均安全，未发现 API 密钥存储")
    print("=" * 60)
    
    return 0 if not any_found else 1


if __name__ == "__main__":
    sys.exit(main())
