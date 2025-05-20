"""Configuration for available Cerebras models."""

from typing import Dict, TypedDict

class ModelConfig(TypedDict):
    name: str
    tokens: int
    developer: str

MODELS: Dict[str, ModelConfig] = {
    "llama3.1-8b": {
        "name": "Llama3.1-8b",
        "tokens": 8192,
        "developer": "Meta"
    },
    "llama-3.3-70b": {
        "name": "Llama-3.3-70b",
        "tokens": 8192,
        "developer": "Meta"
    },
    "llama-4-scout-17b-16e-instruct": {
        "name": "Llama4 Scout",
        "tokens": 8192,
        "developer": "Meta"
    },
    "qwen-3-32b": {
        "name": "Qwen 3 32B",
        "tokens": 8192,
        "developer": "Alibaba"
    }
} 
