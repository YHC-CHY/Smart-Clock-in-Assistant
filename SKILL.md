---
name: clock-in-assistant
description: 帮助管理者自动化管理员工打卡信息的录入。当用户在飞书群聊中上传打卡图片、发送打卡关键词并@机器人时触发。自动下载图片、通过本地Ollama大模型识别文字、将打卡人信息、所属部门及图片写入飞书多维表格。
metadata:
  copaw:
    emoji: "⏰"
---

# Clock-in Assistant（打卡助手 V1.0.0）

## 什么时候用

当用户在飞书群聊中**上传打卡图片**、**发送打卡关键词**并**@机器人**时，使用本 skill。

### 触发条件
- ✅ 用户在飞书群聊中上传图片
- ✅ 用户发送打卡关键词（见下方配置）
- ✅ 用户@机器人
- 同时满足以上三个条件时触发

### 应该使用
- 员工上传打卡截图并@机器人
- 需要自动处理打卡信息录入
- 需要将打卡数据写入飞书多维表格

### 不应使用
- 只是简单的对话，没有上传打卡图片
- 用户没有@机器人
- 图片与打卡无关

## 工作流程

```
1. 检测触发条件：用户上传图片 + 打卡关键词 + @机器人
2. 静默执行：下载打卡图片到指定文件夹
3. 静默执行：调用本地Ollama大模型进行OCR识别
4. 静默执行：从飞书用户信息中获取打卡人姓名和所属部门
5. 静默执行：将打卡人信息、所属部门、OCR识别结果、打卡图片写入飞书多维表格
6. 完成后：在群聊中@打卡人，发送简洁的打卡完成提示
```

## 核心功能

### 1. 图片下载
将用户上传的打卡图片保存到指定的文件夹路径。

### 2. OCR文字识别（本地Ollama大模型）
使用本地部署的Ollama大模型提取打卡图片中的关键信息：
- 打卡时间
- 打卡地点
- 员工姓名
- 其他打卡相关信息

**OCR配置：**（详见 `config.json` → `ocr` 字段）
- 服务地址：`config.ocr.base_url`
- 模型ID：`config.ocr.model`
- 超时时间：`config.ocr.timeout`（秒）
- 最大重试次数：`config.ocr.max_retries`

### 3. 飞书多维表格写入
将以下信息写入飞书多维表格：
- 打卡时间：从图片提取，格式为 2026/01/08 14:00
- 打卡拍照：用户上传的打卡图片（附件）
- 月度：根据打卡时间自动生成，格式为 2026-01
- 打卡人：发起打卡的用户姓名
- 打卡部门：发起打卡的用户所在部门
- 进/出场及打卡分类：暂不填写
- 打卡项目名称：从图片提取
- 其他事项打卡备注：从图片提取（去除时间和项目名称）
- 打卡地点：从图片提取（地点或经纬度）

## 使用示例

### 场景1：员工打卡
**用户输入（飞书群聊）：**
```
[上传打卡截图]
打卡 @机器人
```

**执行流程：**
```
1. 静默执行：检测到打卡图片 + "打卡"关键词 + @机器人，触发打卡流程，不说话
2. 静默执行：下载图片到 [自定义图片保存路径]，不说话
3. 静默执行：调用 OCR 服务（`config.ocr.base_url`）进行识别，不说话
4. 静默执行：从飞书用户信息中获取姓名和部门，不说话
5. 静默执行：将所有信息写入飞书多维表格，不说话
6. 所有流程完成后，返回成功提示："@{user_name}，✅ 打卡完成！"或者失败提示："@{user_name}，❌ 打卡失败！失败原因！".
7. 请严格遵照！机器人只能在流程结束后，直接在群聊中输出"@{user_name}，✅ 打卡完成！"或者"@{user_name}，❌ 打卡失败！失败原因！".绝对不能输出其他任何一个字符！
```

---

## ⚙️ 配置项（请根据实际情况填写）

### 1. 打卡关键词列表
**配置来源：** `config.json` → `keywords.trigger_words`

当前配置的关键词：
- `config.keywords.trigger_words` 数组中的所有关键词（如：打卡、签到等）

**如需修改：** 请直接编辑 `config.json` 中的 `keywords.trigger_words` 数组

### 2. 图片保存路径
**配置来源：** `config.json` → `image.save_path`

**当前配置：**
- 保存路径：`config.image.save_path`
- 支持格式：`config.image.supported_formats`（如：jpg, jpeg, png, gif, bmp）
- 最大文件大小：`config.image.max_size_mb` MB

**如需修改：** 请直接编辑 `config.json` 中的 `image` 字段

### 3. 飞书多维表格配置

**配置来源：** `config.json` → `feishu` 字段

#### 3.1 多维表格访问信息
- App Token：`config.feishu.bitable.app_token`
- Table ID：`config.feishu.bitable.table_id`
- View ID：`config.feishu.bitable.view_id`（可选）

#### 3.2 字段映射配置
字段映射由 `config.feishu.field_mapping` 定义，映射关系如下：

| 数据项 | 飞书表格列名 | 配置字段 |
|--------|-------------|---------|
| 打卡时间 | `field_mapping.clock_in_time` | 日期时间 |
| 打卡拍照 | `field_mapping.clock_in_image` | 附件 |
| 月度 | `field_mapping.month` | 文本 |
| 打卡人 | `field_mapping.employee_name` | 文本 |
| 打卡部门 | `field_mapping.department` | 文本 |
| 进/出场及打卡分类 | `field_mapping.entry_exit_type` | 文本 |
| 打卡项目名称 | `field_mapping.project_name` | 文本 |
| 其他事项打卡备注 | `field_mapping.notes` | 多行文本 |
| 打卡地点 | `field_mapping.clock_in_location` | 文本 |

**字段设置：**（详见 `config.feishu.field_settings`）
- 打卡时间格式：`field_settings.clock_in_time.format`
- 月度格式：`field_settings.month.format`（自动从打卡时间生成）
- 进/出场及打卡分类：`field_settings.entry_exit_type.enabled` 控制是否启用

### 4. OCR 配置
**配置来源：** `config.json` → `ocr` 字段

配置项包括：
- 服务地址：`config.ocr.base_url`
- 模型ID：`config.ocr.model`
- 超时时间：`config.ocr.timeout`
- 最大重试次数：`config.ocr.max_retries`

**如需修改：** 请直接编辑 `config.json` 中的 `ocr` 字段

---

## 注意事项

1. **确保图片清晰**：OCR识别需要清晰的图片才能准确提取信息
2. **飞书权限**：确保飞书机器人有以下权限：
   - 读取群聊消息
   - 下载图片
   - 写入多维表格
3. **OCR服务**：确保 `config.ocr.base_url` 配置的服务可正常访问
4. **图片备份**：建议定期备份打卡图片文件夹

## 常见问题

**Q: OCR服务连接失败怎么办？**
A: 请检查：
1. 网络是否能访问 `config.ocr.base_url` 配置的地址
2. OCR服务是否正常运行
3. 模型 `config.ocr.model` 是否已下载

**Q: 飞书多维表格写入失败怎么办？**
A: 请检查：
1. 机器人是否有表格的编辑权限
2. 表格列名配置是否正确
3. 表格是否存在且可访问

**Q: 如何添加新的打卡关键词？**
A: 在 `config.json` 的 `keywords.trigger_words` 数组中添加新关键词即可。

**Q: 支持哪些图片格式？**
A: 支持 `config.image.supported_formats` 中配置的格式（如：JPG、PNG、GIF、BMP 等）。

---

## 🔧 执行方式

当触发条件满足时，执行以下 Python 脚本：

### 基本命令

```bash
python scripts/clock_in.py \
  --config config.json \
  --image <图片路径> \
  --user-id <飞书用户 user_id>
```

### 或使用 union_id

```bash
python scripts/clock_in.py \
  --config config.json \
  --image <图片路径> \
  --union-id <飞书用户 union_id>
```

### 兼容旧命令（手动指定用户信息）

```bash
python scripts/clock_in.py \
  --config config.json \
  --image <图片路径> \
  --user-name <用户姓名> \
  --department <用户部门>
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--config, -c` | 否 | 配置文件路径，默认为 `config.json` |
| `--image, -i` | 是 | 打卡图片本地路径 |
| `--image-url, -u` | 否 | 打卡图片 URL（如提供，将自动下载） |
| `--user-id` | 否* | 飞书用户 user_id（推荐使用，自动获取真实用户信息） |
| `--union-id` | 否* | 飞书用户 union_id（推荐使用，自动获取真实用户信息） |
| `--user-name, -n` | 否 | 打卡人姓名（可选，如果提供 user-id 会从飞书获取） |
| `--department, -d` | 否 | 打卡人部门（可选，如果提供 user-id 会从飞书获取，无部门信息则留空） |
| `--verbose, -v` | 否 | 显示详细日志 |

**注意：**
- 至少需要提供 `--user-id` 或 `--union-id` 或 `--user-name`
- 推荐使用 `--user-id` 或 `--union-id`，这样会从飞书获取真实的用户姓名和部门信息
- 部门信息如果无法获取，则留空（不胡编乱造）

### 执行示例

#### 示例 1：使用用户 ID 获取真实信息（推荐）

```bash
python scripts/clock_in.py \
  --config config.json \
  --image ./clock_in_images/20260411_090000.jpg \
  --user-id "ou_xxxxxxxxxx"
```

#### 示例 2：使用 union_id

```bash
python scripts/clock_in.py \
  --config config.json \
  --image ./clock_in_images/20260411_090000.jpg \
  --union-id "on_xxxxxxxxxx"
```

#### 示例 3：手动指定用户信息（兼容旧版本）

```bash
python scripts/clock_in.py \
  --config config.json \
  --image ./clock_in_images/20260411_090000.jpg \
  --user-name "张三" \
  --department "技术部"
```

#### 示例 4：使用图片 URL + 用户 ID

```bash
python scripts/clock_in.py \
  --config config.json \
  --image-url "https://example.com/clock_in.jpg" \
  --user-id "ou_xxxxxxxxxx"
```

### 返回结果

脚本执行成功后，返回json对象，**仅将 `message` 字段的内容返回给用户**，不添加任何额外信息。

**脚本执行成功返回示例：**
```json
{
  "success": true,
  "message": "<at user_id=\"ou_123456\"></at>，✅ 打卡完成！",
  "data": {}
}
```

**脚本执行失败返回示例：**
```json
{
  "success": false,
  "message": "<at user_id=\"ou_123456\"></at>，❌ 打卡失败！无法连接到 OCR 服务！",
  "data": {}
}
```

### 用户收到提示模板

在群聊中，打卡完成后，机器人会@打卡人发送简洁的提示：

**成功提示：**
```
<at user_id="ou_123456"></at>，✅ 打卡完成！
```

**失败提示：**
```
<at user_id="ou_123456"></at>，❌打卡失败！错误原因！
```

**注意：**
- 提示信息保持**绝对简洁**，只包含必要的确认信息
- 不添加任何额外的说明、版本信息或询问
- 只返回 `message` 字段的内容，不显示 JSON 结构
- 不在消息中包含识别结果、版本验证等信息
- 飞书群聊会自动将`<at user_id="ou_123456"></at>，✅ 打卡完成！`转换为群聊支持的格式，确保@打卡人，并提示打卡成功。



---

## 📁 文件结构

```
skills/clock-in-assistant/
├── SKILL.md              # 本文件 - AI 助手指导文档
├── config.json           # 配置文件
├── README.md             # 使用说明
└── scripts/              # 执行脚本目录
    ├── __init__.py       # 模块初始化
    ├── clock_in.py       # 主执行脚本
    ├── ocr_service.py    # OCR 服务封装
    └── feishu_api.py     # 飞书 API 封装
└── references/             # 参考文档目录
    ├── agent-config-guide.md       # 智能体配置文件指南
    ├── local-llm-guide.md    # 本地模型配置指南
    └── cloud-llm-guide.md     # 云端模型配置指南
```

---

## 🧪 测试

### 测试 OCR 服务连接

```bash
python -c "
from scripts.ocr_service import create_ocr_service
import json

config = json.load(open('config.json'))
ocr = create_ocr_service(config)
print('OCR 服务连接:', '成功' if ocr.test_connection() else '失败')
"
```

### 测试完整流程

```bash
python scripts/clock_in.py \
  --config config.json \
  --image <测试图片路径> \
  --user-name "测试用户" \
  --department "测试部门" \
  --verbose
```
