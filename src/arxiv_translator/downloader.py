import requests
import os
import shutil

def download_source(arxiv_id: str, output_dir: str, progress_callback=None) -> str:
    """
    Downloads the source files for a given arXiv ID.
    
    Args:
        arxiv_id (str): The arXiv ID (e.g., '2602.04705').
        output_dir (str): The directory to save the downloaded file.
        progress_callback (callable, optional): A function(stage, progress, message).
        
    Returns:
        str: The path to the downloaded file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    filename = f"{arxiv_id}.tar.gz" # arXiv source is usually a tarball
    output_path = os.path.join(output_dir, filename)
    
    if progress_callback:
        progress_callback("download", 0.0, f"Downloading source based on {arxiv_id} from {url}...")
    else:
        print(f"Downloading source based on {arxiv_id} from {url}...")
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    downloaded_size = 0
    chunk_size = 8192

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            f.write(chunk)
            downloaded_size += len(chunk)
            if total_size > 0 and progress_callback:
                progress = downloaded_size / total_size
                progress_callback("download", progress, f"Downloading... {progress:.1%}")
            
    if progress_callback:
        progress_callback("download", 1.0, f"Downloaded to {output_path}")
    else:
        print(f"Downloaded to {output_path}")

    return output_path
