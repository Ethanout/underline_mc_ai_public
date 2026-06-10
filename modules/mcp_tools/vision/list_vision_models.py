#!/usr/bin/env python3
"""查询 SiliconFlow 可用的视觉模型"""

import os
import requests

api_key = os.getenv("Z_AI_API_KEY", "sk-REDACTED")
base_url = "https://api.siliconflow.cn/v1/"

headers = {
    "Authorization": f"Bearer {api_key}",
}

print("正在查询可用模型...")
response = requests.get(f"{base_url}models", headers=headers, timeout=30)

if response.status_code == 200:
    models = response.json()
    vision_models = []
    
    for model in models.get("data", []):
        model_id = model.get("id", "")
        # 查找支持视觉的模型
        if any(keyword in model_id.lower() for keyword in ["vision", "vl", "llava", "qwen2-vl", "glm-4v", "internvl", "cogvlm"]):
            vision_models.append(model_id)
    
    print(f"\n找到 {len(vision_models)} 个可能的视觉模型:\n")
    for model in sorted(vision_models):
        print(f"  - {model}")
else:
    print(f"查询失败: {response.status_code}")
    print(response.text)
