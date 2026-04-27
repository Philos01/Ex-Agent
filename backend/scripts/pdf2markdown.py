import os
import sys
import gc
import torch
import tempfile
import warnings
from pathlib import Path

os.environ["INFERENCE_RAM"] = "3"
os.environ["VRAM_PER_TASK"] = "2"
os.environ["OMP_NUM_THREADS"] = "1"

from marker.models import create_model_dict
from marker.config.parser import ConfigParser
from marker.output import save_output

try:
    import bitsandbytes
except ImportError:
    print("警告: 未检测到 bitsandbytes 库，4bit量化将失效，会导致巨大的显存占用！")
    print("请安装: pip install bitsandbytes")


RECOGNITION_SUB_BATCH_SIZE = 8


def clear_cuda_memory():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    gc.collect()


def patch_ocr_builder():
    from marker.builders.ocr import OcrBuilder
    from surya.recognition import OCRResult
    from ftfy import fix_text
    from marker.schema import BlockTypes
    from marker.schema.text.line import Line

    original_ocr_extraction = OcrBuilder.ocr_extraction

    def patched_ocr_extraction(
        self, document, pages, images, block_polygons, block_ids, block_original_texts
    ):
        if sum(len(b) for b in block_polygons) == 0:
            return

        self.recognition_model.disable_tqdm = self.disable_tqdm
        recognition_batch_size = min(int(self.get_recognition_batch_size()), RECOGNITION_SUB_BATCH_SIZE)

        all_recognition_results = []

        for page_idx in range(len(images)):
            page_image = images[page_idx]
            page_polygons = block_polygons[page_idx]
            page_block_ids_list = block_ids[page_idx]
            page_original_texts = block_original_texts[page_idx]
            total_blocks = len(page_polygons)

            if total_blocks == 0:
                all_recognition_results.append(OCRResult(text_lines=[], image_bbox=[0, 0, 0, 0]))
                continue

            page_text_lines = []
            page_image_bbox = None
            for batch_start in range(0, total_blocks, RECOGNITION_SUB_BATCH_SIZE):
                batch_end = min(batch_start + RECOGNITION_SUB_BATCH_SIZE, total_blocks)
                batch_polys = [page_polygons[batch_start:batch_end]]
                batch_texts = [page_original_texts[batch_start:batch_end]]

                print(f"    文本识别子批次 {batch_start + 1}-{batch_end}/{total_blocks}")

                batch_results = self.recognition_model(
                    images=[page_image],
                    task_names=[self.ocr_task_name],
                    polygons=batch_polys,
                    input_text=batch_texts,
                    recognition_batch_size=recognition_batch_size,
                    sort_lines=False,
                    math_mode=not self.disable_ocr_math,
                    drop_repeated_text=self.drop_repeated_text,
                    max_sliding_window=2148,
                    max_tokens=2048,
                )

                page_text_lines.extend(batch_results[0].text_lines)
                if page_image_bbox is None and hasattr(batch_results[0], 'image_bbox'):
                    page_image_bbox = batch_results[0].image_bbox
                clear_cuda_memory()

            combined_result = OCRResult(text_lines=page_text_lines, image_bbox=page_image_bbox or [0, 0, 0, 0])
            all_recognition_results.append(combined_result)

        assert len(all_recognition_results) == len(images) == len(pages) == len(block_ids), (
            f"Mismatch in OCR lengths: {len(all_recognition_results)}, {len(images)}, {len(pages)}, {len(block_ids)}"
        )

        for document_page, page_recognition_result, page_block_ids, image in zip(
            pages, all_recognition_results, block_ids, images
        ):
            for block_id, block_ocr_result in zip(
                page_block_ids, page_recognition_result.text_lines
            ):
                if block_ocr_result.original_text_good:
                    continue
                if not fix_text(block_ocr_result.text):
                    continue

                block = document_page.get_block(block_id)
                all_line_spans = self.spans_from_html_chars(
                    block_ocr_result.chars, document_page, image
                )
                if block.block_type == BlockTypes.Line:
                    flat_spans = [s for line_spans in all_line_spans for s in line_spans]
                    self.replace_line_spans(document, document_page, block, flat_spans)
                else:
                    for line in block.contained_blocks(document_page, block_types=[BlockTypes.Line]):
                        line.removed = True
                    block.structure = []
                    for line_spans in all_line_spans:
                        new_line = Line(
                            polygon=block.polygon,
                            page_id=block.page_id,
                            text_extraction_method="surya",
                        )
                        document_page.add_full_block(new_line)
                        block.add_structure(new_line)
                        self.replace_line_spans(document, document_page, new_line, line_spans)

    OcrBuilder.ocr_extraction = patched_ocr_extraction
    print(f"✅ 已注入 OcrBuilder.ocr_extraction 分批处理补丁 (子批次大小={RECOGNITION_SUB_BATCH_SIZE})")


def convert_pdf_page_by_page(pdf_path: str, output_dir: str = None):
    from PyPDF2 import PdfWriter, PdfReader

    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(pdf_path), "output")
    os.makedirs(output_dir, exist_ok=True)

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"PDF 总页数: {total_pages}")

    if torch.cuda.is_available():
        device = "cuda"
        print(f"正在使用 GPU: {torch.cuda.get_device_name(0)}")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
        print("正在使用 MPS (Apple Silicon)")
    else:
        device = "cpu"
        print("警告: 未检测到 GPU，使用 CPU 处理（速度非常慢）")

    patch_ocr_builder()

    cli_opts = {
        "output_format": "markdown",
        "device": device,
        "batch_multiplier": 1,
        "disable_image_extraction": True,
        "use_llm": False,
        "load_in_4bit": True,
        "bnb_4bit_compute_dtype": "float16",
    }

    config_parser = ConfigParser(cli_opts)
    converter_cls = config_parser.get_converter_cls()
    renderer = config_parser.get_renderer()
    processor_list = config_parser.get_processors()
    llm_service = config_parser.get_llm_service()

    models = create_model_dict(device=device)
    config = config_parser.generate_config_dict()

    base_fname = config_parser.get_base_filename(pdf_path)
    page_markdown_files = []

    for page_num in range(total_pages):
        print(f"\n{'='*50}")
        print(f"正在处理第 {page_num + 1}/{total_pages} 页...")

        try:
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
                tmp_pdf_path = tmp_pdf.name
                writer.write(tmp_pdf)

            config_parser_page = ConfigParser(cli_opts)
            converter_page = converter_cls(
                config=config_parser_page.generate_config_dict(),
                artifact_dict=models,
                processor_list=processor_list,
                renderer=renderer,
                llm_service=llm_service,
            )

            rendered = converter_page(tmp_pdf_path)

            page_md_name = f"{base_fname}_page_{page_num + 1:04d}.md"
            page_md_path = os.path.join(output_dir, page_md_name)

            if hasattr(rendered, 'full_text') and rendered.full_text:
                with open(page_md_path, "w", encoding="utf-8") as f:
                    f.write(rendered.full_text)
            else:
                from marker.output import text_from_rendered
                text, _, _ = text_from_rendered(rendered)
                with open(page_md_path, "w", encoding="utf-8") as f:
                    f.write(text)

            page_markdown_files.append(page_md_path)
            print(f"  ✅ 第 {page_num + 1} 页已保存: {page_md_name}")

            del writer, rendered, converter_page
            if os.path.exists(tmp_pdf_path):
                os.remove(tmp_pdf_path)
            clear_cuda_memory()

        except Exception as e:
            print(f"  ❌ 第 {page_num + 1} 页处理失败: {e}")
            import traceback
            traceback.print_exc()
            clear_cuda_memory()
            continue

    if page_markdown_files:
        final_md_path = os.path.join(output_dir, f"{base_fname}.md")
        print(f"\n{'='*50}")
        print("正在拼接所有页面...")
        with open(final_md_path, "w", encoding="utf-8") as out:
            for i, md_file in enumerate(page_markdown_files):
                out.write(f"\n\n<!-- Page {i + 1} -->\n\n")
                with open(md_file, "r", encoding="utf-8") as f:
                    out.write(f.read())
                try:
                    os.remove(md_file)
                except:
                    pass

        print(f"✅ 转换成功! 文件路径: {final_md_path}")
        print(f"   共处理 {len(page_markdown_files)}/{total_pages} 页")
    else:
        print("❌ 没有成功处理的页面")

    clear_cuda_memory()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python pdf2markdown.py <pdf路径> [输出目录]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    convert_pdf_page_by_page(pdf_file, output_dir)
