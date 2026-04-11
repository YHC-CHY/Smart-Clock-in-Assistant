"""
OCR Service Module
OCR 服务模块 - 封装 Ollama 大模型调用
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRService:
    """OCR 服务类，使用 Ollama 大模型进行图片文字识别"""

    def __init__(self, base_url: str, model: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def __del__(self):
        self.client.close()

    def encode_image_to_base64(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        从图片中提取文字信息
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            包含提取信息的字典，格式如下：
            {
                "打卡时间": "2026/01/08 14:00",
                "打卡地点": "公司总部",
                "打卡项目名称": "项目A",
                "其他事项": "备注信息",
                "raw_text": "原始识别文本"
            }
        """
        try:
            image_base64 = self.encode_image_to_base64(image_path)
            
            prompt = """请仔细观察这张打卡图片，特别注意图片上的水印、时间戳、拍摄时间、地点、项目名称等信息。

请以 JSON 格式直接返回以下字段，不要有任何其他描述文字：
{
  "打卡时间": "从水印中提取的拍摄时间，格式为 YYYY/MM/DD HH:mm，例如 2026/04/09 10:59",
  "打卡地点": "从水印中提取的地点信息",
  "打卡项目名称": "从水印中提取的项目名称",
  "其他事项": "其他重要信息，如天气等，没有则为空字符串",
  "raw_text": "图片中识别到的所有文字内容"
}

请确保：
- 日期格式转换：如 "2026.04.09 10:59" 转换为 "2026/04/09 10:59"
- 只返回一个纯 JSON 对象，不要有其他文字说明
- 即使某些信息缺失，也要返回完整的 JSON 结构"""

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
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "stream": False
            }

            response = self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 兼容 OpenAI 格式和标准 Ollama 格式
            if "choices" in result:
                # OpenAI 兼容格式
                choices = result.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                else:
                    content = ""
            else:
                # 标准 Ollama 格式
                content = result.get("message", {}).get("content", "")
            
            logger.info(f"OCR 原始响应: {content}")
            
            # 清理内容，移除 ```json 和 ``` 标记
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # 尝试从内容中提取 JSON
            parsed = None
            try:
                # 先尝试直接解析
                parsed = json.loads(content)
            except json.JSONDecodeError:
                # 尝试从文本中提取 JSON
                import re
                json_match = re.search(r'(\{[\s\S]*\})', content)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        pass
            
            if parsed is None:
                logger.warning("无法解析 JSON，使用原始文本")
                parsed = {
                    "打卡时间": None,
                    "打卡地点": None,
                    "打卡项目名称": None,
                    "其他事项": content,
                    "raw_text": content
                }

            if not parsed.get("打卡时间"):
                parsed["打卡时间"] = datetime.now().strftime("%Y/%m/%d %H:%M")
                logger.info(f"未检测到打卡时间，使用当前时间: {parsed['打卡时间']}")

            return parsed

        except Exception as e:
            logger.error(f"OCR 识别失败: {e}")
            raise

    def test_connection(self) -> bool:
        """测试 Ollama 服务连接"""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False


def create_ocr_service(config: Dict[str, Any]) -> OCRService:
    """根据配置创建 OCR 服务实例"""
    ocr_config = config.get("ocr", {})
    return OCRService(
        base_url=ocr_config.get("base_url", "http://localhost:11434"),
        model=ocr_config.get("model", "llava"),
        timeout=ocr_config.get("timeout", 60)
    )
