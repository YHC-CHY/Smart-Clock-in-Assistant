# 云端大模型配置指南

本指南将详细说明如何使用云端大模型替代本地 Ollama 模型，实现打卡图片的 OCR 文字识别功能。

## 📋 支持的云端大模型

- **OpenAI GPT 系列**
- **百度文心一言**
- **阿里通义千问**
- **腾讯混元大模型**
- **字节跳动豆包**

## 1. 准备工作

### 1.1 选择大模型提供商

根据您的需求和预算，选择一个合适的云端大模型提供商：

| 提供商 | 优势 | 适用场景 |
|-------|------|---------|
| OpenAI | 性能最佳 | 全球通用 |
| 百度文心 | 中文支持好 | 国内使用 |
| 阿里通义 | 性价比高 | 国内使用 |
| 腾讯混元 | 集成方便 | 国内使用 |
| 字节豆包 | 响应速度快 | 国内使用 |

### 1.2 获取 API 密钥

1. 注册并登录选择的大模型平台
2. 创建应用或项目
3. 生成 API 密钥
4. 记录 API 密钥和相关配置信息

## 2. 配置修改

### 2.1 修改 config.json 文件

打开 `config.json` 文件，找到 `ocr` 部分，修改为以下配置：

```json
"ocr": {
  "enabled": true,
  "provider": "cloud",
  "api_key": "your_api_key",
  "endpoint": "https://api.example.com/v1/chat/completions",
  "model": "gpt-4o",
  "timeout": 60,
  "max_retries": 3
}
```

### 2.2 配置参数说明

| 参数 | 说明 | 示例值 |
|------|------|--------|
| `provider` | 大模型提供商 | `openai`, `baidu`, `ali`, `tencent`, `bytedance` |
| `api_key` | API 密钥 | `sk-xxxxxxxxxxxxxxxxxxxxxxxx` |
| `endpoint` | API 端点 | `https://api.openai.com/v1/chat/completions` |
| `model` | 模型名称 | `gpt-4o`, `ernie-4.0`, `qwen-turbo` |
| `timeout` | 超时时间（秒） | `60` |
| `max_retries` | 最大重试次数 | `3` |

## 3. 修改 ocr_service.py 文件

### 3.1 查看当前实现

首先查看 `scripts/ocr_service.py` 文件，了解当前的 OCR 服务实现：

```bash
cat scripts/ocr_service.py
```

### 3.2 添加云端大模型支持

修改 `ocr_service.py` 文件，添加云端大模型的支持：

```python
class CloudOCRService:
    """云端大模型 OCR 服务"""
    
    def __init__(self, config):
        self.config = config
        self.api_key = config.get("api_key")
        self.endpoint = config.get("endpoint")
        self.model = config.get("model", "gpt-4o")
        self.timeout = config.get("timeout", 60)
        self.max_retries = config.get("max_retries", 3)
        
    def test_connection(self):
        """测试连接"""
        try:
            # 发送测试请求
            import httpx
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": "测试连接"
                }],
                "max_tokens": 10
            }
            client = httpx.Client(timeout=self.timeout)
            response = client.post(self.endpoint, headers=headers, json=payload)
            return response.status_code == 200
        except:
            return False
    
    def extract_text_from_image(self, image_path):
        """从图片中提取文本"""
        import base64
        import httpx
        
        # 读取并编码图片
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # 构建请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请从以下图片中提取打卡信息，包括：打卡时间、打卡地点、项目名称、打卡人姓名等。返回 JSON 格式，字段包括：打卡时间、打卡地点、打卡项目名称、其他事项。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }],
            "response_format": {
                "type": "json_object"
            }
        }
        
        # 发送请求
        client = httpx.Client(timeout=self.timeout)
        for i in range(self.max_retries):
            try:
                response = client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", {})
            except Exception as e:
                if i == self.max_retries - 1:
                    raise
                import time
                time.sleep(2 ** i)  # 指数退避
```

### 3.3 更新 create_ocr_service 函数

修改 `create_ocr_service` 函数，支持云端大模型：

```python
def create_ocr_service(config):
    """根据配置创建 OCR 服务实例"""
    ocr_config = config.get("ocr", {})
    provider = ocr_config.get("provider", "ollama")
    
    if provider == "ollama":
        from .ocr_service import OllamaOCRService
        return OllamaOCRService(ocr_config)
    elif provider == "cloud":
        from .ocr_service import CloudOCRService
        return CloudOCRService(ocr_config)
    else:
        raise ValueError(f"不支持的 OCR 提供商: {provider}")
```

## 4. 具体大模型配置

### 4.1 OpenAI GPT 配置

```json
"ocr": {
  "enabled": true,
  "provider": "cloud",
  "api_key": "sk-xxxxxxxxxxxxxxxxxxxxxxxx",
  "endpoint": "https://api.openai.com/v1/chat/completions",
  "model": "gpt-4o",
  "timeout": 60,
  "max_retries": 3
}
```

### 4.2 百度文心一言配置

```json
"ocr": {
  "enabled": true,
  "provider": "cloud",
  "api_key": "your_api_key",
  "endpoint": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions",
  "model": "ernie-4.0",
  "timeout": 60,
  "max_retries": 3
}
```

### 4.3 阿里通义千问配置

```json
"ocr": {
  "enabled": true,
  "provider": "cloud",
  "api_key": "your_api_key",
  "endpoint": "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
  "model": "qwen-turbo",
  "timeout": 60,
  "max_retries": 3
}
```

## 5. 测试云端大模型

### 5.1 验证连接

```bash
# 测试云端大模型连接
python -c "
from scripts.ocr_service import create_ocr_service
import json

config = json.load(open('config.json'))
ocr = create_ocr_service(config)
print('OCR 服务连接:', '成功' if ocr.test_connection() else '失败')
"
```

### 5.2 测试 OCR 功能

```bash
# 测试 OCR 功能
python -c "
from scripts.ocr_service import create_ocr_service
import json

config = json.load(open('config.json'))
ocr = create_ocr_service(config)
result = ocr.extract_text_from_image('<测试图片路径>')
print('OCR 识别结果:', result)
"
```

## 6. 性能优化

### 6.1 图片处理优化

1. **压缩图片**：上传前压缩图片以减少传输时间
2. **调整分辨率**：适当降低图片分辨率，提高处理速度
3. **裁剪图片**：只上传包含关键信息的部分

### 6.2 API 调用优化

1. **批量处理**：如果需要处理多张图片，考虑批量调用
2. **缓存结果**：对于相同的图片，缓存识别结果
3. **错误处理**：实现健壮的错误处理和重试机制

## 7. 成本控制

### 7.1 费用计算

不同大模型的费用计算方式不同，通常基于：
- **token 数量**：输入和输出的 token 总数
- **图片大小**：处理的图片大小
- **调用次数**：API 调用次数

### 7.2 成本优化

1. **合理设置 max_tokens**：只设置必要的 token 数量
2. **使用批处理**：减少 API 调用次数
3. **选择合适的模型**：根据需求选择性价比高的模型
4. **监控使用量**：定期查看 API 使用情况，避免超支

## 8. 故障排除

### 8.1 常见错误及解决方案

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `API key 无效` | API 密钥错误 | 检查并更新 API 密钥 |
| `请求超时` | 网络问题或模型处理时间长 | 增加超时时间，检查网络连接 |
| `图片过大` | 图片超过模型限制 | 压缩图片或调整分辨率 |
| `token 超限` | 输入输出 token 超过限制 | 减少请求内容，使用更简洁的提示词 |

### 8.2 日志查看

```bash
# 查看详细日志
python scripts/clock_in.py \
  --config config.json \
  --image <图片路径> \
  --user-name "测试用户" \
  --verbose
```

## 9. 最佳实践

1. **选择合适的模型**：根据精度和成本需求选择模型
2. **优化提示词**：设计简洁有效的提示词，提高识别准确率
3. **监控性能**：定期监控 API 响应时间和识别准确率
4. **备份方案**：准备本地 Ollama 作为备用方案
5. **安全管理**：妥善保管 API 密钥，避免泄露

## 🎉 完成！

恭喜您成功配置了云端大模型！现在您可以使用云端大模型进行 OCR 识别，享受更高的识别准确率和更快的处理速度。

如果您在使用过程中遇到任何问题，请参考本指南的故障排除部分，或联系技术支持。