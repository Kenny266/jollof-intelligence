"""
Shared LLM client wrapping a local open-source model (Mistral / Llama / Qwen).
Both Task A and Task B import from here so model loads once.
"""
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

MODEL_NAME = os.getenv("MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.2")

_pipe = None


def get_pipeline():
    global _pipe
    if _pipe is None:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        _pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=512,
            temperature=0.7,
            do_sample=True,
        )
    return _pipe


def generate(prompt: str, max_new_tokens: int = 512) -> str:
    pipe = get_pipeline()
    output = pipe(prompt, max_new_tokens=max_new_tokens)
    return output[0]["generated_text"][len(prompt):].strip()
