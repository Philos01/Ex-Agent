
"""
统一的嵌入模型服务接口
支持本地部署和云端API两种模式
"""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    """嵌入模型提供者基类"""
    
    @abstractmethod
    def embed_texts(self, texts):
        """
        对文本列表进行嵌入
        
        Args:
            texts: 待嵌入的文本列表
            
        Returns:
            嵌入向量列表，每个向量是float列表
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self):
        """
        获取嵌入向量的维度
        
        Returns:
            嵌入向量的维度
        """
        pass


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """本地Sentence-Transformers嵌入模型提供者"""
    
    def __init__(self, model_name="BAAI/bge-small-zh-v1.5", cache_dir=None):
        """
        初始化本地嵌入模型
        
        Args:
            model_name: Hugging Face模型名称
            cache_dir: 模型缓存目录
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self._model = None
        self._embedding_dim = None
        self._load_model()
    
    def _load_model(self):
        """加载Sentence-Transformers模型"""
        try:
            from sentence_transformers import SentenceTransformer
            
            logger.info(f"正在加载本地嵌入模型: {self.model_name}")
            
            # 构建模型加载参数
            model_kwargs = {}
            if self.cache_dir:
                model_kwargs["cache_folder"] = self.cache_dir
            
            self._model = SentenceTransformer(self.model_name, **model_kwargs)
            
            # 获取嵌入维度
            test_emb = self._model.encode(["test"], show_progress_bar=False)
            self._embedding_dim = len(test_emb[0])
            
            logger.info(f"本地嵌入模型加载成功，维度: {self._embedding_dim}")
            
        except ImportError:
            logger.error("sentence-transformers 库未安装，请运行: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"加载本地嵌入模型失败: {e}")
            raise
    
    def embed_texts(self, texts):
        """对文本列表进行本地嵌入"""
        if not self._model:
            raise RuntimeError("本地模型未初始化")
        
        try:
            embeddings = self._model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"本地嵌入失败: {e}")
            raise
    
    def get_embedding_dimension(self):
        """获取本地嵌入向量维度"""
        if self._embedding_dim is None:
            raise RuntimeError("本地模型未初始化")
        return self._embedding_dim


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI API嵌入模型提供者"""
    
    def __init__(self, api_key, base_url=None, model="text-embedding-3-small"):
        """
        初始化OpenAI嵌入提供者
        
        Args:
            api_key: OpenAI API密钥
            base_url: API基础URL（用于兼容其他API）
            model: 嵌入模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._embedding_dim = None
        self._init_client()
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # 获取嵌入维度
            test_emb = self.embed_texts(["test"])
            self._embedding_dim = len(test_emb[0])
            
            logger.info(f"OpenAI嵌入模型初始化成功，模型: {self.model}, 维度: {self._embedding_dim}")
            
        except Exception as e:
            logger.error(f"初始化OpenAI嵌入模型失败: {e}")
            raise
    
    def embed_texts(self, texts):
        """调用OpenAI API进行嵌入"""
        try:
            response = self._client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [r.embedding for r in response.data]
        except Exception as e:
            logger.error(f"OpenAI嵌入API调用失败: {e}")
            raise
    
    def get_embedding_dimension(self):
        """获取OpenAI嵌入向量维度"""
        if self._embedding_dim is None:
            raise RuntimeError("OpenAI模型未初始化")
        return self._embedding_dim


class EmbeddingService:
    """统一的嵌入服务，支持本地和云端模式切换"""
    
    _instance = None
    _provider = None
    _mode = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, mode="local", config=None):
        """
        初始化嵌入服务
        
        Args:
            mode: 模式，'local' 或 'openai'
            config: 配置字典
        """
        if config is None:
            config = {}
        
        cls._mode = mode
        
        try:
            if mode == "local":
                # 本地模式
                model_name = config.get("local_embedding_model", "BAAI/bge-small-zh-v1.5")
                cache_dir = config.get("local_model_cache_dir")
                cls._provider = LocalEmbeddingProvider(model_name=model_name, cache_dir=cache_dir)
                logger.info("已切换到本地嵌入模式")
                print(f"推荐的本地嵌入模型: {model_name}")
            
            elif mode == "openai":
                # OpenAI模式
                api_key = config.get("openai_api_key")
                base_url = config.get("openai_base_url")
                model = config.get("openai_embedding_model", "text-embedding-3-small")
                
                if not api_key:
                    raise ValueError("OpenAI API密钥未配置")
                
                cls._provider = OpenAIEmbeddingProvider(
                    api_key=api_key,
                    base_url=base_url,
                    model=model
                )
                logger.info("已切换到OpenAI嵌入模式")
            
            else:
                raise ValueError(f"不支持的嵌入模式: {mode}")
        
        except Exception as e:
            logger.error(f"初始化嵌入服务失败: {e}")
            raise
    
    @classmethod
    def embed_texts(cls, texts):
        """
        对文本进行嵌入
        
        Args:
            texts: 待嵌入的文本列表
            
        Returns:
            嵌入向量列表
        """
        if cls._provider is None:
            raise RuntimeError("嵌入服务未初始化，请先调用 initialize()")
        
        return cls._provider.embed_texts(texts)
    
    @classmethod
    def get_embedding_dimension(cls):
        """获取当前嵌入模型的维度"""
        if cls._provider is None:
            raise RuntimeError("嵌入服务未初始化，请先调用 initialize()")
        
        return cls._provider.get_embedding_dimension()
    
    @classmethod
    def get_current_mode(cls):
        """获取当前使用的模式"""
        return cls._mode


# 推荐的本地嵌入模型列表
RECOMMENDED_LOCAL_MODELS = [
    {
        "name": "BAAI/bge-small-zh-v1.5",
        "description": "中文小型嵌入模型，适合普通硬件，语义理解能力良好",
        "dimension": 512,
        "language": "zh",
        "recommended": True
    },
    {
        "name": "BAAI/bge-base-zh-v1.5",
        "description": "中文基础嵌入模型，性能更好，需要更多内存",
        "dimension": 768,
        "language": "zh",
        "recommended": False
    },
    {
        "name": "shibing624/text2vec-base-chinese",
        "description": "轻量级中文文本嵌入模型",
        "dimension": 768,
        "language": "zh",
        "recommended": False
    },
    {
        "name": "all-MiniLM-L6-v2",
        "description": "通用小型多语言嵌入模型，速度快",
        "dimension": 384,
        "language": "multilingual",
        "recommended": False
    },
    {
        "name": "m3e-base",
        "description": "M3E中文嵌入模型，在多项任务上表现优秀",
        "dimension": 768,
        "language": "zh",
        "recommended": False
    }
]


def get_recommended_models():
    """获取推荐的本地嵌入模型列表"""
    return RECOMMENDED_LOCAL_MODELS
