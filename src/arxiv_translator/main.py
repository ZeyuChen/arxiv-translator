import argparse
import os
import shutil
import sys
from .downloader import download_source
from .extractor import extract_source, find_main_tex
from .translator import GeminiTranslator
from .compiler import compile_pdf
from .config import ConfigManager
from .deepdive import DeepDiveAnalyzer
from .logging_utils import logger, log_ipc

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def strip_latex_comments(content: str) -> str:
    """
    Removes lines that are strictly LaTeX comments (starting with %).
    Retains structure but reduces token count.
    """
    lines = content.splitlines()
    # Keep lines that do NOT start with % (ignoring leading whitespace)
    # We do not remove inline comments (e.g. "x = 1 % comment") to avoid breaking code with \%
    cleaned_lines = [line for line in lines if not line.strip().startswith('%')]
    return '\n'.join(cleaned_lines)

def deepdive_analysis_worker(api_key, file_path, model_name="gemini-3-flash-preview"):
    try:
        analyzer = DeepDiveAnalyzer(api_key, model_name=model_name)
        file_name = os.path.basename(file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        analyzed = analyzer.analyze_latex(content, file_name)
        
        if analyzed != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(analyzed)
            return True, file_name
        return False, file_name
    except Exception as e:
        logger.error(f"DeepDive worker failed for {os.path.basename(file_path)}: {e}", exc_info=True)
        return False, os.path.basename(file_path)

def translate_file_worker(api_key, model_name, file_path, main_tex_path):
    import re
    try:
        file_name = os.path.basename(file_path)
        # Re-instantiate translator in worker process
        translator = GeminiTranslator(api_key=api_key, model_name=model_name)
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Pre-processing: Strip LaTeX comments to save tokens
        content = strip_latex_comments(content)
            
        translated = translator.translate_latex(content)
        
        # Inject ctex if main file
        if os.path.abspath(file_path) == os.path.abspath(main_tex_path):
            logger.debug(f"Worker interacting with main file: {file_name}")
            import re
            translated = re.sub(r'\\usepackage\{CJK.*\}', '', translated)
            translated = re.sub(r'\\usepackage\{xeCJK\}', '', translated)
            
            if "\\documentclass" in translated and "ctex" not in translated:
                preamble = "\n\\usepackage[fontset=fandol]{ctex}\n\\usepackage{xspace}\n"
                
                if "\\begin{document}" in translated:
                    translated = translated.replace("\\begin{document}", preamble + "\\begin{document}")

            # Remove CJK* environment tags (Tectonic/ctex handles this natively)
            # Pattern: \begin{CJK*}{UTF8}{gbsn} ... \end{CJK*}
            translated = re.sub(r'\\begin\{CJK\*\}\{.*?\}\{.*?\}', '', translated)
            translated = re.sub(r'\\end\{CJK\*\}', '', translated)

        # Conflict Resolution: \chinese command (e.g. from 2602.02276)
        # Apply GLOBALLY to all files to handle usage in files that don't define it
        # Scan for usage of \chinese
        if r"\chinese" in translated:
            logger.debug(f"Renaming potential \\chinese conflict in {file_name}...")
            import re
            # Use regex to avoid replacing \chinesefont etc.
            translated = re.sub(r'\\chinese(?![a-zA-Z])', r'\\mychinese', translated)
            
            # If we renamed the definition, simplify it
            if r"\newcommand{\mychinese}" in translated or r"\def\mychinese" in translated:
                 # Redefine to pass-through (removing CJK* dependency)
                 # Pattern: \newcommand{\mychinese}[1]{\begin{CJK*}{UTF8}{gbsn}{#1}\end{CJK*}}
                 translated = re.sub(
                    r'\\newcommand\{\\mychinese\}\[1\]\{.*?\\end\{CJK\*\}\}', 
                    r'\\newcommand{\\mychinese}[1]{#1}', 
                    translated, 
                    flags=re.DOTALL
                 )

        if "{minted}" in translated:
             logger.debug(f"Fixing minted package options in {file_name}...")
             import re
             translated = re.sub(r'\\usepackage\[.*?\]\{minted\}', r'\\usepackage[outputdir=.]{minted}', translated)
        
        # Switch backend=biber to backend=bibtex to avoid external dependency issues
        if "backend=biber" in translated:
            import re # Ensure re is imported if not already
            translated = translated.replace("backend=biber", "backend=bibtex")
            
        # Fix duplicate labels (common in translation)
        # Scan for \label{...} and keep only first occurrence of each unique label
        label_pattern = re.compile(r'\\label\{([^}]+)\}')
        seen_labels = set()
        
        def replace_label(match):
            lbl = match.group(1)
            if lbl in seen_labels:
                return f"% Duplicate label removed: {lbl}"
            seen_labels.add(lbl)
            return match.group(0)
            
        translated = label_pattern.sub(replace_label, translated)
        
        # General LaTeX Fixes for LLM artifacts
        # Fix broken escapes like "\ }" -> "\}"
        translated = translated.replace(r"\ }", r"\}")
        translated = translated.replace(r"\ {", r"\{")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(translated)
            
        return True
    except Exception as e:
        # Worker failure logged by executor usually, but good to be explicit
        logger.error(f"Worker failed for {file_path}: {e}")
        raise e

def main():
    # Force line buffering for real-time progress updates
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(line_buffering=True)
        
    parser = argparse.ArgumentParser(description="arXiv LaTeX Translator - Translate arXiv papers to Chinese")
    
    # Exclusive group for mutually exclusive actions (translate vs config)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("arxiv_url", nargs="?", help="URL or ID of the arXiv paper (e.g., https://arxiv.org/abs/2602.04705)")
    group.add_argument("--set-key", help="Save Gemini API key to configuration and exit")
    
    parser.add_argument("--model", default="gemini-3-flash-preview", help="Gemini model to use (flash or pro)")
    parser.add_argument("--output", "-o", help="Custom output path for the translated PDF")
    parser.add_argument("--keep", action="store_true", help="Keep intermediate files for debugging")
    parser.add_argument("--deepdive", action="store_true", help="Enable AI DeepDive (Technical Analysis)")
    
    args = parser.parse_args()
    config_manager = ConfigManager()

    # Handle --set-key
    if args.set_key:
        config_manager.set_api_key(args.set_key)
        sys.exit(0)

    # Check for arXiv URL/ID
    if not args.arxiv_url:
        parser.print_help()
        sys.exit(1)

    # Load API Key: CLI (not arg here, but maybe future) > Env > Config
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = config_manager.get_api_key()
    
    if not api_key:
        print("Error: Gemini API Key not found.")
        print("Please set it via environment variable GEMINI_API_KEY")
        print("OR run: arxiv-translator --set-key YOUR_API_KEY")
        sys.exit(1)

    # Handle model aliases
    model_name = args.model
    if model_name.lower() == "flash":
        model_name = "gemini-3-flash-preview"
    elif model_name.lower() == "pro":
        model_name = "gemini-3-pro-preview"
    
    # Extract ID
    # heuristics: 2602.04705 or https://arxiv.org/abs/2602.04705 or https://arxiv.org/pdf/2602.04705
    arxiv_id = args.arxiv_url.split("/")[-1].replace(".pdf", "")

    arxiv_id = args.arxiv_url.split("/")[-1].replace(".pdf", "")

    logger.info(f"Starting translation for {arxiv_id} using model {model_name}")
    logger.info(f"DeepDive Mode: {'ENABLED' if args.deepdive else 'DISABLED'}")
    # print(f"Using model: {model_name}") # Logged above
        
    work_dir = os.path.abspath(f"workspace_{arxiv_id}")
    
    if os.path.exists(work_dir) and not args.keep:
         shutil.rmtree(work_dir)
    
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    
    logger.info(f"Work directory: {work_dir}")
    # print(f"Work directory: {work_dir}") # Logged above
    
    try:
        # 1. Download source
        log_ipc(f"PROGRESS:DOWNLOADING:Downloading source for {arxiv_id}...")
        tar_path = os.path.join(work_dir, f"{arxiv_id}.tar.gz")
        if not os.path.exists(tar_path):
             tar_path = download_source(arxiv_id, work_dir)
             logger.info(f"Downloaded source to {tar_path}")
        else:
             logger.info("Using existing source archive.")
        
        # 2. Extract
        # 2. Extract
        log_ipc(f"PROGRESS:EXTRACTING:Extracting source files...")
        source_dir = os.path.join(work_dir, "source")
        if not os.path.exists(source_dir):
            extract_source(tar_path, source_dir)
        
        # 3. Translate
        # Copy source to source_zh
        source_zh_dir = os.path.join(work_dir, "source_zh")
        if os.path.exists(source_zh_dir):
            shutil.rmtree(source_zh_dir) # Always fresh copy for translation
        shutil.copytree(source_dir, source_zh_dir)
        
        main_tex = find_main_tex(source_zh_dir)
        logger.info(f"Main TeX file found: {main_tex}")
        # print(f"Main TeX file: {main_tex}", flush=True)
        
        translator = GeminiTranslator(api_key=api_key, model_name=model_name)
        
        # Translate all TeX files
        # Translate all TeX files
        log_ipc(f"PROGRESS:TRANSLATING:0:0:Starting translation with {model_name}...")
        
        # Pre-count and collect files
        tex_files_to_translate = []
        for root, dirs, files in os.walk(source_zh_dir):
            for file in files:
                if file == "math_commands.tex":
                    # print(f"Skipping {file} (definitions)...")
                    continue
                if file.endswith(".tex"):
                     tex_files_to_translate.append(os.path.join(root, file))
        
        total_files = len(tex_files_to_translate)
        total_files = len(tex_files_to_translate)
        logger.info(f"Found {total_files} TeX files to translate.")
        
        # Concurrent Translation
        from concurrent.futures import ProcessPoolExecutor, as_completed
        
        # Helper to be pickled
        # define worker inside main or import? needs to be picklable, so top level is best.
        # But we can't move it easily with replace_file_content unless we replace whole file or use a separate file.
        # We can define it at top of main() but better at module level.
        # Impl note: python multiprocessing needs top-level function.
        # I will use a separate small replace to add the worker function at the top, or just put it here if I am replacing a big chunk.
        # Actually, I can't put it here inside main().
        # I HAVE TO MOVE IT OUT.
        # I will replace the whole file or add it before main().
        # Since I am using replace_file_content on a range, I can't easily add to top.
        # Strategy: 
        # 1. Use `replace_file_content` to add imports and the worker function BEFORE `main`.
        # 2. Use `replace_file_content` to rewrite the loop inside `main`.
        
        # Let's do step 2 (loop rewrite) here assuming step 1 (worker def) is done? 
        # No, sequential tools. I should abort this tool call and do the worker def first.
        # But I can't abort myself.
        # I will use this tool call to rewrite the loop, but call the worker `translate_file_worker` which I will define in the NEXT tool call at the top of the file?
        # Python will fail if I run it before defining. But I am editing code.
        # I will define `translate_file_worker` in the NEXT tool call at the top.
        # WAIT, if I edit the loop to call `translate_file_worker`, and then edit top to add it, the file is broken in between. That's fine.
        
        completed_count = 0
        with ProcessPoolExecutor(max_workers=12) as executor:
            future_to_file = {
                executor.submit(translate_file_worker, api_key, model_name, f, main_tex): f 
                for f in tex_files_to_translate
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                file_name = os.path.basename(file_path)
                completed_count += 1
                try:
                    res = future.result()
                    # res is boolean or message?
                    log_ipc(f"PROGRESS:TRANSLATING:{completed_count}:{total_files}:Translated {file_name}")
                except Exception as exc:
                    logger.error(f"Generated an exception for {file_name}: {exc}", exc_info=True)
                    log_ipc(f"PROGRESS:TRANSLATING:{completed_count}:{total_files}:Failed {file_name}")

        # 3.5. DeepDive Analysis (Optional)
        if args.deepdive:
            log_ipc(f"PROGRESS:ANALYZING:Starting parallel AI DeepDive Analysis (12 workers)...")
            aux_count = 0
            
            with ProcessPoolExecutor(max_workers=12) as executor:
                future_to_file = {
                    executor.submit(deepdive_analysis_worker, api_key, f, model_name): f 
                    for f in tex_files_to_translate
                }
                
                for future in as_completed(future_to_file):
                    f_path = future_to_file[future]
                    fname = os.path.basename(f_path)
                    aux_count += 1
                    try:
                        is_changed, _ = future.result()
                        if is_changed:
                            log_ipc(f"PROGRESS:ANALYZING:{aux_count}:{total_files}:Analyzed {fname}")
                        else:
                            log_ipc(f"PROGRESS:ANALYZING:{aux_count}:{total_files}:Skipped {fname}")
                    except Exception as e:
                        logger.error(f"Analysis failed for {fname}: {e}", exc_info=True)

        # 4. Compile
        log_ipc(f"PROGRESS:COMPILING:Compiling PDF with Tectonic...")
        compile_pdf(source_zh_dir, main_tex)
        
        # Move PDF to root or custom output
        pdf_name = os.path.basename(main_tex).replace(".tex", ".pdf")
        compiled_pdf = os.path.join(source_zh_dir, pdf_name)
        
        # Suffix handling
        if args.output:
            final_pdf = args.output
        else:
            suffix = "_zh"
            if "pro" in model_name.lower():
                suffix = "_zh_pro"
            elif "flash" in model_name.lower():
                suffix = "_zh_flash"
            final_pdf = f"{arxiv_id}{suffix}.pdf"
        
        if os.path.exists(compiled_pdf):
            shutil.copy(compiled_pdf, final_pdf)
            logger.info(f"SUCCESS: Generated {final_pdf}")
            log_ipc(f"PROGRESS:COMPLETED:Translation finished successfully.")
        else:
            logger.error("ERROR: PDF was not generated.")
            log_ipc(f"PROGRESS:FAILED:PDF compilation failed.")
            
    except Exception as e:
        logger.error(f"Translation FAILED: {e}", exc_info=True)
        print(f"FAILED: {e}") # Print to stdout for CLI visibility if logger goes to stderr only
        # traceback.print_exc() # Handled by exc_info=True in logger
    finally:
        if not args.keep:
            # shutil.rmtree(work_dir)
            pass # Keep by default for debug
            
if __name__ == "__main__":
    main()
