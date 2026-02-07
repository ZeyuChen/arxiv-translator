import argparse
import os
import shutil
import sys
from .downloader import download_source
from .extractor import extract_source, find_main_tex
from .translator import GeminiTranslator
from .compiler import compile_pdf
from .config import ConfigManager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def main():
    parser = argparse.ArgumentParser(description="arXiv LaTeX Translator - Translate arXiv papers to Chinese")
    
    # Exclusive group for mutually exclusive actions (translate vs config)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("arxiv_url", nargs="?", help="URL or ID of the arXiv paper (e.g., https://arxiv.org/abs/2602.04705)")
    group.add_argument("--set-key", help="Save Gemini API key to configuration and exit")
    
    parser.add_argument("--model", default="gemini-3-flash-preview", help="Gemini model to use (flash or pro)")
    parser.add_argument("--output", "-o", help="Custom output path for the translated PDF")
    parser.add_argument("--keep", action="store_true", help="Keep intermediate files for debugging")
    
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

    print(f"Using model: {model_name}")
        
    work_dir = os.path.abspath(f"workspace_{arxiv_id}")
    
    if os.path.exists(work_dir) and not args.keep:
         shutil.rmtree(work_dir)
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    
    print(f"Work directory: {work_dir}")
    
    try:
        # 1. Download source
        tar_path = os.path.join(work_dir, f"{arxiv_id}.tar.gz")
        if not os.path.exists(tar_path):
             tar_path = download_source(arxiv_id, work_dir)
        else:
             print("Using existing source archive.")
        
        # 2. Extract
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
        main_tex_abs = os.path.abspath(main_tex)
        print(f"Main TeX file: {main_tex}")
        
        translator = GeminiTranslator(api_key=api_key, model_name=model_name)
        
        # Translate all TeX files
        for root, dirs, files in os.walk(source_zh_dir):
            for file in files:
                if file == "math_commands.tex":
                    print(f"Skipping {file} (definitions)...")
                    continue

                if file.endswith(".tex"):
                    file_path = os.path.join(root, file)
                    print(f"Translating {file}...")
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        translated = translator.translate_latex(content)
                        
                        # Inject Chinese support if this is the main tex file
                        if os.path.abspath(file_path) == main_tex_abs:
                            print("Injecting ctex support into main file...")
                            
                            # Remove conflicting CJK packages
                            import re
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
                        print(f"Error translating {file}: {e}")
                        # Continue to next file
                        
        # 4. Compile
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
            print(f"SUCCESS: Generated {final_pdf}")
        else:
            print("ERROR: PDF was not generated.")
            
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if not args.keep:
            # shutil.rmtree(work_dir)
            pass # Keep by default for debug
            
if __name__ == "__main__":
    main()
