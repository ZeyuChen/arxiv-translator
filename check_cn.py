import subprocess
import os
import sys

tex = r"""
\documentclass{article}
\usepackage{xeCJK}
\setCJKmainfont{FandolSong-Regular}
\begin{document}
你好，世界。 This is a test.
\end{document}
"""

with open("test_cn.tex", "w", encoding="utf-8") as f:
    f.write(tex)

print("Running tectonic on test_cn.tex...")
try:
    subprocess.run(["tectonic", "test_cn.tex"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if os.path.exists("test_cn.pdf"):
        print("SUCCESS: Chinese PDF generated.")
    else:
        print("FAIL: PDF not found.")
        sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"FAIL: Tectonic failed with code {e.returncode}")
    print(e.stderr.decode('utf-8'))
    sys.exit(1)
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
