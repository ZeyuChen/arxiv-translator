import argparse
import os
import sys
from .core import process_arxiv_paper
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
    arxiv_id = args.arxiv_url.split("/")[-1].replace(".pdf", "")

    print(f"Using model: {model_name}")
    
    def console_progress(stage, progress, message):
        pct = f"{progress*100:.1f}%" if progress >= 0 else "..."
        print(f"[{stage.upper()}] {pct} - {message}")

    try:
        process_arxiv_paper(
            arxiv_id=arxiv_id,
            model_name=model_name,
            api_key=api_key,
            output_path=args.output,
            keep=args.keep,
            progress_callback=console_progress
        )
    except Exception as e:
        print(f"Processing failed: {e}")
        # traceback is printed in core if needed, or we can print here
            
if __name__ == "__main__":
    main()
