"""
Question-answer logic: retrieve and call LLM
"""
import logging
from datetime import datetime
from app.services.vector_store import search
from app.services.hybrid_search import hybrid_search
from app.core.config import load_config
from app.skills.skill_manager import get_skill_manager
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

logger = logging.getLogger(__name__)


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


def answer_question(question: str, provider: str = "openai", top_k: int = 5, session_id: str = "default") -> Tuple[str, List[dict]]:
    cfg = load_config()
    
    # 获取当前时间（北京时间）
    from zoneinfo import ZoneInfo
    beijing_tz = ZoneInfo('Asia/Shanghai')
    current_datetime = datetime.now(beijing_tz)
    current_date_str = current_datetime.strftime('%Y年%m月%d日')
    current_year = current_datetime.year
    
    # 选择检索方式
    docs = _retrieve_documents(question, provider, top_k)
    
    # 获取过滤后的历史上下文
    history_messages = _get_filtered_history(session_id)
    
    # 构建包含对话历史的消息列表
    conversation_history = ""
    if history_messages and len(history_messages) > 0:
        conversation_history = "### 💬 对话历史：\n"
        for msg in history_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                conversation_history += f"用户: {content}\n"
            elif role == "assistant":
                conversation_history += f"助手: {content}\n"
        conversation_history += "\n"
    
    context = "\n\n".join([d.get("text", "") for d in docs])
    prompt = f"""
    # Role: 宁波大学 RS-NBU 课题组专属学术助理

    ## 👤 Profile
    你是专门为**宁波大学 RS-NBU（Remote Sensing - Ningbo University）课题组**深度定制的 AI 学术助理。你熟知遥感图像处理领域的前沿知识，并且你的知识库中包含了该课题组所有的内部文献、实验数据、代码库、会议记录和项目申请书。

    ## ⏰ 重要时间信息
    - **当前日期**：{current_date_str}
    - **当前年份**：{current_year}年
    请注意：这是真实的当前时间，你需要基于这个时间信息回答用户关于时间、年份的问题。

    ---

    ## 📥 输入数据区
    <conversation_history>
    {conversation_history}
    </conversation_history>

    <retrieved_context>
    {context}
    </retrieved_context>

    <user_question>
    {question}
    </user_question>

    ---

    ## 🚫 约束
    1. **使用正确的时间**：必须基于上面提供的当前时间信息（{current_date_str}，{current_year}年）回答问题，不要使用你训练数据中的截止日期。

    ## 请根据上下文回答问题，并给出引用来源：
    """
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
                # # 正则化处理输出
                # text = regularize_output(text)
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
                  messages: List[dict] = None, include_state: bool = False):
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
        include_state: 是否包含思考状态事件输出
    """
    cfg = load_config()
    
    # 检查是否需要使用技能
    skill_manager = get_skill_manager()
    use_skill, skill_name, skill_params = skill_manager.should_use_skill(question)
    
    print(f"[QA DEBUG] Question: {question}")
    print(f"[QA DEBUG] Use skill: {use_skill}")
    print(f"[QA DEBUG] Skill name: {skill_name}")
    print(f"[QA DEBUG] Skill params: {skill_params}")
    
    skill_result_text = ""
    docs = []
    sources = []
    
    if use_skill and skill_name and skill_params:
        # 使用技能，不进行 RAG 检索
        print(f"[QA DEBUG] Using skill mode - skipping RAG retrieval")
        if include_state:
            yield {"type": "state", "phase": "skill_call", "message": f"正在调用 {skill_name} 技能...", "progress": 10}
        
        skill_result = skill_manager.execute_skill(skill_name, **skill_params)
        skill_result_text = skill_manager.format_skill_result(skill_result)
        
        # 发送技能结果事件，供前端保存到对话历史
        yield {"type": "skill_result", "skill_name": skill_name, "result": skill_result_text}
        
        if include_state:
            yield {"type": "state", "phase": "skill_call", "message": f"{skill_name} 技能执行完成", "progress": 40}
        
        context = f"## 技能执行结果\n{skill_result_text}"
        print(f"[QA DEBUG] Context (skill mode): {context[:200]}...")
    else:
        # 不使用技能，进行正常的 RAG 检索
        print(f"[QA DEBUG] Using RAG mode")
        summary_config = cfg.get("summary_search", {})
        use_two_layer = summary_config.get("enabled", False)
        hybrid_config = cfg.get("hybrid_search", {})
        use_hybrid = hybrid_config.get("enabled", True)
        
        if include_state:
            if use_two_layer:
                yield {"type": "state", "phase": "retrieving", "message": "正在使用双层检索系统（先检索摘要）...", "progress": 0}
            elif use_hybrid:
                yield {"type": "state", "phase": "retrieving", "message": "正在使用混合检索系统查找相关文档...", "progress": 0}
            else:
                yield {"type": "state", "phase": "retrieving", "message": "正在连接 Chroma 向量库...", "progress": 0}
        
        docs = _retrieve_documents(question, provider, top_k)
        
        if include_state:
            yield {"type": "state", "phase": "retrieving", "message": f"检索到 {len(docs)} 篇高度相关的文献", "progress": 25}
        
        context = "\n\n".join([d.get("text", "") for d in docs])
        print(f"[QA DEBUG] Context (RAG mode): {context[:200]}...")
    
    # 构建包含对话历史的消息列表
    conversation_history = ""
    if messages and len(messages) > 0:
        conversation_history = "### 💬 对话历史：\n"
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # 检查是否包含技能结果标记
            skill_result_tag = msg.get("skill_result", None)
            skill_name_tag = msg.get("skill_name", None)
            
            if role == "user":
                conversation_history += f"用户: {content}\n"
            elif role == "assistant":
                conversation_history += f"助手: {content}\n"
            
            # 如果有技能结果，添加到对话历史
            if skill_result_tag:
                if skill_name_tag:
                    conversation_history += f"[技能结果 - {skill_name_tag}] {skill_result_tag}\n"
                else:
                    conversation_history += f"[技能结果] {skill_result_tag}\n"
        conversation_history += "\n"
    
    # 如果当前轮次使用了技能，将技能结果添加到上下文
    current_skill_context = ""
    if use_skill and skill_result_text:
        current_skill_context = f"## 当前技能执行结果\n{skill_result_text}\n"
    
    # 获取当前时间（北京时间）
    from zoneinfo import ZoneInfo
    beijing_tz = ZoneInfo('Asia/Shanghai')
    current_datetime = datetime.now(beijing_tz)
    current_date_str = current_datetime.strftime('%Y年%m月%d日')
    current_year = current_datetime.year
    
    # 根据是否使用技能，调整 prompt
    if use_skill and skill_name:
        # 使用技能模式的 prompt
        prompt = f"""
# Role: 宁波大学 RS-NBU 课题组专属学术助理 (RS-NBU Academic AI Assistant)

## 👤 Profile
你是专门为**宁波大学 RS-NBU（Remote Sensing - Ningbo University）课题组**深度定制的 AI 学术助理。
你的核心职责是：基于技能执行的结果解答用户的问题。

## ⏰ 重要时间信息
- **当前日期**：{current_date_str}
- **当前年份**：{current_year}年
请注意：这是真实的当前时间，你需要基于这个时间信息回答用户关于时间、年份的问题。

---

## 📥 输入数据区
<conversation_history>
{conversation_history}
</conversation_history>

<current_skill_result>
{current_skill_context}
</current_skill_result>

<user_question>
{question}
</user_question>

---

## 🧠 核心工作流 (Skill Mode)
你现在处于**技能执行模式**：

### 🔴 优先级 1：自我认知类 (Identity & Meta-questions)
- **触发条件**：询问你的身份、创造者、能力范围或组内定位。
- **执行动作**：
  1. 忽略 `<current_skill_result>`。
  2. 骄傲且专业地回答："我是宁波大学 RS-NBU 课题组的专属 AI 学术助理。"

### 🟡 优先级 2：基于技能结果的问答 (Skill Result Mode)
- **触发条件**：`<current_skill_result>` 中有技能执行的结果，或者对话历史中有 `[技能结果]` 标记。
- **执行动作**：
  1. **基于技能结果回答**：严格基于 `<current_skill_result>` 和对话历史中的技能结果回答用户问题，不要编造。
  2. **不要提及组内资料**：这是技能模式，不要去查找或提及组内资料。
  3. **提供完整信息**：如果技能返回了论文信息，请提供论文标题、摘要、链接等。
  4. **不要去检索组内资料**：只使用技能返回的结果。
  5. **参考对话历史**：如果之前的对话中有相关的技能结果，也要参考。

---

## 🚫 约束
1. **不要编造**：如果技能结果中没有信息，请如实告知。
2. **不要提及组内资料**：这是技能模式，专注于技能返回的结果。
3. **上下文连贯**：作答前必须参考 `<conversation_history>`。
4. **使用正确的时间**：必须基于上面提供的当前时间信息（{current_date_str}，{current_year}年）回答问题，不要使用你训练数据中的截止日期。

### ✍️ 最终执行指令：
请仔细阅读技能结果，现在开始生成你的回答。
"""
    else:
        # 正常 RAG 模式的 prompt
        prompt = f"""
# Role: 宁波大学 RS-NBU 课题组专属学术助理 (RS-NBU Academic AI Assistant)

## 👤 Profile
你是专门为**宁波大学 RS-NBU（Remote Sensing - Ningbo University）课题组**深度定制的 AI 学术助理。你熟知遥感图像处理领域的前沿知识，并且你的知识库中包含了该课题组所有的内部文献、实验数据、代码库、会议记录和项目申请书。
你的核心职责是：作为组内师生的科研"超级大脑"，基于课题组的内部资料和外部搜索结果解答疑问、提供算法实现思路、梳理研究脉络，并辅助日常科研工作。

## ⏰ 重要时间信息
- **当前日期**：{current_date_str}
- **当前年份**：{current_year}年
请注意：这是真实的当前时间，你需要基于这个时间信息回答用户关于时间、年份的问题。

## 🎯 Core Research Areas
- 多源遥感图像融合（Pansharpening, 时空融合, 多光谱与高光谱融合等）
- 像素级、特征级、决策级融合算法（含传统算法与深度学习/大模型方法）
- 图像质量评估（PSNR, SSIM, SAM, ERGAS, Q8, SCC 等指标）
- 遥感下游应用（变化检测、目标检测、地物分类、语义分割等）
- 课题组内部传承的预处理流、配准方法与私有数据集规范

---

## 📥 输入数据区
<conversation_history>
{conversation_history}
</conversation_history>

<retrieved_context>
{context}
</retrieved_context>

<user_question>
{question}
</user_question>

---

## 🧠 核心工作流与路由逻辑 (Workflow & Routing)
请严格按照以下优先级（从 1 到 5）分析 `&lt;user_question&gt;`，并执行对应的响应策略：

### 🔴 优先级 1：自我认知类 (Identity &amp; Meta-questions)
- **触发条件**：询问你的身份、创造者、能力范围或组内定位（如"你是谁？"、"你能干嘛？"）。
- **执行动作**：
  1. 忽略 `&lt;retrieved_context&gt;`。
  2. 骄傲且专业地回答："我是宁波大学 RS-NBU 课题组的专属 AI 学术助理。我的大脑中汇集了课题组的论文、代码、会议记录等宝贵资料。我在这里帮助组内师生解决多源遥感图像融合、深度学习算法开发及各项科研问题。我还可以帮你搜索最新的 ArXiv 学术论文！"

### 🟡 优先级 2：基于外部搜索结果的问答 (External Search Mode)
- **触发条件**：`&lt;retrieved_context&gt;` 中包含"## 外部搜索结果"，且用户问题与搜索内容相关。
- **执行动作**：
  1. **优先使用外部搜索结果**：如果用户询问最新研究、论文、学术动态等，首先使用外部搜索到的 ArXiv 论文信息进行回答。
  2. **论文摘要总结**：对搜索到的每篇论文进行简要总结，突出核心贡献、方法和结论。
  3. **提供链接**：务必提供每篇论文的 PDF 链接和详情链接。
  4. **结合内部知识**：如果内部知识库中有相关内容，可以结合起来回答。

### 🟢 优先级 3：基于组内知识库的问答 (Internal RAG Mode) - 【核心功能】
- **触发条件**：问题涉及具体的算法细节、论文出处、历年实验数据、组内规范等，且 `<retrieved_context>` 中包含相关信息。
- **执行动作**：
  1. **绝对忠诚**：严格基于 `<retrieved_context>` 提供的信息作答，禁止凭空捏造组内未做过的研究。
  2. **溯源引用**：在每个关键结论或数据后，必须以学术规范标注来源。格式示例：`[引用: 2023_张三_TGRS论文.pdf]` 或 `[引用: 20240312_组会记录]`。
  3. **结构化输出**：如果是询问算法对比或实验步骤，请用 Markdown 表格或有序列表呈现。
  4. **信息不足处理**：如果检索到的组内资料不全，请明确告知："根据检索到的课题组内部资料，仅包含以下信息..."，然后无缝切换至【优先级 4】补充通用学术知识。

### 🔵 优先级 4：遥感领域专业探讨 (Domain Expert Mode)
- **触发条件**：用户询问宽泛的学术概念、前沿趋势、代码 Bug 排查，且 `<retrieved_context>` 中无直接答案。
- **执行动作**：
  1. 动用你作为遥感领域专家的内部知识进行解答。
  2. 语气须保持**学术严谨**，涉及公式请使用 LaTeX 格式（如 $E=mc^2$ 或 `$$公式$$`），涉及代码请使用标准 Markdown 代码块并注明语言（如 Python, PyTorch, MATLAB）。
  3. 必须在回答开头或结尾声明边界："*注：检索库中未找到组内直接相关的材料，以下基于遥感领域通用知识为您解答：*"

### ⚪ 优先级 5：日常闲聊与通用辅助 (General Assistance)
- **触发条件**：与遥感科研无关的闲聊、通用文本处理（如润色英文摘要、写邮件等）。
- **执行动作**：
  1. 提供高质量的润色、翻译或礼貌的日常回复。
  2. 保持热情、专业的学长/学姐口吻，随时准备将话题引导回科研工作。

---

## 🚫 全局安全与格式约束 (Strict Constraints)
1. **防幻觉（Zero Hallucination）**：绝不编造课题组未发表的论文、未取得的指标（如捏造某算法在某数据集上达到了 0.99 的 SSIM）。不知道就回答"资料未记载"。
2. **知识隔离**：如果用户的提问同时涉及内部资料和外部常识，请明确区分"课题组资料显示..."与"学术界通常认为..."与"ArXiv 最新论文显示..."。
3. **Markdown 优先**：复杂的数学公式必须严格使用 LaTeX 语法；代码必须有完整的注释；对比内容优先使用表格。
4. **上下文连贯**：作答前必须参考 `<conversation_history>`，避免重复回答或语境断裂。
5. **使用正确的时间**：必须基于上面提供的当前时间信息（{current_date_str}，{current_year}年）回答问题，不要使用你训练数据中的截止日期。

### ✍️ 最终执行指令：
请深呼吸，作为 RS-NBU 的一员，仔细阅读上述数据和规则，现在开始生成你的回答。
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
        """处理流式输出的单个chunk - 保留markdown格式"""
        if not chunk:
            return chunk
        
        # 保留GPT输出的markdown格式，不在后端进行处理
        # 让前端使用专门的markdown渲染库进行展示
        return chunk

    # 发送分析阶段状态 - 仅在RAG模式
    if include_state and not use_skill:
        yield {"type": "state", "phase": "analyzing", "message": "正在分析检索结果...", "progress": 50}
    
    # 发送生成阶段状态
    if include_state:
        if use_skill:
            # 技能模式的生成状态
            yield {"type": "state", "phase": "generating", "message": f"正在基于 {skill_name} 结果生成回答...", "progress": 75}
        else:
            # RAG模式的生成状态
            yield {"type": "state", "phase": "generating", "message": f"正在使用 {provider} 模型生成回答...", "progress": 75}

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
            # Ollama 流式结束，发送 done 状态
            if include_state:
                yield {"type": "state", "phase": "done", "message": "生成完毕", "progress": 100}
        except Exception as e:
            print(f"[ERROR] Ollama stream failed: {str(e)}")
            import traceback
            traceback.print_exc()
            if include_state:
                yield {"type": "state", "phase": "done", "message": "生成出错", "progress": 100}
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
            # OpenAI 流式结束，发送 done 状态
            if include_state:
                yield {"type": "state", "phase": "done", "message": "生成完毕", "progress": 100}
        except Exception as e:
            print(f"[ERROR] OpenAI stream failed: {str(e)}")
            import traceback
            traceback.print_exc()
            if include_state:
                yield {"type": "state", "phase": "done", "message": "生成出错", "progress": 100}
            yield f"LLM 调用失败，请检查配置与网络。错误: {str(e)}"


def _retrieve_documents(question: str, provider: str = "openai", top_k: int = 5):
    """
    检索文档，根据配置选择适当的检索方式
    
    Args:
        question: 用户问题
        provider: LLM提供商
        top_k: 检索数量
        
    Returns:
        检索到的文档列表
    """
    cfg = load_config()
    
    # 检查是否启用双层检索
    summary_config = cfg.get("summary_search", {})
    use_two_layer = summary_config.get("enabled", False)
    
    if use_two_layer:
        try:
            from app.services.two_layer_search import two_layer_search
            logger.info("使用双层检索")
            return two_layer_search(question, provider=provider)
        except Exception as e:
            logger.error(f"双层检索失败，回退到混合检索: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # 检查是否启用混合检索
    hybrid_config = cfg.get("hybrid_search", {})
    use_hybrid = hybrid_config.get("enabled", True)
    
    if use_hybrid:
        try:
            from app.services.hybrid_search import hybrid_search
            logger.info("使用混合检索")
            return hybrid_search(question, provider=provider)
        except Exception as e:
            logger.error(f"混合检索失败，回退到向量检索: {e}")
    
    # 默认使用向量检索
    logger.info("使用向量检索")
    return search(question, top_k=top_k, provider=provider)


def _get_filtered_history(session_id: str = "default") -> List[dict]:
    """
    获取过滤后的历史对话
    
    Args:
        session_id: 会话ID
        
    Returns:
        过滤后的历史消息列表
    """
    cfg = load_config()
    context_config = cfg.get("context_management", {})
    
    if not context_config.get("enabled", True):
        return []
    
    try:
        from app.services.context_manager import get_context_manager
        
        max_history = context_config.get("max_history_rounds", 5)
        exclude_errors = context_config.get("exclude_error_messages", True)
        exclude_questionable = context_config.get("exclude_questionable_messages", False)
        
        context_mgr = get_context_manager(session_id, max_history=max_history)
        filtered_history = context_mgr.get_filtered_history(
            exclude_errors=exclude_errors,
            exclude_questionable=exclude_questionable
        )
        
        logger.debug(f"获取到 {len(filtered_history)} 条过滤后的历史消息")
        return filtered_history
        
    except Exception as e:
        logger.error(f"获取过滤历史失败: {e}")
        import traceback
        traceback.print_exc()
        return []


def _add_to_history(
    role: str, 
    content: str, 
    session_id: str = "default"
):
    """
    添加消息到历史记录
    
    Args:
        role: 角色（"user" 或 "assistant"）
        content: 消息内容
        session_id: 会话ID
    """
    cfg = load_config()
    context_config = cfg.get("context_management", {})
    
    if not context_config.get("enabled", True):
        return
    
    try:
        from app.services.context_manager import get_context_manager
        
        max_history = context_config.get("max_history_rounds", 5)
        context_mgr = get_context_manager(session_id, max_history=max_history)
        context_mgr.add_message(role, content)
        
        logger.debug(f"已添加 {role} 消息到历史")
    except Exception as e:
        logger.error(f"添加到历史失败: {e}")
        import traceback
        traceback.print_exc()
