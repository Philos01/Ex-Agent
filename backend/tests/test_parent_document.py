import pytest
import sys
import os
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.parent_document import (
    ParentDocument,
    generate_parent_documents,
    generate_child_chunks,
    _merge_short_parents,
    _split_long_parents,
)


class TestParentDocumentGeneration:

    def test_basic_markdown_headers(self):
        text = textwrap.dedent("""\
            # 第一章 概述

            这是第一章的内容，包含了一些基础信息。

            ## 1.1 研究背景

            研究背景的详细描述，说明了为什么需要这项研究。

            ## 1.2 研究目标

            本研究的目标是解决遥感图像融合中的关键问题。

            # 第二章 方法

            本章介绍了所采用的方法。

            ## 2.1 数据预处理

            数据预处理包括辐射校正和几何校正。
        """)
        parents = generate_parent_documents(text, "test.md", min_parent_chars=1)
        assert len(parents) >= 2
        assert any("概述" in p.title for p in parents)
        assert any("方法" in p.title for p in parents)

    def test_chinese_section_headers(self):
        text = textwrap.dedent("""\
            摘要

            本文提出了一种新的遥感图像融合方法。

            引言

            遥感图像融合是遥感领域的重要研究方向。

            方法

            我们采用了深度学习方法进行图像融合。

            结论

            实验结果表明，所提方法优于现有方法。
        """)
        parents = generate_parent_documents(text, "cn_paper.md", min_parent_chars=1)
        assert len(parents) >= 2

    def test_english_section_headers(self):
        text = textwrap.dedent("""\
            1. Introduction

            This paper presents a novel approach.

            2. Methodology

            We propose a deep learning based method.

            3. Results

            Our method achieves state-of-the-art performance.
        """)
        parents = generate_parent_documents(text, "en_paper.md", min_parent_chars=1)
        assert len(parents) >= 2

    def test_empty_text(self):
        parents = generate_parent_documents("", "empty.md")
        assert len(parents) == 0

    def test_short_text(self):
        parents = generate_parent_documents("这是一段短文本，但足够长以通过最小长度检查。", "short.md", min_parent_chars=1)
        assert len(parents) >= 1

    def test_title_hierarchy(self):
        text = textwrap.dedent("""\
            # 第一章

            第一章内容。

            ## 1.1 子节

            子节内容。
        """)
        parents = generate_parent_documents(text, "hierarchy.md", min_parent_chars=1)
        for p in parents:
            assert isinstance(p.title_hierarchy, list)

    def test_parent_id_is_uuid(self):
        text = "# 测试\n\n一些内容。"
        parents = generate_parent_documents(text, "uuid_test.md")
        for p in parents:
            assert len(p.parent_id) == 36
            assert p.parent_id.count('-') == 4


class TestMergeShortParents:

    def test_merge_short(self):
        parents = [
            ParentDocument(
                parent_id="1", title="长章节", title_hierarchy=["长章节"],
                content="A" * 500, filename="test.md",
                section_level=1, char_count=500
            ),
            ParentDocument(
                parent_id="2", title="短章节", title_hierarchy=["短章节"],
                content="B" * 50, filename="test.md",
                section_level=1, char_count=50
            ),
        ]
        merged = _merge_short_parents(parents, min_chars=300)
        assert len(merged) == 1
        assert "A" * 500 in merged[0].content
        assert "B" * 50 in merged[0].content

    def test_no_merge_when_all_long(self):
        parents = [
            ParentDocument(
                parent_id="1", title="章节1", title_hierarchy=["章节1"],
                content="A" * 500, filename="test.md",
                section_level=1, char_count=500
            ),
            ParentDocument(
                parent_id="2", title="章节2", title_hierarchy=["章节2"],
                content="B" * 500, filename="test.md",
                section_level=1, char_count=500
            ),
        ]
        merged = _merge_short_parents(parents, min_chars=300)
        assert len(merged) == 2


class TestSplitLongParents:

    def test_split_long(self):
        long_content = "\n\n".join([f"段落{i}的内容，包含了一些文字描述。" for i in range(200)])
        parents = [
            ParentDocument(
                parent_id="1", title="长章节", title_hierarchy=["长章节"],
                content=long_content, filename="test.md",
                section_level=1, char_count=len(long_content)
            ),
        ]
        split = _split_long_parents(parents, max_chars=800)
        assert len(split) > 1
        for p in split:
            assert p.char_count <= 820

    def test_no_split_when_short(self):
        parents = [
            ParentDocument(
                parent_id="1", title="短章节", title_hierarchy=["短章节"],
                content="短内容", filename="test.md",
                section_level=1, char_count=3
            ),
        ]
        split = _split_long_parents(parents, max_chars=8000)
        assert len(split) == 1


class TestChildChunkGeneration:

    def test_basic_chunking(self):
        parent = ParentDocument(
            parent_id="test-uuid",
            title="测试章节",
            title_hierarchy=["测试章节"],
            content="这是第一句话。这是第二句话。这是第三句话。这是第四句话。这是第五句话。",
            filename="test.md",
            section_level=1,
            char_count=30
        )
        children = generate_child_chunks(parent, child_chunk_size=20, child_chunk_overlap=4)
        assert len(children) >= 1
        for child in children:
            assert child["parent_id"] == "test-uuid"
            assert "section_title" in child
            assert "filename" in child
            assert "chunk_index" in child

    def test_child_chunk_ids_updated(self):
        parent = ParentDocument(
            parent_id="test-uuid-2",
            title="测试",
            title_hierarchy=["测试"],
            content="这是一些测试内容。用来验证子切片ID是否正确更新。需要更多内容来确保生成多个切片。",
            filename="test.md",
            section_level=1,
            char_count=40
        )
        generate_child_chunks(parent, child_chunk_size=30, child_chunk_overlap=6)
        assert len(parent.child_chunk_ids) > 0
        for cid in parent.child_chunk_ids:
            assert cid.startswith("test-uuid-2_")

    def test_empty_parent(self):
        parent = ParentDocument(
            parent_id="empty-uuid",
            title="空",
            title_hierarchy=["空"],
            content="",
            filename="test.md",
            section_level=1,
            char_count=0
        )
        children = generate_child_chunks(parent)
        assert len(children) == 0

    def test_long_sentence_forced_split(self):
        parent = ParentDocument(
            parent_id="long-uuid",
            title="长句",
            title_hierarchy=["长句"],
            content="A" * 500,
            filename="test.md",
            section_level=1,
            char_count=500
        )
        children = generate_child_chunks(parent, child_chunk_size=100, child_chunk_overlap=20)
        assert len(children) >= 5
        for child in children:
            assert len(child["text"]) <= 120


class TestParentDocumentDataclass:

    def test_default_child_chunk_ids(self):
        p = ParentDocument(
            parent_id="test",
            title="测试",
            title_hierarchy=[],
            content="内容",
            filename="test.md",
            section_level=1,
            char_count=2
        )
        assert p.child_chunk_ids == []

    def test_custom_child_chunk_ids(self):
        p = ParentDocument(
            parent_id="test",
            title="测试",
            title_hierarchy=[],
            content="内容",
            filename="test.md",
            section_level=1,
            char_count=2,
            child_chunk_ids=["id1", "id2"]
        )
        assert len(p.child_chunk_ids) == 2


class TestEndToEnd:

    def test_full_pipeline(self):
        text = textwrap.dedent("""\
            # 遥感图像融合方法研究

            ## 1. 引言

            遥感图像融合是遥感数据处理中的关键技术之一。通过融合不同分辨率的图像，可以获得既具有高空间分辨率又具有丰富光谱信息的融合图像。本文针对全色与多光谱图像融合问题，提出了一种基于深度学习的新方法。

            ## 2. 相关工作

            传统的图像融合方法包括IHS变换、PCA变换和Brovey变换等。这些方法虽然简单高效，但容易产生光谱失真。近年来，深度学习方法在图像融合领域取得了显著进展。

            ## 3. 方法

            ### 3.1 网络架构

            我们设计了一个双分支网络架构，分别处理全色图像和多光谱图像。全色分支提取空间细节特征，多光谱分支提取光谱特征。

            ### 3.2 损失函数

            损失函数由三部分组成：重建损失、光谱损失和空间损失。重建损失使用L1范数，光谱损失使用SAM指标，空间损失使用梯度差异。

            ## 4. 实验

            我们在WorldView-3和QuickBird数据集上进行了实验。实验结果表明，所提方法在PSNR和SSIM指标上均优于对比方法。

            ## 5. 结论

            本文提出了一种新的遥感图像融合方法，实验结果验证了方法的有效性。
        """)
        parents = generate_parent_documents(text, "fusion_paper.md", min_parent_chars=50, max_parent_chars=8000)
        assert len(parents) >= 2

        all_children = []
        for parent in parents:
            children = generate_child_chunks(parent, child_chunk_size=200, child_chunk_overlap=40)
            all_children.extend(children)

        assert len(all_children) >= len(parents)

        for child in all_children:
            assert "parent_id" in child
            assert "text" in child
            assert "section_title" in child
            assert "filename" in child
            assert child["filename"] == "fusion_paper.md"

        parent_ids_in_children = set(c["parent_id"] for c in all_children)
        parent_ids_in_parents = set(p.parent_id for p in parents)
        assert parent_ids_in_children.issubset(parent_ids_in_parents)
