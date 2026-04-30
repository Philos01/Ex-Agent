import re
import uuid
import logging
from typing import List, Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParentDocument:
    parent_id: str
    title: str
    title_hierarchy: List[str]
    content: str
    filename: str
    section_level: int
    char_count: int
    child_chunk_ids: List[str] = field(default_factory=list)


def generate_parent_documents(
    text: str,
    filename: str,
    min_parent_chars: int = 300,
    max_parent_chars: int = 8000
) -> List[ParentDocument]:
    lines = text.split('\n')
    parents = []
    current_lines = []
    current_title = ""
    current_hierarchy = []
    current_level = 0

    md_header_pattern = re.compile(
        r'^(#{1,4})\s+(.+?)(?:\s*\{#[\w-]+\})?\s*$'
    )

    en_section_pattern = re.compile(
        r'^\s*(\d+\.?\s+[A-Z][a-zA-Z\s,:\-]+)',
        re.MULTILINE
    )

    cn_section_pattern = re.compile(
        r'^\s*(摘要|引言|相关工作|方法|实验|结果|讨论|结论|参考文献|致谢|附录)',
        re.MULTILINE
    )

    def flush_parent():
        nonlocal current_lines, current_title, current_hierarchy, current_level
        content = '\n'.join(current_lines).strip()
        if not content or len(content) < 20:
            current_lines = []
            return

        parent = ParentDocument(
            parent_id=str(uuid.uuid4()),
            title=current_title or "无标题",
            title_hierarchy=current_hierarchy.copy(),
            content=content,
            filename=filename,
            section_level=current_level,
            char_count=len(content)
        )
        parents.append(parent)
        current_lines = []

    for line in lines:
        md_match = md_header_pattern.match(line)
        en_match = en_section_pattern.match(line)
        cn_match = cn_section_pattern.match(line)

        is_section_header = False
        header_text = ""
        header_level = 0

        if md_match:
            is_section_header = True
            header_level = len(md_match.group(1))
            header_text = md_match.group(2).strip()
        elif en_match and len(line.strip()) < 100:
            is_section_header = True
            header_level = 2
            header_text = en_match.group(1).strip()
        elif cn_match and len(line.strip()) < 100:
            is_section_header = True
            header_level = 2
            header_text = cn_match.group(1).strip()

        if is_section_header:
            flush_parent()

            current_title = header_text
            current_level = header_level
            if header_level == 1:
                current_hierarchy = [header_text]
            elif header_level == 2:
                current_hierarchy = [current_hierarchy[0]] if current_hierarchy else []
                current_hierarchy.append(header_text)
            else:
                current_hierarchy.append(header_text)
            current_lines = [line]
        else:
            current_lines.append(line)

    flush_parent()

    parents = _merge_short_parents(parents, min_parent_chars)

    parents = _split_long_parents(parents, max_parent_chars)

    logger.info(f"父文档生成完成: {filename} → {len(parents)} 个父文档")
    return parents


def _merge_short_parents(
    parents: List[ParentDocument],
    min_chars: int
) -> List[ParentDocument]:
    merged = []
    for p in parents:
        if merged and p.char_count < min_chars:
            merged[-1].content += '\n\n' + p.content
            merged[-1].char_count += p.char_count
            merged[-1].title_hierarchy.extend(p.title_hierarchy)
            merged[-1].child_chunk_ids.extend(p.child_chunk_ids)
        else:
            merged.append(p)
    return merged


def _create_sub_parent(original: ParentDocument, content: str, part_num: int) -> ParentDocument:
    return ParentDocument(
        parent_id=str(uuid.uuid4()),
        title=f"{original.title} (第{part_num}部分)",
        title_hierarchy=original.title_hierarchy.copy(),
        content=content,
        filename=original.filename,
        section_level=original.section_level,
        char_count=len(content.strip())
    )


def _split_long_parents(
    parents: List[ParentDocument],
    max_chars: int
) -> List[ParentDocument]:
    result = []
    for p in parents:
        if p.char_count <= max_chars:
            result.append(p)
            continue

        paragraphs = p.content.split('\n\n')
        sub_parents = []
        current_text = ""
        part_num = 1

        for para in paragraphs:
            if len(current_text) + len(para) < max_chars:
                current_text = (current_text + '\n\n' + para).strip()
            else:
                if current_text:
                    sub_parents.append(_create_sub_parent(p, current_text, part_num))
                    part_num += 1
                current_text = para

        if current_text:
            sub_parents.append(_create_sub_parent(p, current_text, part_num))

        result.extend(sub_parents)
    return result


def generate_child_chunks(
    parent: ParentDocument,
    child_chunk_size: int = 300,
    child_chunk_overlap: int = 60
) -> List[Dict]:
    text = parent.content
    children = []

    sentences = re.split(r'(?<=[。！？\.\!\?\n])\s*', text)

    current_chunk = ""
    chunk_index = 0

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= child_chunk_size:
            current_chunk += sentence
        else:
            if current_chunk.strip():
                children.append({
                    "text": current_chunk.strip(),
                    "parent_id": parent.parent_id,
                    "chunk_index": chunk_index,
                    "section_title": parent.title,
                    "filename": parent.filename
                })
                chunk_index += 1

            if len(sentence) > child_chunk_size:
                step = child_chunk_size - child_chunk_overlap
                for i in range(0, len(sentence), step):
                    sub = sentence[i:i + child_chunk_size]
                    if sub.strip():
                        children.append({
                            "text": sub.strip(),
                            "parent_id": parent.parent_id,
                            "chunk_index": chunk_index,
                            "section_title": parent.title,
                            "filename": parent.filename
                        })
                        chunk_index += 1
                current_chunk = ""
            else:
                if current_chunk and child_chunk_overlap > 0:
                    overlap_text = current_chunk[-child_chunk_overlap:]
                else:
                    overlap_text = ""
                current_chunk = overlap_text + sentence

    if current_chunk.strip():
        children.append({
            "text": current_chunk.strip(),
            "parent_id": parent.parent_id,
            "chunk_index": chunk_index,
            "section_title": parent.title,
            "filename": parent.filename
        })

    parent.child_chunk_ids = [f"{parent.parent_id}_{c['chunk_index']}" for c in children]

    return children
