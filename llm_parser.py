"""
Local LLM Integration Module for Spatial IR Parsing.
Supports any local OpenAI-compatible API server (e.g. LM Studio, Ollama, vLLM, llama-cpp-python).
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
from spatial_ir import SpatialIR

SYSTEM_PROMPT = """
You are a spatial reasoning parser. Convert the user's natural language description of spaces into JSON Spatial IR.
Return ONLY valid JSON matching this schema:
{
  "spaces": [
    {"id": "snake_case_id", "name": "Title Case Name", "space_type": "room_type"}
  ],
  "relations": [
    {"source": "space_id_1", "target": "space_id_2", "relation_type": "ADJACENT" | "NEAR" | "FAR"}
  ]
}
Do not include any explanation or markdown formatting around the JSON.
"""

class LocalLLMSpatialParser:
    def __init__(self, api_url: str = "http://localhost:1234/v1/chat/completions", model_name: str = "local-model"):
        """
        Initialize connection to local LLM server (LM Studio, Ollama, vLLM, etc.).
        """
        self.api_url = api_url
        self.model_name = model_name

    def is_server_available(self) -> bool:
        try:
            url = self.api_url.split("/chat/completions")[0] + "/models"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def parse(self, text: str) -> Optional[SpatialIR]:
        """
        Send natural language prompt to local LLM server and return parsed SpatialIR.
        """
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
                {"role": "user", "content": f"Extract spaces and relations from: {text}"}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                content = result["choices"][0]["message"]["content"]
                ir_dict = json.loads(content)
                ir = SpatialIR.from_dict(ir_dict)
                ir.metadata["raw_description"] = text
                ir.metadata["parsed_by"] = f"Local LLM ({self.model_name})"
                return ir
        except Exception as e:
            print(f"[LocalLLMSpatialParser] Error communicating with local server at {self.api_url}: {e}")
            return None
