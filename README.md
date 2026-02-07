# arXiv LaTeX Translator 🤖📄

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**arXiv LaTeX Translator** is a powerful tool configured to automatically translate arXiv papers from English to Chinese. It downloads the LaTeX source, translates the content using **Google Gemini 3.0** (Flash or Pro), and recompiles the paper into a professional PDF, preserving the original layout, equations, and citations.

## ✨ Features

- **Automated Workflow**: Downloads source -> Extracts -> Translates -> Recompiles.
- **Model Selection**: Choose between **Gemini 3.0 Flash** (fast/cheap) or **Gemini 3.0 Pro** (higher quality).
- **Academic Quality**: Uses specialized prompts to ensure accurate translation of AI/ML terminology and academic tone.
- **Robust Processing**:
  - Handles Large Files: Automatically chunks large LaTeX files to avoid API limits.
  - Error Resilience: Retries on network failures.
  - LaTeX Preservation: Strictly preserves mathematical formulas, citations, and structural commands.
- **Chinese Support**: Automatically injects `ctex` package for proper Chinese rendering.

## 🚀 Prerequisites

1.  **Python 3.11+**
2.  **Tectonic**: A modern, self-contained LaTeX engine.
    -   *Installation*: `curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh` (or via your package manager).
    -   *Micromamba/Conda*: `micromamba install tectonic`
3.  **Google Gemini API Key**: Get one from [Google AI Studio](https://aistudio.google.com/).

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/ZeyuChen/arxiv-translator.git
    cd arxiv-translator
    ```

2.  **Install Config Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**
    Copy the example environment file and add your API key:
    ```bash
    cp .env.example .env
    ```
    Open `.env` and paste your key:
    ```
    GEMINI_API_KEY=your_actual_api_key_here
    ```

## 📖 Usage

Run the translator by providing the arXiv URL or ID:

```bash
python -m src.main https://arxiv.org/abs/2602.04705 --model flash
```

### Arguments

-   `arxiv_url`: The URL or ID of the paper (e.g., `2602.04705` or `https://arxiv.org/abs/...`).
-   `--model`: The model to use. Options: `flash` (default) or `pro`.
-   `--keep`: Keep intermediate files (workspace directory) for debugging purposes.

### Examples

**Use Gemini 3.0 Flash (Default)**
```bash
python -m src.main 2602.04705
```

**Use Gemini 3.0 Pro (Higher Quality)**
```bash
python -m src.main 2602.04705 --model pro
```

**Keep Intermediate Files**
```bash
python -m src.main 2602.04705 --keep
```

## 📂 Output

The translated PDF will be generated in the project root with the format:
-   `{arxiv_id}_zh_flash.pdf` (for Flash model)
-   `{arxiv_id}_zh_pro.pdf` (for Pro model)

## 🔧 Technical Details

-   **Parser**: Extracts the main LaTeX file automatically.
-   **Translator**: Uses `google-genai` SDK. Implements smart chunking for long sections.
-   **Compiler**: Uses `tectonic` for hassle-free compilation, automatically downloading necessary LaTeX packages.

## 🤝 Contributing

Contributions are welcome! Please submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
