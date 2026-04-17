#!/usr/bin/env python3
"""
测试ReAct修复方案的脚本
"""
import sys
import os

# 添加backend目录到Python路径
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from app.services.qa import stream_answer
from app.core.config import load_config

def test_react_integration():
    """测试ReAct集成是否正常"""
    print("=" * 60)
    print("测试 ReAct 修复方案")
    print("=" * 60)
    
    # 加载配置
    cfg = load_config()
    print(f"\n[配置] 提供商: {cfg.get('provider')}")
    print(f"[配置] ReAct 模式: {cfg.get('react', {}).get('enabled', False)}")
    
    # 测试问题
    test_question = "宁波今天天气怎么样？"
    print(f"\n[测试问题] {test_question}")
    print("\n[开始流式响应]")
    print("-" * 60)
    
    try:
        # 测试ReAct模式
        events = list(stream_answer(
            test_question,
            provider=cfg.get('provider'),
            use_react=True,
            include_state=True
        ))
        
        print("\n" + "-" * 60)
        print(f"[测试完成] 共收到 {len(events)} 个事件")
        print("\n[事件类型统计]")
        
        # 统计事件类型
        event_types = {}
        for i, event in enumerate(events):
            if isinstance(event, dict):
                event_type = event.get('type', 'unknown')
                event_types[event_type] = event_types.get(event_type, 0) + 1
                print(f"  {i+1}. {event_type}")
            else:
                event_types['content'] = event_types.get('content', 0) + 1
                print(f"  {i+1}. content: {str(event)[:50]}...")
        
        print("\n[事件类型汇总]")
        for event_type, count in event_types.items():
            print(f"  - {event_type}: {count} 次")
        
        # 检查关键事件
        has_react_thought = 'react_thought' in event_types
        has_react_final_answer = 'react_final_answer' in event_types
        has_content = 'content' in event_types
        
        print("\n[关键事件检查]")
        print(f"  ✓ react_thought: {'是' if has_react_thought else '否'}")
        print(f"  ✓ react_final_answer: {'是' if has_react_final_answer else '否'}")
        print(f"  ✓ content: {'是' if has_content else '否'}")
        
        if has_react_thought and has_react_final_answer and has_content:
            print("\n✅ 测试通过！ReAct集成工作正常。")
            return True
        else:
            print("\n❌ 测试失败！缺少关键事件。")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_react_integration()
    sys.exit(0 if success else 1)
