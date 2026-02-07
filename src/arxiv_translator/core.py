import os
import shutil
import re
from .downloader import download_source
from .extractor import extract_source, find_main_tex
from .translator import GeminiTranslator
from .compiler import compile_pdf

def process_arxiv_paper(arxiv_id: str, model_name: str, api_key: str, output_path: str = None, keep: bool = False, progress_callback=None):
    """
    Orchestrates the download, translation, and compilation of an arXiv paper.

    Args:
        arxiv_id (str): The arXiv ID.
        model_name (str): The Gemini model name.
        api_key (str): The Gemini API key.
        output_path (str, optional): Custom output path for the PDF.
        keep (bool): Whether to keep intermediate files.
        progress_callback (callable, optional): A function(stage, progress, message) for status updates.
    """

    def report(stage, progress, message):
        if progress_callback:
            progress_callback(stage, progress, message)
        else:
            print(f"[{stage}] {message}")

    work_dir = os.path.abspath(f"workspace_{arxiv_id}")

    if os.path.exists(work_dir) and not keep:
         shutil.rmtree(work_dir)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)

    report("setup", 0.0, f"Work directory: {work_dir}")

    try:
        # 1. Download source
        tar_path = os.path.join(work_dir, f"{arxiv_id}.tar.gz")
        report("download", 0.0, "Starting download...")
        if not os.path.exists(tar_path):
             # We pass a lambda wrapper to adapt the callback signature if needed,
             # but here download_source uses the same signature (stage, progress, message).
             # However, download_source might be called with just (id, dir) by old code.
             # We updated download_source to accept progress_callback.
             tar_path = download_source(arxiv_id, work_dir, progress_callback=progress_callback)
        else:
             report("download", 1.0, "Using existing source archive.")

        # 2. Extract
        source_dir = os.path.join(work_dir, "source")
        report("extract", 0.0, "Extracting source...")
        if not os.path.exists(source_dir):
            extract_source(tar_path, source_dir)
        report("extract", 1.0, "Extraction complete.")

        # 3. Translate
        # Copy source to source_zh
        source_zh_dir = os.path.join(work_dir, "source_zh")
        if os.path.exists(source_zh_dir):
            shutil.rmtree(source_zh_dir) # Always fresh copy for translation
        shutil.copytree(source_dir, source_zh_dir)

        main_tex = find_main_tex(source_zh_dir)
        report("translate", 0.0, f"Main TeX file: {main_tex}")

        translator = GeminiTranslator(api_key=api_key, model_name=model_name)

        # Identify files to translate
        tex_files = []
        for root, dirs, files in os.walk(source_zh_dir):
            for file in files:
                if file == "math_commands.tex":
                    continue
                if file.endswith(".tex"):
                    tex_files.append(os.path.join(root, file))

        total_files = len(tex_files)

        for idx, file_path in enumerate(tex_files):
            file_name = os.path.basename(file_path)
            report("translate", idx / total_files, f"Translating {file_name} ({idx+1}/{total_files})...")

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Pass callback for chunked progress
                # We wrap the main progress_callback to distinguish chunks
                def chunk_callback(stage, progress, message):
                    # We are inside "Translating file X". Chunks are sub-progress.
                    # Maybe we don't need to report chunks to the main progress if it's too noisy.
                    # Or we can report them as detailed messages.
                    # Let's report them.
                    report("translate", idx / total_files, f"File {idx+1}/{total_files}: {message}")

                translated = translator.translate_latex(content, progress_callback=chunk_callback)

                # Inject Chinese support if this is the main tex file
                if os.path.abspath(file_path) == os.path.abspath(main_tex):
                    report("translate", (idx + 0.9) / total_files, "Injecting ctex support into main file...")

                    # Remove conflicting CJK packages
                    translated = re.sub(r'\\usepackage\{CJK.*\}', '', translated)
                    translated = re.sub(r'\\usepackage\{xeCJK\}', '', translated) # Clean old if exists

                    # Insert ctex
                    if "\\documentclass" in translated and "ctex" not in translated:
                        preamble = "\n\\usepackage[fontset=fandol]{ctex}\n\\usepackage{xspace}\n"

                        # Insert before \begin{document} which is safer
                        if "\\begin{document}" in translated:
                            translated = translated.replace("\\begin{document}", preamble + "\\begin{document}")
                        else:
                            pass

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(translated)
            except Exception as e:
                report("translate", idx / total_files, f"Error translating {file_name}: {e}")
                # Continue to next file

        report("translate", 1.0, "Translation complete.")

        # 4. Compile
        report("compile", 0.0, "Starting compilation...")
        compile_pdf(source_zh_dir, main_tex, progress_callback=progress_callback)
        report("compile", 1.0, "Compilation complete.")

        # Move PDF to root or custom output
        pdf_name = os.path.basename(main_tex).replace(".tex", ".pdf")
        compiled_pdf = os.path.join(source_zh_dir, pdf_name)

        # Suffix handling
        if output_path:
            final_pdf = output_path
        else:
            suffix = "_zh"
            if "pro" in model_name.lower():
                suffix = "_zh_pro"
            elif "flash" in model_name.lower():
                suffix = "_zh_flash"
            final_pdf = f"{arxiv_id}{suffix}.pdf"

        if os.path.exists(compiled_pdf):
            shutil.copy(compiled_pdf, final_pdf)
            report("done", 1.0, f"SUCCESS: Generated {final_pdf}")
        else:
            report("error", 1.0, "ERROR: PDF was not generated.")
            raise Exception("PDF generation failed")

    except Exception as e:
        report("error", 1.0, f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        if not keep:
            # shutil.rmtree(work_dir)
            pass # Keep by default for debug
