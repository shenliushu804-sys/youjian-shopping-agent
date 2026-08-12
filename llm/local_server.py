"""本地 Qwen3.5-2B 推理服务（OpenAI 兼容 /v1/chat/completions）

启动: python3 llm/local_server.py
端口: 127.0.0.1:8001
"""

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import sys as _sys
from pathlib import Path

_sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import MODEL_PATH, LOCAL_LLM_PORT

_model = None
_processor = None


def load_model():
    global _model, _processor
    if _model is not None:
        return
    print(f"[local-llm] loading {MODEL_PATH} ...", flush=True)
    from mlx_vlm.utils import load
    _model, _processor = load(MODEL_PATH)
    import mlx.core as mx
    print(f"[local-llm] loaded on {mx.default_device()}", flush=True)


def chat_completion(messages, temperature=0.2, max_tokens=1024):
    """调用本地模型生成回复"""
    load_model()
    from mlx_vlm import generate as mlx_generate
    from mlx_vlm.prompt_utils import apply_chat_template

    # 构建聊天消息（纯文本，无图像）
    prompt = apply_chat_template(
        _processor,
        _model.config,
        messages,
        add_generation_prompt=True,
    )
    t0 = time.time()
    result = mlx_generate(
        _model,
        _processor,
        prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    elapsed = time.time() - t0
    print(f"[local-llm] inference {elapsed:.1f}s", file=sys.stderr, flush=True)
    return result.text.strip()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/v1/models":
            self._send_json({
                "object": "list",
                "data": [{"id": "qwen3.5-2b", "object": "model", "owned_by": "local"}],
            })
        elif self.path == "/health":
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            self._send_json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))
            messages = payload.get("messages", [])
            temperature = payload.get("temperature", 0.2)
            max_tokens = payload.get("max_tokens", 1024)
            content = chat_completion(messages, temperature, max_tokens)
            self._send_json({
                "id": "local-qwen3.5-2b",
                "object": "chat.completion",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            })
        except Exception as e:
            self._send_json({"error": {"message": str(e)}}, 500)


def main():
    load_model()
    server = ThreadingHTTPServer(("127.0.0.1", LOCAL_LLM_PORT), Handler)
    print(f"[local-llm] serving on http://127.0.0.1:{LOCAL_LLM_PORT}/v1/chat/completions", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
