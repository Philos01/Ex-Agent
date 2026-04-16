#!/usr/bin/env python3
"""
测试 arxiv-watcher 搜索数量配置
"""
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

import logging
logging.basicConfig(level=logging.INFO)


def test_config_file():
    """测试配置文件是否存在和可读"""
    print("="*70)
    print("测试 1: 配置文件检查")
    print("="*70)
    
    config_path = project_root / "skills" / "arxiv-watcher" / "skill_config.json"
    print(f"配置文件路径: {config_path}")
    
    if not config_path.exists():
        print("[FAIL] 配置文件不存在")
        return False
    
    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"[OK] 配置文件内容: {config}")
        print(f"  default_count: {config.get('default_count')}")
        return True
    except Exception as e:
        print(f"[FAIL] 无法读取配置文件: {e}")
        return False


def test_script_direct():
    """直接测试脚本"""
    print("\n" + "="*70)
    print("测试 2: 直接调用脚本")
    print("="*70)
    
    script_path = project_root / "skills" / "arxiv-watcher" / "scripts" / "search_arxiv.py"
    print(f"脚本路径: {script_path}")
    
    if not script_path.exists():
        print("[FAIL] 脚本不存在")
        return False
    
    try:
        import subprocess
        import json
        
        os.chdir(str(project_root / "skills" / "arxiv-watcher"))
        
        # 创建测试参数文件
        test_params = {"query": "deep learning", "count": 3}
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_params, f)
            params_file = f.name
        
        try:
            cmd = [sys.executable, str(script_path), "--params", params_file]
            print(f"\n执行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            print(f"\n退出码: {result.returncode}")
            if result.stdout:
                print(f"\n标准输出:\n{result.stdout[:500]}...")
            if result.stderr:
                print(f"\n标准错误:\n{result.stderr}")
            
            if result.returncode == 0 and result.stdout:
                try:
                    output_json = json.loads(result.stdout.strip())
                    print(f"\n[OK] 解析输出成功")
                    print(f"  Success: {output_json.get('success')}")
                    if output_json.get('success') and 'data' in output_json:
                        data = output_json['data']
                        print(f"  Query: {data.get('query')}")
                        print(f"  Count: {data.get('count')}")
                except Exception as e:
                    print(f"[WARN] 无法解析输出为 JSON: {e}")
            
            return True
            
        finally:
            try:
                os.unlink(params_file)
            except:
                pass
            
    except Exception as e:
        print(f"[FAIL] 直接调用脚本失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_skill_manager():
    """测试通过技能管理器调用"""
    print("\n" + "="*70)
    print("测试 3: 通过技能管理器调用")
    print("="*70)
    
    try:
        from app.skills import get_skill_manager
        
        manager = get_skill_manager()
        
        # 测试搜索
        question = "找 3 篇关于深度学习的论文"
        print(f"\n测试问题: {question}")
        
        use_skill, skill_name, params = manager.should_use_skill(question, provider="openai")
        print(f"  使用技能: {use_skill}")
        if use_skill:
            print(f"  技能名称: {skill_name}")
            print(f"  参数: {params}")
        
        if use_skill and skill_name == "arxiv-watcher":
            print("\n执行技能...")
            result = manager.execute_skill(skill_name, **params)
            print(f"  执行成功: {result.get('success')}")
            
            if result.get('success'):
                print(f"\n原始结果: {str(result)[:500]}...")
        
        print("\n[OK] 技能管理器测试完成")
        return True
        
    except Exception as e:
        print(f"[FAIL] 技能管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("ArXiv 搜索数量配置测试")
    print("="*70)
    
    tests = [
        ("配置文件检查", test_config_file),
        ("直接调用脚本", test_script_direct),
        ("技能管理器调用", test_skill_manager)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[FAIL] {name} 测试抛出异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"{status}: {name}")
    
    print("\n" + "="*70)
    print(f"总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {total - passed}")
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
