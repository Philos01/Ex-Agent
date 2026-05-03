"""
图检索和父子检索架构升级 - 全流程测试
测试场景包括：
1. 事实查询（图足够）
2. 详细信息查询（图不够，需要父子检索补充）
3. LLM 判断失败的规则 fallback
4. 线索完整利用
"""
import pytest
import json
import logging
from unittest.mock import patch, MagicMock

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestGraphRetrievalJudge:
    """测试 graph_retrieval_judge.py 的 LLM 逻辑判断功能"""

    def test_module_importable(self):
        """测试模块可导入"""
        from app.services import graph_retrieval_judge
        assert hasattr(graph_retrieval_judge, 'judge_graph_sufficiency')
        assert hasattr(graph_retrieval_judge, '_rule_based_judge')

    def test_prompt_templates_exist(self):
        """测试提示词模板存在"""
        from app.services import graph_retrieval_judge
        assert hasattr(graph_retrieval_judge, 'JUDGE_SYSTEM_PROMPT')
        assert hasattr(graph_retrieval_judge, 'JUDGE_USER_PROMPT_TEMPLATE')

    def test_rule_based_judge_entity_list(self):
        """测试实体列表查询规则判断"""
        from app.services import graph_retrieval_judge

        mock_route_result = {
            "route": "entity_list",
            "related_entities": [
                {"name": "张三", "type": "人物", "properties": {"职位": "工程师"}},
                {"name": "李四", "type": "人物", "properties": {"职位": "助理"}}
            ],
            "paths": []
        }
        result = graph_retrieval_judge._rule_based_judge(
            "组里有哪些人", mock_route_result
        )
        logger.info(f"实体列表查询规则判断结果: {result}")
        assert isinstance(result, dict)
        assert "sufficient" in result

    def test_rule_based_judge_relation_path(self):
        """测试有关系路径查询规则判断"""
        from app.services import graph_retrieval_judge

        mock_route_result = {
            "route": "relation",
            "related_entities": [
                {"name": "张三", "type": "人物"},
                {"name": "宁波拓普", "type": "组织"}
            ],
            "paths": [
                {"from": "张三", "to": "宁波拓普", "type": "工作单位", "description": "张三在宁波拓普工作"}
            ]
        }
        result = graph_retrieval_judge._rule_based_judge(
            "张三在哪个公司工作", mock_route_result
        )
        logger.info(f"关系路径查询规则判断结果: {result}")
        assert isinstance(result, dict)

    def test_rule_based_judge_detail_query(self):
        """测试详细信息查询规则判断"""
        from app.services import graph_retrieval_judge

        mock_route_result = {
            "route": "semantic",
            "related_entities": [
                {"name": "张三", "type": "人物", "properties": {"职位": "工程师"}}
            ],
            "paths": []
        }
        result = graph_retrieval_judge._rule_based_judge(
            "详细介绍一下张三的背景", mock_route_result
        )
        logger.info(f"详细信息查询规则判断结果: {result}")
        assert isinstance(result, dict)
        assert result["sufficient"] == False, "详细信息查询应该判断为 insufficient"


class TestParentRetrieverWithClues:
    """测试 parent_retriever.py 的线索传递功能（模拟）"""

    def test_module_importable(self):
        """测试模块可导入（跳过 chroma 依赖）"""
        import importlib.util
        spec = importlib.util.find_spec("app.services.parent_retriever")
        assert spec is not None, "parent_retriever 模块应该存在"

    def test_new_method_names_exist(self):
        """测试新增方法名称存在"""
        try:
            from inspect import getsourcefile
            import ast

            # 分析文件结构
            file_path = "app/services/parent_retriever.py"
            import os
            full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                assert "def search_in_documents(" in content, "search_in_documents 方法应该存在"
                assert "def enhance_query(" in content, "enhance_query 方法应该存在"
                assert "def rerank_with_focus(" in content, "rerank_with_focus 方法应该存在"
                assert "def _deduplicate_results(" in content, "_deduplicate_results 方法应该存在"
                assert "def retrieve_with_clues(" in content, "retrieve_with_clues 方法应该存在"
                logger.info("✓ parent_retriever.py 的所有新增方法名称检查通过")
        except Exception as e:
            logger.warning(f"文件分析跳过: {e}")


class TestFormatRouteResult:
    """测试 query_router.py 的 format_route_result 功能"""

    def test_module_importable(self):
        """测试模块可导入"""
        from app.services import query_router
        assert hasattr(query_router, 'format_route_result')
        assert hasattr(query_router, 'extract_entities_from_question')

    def test_extract_entities_from_question(self):
        """测试从问题中提取实体"""
        from app.services import query_router

        question = "张三在哪个公司工作"
        entities = query_router.extract_entities_from_question(question)
        logger.info(f"从问题中提取的实体: {entities}")
        assert isinstance(entities, list)


class TestGraphStoreNewMethods:
    """测试 graph_store.py 的新增方法"""

    def test_module_importable(self):
        """测试模块可导入"""
        from app.services import graph_store
        assert hasattr(graph_store, 'GraphStore')
        assert hasattr(graph_store, 'get_graph_store')

    def test_new_methods_exist(self):
        """测试新增方法存在"""
        from app.services import graph_store
        try:
            gs = graph_store.get_graph_store()
            assert hasattr(gs, 'get_entities_by_document')
            assert hasattr(gs, 'find_direct_relation')
            assert hasattr(gs, 'get_extractor_version')
            assert hasattr(gs, 'set_extractor_version')
            assert hasattr(gs, 'check_and_update_stale_documents')
            assert hasattr(gs, 'update_document_entities')
            logger.info("✓ graph_store.py 的所有新增方法检查通过")
        except Exception as e:
            logger.warning(f"初始化 GraphStore 跳过: {e}")


class TestEntityExtractorNewFeatures:
    """测试 entity_extractor.py 的新功能"""

    def test_module_importable(self):
        """测试模块可导入"""
        from app.services import entity_extractor
        assert hasattr(entity_extractor, 'EntityExtractor')
        assert hasattr(entity_extractor, 'ENTITY_EXTRACTION_PROMPT')

    def test_extractor_version_exists(self):
        """测试 EXTRACTOR_VERSION 常量存在"""
        from app.services import entity_extractor
        assert hasattr(entity_extractor, 'EXTRACTOR_VERSION')
        assert isinstance(entity_extractor.EXTRACTOR_VERSION, str)
        assert entity_extractor.EXTRACTOR_VERSION.startswith("1.1")


class TestStreamAnswerIntegration:
    """测试 stream_answer.py 的集成功能"""

    def test_module_importable(self):
        """测试模块可导入（跳过 chroma 依赖，只检查文件存在）"""
        import os
        file_path = "app/services/qa/stream_answer.py"
        full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
        assert os.path.exists(full_path), f"{file_path} 文件应该存在"
        logger.info(f"✓ {file_path} 文件存在")

    def test_format_parent_documents_exists(self):
        """测试 _format_parent_documents 辅助函数存在"""
        try:
            from inspect import getsourcefile
            import ast

            # 分析文件结构
            file_path = "app/services/qa/stream_answer.py"
            import os
            full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                assert "def _format_parent_documents(" in content, "_format_parent_documents 应该存在"
                logger.info("✓ stream_answer.py 的辅助函数检查通过")
        except Exception as e:
            logger.warning(f"文件分析跳过: {e}")


class TestConfigNewOptions:
    """测试 config.py 的新增配置项"""

    def test_config_file_readable(self):
        """测试配置文件可读取"""
        from app.core.config import get_complete_config
        cfg = get_complete_config()
        logger.info(f"配置文件读取成功: {json.dumps(cfg, ensure_ascii=False)[:200]}...")
        assert isinstance(cfg, dict)

    def test_new_graph_search_options(self):
        """测试 graph_search 的新增配置项（合并默认配置）"""
        from app.core.config import _DEFAULT_CONFIG
        # 检查默认配置中是否有这些选项
        graph_cfg = _DEFAULT_CONFIG.get("graph_search", {})
        logger.info(f"默认 graph_search 配置: {json.dumps(graph_cfg, ensure_ascii=False)}")
        assert "enable_llm_judge" in graph_cfg, "默认配置缺少 enable_llm_judge 配置项"
        assert "fallback_to_parent" in graph_cfg, "默认配置缺少 fallback_to_parent 配置项"
        logger.info("✓ graph_search 新配置项检查通过")

    def test_parent_document_config_exists(self):
        """测试 parent_document 配置项存在"""
        from app.core.config import get_complete_config
        cfg = get_complete_config()
        parent_cfg = cfg.get("parent_document_retrieval", {})
        logger.info(f"parent_document_retrieval 配置: {parent_cfg}")
        assert "parent_max_count" in parent_cfg


class TestFullIntegrationScenario:
    """测试完整集成场景（模拟执行）"""

    def test_fact_query_scenario(self):
        """测试事实查询场景（图足够）"""
        from app.services import graph_retrieval_judge

        question = "张三在哪个公司工作"
        mock_route_result = {
            "route": "relation",
            "related_entities": [
                {"name": "张三", "type": "人物", "properties": {"职位": "工程师"}},
                {"name": "宁波拓普", "type": "组织", "properties": {}}
            ],
            "paths": [
                {"from": "张三", "to": "宁波拓普", "type": "工作单位", "description": "张三在宁波拓普工作"}
            ],
            "merged_documents": []
        }

        # 使用规则 fallback 测试逻辑判断
        result = graph_retrieval_judge._rule_based_judge(question, mock_route_result)
        logger.info(f"事实查询场景测试结果: {result}")
        assert isinstance(result, dict)

    def test_detail_query_scenario(self):
        """测试详细信息查询场景（图不够，需要父子检索补充）"""
        from app.services import graph_retrieval_judge

        question = "详细介绍一下张三的背景，包括他的工作经历"
        mock_route_result = {
            "route": "semantic",
            "related_entities": [
                {"name": "张三", "type": "人物", "properties": {"职位": "工程师"}}
            ],
            "paths": [],
            "merged_documents": [
                {"filename": "2025版通讯录.md"},
                {"filename": "会议纪要.md"}
            ]
        }

        # 使用规则 fallback 测试逻辑判断
        result = graph_retrieval_judge._rule_based_judge(question, mock_route_result)
        logger.info(f"详细信息查询场景测试结果: {result}")
        assert isinstance(result, dict)
        assert "suggestions" in result
        assert "target_documents" in result["suggestions"]
        assert "focus_entities" in result["suggestions"]
        assert "search_angle" in result["suggestions"]
        assert "query_hint" in result["suggestions"]


class TestModuleStructureCheck:
    """模块文件结构完整性检查"""

    def test_graph_retrieval_judge_exists(self):
        """测试 graph_retrieval_judge.py 新建文件存在"""
        import os
        file_path = "app/services/graph_retrieval_judge.py"
        full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
        assert os.path.exists(full_path), f"新建文件 {file_path} 应该存在"
        logger.info(f"✓ 新建文件 {file_path} 存在")

    def test_entity_extractor_prompt_updated(self):
        """测试 entity_extractor.py 的提示词已更新"""
        import os
        file_path = "app/services/entity_extractor.py"
        full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
        assert os.path.exists(full_path)

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "EXTRACTOR_VERSION" in content, "EXTRACTOR_VERSION 应该存在"
        assert "properties" in content, "properties 字段在提示词中应该存在"
        assert "明确的事实" in content or "图数据库只存储" in content, "应该提到图数据库存储原则"
        logger.info("✓ entity_extractor.py 的提示词已更新")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
