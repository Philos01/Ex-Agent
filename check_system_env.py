#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查系统环境变量中是否有 API 密钥
"""
import os
import sys

print("=" * 60)
print("检查系统环境变量")
print("=" * 60)

found = False

# 检查所有环境变量
print("\n正在检查环境变量...")
for key, value in os.environ.items():
    if 'OPENAI' in key.upper() or 'API' in key.upper():
        if value and len(value) > 10:
            print(f"\n[WARNING] 发现相关环境变量: {key}")
            if 'sk-' in value:
                print(f"   值包含 'sk-' 前缀!")
                print(f"   长度: {len(value)}")
                print(f"   预览: {value[:15]}...")
                found = True

if not found:
    print("\n[PASS] 未在环境变量中发现 API 密钥")

print("\n" + "=" * 60)
print("当前 OPENAI_API_KEY 环境变量值:")
print("=" * 60)

current_key = os.environ.get('OPENAI_API_KEY', '')
if current_key:
    print(f"值存在，长度: {len(current_key)}")
    print(f"前缀: {current_key[:10]}...")
    if current_key.startswith('sk-'):
        print("[WARNING] 这是一个 OpenAI 风格的 API 密钥!")
else:
    print("[PASS] OPENAI_API_KEY 环境变量为空或不存在")

print("\n" + "=" * 60)
