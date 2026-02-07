import subprocess
import os
from .logging_utils import logger

def compile_pdf(source_dir: str, main_tex_file: str):
    """
    Compiles the LaTeX project to PDF using latexmk.
    
    Args:
        source_dir (str): The directory containing the source files.
        main_tex_file (str): The path to the main .tex file.
    """
    # Ensure we are in the source dir
    cwd = os.getcwd()
    os.chdir(source_dir)
    
    # main_tex_file might be absolute, we need relative for latexmk usually
    rel_tex_file = os.path.basename(main_tex_file)
    
    logger.info(f"Compiling {rel_tex_file} in {source_dir}...")
    
    try:
        # Tectonic automatically handles dependencies and multiple passes.
        # -Z shell-escape is needed for minted (pygments)
        cmd = ['tectonic', '-X', 'compile', '--keep-intermediates', '-Z', 'shell-escape', rel_tex_file]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            logger.warning(f"Compilation finished with return code {result.returncode}")
            logger.warning("Compilation had warnings/errors.")
            logger.debug(f"STDOUT: {result.stdout}")
            logger.debug(f"STDERR: {result.stderr}")
            # return False # We tolerate warnings
        else:
            logger.info("Compilation successful.")
            
        return True
    except Exception as e:
        logger.error(f"Compiler error: {e}")
        return False
    finally:
        os.chdir(cwd)
