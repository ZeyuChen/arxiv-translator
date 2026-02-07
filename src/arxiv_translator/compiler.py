import subprocess
import os

def compile_pdf(source_dir: str, main_tex_file: str, progress_callback=None):
    """
    Compiles the LaTeX project to PDF using latexmk.
    
    Args:
        source_dir (str): The directory containing the source files.
        main_tex_file (str): The path to the main .tex file.
        progress_callback (callable, optional): A function(stage, progress, message).
    """
    # Ensure we are in the source dir
    cwd = os.getcwd()
    os.chdir(source_dir)
    
    # main_tex_file might be absolute, we need relative for latexmk usually
    rel_tex_file = os.path.basename(main_tex_file)
    
    msg = f"Compiling {rel_tex_file} in {source_dir}..."
    print(msg)
    if progress_callback:
        progress_callback("compile", 0.0, msg)
    
    try:
        # Tectonic automatically handles dependencies and multiple passes.
        # It essentially replaces latexmk -xelatex (since it uses xetex engine under the hood)
        cmd = ['tectonic', rel_tex_file]
        
        # We merge stderr into stdout to avoid deadlock and simplify capturing
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        stdout_output = []

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                stdout_output.append(output)
                # print(output.strip()) # Verbose?

        # Collect rest
        out, _ = process.communicate()
        if out: stdout_output.append(out)

        if process.returncode != 0:
            print("Compilation had warnings/errors.")
            print("OUTPUT:", ''.join(stdout_output))
            if progress_callback:
                progress_callback("compile", 1.0, "Compilation failed.")
        else:
            print("Compilation successful.")
            if progress_callback:
                progress_callback("compile", 1.0, "Compilation successful.")
            
    except Exception as e:
        print(f"Compiler error: {e}")
        if progress_callback:
            progress_callback("compile", 1.0, f"Compiler error: {e}")
    finally:
        os.chdir(cwd)
