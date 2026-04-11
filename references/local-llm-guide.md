# Clock-in Assistant 详细使用教程

本教程将一步一步引导您如何配置和使用 Clock-in Assistant 打卡助手，确保您能够快速上手并实现自动化打卡功能。

## 📋 教程概览

1. **环境准备** - 安装必要的软件和依赖
2. **项目配置** - 填写配置文件中的各项参数
3. **飞书设置** - 创建机器人和配置权限
4. **表格设置** - 配置飞书多维表格
5. **测试运行** - 验证功能是否正常
6. **日常使用** - 如何在群聊中使用

## 1. 环境准备

### 1.1 安装 Python

确保您的系统已安装 Python 3.8 或更高版本：

```bash
# 检查 Python 版本
python --version
```

如果未安装，请从 [Python 官网](https://www.python.org/) 下载并安装。

### 1.2 安装 Ollama

1. 从 [Ollama 官网](https://ollama.com/) 下载并安装 Ollama
2. 启动 Ollama 服务
3. 下载所需的模型：

```bash
# 打开命令行，运行以下命令
transformers-cli download Qwen/Qwen3.5-35B-A3B-v3
```

### 1.3 克隆项目

将项目克隆到您的本地目录：

```bash
git clone <项目地址>
cd skills/clock-in-assistant
```

### 1.4 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt
```

## 2. 项目配置

### 2.1 配置文件结构

打开 `config.json` 文件，您会看到以下结构：

```json
{
  "version": "1.0.0",
  "name": "clock-in-assistant-config",
  "description": "Clock-in Assistant 配置文件",
  "ocr": {...},
  "keywords": {...},
  "image": {...},
  "feishu": {...},
  "notification": {...}
}
```

### 2.2 填写图片保存路径

找到 `image` 部分，填写您希望保存打卡图片的路径：

```json
"image": {
  "save_path": "C:\\Users\\YourName\\Desktop\\打卡图片",
  "supported_formats": ["jpg", "jpeg", "png", "gif", "bmp"],
  "max_size_mb": 10
}
```

**注意**：
- Windows 路径需要使用双反斜杠 `\\`
- 确保该路径存在且有写入权限

### 2.3 配置打卡关键词

找到 `keywords` 部分，添加您需要的打卡关键词：

```json
"keywords": {
  "trigger_words": [
    "打卡",
    "我要打卡",
    "帮我打卡",
    "daka"
  ],
  "case_sensitive": false
}
```

### 2.4 配置 OCR 服务

#### 2.4.1 本地 Ollama 服务配置

如果您在本地运行了 Ollama 服务，找到 `ocr` 部分，填写本地 Ollama 服务的地址和模型：

```json
"ocr": {
  "enabled": true,
  "provider": "ollama",
  "base_url": "http://localhost:11434",  // 本地 Ollama 默认端口
  "model": "Qwen3.5-35B-A3B-v3-Q8_0.gguf",
  "timeout": 60,
  "max_retries": 3
}
```

#### 2.4.2 直接使用本地模型文件

如果您没有运行 Ollama 服务，而是直接使用本地模型文件，您需要使用其他 OCR 提供商。例如，使用 Tesseract OCR：

```json
"ocr": {
  "enabled": true,
  "provider": "tesseract",  // 切换到 Tesseract OCR
  "tesseract_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",  // Tesseract 安装路径
  "language": "chi_sim+eng",  // 中文简体 + 英文
  "timeout": 60,
  "max_retries": 3
}
```

**注意：** 使用 Tesseract OCR 需要先安装 Tesseract 软件并下载相应的语言包。

#### 2.4.3 配置说明

- **base_url**：Ollama 服务的地址，本地运行时通常为 `http://localhost:11434`
- **model**：使用的模型名称，需要确保该模型已在 Ollama 中下载
- **provider**：OCR 服务提供商，可选值：`ollama`、`tesseract`、`baidu` 等
- **timeout**：OCR 请求的超时时间（秒）
- **max_retries**：失败时的最大重试次数

### 2.5 配置飞书信息

找到 `feishu` 部分，填写以下信息：

```json
"feishu": {
  "enabled": true,
  "app_id": "your_app_id",
  "app_secret": "your_app_secret",
  "bitable": {
    "app_token": "your_app_token",
    "table_id": "your_table_id",
    "view_id": ""
  },
  "field_mapping": {
    "clock_in_time": "打卡时间",
    "clock_in_image": "打卡拍照",
    "month": "月度",
    "employee_name": "打卡人",
    "department": "打卡部门",
    "entry_exit_type": "进/出场及打卡分类",
    "project_name": "打卡项目名称",
    "notes": "其他事项打卡备注",
    "clock_in_location": "打卡地点"
  }
}
```

## 3. 飞书设置

### 3.1 创建飞书应用

1. 登录 [飞书开放平台](https://open.feishu.cn/)
2. 点击「创建企业自建应用」
3. 填写应用名称（如「打卡助手」）和描述
4. 点击「创建」

### 3.2 添加权限

#### 方法一：手动添加

1. 在应用详情页，点击「权限管理」
2. 添加以下权限：
   - `im.message:readonly` - 读取消息
   - `im.file:readonly` - 下载文件
   - `bitable:app` - 操作多维表格
   - `contact:user.readonly` - 读取用户信息
3. 点击「批量申请」并提交

#### 方法二：一键导入

复制以下 JSON 配置，在飞书开放平台的「权限管理」页面点击「批量导入」，粘贴并提交：

```json
{
  "scopes": {
    "tenant": [
      "aily:message:read",
      "aily:message:write",
      "bitable:app",
      "contact:user.base:readonly",
      "contact:user.employee_id:readonly",
      "drive:file",
      "im:message",
      "im:message.group_at_msg:readonly",
      "im:message:send_as_bot"
    ],
    "user": []
  }
}
```

**说明**：以上权限包含了打卡助手所需的所有最少权限，确保机器人能够正常运行。如果需要，请酌情添加。

### 3.3 获取凭证

1. 在应用详情页，点击「凭证与基础信息」
2. 复制 `App ID` 和 `App Secret`，填写到 `config.json` 中

### 3.4 事件配置

1. 在应用详情页，点击「订阅方式」
2. 使用长连接接收事件
3. 点击「保存」

### 3.5 配置事件订阅

1. 在应用详情页，点击「事件订阅」
2. 启用事件订阅
3. 填写「请求 URL」（根据您的服务器地址设置）
4. 添加 `im.message.receive_v1` 事件
5. 点击「保存」

## 4. 表格设置

### 4.1 创建多维表格

1. 打开飞书，点击「多维表格」
2. 点击「新建」→「从模板创建」→「空白表格」
3. 给表格命名（如「打卡记录」）

### 4.2 添加列

在表格中添加以下列：

| 列名 | 字段类型 | 说明 |
|------|---------|------|
| 打卡时间 | 日期时间 | 存储打卡时间 |
| 打卡拍照 | 附件 | 存储打卡图片 |
| 月度 | 文本 | 存储月份（格式：2026-01） |
| 打卡人 | 文本 | 存储打卡人姓名 |
| 打卡部门 | 文本 | 存储打卡人部门 |
| 进/出场及打卡分类 | 文本 | 暂不使用 |
| 打卡项目名称 | 文本 | 存储项目名称 |
| 其他事项打卡备注 | 多行文本 | 存储备注信息 |
| 打卡地点 | 文本 | 存储打卡地点 |

### 4.3 获取表格信息

1. 打开表格，点击右上角「分享」→「复制链接」→「在浏览器打开」
2. 从浏览器地址栏中提取信息：
   - `app_token` - 链接中 `base/` 后面的部分
   - `table_id` - 链接中 `table=` 后面的部分
3. 将这些信息填写到 `config.json` 中

## 5. 测试运行

### 5.1 验证 Ollama 服务

```bash
# 测试 Ollama 服务是否正常
python -c "
from scripts.ocr_service import create_ocr_service
import json

config = json.load(open('config.json'))
ocr = create_ocr_service(config)
print('OCR 服务连接:', '成功' if ocr.test_connection() else '失败')
"
```

### 5.2 测试完整流程

```bash
# 使用测试图片运行完整流程
python scripts/clock_in.py \
  --config config.json \
  --image <测试图片路径> \
  --user-name "测试用户" \
  --department "测试部门" \
  --verbose
```

### 5.3 在飞书群聊中测试

1. 将机器人添加到群聊
2. 上传一张打卡图片
3. 发送消息：`打卡 @机器人`
4. 观察机器人的回复

## 6. 日常使用

### 6.1 员工打卡流程

1. 员工在群聊中上传打卡图片
2. 员工发送消息：`打卡 @机器人`
3. 机器人自动处理：
   - 下载图片到指定目录
   - 使用 Ollama 进行 OCR 识别
   - 从飞书获取用户信息
   - 写入多维表格
   - 回复：`@用户姓名，✅ 打卡完成！`

### 6.2 管理员查看记录

1. 打开飞书多维表格
2. 查看打卡记录
3. 可以根据需要进行筛选和统计

### 6.3 图片管理

1. 打开配置的图片保存目录
2. 查看所有打卡图片
3. 图片命名格式：`clock_in_时间戳_用户姓名.jpg`

## 7. 故障排除

### 7.1 常见错误及解决方案

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `无法连接到 OCR 服务` | Ollama 服务未运行 | 启动 Ollama 服务 |
| `图片下载失败` | 网络问题或权限不足 | 检查网络连接和路径权限 |
| `飞书 API 调用失败` | app_id 或 app_secret 错误 | 检查配置文件中的凭证 |
| `表格写入失败` | 表格权限不足或列名不匹配 | 检查机器人权限和表格列名 |

### 7.2 日志查看

```bash
# 查看详细日志
python scripts/clock_in.py \
  --config config.json \
  --image <图片路径> \
  --user-name "测试用户" \
  --verbose
```

## 8. 最佳实践

1. **定期备份**：定期备份打卡图片和表格数据
2. **权限管理**：仅授予必要的权限给机器人
3. **图片质量**：确保打卡图片清晰，便于 OCR 识别
4. **网络稳定**：确保服务器网络稳定，避免打卡失败
5. **定期检查**：定期检查 OCR 服务和飞书 API 连接状态

## 🎉 完成！

恭喜您成功配置并使用 Clock-in Assistant 打卡助手！现在您可以享受自动化打卡带来的便利了。

如果您在使用过程中遇到任何问题，请参考本教程的故障排除部分，或联系技术支持。