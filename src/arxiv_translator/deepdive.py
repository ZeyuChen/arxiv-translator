from google import genai
from google.genai import types
import os
import re
import time
from .logging_utils import logger

class DeepDiveAnalyzer:
    def __init__(self, api_key: str, model_name: str = "gemini-3.0-pro-exp"):
        self.api_key = api_key
        # Use Pro model as requested for deeper reasoning, or default if not specified
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key, http_options={'api_version': 'v1beta', 'timeout': 600000})
        
        # Load Prompt
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "deepdive_prompt.txt")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read()
        else:
            # Fallback simple prompt
            self.system_prompt = "Analyze the technical content and insert explanation boxes in Chinese using tcolorbox for DeepDive."

    def analyze_latex(self, latex_content: str, filename: str) -> str:
        """
        Analyzes the LaTeX content and injects DeepDive reading blocks.
        """
        # Heuristic filtering: Only process files that likely contain technical depth
        # Skip standard boilerplate files
        if filename in ["main.tex", "references.tex", "appendix.tex", "math_commands.tex"]:
            # main.tex might have content, but often just includes. 
            # If it's short, skip.
            if len(latex_content) < 500: 
                return latex_content

        # Simple keyword check to avoid wasting tokens on non-technical files
        # Keywords: method, algorithm, equation, theorem, proof, architecture, layer, loss
        keywords = ["method", "algorithm", "equation", "theorem", "proof", "architecture", "layer", "loss", "model", "training"]
        if not any(k in latex_content.lower() for k in keywords):
            return latex_content

        # Chunking: Pro model is slower, so we limit context size.
        # Currently processing the entire file if within token limits.
        
        # Limit file size to avoid timeout/cost issues
        if len(latex_content) > 131072:
            logger.info(f"Skipping {filename} (File too large for single-pass analysis).")
            return latex_content

        try:
            # logger.debug(f"Analyzing technical content in {filename}...") # Verbose logging removed for cleaner CLI output
            response = self.client.models.generate_content(
                model=self.model_name,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.2, 
                ),
                contents=[latex_content]
            )
            
            if response.text:
                return self._clean_output(response.text)
            
            return latex_content

        except Exception as e:
            logger.error(f"DeepDive analysis failed for {filename}: {e}")
            return latex_content

    def _clean_output(self, text: str) -> str:
        # Remove markdown code fences if present
        pattern = r"^```(?:latex)?\s*(.*?)\s*```$"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        return text
