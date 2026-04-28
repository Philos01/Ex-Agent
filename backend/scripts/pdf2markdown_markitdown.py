import os
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import get_complete_config

logger = logging.getLogger(__name__)


def pdf_to_markdown_markitdown(pdf_path: str, output_dir: str = None) -> str:
    """
    使用 MarkItDown 将 PDF 文件转换为 Markdown 格式

    Args:
        pdf_path: PDF 文件路径
        output_dir: 输出目录，如果为 None 则使用 PDF 文件所在目录

    Returns:
        转换后的 Markdown 文件路径

    Raises:
        Exception: 转换失败时抛出异常
    """
    if output_dir is None:
        output_dir = os.path.dirname(pdf_path)

    os.makedirs(output_dir, exist_ok=True)

    cfg = get_complete_config()
    timeout = (
        cfg.get("timeouts", {}).get("pdf_conversion", 300)
        if cfg.get("timeouts", {}).get("enabled", True) else None
    )

    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.md")

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    try:
        from markitdown import MarkItDown

        logger.info(f"[DEBUG] 使用 MarkItDown 转换 PDF 文件: {pdf_path}")

        md = MarkItDown()
        result = md.convert(pdf_path)
        markdown_text = result.text_content

        if not markdown_text or not markdown_text.strip():
            raise Exception("MarkItDown 转换结果为空")

        with open(output_path, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_text)

        logger.info(f"[DEBUG] MarkItDown PDF 转换成功: {output_path}")
        return output_path

    except ImportError:
        logger.error("[DEBUG] MarkItDown 库未安装")
        raise Exception(
            "MarkItDown 库未安装，请运行: pip install 'markitdown[pdf]'"
        )
    except Exception as e:
        logger.error(f"[DEBUG] MarkItDown PDF 转换失败: {e}")
        import traceback
        traceback.print_exc()
        raise


def pdf_to_markdown_simple(pdf_path: str) -> str:
    """
    简单的 PDF 转 Markdown 转换，直接返回 Markdown 文本，不保存文件

    Args:
        pdf_path: PDF 文件路径

    Returns:
        Markdown 格式的字符串
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")

    try:
        from markitdown import MarkItDown
        md = MarkItDown()
        result = md.convert(pdf_path)
        return result.text_content
    except Exception as e:
        logger.error(f"[ERROR] PDF 转 Markdown 失败: {e}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python pdf2markdown_markitdown.py <pdf文件路径> [输出目录]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        output_path = pdf_to_markdown_markitdown(pdf_path, output_dir)
        print(f"转换成功: {output_path}")
    except Exception as e:
        print(f"转换失败: {e}")
        sys.exit(1)
