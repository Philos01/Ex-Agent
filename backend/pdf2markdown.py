import os
import sys
import json
import torch
from typing import Dict

# 使用已安装的 marker 库的当前 API
from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.output import save_output

def test_pdf_to_markdown(pdf_path: str, output_dir: str = None):
    """
    将指定的 PDF 文件转换为 Markdown 并保存。
    
    Args:
        pdf_path (str): 输入 PDF 文件的路径。
        output_dir (str): 输出 Markdown 文件的目录。如果为None，则使用PDF所在目录的output子目录。
    """
    # 如果没有指定输出目录，使用PDF所在目录的output子目录
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(pdf_path), "output")
    
    # 1. 检查文件是否存在
    if not os.path.exists(pdf_path):
        print(f"错误: 文件不存在 - {pdf_path}")
        return

    # 2. 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    print("正在加载模型... (首次运行可能需要下载模型，请耐心等待)")
    try:
        # 自动检测可用设备
        print(f"PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA设备数: {torch.cuda.device_count()}")
            print(f"当前CUDA设备: {torch.cuda.current_device()}")
            print(f"CUDA设备名称: {torch.cuda.get_device_name(0)}")
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"  # Apple Silicon Mac
        else:
            device = "cpu"
            
        print(f"当前使用设备: {device.upper()}")
        
        # 将 device 传入模型字典（新版 marker 支持）
        models = create_model_dict(device=device)
    except Exception as e:
        print(f"模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"开始转换 PDF: {pdf_path} ...")

    try:
        # 在配置中明确指定设备
        cli_opts = {
            "output_dir": output_dir,
            "output_format": "markdown",
            "device": device,          # ✅ 核心：启用 GPU
            "langs": ["zh", "en"],     # ✅ 建议：指定中英混合
            "batch_multiplier": 1,     # ⚠️ 显存不足时保持为1，充足可改为2或3
            "disable_image_extraction": True,
            "use_llm": False,
            "load_in_4bit": True,
            "bnb_4bit_compute_dtype": torch.float16  
        }
        
        config_parser = ConfigParser(cli_opts)

        converter_cls = config_parser.get_converter_cls()
        converter = converter_cls(
            config=config_parser.generate_config_dict(),
            artifact_dict=models,
            processor_list=config_parser.get_processors(),
            renderer=config_parser.get_renderer(),
            llm_service=config_parser.get_llm_service(),
        )

        rendered = converter(pdf_path)

        # out_folder = config_parser.get_output_folder(pdf_path)
        base_fname = config_parser.get_base_filename(pdf_path)

        # 保存输出（marker 提供的 save_output 会处理 markdown/html/json）
        save_output(rendered, output_dir, base_fname)

        output_path = os.path.join(output_dir, f"{base_fname}.md")
        print(f"Output path: {output_path}")
        print("-" * 30)
        print("转换成功!")
        print(f"Markdown 文件已保存至: {output_path}")
        print("-" * 30)

        # 可选：打印前 500 个字符预览（如果 rendered 可转换为文本）
        try:
            # 尝试使用 marker.output.text_from_rendered 获取文本
            from marker.output import text_from_rendered

            full_text, _, _ = text_from_rendered(rendered)
            print("\n--- 内容预览 (前500字符) ---")
            print(full_text[:500])
            print("...\n")
        except Exception:
            pass

    except Exception as e:
        print(f"转换过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # === 配置区域 ===
    # 请替换为你实际的 PDF 文件路径
    TARGET_PDF = r"C:\\Users\\24117\Desktop\\troublesome\Agent\\实验室Agent\\2311100200_钟鑫涛_085402通信工程（含宽带网络、移动通信等）（简洁）.pdf" 
    OUTPUT_DIR = None
    
    # 如果没有提供参数，尝试查找当前目录下的 pdf 文件用于测试
    if len(sys.argv) > 1:
        TARGET_PDF = sys.argv[1]
    if len(sys.argv) > 2:
        OUTPUT_DIR = sys.argv[2]
    else:
        # 为了演示，如果找不到文件，创建一个提示
        if not os.path.exists(TARGET_PDF):
            print(f"未找到 '{TARGET_PDF}'。")
            print("请将一个 PDF 文件放在当前目录下并命名为 'test_document.pdf'，")
            print("或者运行命令: python test_pdf_to_md.py your_file.pdf [output_dir]")
            sys.exit(1)

    # 执行转换
    test_pdf_to_markdown(TARGET_PDF, OUTPUT_DIR)