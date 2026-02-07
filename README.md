# arXiv LaTeX Translator 🤖📄

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
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
-   **Automated Workflow**: Downloads source -> Extracts -> Translates -> Recompiles.
-   **Model Selection**: Choose between **Gemini 3.0 Flash** (fast/cheap) or **Gemini 3.0 Pro** (higher quality).
-   **Academic Quality**: Uses specialized prompts to ensure accurate translation of AI/ML terminology and academic tone.
-   **Robust Processing**:
    -   Handles Large Files: Automatically chunks large LaTeX files to avoid API limits.
    -   Error Resilience: Retries on network failures.
    -   LaTeX Preservation: Strictly preserves mathematical formulas, citations, and structural commands.
-   **Chinese Support**: Automatically injects `ctex` package for proper Chinese rendering.

## 🚀 Installation

### Option 1: Install from Source (Recommended for Users)

```bash
git clone https://github.com/ZeyuChen/arxiv-translator.git
cd arxiv-translator
pip install .
```

### Option 2: Development Setup (Recommended for Contributors)

```bash
git clone https://github.com/ZeyuChen/arxiv-translator.git
cd arxiv-translator

# Install micromamba environment (optional but recommended)
micromamba create -f environment.yml
micromamba activate arxiv-translator

# Install package in editable mode with dev dependencies
pip install -e .
```

### 3. Install Tectonic (TeX Engine)
The translator uses [Tectonic](https://tectonic-typesetting.github.io/) for robust PDF compilation.

```bash
# If using micromamba environment (already installed via environment.yml)
micromamba install tectonic -c conda-forge

# Or install manually
curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh
```

### 4. Configuration
Create a `.env` file in the project root:
```bash
cp .env.example .env
```
Edit `.env` and add your Gemini API key:
```ini
GEMINI_API_KEY=your_api_key_here
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

## 📊 Performance Benchmark

**Test Case**: [arXiv:2602.04705](https://arxiv.org/abs/2602.04705) (DeepSeek-V3 Technical Report)

| Model | Time | Translation Quality | Note |
| :--- | :--- | :--- | :--- |
| **Gemini 3.0 Flash** | ~11 min | Good | Fast, reliable. Recommended for most papers. |
| **Gemini 3.0 Pro** | ~20 min | Excellent | Slower, higher precision in detailed academic phrasing. |

### Comparison Preview

### Original English
*(Please manually replace with screenshot: `screenshots/original_en.png`)*
![Original](screenshots/original_en.png)

### Gemini 3.0 Flash (Chinese)
*(Please manually replace with screenshot: `screenshots/flash_zh.png`)*
![Flash](screenshots/flash_zh.png)

### Gemini 3.0 Pro (Chinese)
*(Please manually replace with screenshot: `screenshots/pro_zh.png`)*
![Pro](screenshots/pro_zh.png)

## 📄 License

This project is licensed under the Apache License 2.0.
