from google import genai
from google.genai import types
import os
import re
import time
from .logging_utils import logger

class GeminiTranslator:
    def __init__(self, api_key: str, model_name: str = "gemini-3-flash-preview"): 
        self.api_key = api_key
        # Default to Gemini 3 Flash Preview as per docs
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1beta', 'timeout': 600000})

    @property
    def _system_prompt(self) -> str:
        return """You are a professional academic translator specializing in computer science and mathematics. 
Your task is to translate the following LaTeX source code from English to Chinese.

CRITICAL RULES:
1. STRICTLY PRESERVE all LaTeX commands, environments, macros, citations, references, and mathematical formulas. 
   - Do NOT translate content inside `\\cite{...}`, `\\ref{...}`, `\\label{...}`, `\\usepackage{...}`, `\\documentclass{...}`.
   - Do NOT translate equation environments like `\\begin{equation} ... \\end{equation}`, `$$ ... $$`, `$ ... $`.
   - Do NOT translate code blocks or verbatim environments.
2. Only translate the human-readable text content (paragraphs, section titles, captions).
3. Ensure the translation is professional, academic, and flows naturally in Chinese. 
   - Use precise and standard AI/ML terminology (e.g., "Transformer", "Zero-shot", "End-to-end", "Ablation study").
   - Maintain a formal academic tone suitable for top-tier conference papers.
4. Do NOT output markdown code fences (like ```latex ... ```). Output ONLY the raw translated LaTeX content.
5. If the input is too long, the system might have split it. Translate exactly what is given.
"""

    def translate_latex(self, latex_content: str) -> str:
        """
        Translates LaTeX content from English to Chinese using Gemini.
        Preserves LaTeX structure.
        """
        # Gemini Flash has 1M context, so we can probably send the whole file or large chunks.
        # But for valid JSON/Request limits, maybe chunking is safer? 
        # 1M context is huge. We can sending whole files usually.
        
        try:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        config=types.GenerateContentConfig(
                            system_instruction=self._system_prompt,
                            temperature=0.1, 
                        ),
                        contents=[latex_content]
                    )
                    
                    if response.text:
                        cleaned = self._clean_output(response.text)
                        return cleaned
                except Exception as e:
                    logger.warning(f"Translation attempt {attempt+1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 * (attempt + 1))
                    else:
                        logger.warning("Max retries reached. Attempting to chunk...")
                        return self._translate_large_latex(latex_content)
            
            return latex_content
            
        except Exception as e:
            logger.error(f"Translation error after retries: {e}")
            return latex_content

    def _translate_large_latex(self, content: str, chunk_size=150) -> str:
        """Splits content into chunks of ~chunk_size lines and translates them."""
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        
        for line in lines:
            current_chunk.append(line)
            if len(current_chunk) >= chunk_size:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        translated_chunks = []
        logger.info(f"Split content into {len(chunks)} chunks for translation.")
        
        for i, chunk in enumerate(chunks):
            logger.debug(f"Translating chunk {i+1}/{len(chunks)}...")
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    config=types.GenerateContentConfig(
                        system_instruction=self._system_prompt,
                        temperature=0.1, 
                    ),
                    contents=[chunk]
                )
                if response.text:
                    cleaned = self._clean_output(response.text)
                    translated_chunks.append(cleaned)
                else:
                    # Fallback: Use original chunk but still clean comments
                    cleaned_fallback = self._clean_output(chunk)
                    translated_chunks.append(cleaned_fallback)
            except Exception as e:
                logger.error(f"Chunk {i+1} failed: {e}")
                # Fallback: Use original chunk but still clean comments
                cleaned_fallback = self._clean_output(chunk)
                translated_chunks.append(cleaned_fallback)
            
            # Rate limiting for Pro model to avoid overloading
            if "pro" in self.model_name.lower():
                time.sleep(2)  # 2 seconds delay between chunks
                
        return '\n'.join(translated_chunks)

    def _clean_output(self, text: str) -> str:
        # Remove ```latex ... ``` or ``` ... ```
        pattern = r"^```(?:latex)?\s*(.*?)\s*```$"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            text = match.group(1)
            
        # Remove LaTeX comment lines (lines starting with %)
        # This reduces token usage for subsequent steps (DeepDive) and reduces interference
        lines = text.splitlines()
        # Keep lines that are NOT comments (ignoring leading whitespace)
        # We perform this post-processing to ensure clean input for DeepDive
        cleaned_lines = [line for line in lines if not line.strip().startswith('%')]
        
        return '\n'.join(cleaned_lines)
