import subprocess
import os

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
    
    print(f"Compiling {rel_tex_file} in {source_dir}...")
    
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
            print("Compilation had warnings/errors.")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        else:
            print("Compilation successful.")
            
    except Exception as e:
        print(f"Compiler error: {e}")
    finally:
        os.chdir(cwd)
