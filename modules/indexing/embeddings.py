from pathlib import Path
from ..config import SILICONFLOW_KEY

class SiliconFlowEF:
    MODEL = "Qwen/Qwen3-Embedding-4B"
    _key = SILICONFLOW_KEY.read_text().strip()

    def _embed(self, texts):
        import requests

        results = []
        for i in range(0, len(texts), 32):
            batch = texts[i : i + 32]
            r = requests.post(
                "https://api.siliconflow.cn/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self._key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.MODEL,
                    "input": batch,
                    "encoding_format": "float",
                },
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()["data"]
            data.sort(key=lambda x: x["index"])
            results.extend(item["embedding"] for item in data)
        return results

    def __call__(self, input):
        return self._embed(input)

    def embed_query(self, input):
        return self._embed(input)

    def name(self):
        return "SiliconFlowEF"