#!/usr/bin/env python3
"""
测试ReAct修复方案的三种流程场景
"""
import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from unittest.mock import MagicMock, patch
from app.services.qa import _stream_answer_react

def mock_react_agent():
    """创建模拟的ReActAgent，用于测试三种不同流程场景"""
    
    class MockReActAgent:
        def __init__(self, provider=None):
            self.provider = provider
        
        def stream_run(self, question, conversation_history=""):
            """根据问题类型返回不同的流程场景"""
            
            # 场景1: 思考、行动、观察、思考、最终答案 (5步)
            if "场景1" in question or "5步" in question:
                print("[模拟] 场景1: 思考 → 行动 → 观察 → 思考 → 最终答案")
                yield {"type": "thinking", "iteration": 1, "total": 5}
                yield {"type": "thought", "content": "我需要先了解用户的问题"}
                yield {"type": "action", "name": "amap-weather", "input": {"city": "宁波"}}
                yield {"type": "observation", "content": "宁波今天的天气是晴天，温度20°C"}
                yield {"type": "thought", "content": "现在我有足够的信息回答了"}
                yield {"type": "final_answer", "content": "宁波今天天气晴朗，温度20°C，非常适合外出活动！"}
                yield {"type": "done", "final_answer": "宁波今天天气晴朗，温度20°C，非常适合外出活动！", "steps": [], "success": True}
            
            # 场景2: 思考、观察、思考、观察、思考、观察、思考、最终答案 (8步)
            elif "场景2" in question or "8步" in question:
                print("[模拟] 场景2: 思考 → 观察 → 思考 → 观察 → 思考 → 观察 → 思考 → 最终答案")
                yield {"type": "thinking", "iteration": 1, "total": 5}
                yield {"type": "thought", "content": "让我开始分析这个问题"}
                yield {"type": "observation", "content": "第一次观察结果"}
                yield {"type": "thought", "content": "基于第一次观察，我需要更多信息"}
                yield {"type": "observation", "content": "第二次观察结果"}
                yield {"type": "thought", "content": "我还需要最后一次确认"}
                yield {"type": "observation", "content": "第三次观察结果"}
                yield {"type": "thought", "content": "现在我可以给出完整答案了"}
                yield {"type": "final_answer", "content": "经过多轮观察和思考，我已经收集了足够的信息来回答您的问题！"}
                yield {"type": "done", "final_answer": "经过多轮观察和思考，我已经收集了足够的信息来回答您的问题！", "steps": [], "success": True}
            
            # 场景3: 思考、观察、思考、最终答案 (4步)
            elif "场景3" in question or "4步" in question:
                print("[模拟] 场景3: 思考 → 观察 → 思考 → 最终答案")
                yield {"type": "thinking", "iteration": 1, "total": 5}
                yield {"type": "thought", "content": "让我分析一下这个简单的问题"}
                yield {"type": "observation", "content": "关键观察结果"}
                yield {"type": "thought", "content": "好的，我已经理解了"}
                yield {"type": "final_answer", "content": "这是一个简短而直接的答案！"}
                yield {"type": "done", "final_answer": "这是一个简短而直接的答案！", "steps": [], "success": True}
            
            # 默认场景
            else:
                print("[模拟] 默认场景: 简单的思考 → 最终答案")
                yield {"type": "thought", "content": "让我简单思考一下"}
                yield {"type": "final_answer", "content": "默认答案"}
                yield {"type": "done", "final_answer": "默认答案", "steps": [], "success": True}
    
    return MockReActAgent

def test_scenario(scenario_name, test_question):
    """测试单个场景"""
    print("\n" + "=" * 80)
    print(f"测试 {scenario_name}")
    print("=" * 80)
    
    # 使用模拟的ReActAgent
    with patch('app.services.qa.ReActAgent', new=mock_react_agent()):
        try:
            # 收集所有事件
            events = list(_stream_answer_react(
                test_question,
                provider="test"
            ))
            
            print(f"\n[事件总数] {len(events)} 个事件")
            print("\n[事件序列]")
            
            # 分析事件序列
            event_sequence = []
            has_react_thought = False
            has_react_final_answer = False
            has_content = False
            has_react_steps = False
            
            for i, event in enumerate(events):
                if isinstance(event, dict):
                    event_type = event.get('type')
                    event_sequence.append(event_type)
                    print(f"  {i+1}. [{event_type}] {event.get('content', event.get('name', ''))[:50]}")
                    
                    if event_type == 'react_thought':
                        has_react_thought = True
                    elif event_type == 'react_final_answer':
                        has_react_final_answer = True
                    elif event_type == 'react_steps':
                        has_react_steps = True
                else:
                    event_sequence.append('content')
                    has_content = True
                    print(f"  {i+1}. [content] {str(event)[:50]}")
            
            # 检查是否满足所有条件
            print("\n" + "-" * 80)
            print("[验证检查]")
            
            checks = [
                ("✓ 包含 react_thought 事件", has_react_thought),
                ("✓ 包含 react_final_answer 事件", has_react_final_answer),
                ("✓ 包含 content 事件", has_content),
                ("✓ 包含 react_steps 事件", has_react_steps),
            ]
            
            all_passed = True
            for check_name, passed in checks:
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name}")
                if not passed:
                    all_passed = False
            
            if all_passed:
                print(f"\n✅ {scenario_name} 测试通过！")
                return True
            else:
                print(f"\n❌ {scenario_name} 测试失败！")
                return False
                
        except Exception as e:
            print(f"\n❌ 测试出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主测试函数"""
    print("=" * 80)
    print("ReAct 修复方案 - 三种流程场景测试")
    print("=" * 80)
    
    # 定义三个测试场景
    scenarios = [
        ("场景1: 思考、行动、观察、思考、最终答案 (5步)", "测试场景1，5步流程"),
        ("场景2: 思考、观察、思考、观察、思考、观察、思考、最终答案 (8步)", "测试场景2，8步流程"),
        ("场景3: 思考、观察、思考、最终答案 (4步)", "测试场景3，4步流程"),
    ]
    
    # 执行所有测试
    results = []
    for scenario_name, test_question in scenarios:
        result = test_scenario(scenario_name, test_question)
        results.append((scenario_name, result))
    
    # 汇总测试结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    passed_count = 0
    for scenario_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {scenario_name}: {status}")
        if result:
            passed_count += 1
    
    print(f"\n总计: {passed_count}/{len(results)} 个场景通过测试")
    
    if passed_count == len(results):
        print("\n🎉 所有测试场景都通过！修复方案有效！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查修复方案")
        return 1

if __name__ == "__main__":
    sys.exit(main())
