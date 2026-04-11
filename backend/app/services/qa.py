"""
Question-answer logic: retrieve and call LLM
"""
from app.services.vector_store import search
from app.core.config import load_config
from openai import OpenAI
import requests
import re
import json
from typing import Tuple, List
try:
    from ollama import chat
    OLLAMA_SDK_AVAILABLE = True
except ImportError:
    OLLAMA_SDK_AVAILABLE = False


def regularize_output(text: str) -> str:
    """
    正则化处理LLM输出，提升可读性
    - 处理markdown标记（###、***等）
    - 优化文本结构
    - 保持学术严谨性
    - 确保信息完整
    """
    if not text:
        return text
    
    # 1. 处理markdown标题标记，保留标题结构
    # 将### 标题 转换为 <h3>标题</h3> 格式
    text = re.sub(r'^\s*###\s+(.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*##\s+(.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*#\s+(.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # 2. 处理强调标记，保留强调
    # 保留粗体和斜体
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    
    # 3. 处理多余的空行，保持适当的段落间距
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 4. 处理行首空格
    text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
    
    # 5. 优化列表格式
    lines = text.split('\n')
    optimized_lines = []
    in_list = False
    list_type = ''
    
    for line in lines:
        # 处理数字列表
        if re.match(r'^\s*\d+\s*[.,)]\s*', line):
            if not in_list or list_type != 'numbered':
                optimized_lines.append('<ol>')
                in_list = True
                list_type = 'numbered'
            item = re.sub(r'^\s*\d+\s*[.,)]\s*', '', line)
            optimized_lines.append(f'  <li>{item}</li>')
        # 处理项目符号列表
        elif re.match(r'^\s*[•●○▸▶►-\*]\s*', line):
            if not in_list or list_type != 'bulleted':
                optimized_lines.append('<ul>')
                in_list = True
                list_type = 'bulleted'
            item = re.sub(r'^\s*[•●○▸▶►-\*]\s*', '', line)
            optimized_lines.append(f'  <li>{item}</li>')
        else:
            if in_list:
                optimized_lines.append('</' + ('ol' if list_type == 'numbered' else 'ul') + '>')
                in_list = False
                list_type = ''
            optimized_lines.append(line)
    
    # 关闭未闭合的列表
    if in_list:
        optimized_lines.append('</' + ('ol' if list_type == 'numbered' else 'ul') + '>')
    
    text = '\n'.join(optimized_lines)
    
    # 6. 处理专业术语和论文标题
    # 处理期刊名称如TGRS
    text = re.sub(r'\b([A-Z]{2,})\b', r'<span class="font-bold">\1</span>', text)
    # 处理论文标题（驼峰命名）
    text = re.sub(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', r'<span class="font-italic">\1</span>', text)
    
    # 7. 再次处理多余空行，确保格式整洁
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 8. 确保段落间距，添加适当的段落标签
    # 将连续文本行包装在<p>标签中
    paragraphs = []
    current_paragraph = []
    
    for line in text.split('\n'):
        if line.strip() == '' or line.startswith('<h') or line.startswith('<ul') or line.startswith('<ol') or line.startswith('</'):
            if current_paragraph:
                paragraphs.append('<p>' + ' '.join(current_paragraph) + '</p>')
                current_paragraph = []
            paragraphs.append(line)
        else:
            current_paragraph.append(line)
    
    if current_paragraph:
        paragraphs.append('<p>' + ' '.join(current_paragraph) + '</p>')
    
    text = '\n'.join(paragraphs)
    
    # 9. 确保首尾没有多余空白
    text = text.strip()
    
    return text


def _get_openai_client(cfg):
    """获取OpenAI客户端实例"""
    key = cfg.get("openai_api_key")
    base_url = cfg.get("openai_base_url")
    
    client_kwargs = {}
    if key:
        client_kwargs["api_key"] = key
    if base_url:
        client_kwargs["base_url"] = base_url
    
    print(f"[DEBUG] OpenAI Client config: {client_kwargs}")
    return OpenAI(**client_kwargs)


def answer_question(question: str, provider: str = "openai", top_k: int = 5) -> Tuple[str, List[dict]]:
    cfg = load_config()
    docs = search(question, top_k=top_k, provider=provider)
    context = "\n\n".join([d.get("text", "") for d in docs])
    prompt = f"根据下面的上下文回答问题，并给出引用来源:\n\n{context}\n\n问题: {question}\n\n简要回答："
    if provider == "ollama":
        # simple HTTP call to Ollama generation endpoint (用户需自行配置 Ollama)
        try:
            endpoint = cfg.get("ollama_url").rstrip("/") + "/api/generate"
            r = requests.post(endpoint, json={"model": cfg.get("ollama_model"), "prompt": prompt}, timeout=60)
            r.raise_for_status()
            text = r.json().get("response", "")
        except Exception as e:
            print(f"[ERROR] Ollama call failed: {str(e)}")
            text = f"无法连接 Ollama 服务，请检查配置。错误: {str(e)}"
    else:
        try:
            client = _get_openai_client(cfg)
            print(f"[DEBUG] Calling OpenAI with model: {cfg.get('openai_chat_model', 'gpt-3.5-turbo')}")
            
            completion = client.chat.completions.create(
                model=cfg.get("openai_chat_model", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=cfg.get("temperature", 0.1),
            )
            
            # 安全地检查响应格式
            if (
                completion.choices 
                and len(completion.choices) > 0 
                and completion.choices[0].message 
                and completion.choices[0].message.content
            ):
                text = completion.choices[0].message.content.strip()
                # 正则化处理输出
                text = regularize_output(text)
            else:
                text = "API返回格式错误，请检查配置。"
        except Exception as e:
            print(f"[ERROR] OpenAI call failed: {str(e)}")
            import traceback
            traceback.print_exc()
            text = f"LLM 调用失败，请检查配置与网络。错误: {str(e)}"

    sources = [d.get("metadata", {}) for d in docs]
    return text, sources


def stream_answer(question: str, provider: str = "openai", top_k: int = 5, temperature: float = None, 
                  top_p: float = None, max_tokens: int = None, 
                  presence_penalty: float = None, frequency_penalty: float = None,
                  messages: List[dict] = None):
    """
    流式回答问题
    
    Args:
        question: 当前用户问题
        provider: LLM供应商
        top_k: 检索文档数量
        temperature: 温度参数
        top_p: top_p参数
        max_tokens: 最大令牌数
        presence_penalty: 存在惩罚
        frequency_penalty: 频率惩罚
        messages: 对话历史，格式为 [{"role": "user"|"assistant", "content": "..."}]
    """
    cfg = load_config()
    docs = search(question, top_k=top_k, provider=provider)
    context = "\n\n".join([d.get("text", "") for d in docs])
    
    # 构建包含对话历史的消息列表
    conversation_history = ""
    if messages and len(messages) > 0:
        conversation_history = "### 💬 对话历史：\n"
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                conversation_history += f"用户: {content}\n"
            elif role == "assistant":
                conversation_history += f"助手: {content}\n"
        conversation_history += "\n"
    
    prompt = f"""你是遥感图像融合领域的专业智能助手，服务于遥感图像处理研究团队。你的核心研究方向包括：
- 多源遥感图像融合（Multi-source Remote Sensing Image Fusion）
- 像素级、特征级、决策级融合算法
- 深度学习在遥感图像融合中的应用
- 图像质量评估与性能指标（如：PSNR、SSIM、SAM、ERGAS等）
- 遥感图像预处理、配准、融合后处理
- 相关的遥感应用（如：变化检测、目标识别、分类等）

{conversation_history}
### 📚 参考上下文（检索结果）：
{context}

### ❓ 当前用户问题：
{question}

---

### 🧠 第一步：意图识别与路由（最高优先级）
请首先判断用户问题的类型，并按以下优先级执行：

#### 🟢 优先级 1：自我认知类（Self-Identity）
- **触发条件**：询问助手的身份、模型名称、开发者、能力边界等（如"你是谁？"、"你基于什么模型？"、"你能做什么？"）。
- **执行策略**：
  1. **忽略**上述 `{context}` 中的业务内容。
  2. **诚实回答**你的真实身份："我是为遥感图像融合研究团队开发的专业智能助手，专注于多源遥感图像处理、融合算法及相关应用研究。"
  3. 语气专业、严谨、友好，无需引用上下文。

#### 🔵 优先级 2：基于上下文的问答（RAG Mode）
- **触发条件**：问题涉及遥感图像融合及相关技术，且预期答案在 `{context}` 中。
- **子模式判断**：
  - **A. 专业模式**（问题正式/技术/客观）：
    1. 严格基于 `{context}` 作答，同时参考对话历史了解上下文。
    2. 关键结论后必须标注 `[引用: 原文片段]`。
    3. 若上下文无相关信息，明确回复："根据提供的检索内容，暂时无法找到该问题的答案。"
    4. 禁止编造，禁止引入外部知识。
    5. 保持学术严谨性，使用专业术语准确。
  
  - **B. 闲聊模式**（问题随意/主观/带情绪）：
    1. 核心事实仍须源自 `{context}`，但语气自然亲切。
    2. 引用融入对话，如"资料里提到'...'，所以我觉得..."。
    3. 可补充通用常识（需标注 💡），可适当表达共情。
    4. 若上下文缺失关键信息，可结合常识推测但需声明"资料未提及，不过通常来说..."。

#### 🟠 优先级 3：遥感领域专业问题（Domain Expert Mode）
- **触发条件**：问题涉及遥感图像融合、图像处理、算法等专业问题，但 `{context}` 中无直接答案
- **执行策略**：
  1. 基于你的遥感领域专业知识给出准确、专业的回答
  2. 保持学术严谨性，专业术语准确
  3. 可适当提及相关经典算法或研究方向
  4. 如有不确定性问题，明确说明"根据我的专业知识范围"

#### 🟡 优先级 4：纯闲聊/通用知识（Out-of-Scope）
- **触发条件**：问题与遥感领域完全无关，且非自我认知类（如"今天天气如何？"、"讲个笑话"）。
- **执行策略**：
  1. 忽略 `{context}`。
  2. 利用你的内部知识库进行友好回答。
  3. 保持轻松愉快的语调。

---

### 🚫 全局安全约束
1. **真实性第一**：在优先级 2 中，绝不捏造上下文中不存在的事实。
2. **冲突处理**：若上下文存在矛盾，需指出"不同来源存在差异：[来源A说...] vs [来源B说...]"。
3. **隐私保护**：不泄露任何敏感个人信息。
4. **学术严谨**：对于遥感专业问题，保持专业、准确的回答。
5. **对话连续性**：根据对话历史，保持回答的连贯性和一致性。

### ✍️ 请根据上述路由逻辑，结合对话历史，生成最终回答：
"""
    
    # 使用传入的参数或配置中的默认值
    temp = temperature if temperature is not None else cfg.get("temperature", 0.7)
    tp = top_p if top_p is not None else cfg.get("top_p", 0.9)
    mt = max_tokens if max_tokens is not None else cfg.get("max_tokens", 2048)
    pp = presence_penalty if presence_penalty is not None else cfg.get("presence_penalty", 0.0)
    fp = frequency_penalty if frequency_penalty is not None else cfg.get("frequency_penalty", 0.0)
    
    # 调试日志
    print(f"[DEBUG] stream_answer using parameters:")
    print(f"[DEBUG]   temperature: {temp}")
    print(f"[DEBUG]   top_p: {tp}")
    print(f"[DEBUG]   max_tokens: {mt}")
    print(f"[DEBUG]   presence_penalty: {pp}")
    print(f"[DEBUG]   frequency_penalty: {fp}")
    
    # 流式输出处理函数
    def process_stream_chunk(chunk):
        """处理流式输出的单个chunk"""
        if not chunk:
            return chunk
        
        # 处理常见的markdown标记
        # 注意：由于是流式输出，我们只处理已经确定的标记
        chunk = re.sub(r'^\s*#{1,6}\s*', '', chunk, flags=re.MULTILINE)
        chunk = re.sub(r'\*\*\*+', '', chunk)
        chunk = re.sub(r'\*\*', '', chunk)
        chunk = re.sub(r'^\s+', '', chunk, flags=re.MULTILINE)
        
        return chunk
    
    if provider == "ollama":
        # Ollama流式响应 - 使用官方SDK或回退到HTTP请求
        try:
            if OLLAMA_SDK_AVAILABLE:
                # 使用ollama Python SDK
                print(f"[DEBUG] Using Ollama SDK with model: {cfg.get('ollama_model')}")
                stream = chat(
                    model=cfg.get('ollama_model'),
                    messages=[{'role': 'user', 'content': prompt}],
                    options={
                        "temperature": temp,
                        "top_p": tp,
                        "top_k": cfg.get("top_k", 5),
                        "num_predict": mt
                    },
                    stream=True,
                    think=False  # 启用thinking阶段输出（如果模型支持）
                )
                
                in_thinking = False
                for chunk in stream:
                    if hasattr(chunk, 'message'):
                        # 检查是否有thinking字段（Qwen3.5等模型）
                        if hasattr(chunk.message, 'thinking') and chunk.message.thinking and not in_thinking:
                            in_thinking = True
                            print('Thinking phase started')
                        
                        if hasattr(chunk.message, 'thinking') and chunk.message.thinking:
                            # 输出思考过程（可选，用于调试）
                            # print(chunk.message.thinking, end='')
                            pass
                        elif hasattr(chunk.message, 'content') and chunk.message.content:
                            if in_thinking:
                                in_thinking = False
                            # 输出最终答案
                            processed_chunk = process_stream_chunk(chunk.message.content)
                            yield processed_chunk
            else:
                # 回退到直接HTTP请求
                print(f"[DEBUG] Ollama SDK not available, falling back to HTTP request")
                endpoint = cfg.get("ollama_url").rstrip("/") + "/api/generate"
                ollama_options = {
                    "temperature": temp,
                    "top_p": tp,
                    "top_k": cfg.get("top_k", 5),
                    "num_predict": mt
                }
                
                r = requests.post(endpoint, json={
                    "model": cfg.get("ollama_model"), 
                    "prompt": prompt, 
                    "stream": True,
                    "options": ollama_options
                }, stream=True, timeout=60)
                r.raise_for_status()
                
                in_thinking = False
                for line in r.iter_lines():
                    if line:
                        try:
                            line_str = line.decode('utf-8')
                            data = json.loads(line_str)
                            
                            # 检查thinking字段（Qwen3.5等模型）
                            if "thinking" in data and data["thinking"] and not in_thinking:
                                in_thinking = True
                            
                            if "thinking" in data and data["thinking"]:
                                # 输出思考过程（可选，用于调试）
                                pass
                            elif "response" in data and data["response"]:
                                if in_thinking:
                                    in_thinking = False
                                processed_chunk = process_stream_chunk(data["response"])
                                yield processed_chunk
                            
                            if data.get("done", False):
                                break
                        except Exception as e:
                            print(f"[DEBUG] Failed to parse JSON: {e}")
                            pass
        except Exception as e:
            print(f"[ERROR] Ollama stream failed: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"无法连接 Ollama 服务，请检查配置。错误: {str(e)}"
    else:
        # OpenAI流式响应
        try:
            client = _get_openai_client(cfg)
            model_name = cfg.get("openai_chat_model", "gpt-3.5-turbo")
            print(f"[DEBUG] Calling OpenAI stream with:")
            print(f"[DEBUG]   model: {model_name}")
            print(f"[DEBUG]   max_tokens: {mt}")
            print(f"[DEBUG]   temperature: {temp}")
            print(f"[DEBUG]   top_p: {tp}")
            print(f"[DEBUG]   presence_penalty: {pp}")
            print(f"[DEBUG]   frequency_penalty: {fp}")
            
            stream = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=mt,
                temperature=temp,
                top_p=tp,
                presence_penalty=pp,
                frequency_penalty=fp,
                stream=True,
            )
            
            for chunk in stream:
                # 安全地检查choices数组和delta
                if (
                    chunk.choices 
                    and len(chunk.choices) > 0 
                    and chunk.choices[0].delta 
                    and chunk.choices[0].delta.content
                ):
                    content = chunk.choices[0].delta.content
                    processed_chunk = process_stream_chunk(content)
                    yield processed_chunk
        except Exception as e:
            print(f"[ERROR] OpenAI stream failed: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"LLM 调用失败，请检查配置与网络。错误: {str(e)}"
