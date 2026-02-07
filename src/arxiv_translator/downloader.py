import requests
import os
import shutil
from .logging_utils import logger

def download_source(arxiv_id: str, output_dir: str) -> str:
    """
    Downloads the source files for a given arXiv ID.
    
    Args:
        arxiv_id (str): The arXiv ID (e.g., '2602.04705').
        output_dir (str): The directory to save the downloaded file.
        
    Returns:
        str: The path to the downloaded file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    filename = f"{arxiv_id}.tar.gz" # arXiv source is usually a tarball
    output_path = os.path.join(output_dir, filename)
    
    logger.info(f"Downloading source based on {arxiv_id} from {url}...")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    logger.info(f"Downloaded to {output_path}")
    return output_path
