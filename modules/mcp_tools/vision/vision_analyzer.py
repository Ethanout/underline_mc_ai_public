#!/usr/bin/env python3
"""
Minecraft Screenshot Vision Analyzer
使用 GLM-4.5V 等视觉模型分析 Minecraft 截图
"""

import os
import sys
import base64
import json
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库")
    print("运行: pip install requests")
    sys.exit(1)


class VisionAnalyzer:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key or os.getenv("Z_AI_API_KEY")
        self.base_url = base_url or os.getenv("Z_AI_BASE_URL", "https://api.siliconflow.cn/v1/")
        self.model = model or os.getenv("Z_AI_VISION_MODEL", "Pro/THUDM/glm-4v-flash")
        
        if not self.api_key:
            raise ValueError("需要设置 Z_AI_API_KEY 环境变量或传入 api_key 参数")
        
        # 确保 base_url 以 / 结尾
        if not self.base_url.endswith('/'):
            self.base_url += '/'
    
    def encode_image(self, image_path):
        """将图片转为 base64 编码"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_image(self, image_path, prompt="请详细描述这张 Minecraft 截图中的内容", max_tokens=2000):
        """
        分析图片
        
        Args:
            image_path: 图片文件路径
            prompt: 分析提示词
            max_tokens: 最大生成 token 数
        
        Returns:
            str: 模型分析结果
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 编码图片
        base64_image = self.encode_image(image_path)
        
        # 构建请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens
        }
        
        # 发送请求
        url = f"{self.base_url}chat/completions"
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            raise Exception(f"API 请求失败 ({response.status_code}): {response.text}")
        
        result = response.json()
        
        # 提取回复内容
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API 返回格式异常: {result}")


def main():
    parser = argparse.ArgumentParser(description="Minecraft 截图视觉分析工具")
    parser.add_argument("image", help="截图文件路径")
    parser.add_argument("-p", "--prompt", default="请详细描述这张 Minecraft 截图中的内容，包括地面图案、方块颜色、建筑结构等",
                        help="分析提示词")
    parser.add_argument("-m", "--model", help="视觉模型名称")
    parser.add_argument("-k", "--api-key", help="API Key")
    parser.add_argument("-u", "--base-url", help="API Base URL")
    parser.add_argument("--max-tokens", type=int, default=2000, help="最大生成 token 数")
    parser.add_argument("--json", action="store_true", help="以 JSON 格式输出")
    
    args = parser.parse_args()
    
    try:
        # 初始化分析器
        analyzer = VisionAnalyzer(
            api_key=args.api_key,
            base_url=args.base_url,
            model=args.model
        )
        
        # 分析图片
        result = analyzer.analyze_image(
            image_path=args.image,
            prompt=args.prompt,
            max_tokens=args.max_tokens
        )
        
        # 输出结果
        if args.json:
            output = {
                "success": True,
                "image": args.image,
                "model": analyzer.model,
                "prompt": args.prompt,
                "result": result
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"=== 图片分析结果 ===")
            print(f"文件: {args.image}")
            print(f"模型: {analyzer.model}")
            print(f"\n{result}")
    
    except Exception as e:
        if args.json:
            output = {
                "success": False,
                "error": str(e)
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
