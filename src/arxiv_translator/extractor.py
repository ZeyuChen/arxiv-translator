import tarfile
import os
import shutil
from .logging_utils import logger

def extract_source(file_path: str, extract_to: str):
    """
    Extracts the downloaded arXiv source file.
    
    Args:
        file_path (str): Path to the downloaded tar.gz file.
        extract_to (str): Directory to extract files into.
    """
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
        
    logger.info(f"Extracting {file_path} to {extract_to}...")
    
    try:
        if tarfile.is_tarfile(file_path):
            with tarfile.open(file_path, 'r:*') as tar:
                # Security check: avoid zip slip, though low risk from arxiv
                tar.extractall(path=extract_to, filter='data')
        else:
            # Sometimes single file or pdf? But e-print should be source.
            # If it's a gzip file but not tar?
            raise ValueError(f"File {file_path} is not a valid tar archive.")
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        # Identify if it's just a .tex file (rare but possible for old papers)
        # TODO: Handle single .tex file case if needed.
        raise e

def find_main_tex(source_dir: str) -> str:
    r"""
    Attempts to identify the main .tex file in the directory.
    Heuristic: Look for \documentclass. If multiple, pick 'main.tex' or 'ms.tex' or the one with \begin{document}.
    """
    tex_files = [f for f in os.listdir(source_dir) if f.endswith('.tex')]
    
    if not tex_files:
        raise FileNotFoundError("No .tex files found in source.")
        
    if len(tex_files) == 1:
        return os.path.join(source_dir, tex_files[0])
        
    # Heuristics
    candidates = []
    for f in tex_files:
        path = os.path.join(source_dir, f)
        with open(path, 'r', encoding='utf-8', errors='ignore') as content:
            text = content.read()
            if '\\documentclass' in text:
                candidates.append(f)
                
    if len(candidates) == 1:
        return os.path.join(source_dir, candidates[0])
    
    # Priority names
    priority = ['main.tex', 'ms.tex', 'paper.tex', 'article.tex']
    for p in priority:
        if p in candidates:
            return os.path.join(source_dir, p)
            
    # Fallback to first candidate or first tex
    return os.path.join(source_dir, candidates[0] if candidates else tex_files[0])
