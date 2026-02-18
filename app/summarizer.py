from typing import Tuple
from app.config import MODEL_FAST, MODEL_TRAVEL
from app.prompts import SYSTEM_PROMPT, digest_rules, work_rules, travel_rules
from app.llm import call_ollama
from app.cleaning import cleanup_output

def summarize(text: str, mode: str = "travel") -> Tuple[str, str]:
    """
    returns (result, model_used)
    """
    if mode == "digest":
        prompt = f"{SYSTEM_PROMPT}\n\n{digest_rules()}\n\nTEXT:\n{text}"
        raw = call_ollama(prompt, model=MODEL_FAST, num_predict=760, timeout=260)
        return cleanup_output(raw), MODEL_FAST

    if mode == "work":
        prompt = f"{SYSTEM_PROMPT}\n\n{work_rules()}\n\nTEXT:\n{text}"
        raw = call_ollama(prompt, model=MODEL_FAST, num_predict=650, timeout=240)
        return cleanup_output(raw), MODEL_FAST

    prompt = f"{SYSTEM_PROMPT}\n\n{travel_rules()}\n\nTEXT:\n{text}"
    raw = call_ollama(prompt, model=MODEL_TRAVEL, num_predict=560, timeout=260)
    return cleanup_output(raw), MODEL_TRAVEL
