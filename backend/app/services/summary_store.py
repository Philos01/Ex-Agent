"""
文档摘要存储服务
管理文档摘要的存储、检索和更新
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from app.core.config import load_config, ensure_data_dirs
from app.services.document_summary import DocumentSummary

logger = logging.getLogger(__name__)


class SummaryStore:
    """文档摘要存储管理器"""
    
    def __init__(self):
        self.cfg = load_config()
        ensure_data_dirs()
        from app.core.config import DATA_DIR
        self.summary_dir = DATA_DIR / "summaries"
        self.summary_dir.mkdir(exist_ok=True)
        self.index_file = self.summary_dir / "summary_index.json"
        self._load_index()
    
    def _load_index(self):
        """加载摘要索引"""
        self.index: Dict[str, str] = {}  # filename -> summary_file_path
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.error(f"加载摘要索引失败: {e}")
                self.index = {}
    
    def _save_index(self):
        """保存摘要索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存摘要索引失败: {e}")
    
    def _get_summary_file_path(self, filename: str) -> Path:
        """获取摘要文件路径"""
        import hashlib
        # 使用文件名的hash作为文件名，避免特殊字符问题
        filename_hash = hashlib.md5(filename.encode('utf-8')).hexdigest()
        return self.summary_dir / f"{filename_hash}.json"
    
    def save_summary(self, summary: DocumentSummary) -> bool:
        try:
            summary_file = self._get_summary_file_path(summary.filename)
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary.to_dict(), f, ensure_ascii=False, indent=2)
            
            relative_path = str(summary_file.relative_to(self.summary_dir))
            self.index[summary.filename] = relative_path
            self._save_index()
            
            logger.info(f"摘要保存成功: {summary.filename}")
            return True
        except Exception as e:
            logger.error(f"保存摘要失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_summary(self, filename: str) -> Optional[DocumentSummary]:
        try:
            if filename not in self.index:
                return None
            
            stored_path = self.index[filename]
            summary_file = Path(stored_path)
            if not summary_file.is_absolute():
                summary_file = self.summary_dir / summary_file
            if not summary_file.exists():
                return None
            
            with open(summary_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return DocumentSummary.from_dict(data)
        except Exception as e:
            logger.error(f"获取摘要失败: {e}")
            return None
    
    def delete_summary(self, filename: str) -> bool:
        try:
            if filename not in self.index:
                return True
            
            stored_path = self.index[filename]
            summary_file = Path(stored_path)
            if not summary_file.is_absolute():
                summary_file = self.summary_dir / summary_file
            if summary_file.exists():
                summary_file.unlink()
            
            del self.index[filename]
            self._save_index()
            
            logger.info(f"摘要删除成功: {filename}")
            return True
        except Exception as e:
            logger.error(f"删除摘要失败: {e}")
            return False
    
    def list_summaries(self) -> List[str]:
        """
        列出所有有摘要的文件
        
        Returns:
            文件名列表
        """
        return list(self.index.keys())
    
    def get_all_summaries(self) -> List[DocumentSummary]:
        """
        获取所有文档摘要
        
        Returns:
            DocumentSummary对象列表
        """
        summaries = []
        for filename in self.index.keys():
            summary = self.get_summary(filename)
            if summary:
                summaries.append(summary)
        return summaries
    
    def update_summary(self, filename: str, summary: DocumentSummary) -> bool:
        """
        更新文档摘要
        
        Args:
            filename: 原文件名
            summary: 新的DocumentSummary对象
            
        Returns:
            是否更新成功
        """
        # 如果文件名改变了，先删除旧的
        if filename != summary.filename and filename in self.index:
            self.delete_summary(filename)
        
        return self.save_summary(summary)


# 全局摘要存储实例
_summary_store = None


def get_summary_store() -> SummaryStore:
    """
    获取或创建全局摘要存储实例
    
    Returns:
        SummaryStore 实例
    """
    global _summary_store
    if _summary_store is None:
        _summary_store = SummaryStore()
    return _summary_store


def save_document_summary(summary: DocumentSummary) -> bool:
    """
    便捷函数：保存文档摘要
    
    Args:
        summary: DocumentSummary对象
        
    Returns:
        是否保存成功
    """
    store = get_summary_store()
    return store.save_summary(summary)


def get_document_summary(filename: str) -> Optional[DocumentSummary]:
    """
    便捷函数：获取文档摘要
    
    Args:
        filename: 文件名
        
    Returns:
        DocumentSummary对象，如果不存在则返回None
    """
    store = get_summary_store()
    return store.get_summary(filename)


def delete_document_summary(filename: str) -> bool:
    """
    便捷函数：删除文档摘要
    
    Args:
        filename: 文件名
        
    Returns:
        是否删除成功
    """
    store = get_summary_store()
    return store.delete_summary(filename)
