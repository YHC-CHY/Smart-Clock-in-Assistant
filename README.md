# Clock-in Assistant 打卡助手

## 📋 项目简介

Clock-in Assistant 是一个基于飞书 和 Ollama 本地大模型的自动化打卡工具，用于打卡管理。当用户在飞书群聊中上传打卡图片并@机器人时，系统会自动处理图片、识别信息并写入飞书多维表格。

### 核心功能

- 👤 **用户信息获取**：从飞书 API 获取打开用户的姓名和部门
- 📸 **自动图片处理**：下载并保存打卡图片到自定义文件夹
- 🔍 **OCR 文字识别**：使用本地 Ollama 大模型提取图片中的打卡信息
- 📊 **飞书多维表格集成**：自动将打卡数据写入飞书多维表格
- 💬 **简洁反馈**：打卡完成后向打卡人发送简洁的成功/失败提示

## 🚀 快速开始

### 1. 环境要求

- **Python 3.8+**
- **飞书开发者账号**（用于创建机器人和获取 API 权限）
- **Ollama 本地大模型**
- **网络连接**（用于访问飞书 API）

### 2. 安装依赖

```bash
# 进入项目目录
cd skills/clock-in-assistant

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置文件设置

编辑 `config.json` 文件，填写以下信息：

#### 3.1 图片保存路径

```json
"image": {
  "save_path": "C:\\Users\\A\\Desktop\\打卡图片", //打卡图片保存路径,可自定义，请确保正确使用地址分隔符
  "supported_formats": ["jpg", "jpeg", "png", "gif", "bmp"], //支持的图片格式
   "max_size_mb": 10 //最大图片大小，单位 MB
}
```

#### 3.2 飞书配置

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

#### 3.3 OCR 配置

```json
"ocr": {
  "enabled": true,
  "provider": "ollama",
  "base_url": "你的大模型地址",
  "model": "模型名称",
  "timeout": 60, //调用 Ollama 大模型进行图片文字识别时，最多等待 60 秒，超过这个时间就会报超时错误
  "max_retries": 3 //最大重试次数。如果识别失败，会尝试重试 3 次。
}
```

### 4. 飞书机器人设置

1. **创建飞书应用**：登录 [飞书开放平台](https://open.feishu.cn/) 创建企业自建应用
2. **添加权限(具体权限参考 references/local-llm-guide.md 中的权限说明)**：
   - `im.message:readonly`（读取消息）
   - `im.file:readonly`（下载文件）
   - `bitable:app`（操作多维表格）
   - `contact:user.readonly`（读取用户信息）
3. **获取凭证**：在应用详情页获取 `app_id` 和 `app_secret`
4. **配置事件订阅**：设置消息接收地址，用于接收群聊消息

### 5. 飞书多维表格设置

1. **创建表格**：在飞书创建一个多维表格
2. **添加列**：创建以下列：
   - 打卡时间（日期时间）
   - 打卡拍照（附件）
   - 月度（文本）
   - 打卡人（文本）
   - 打卡部门（文本）
   - 进/出场及打卡分类（文本,可改为单选，通过用户打卡填写表单获取）
   - 打卡项目名称（文本）
   - 其他事项打卡备注（多行文本）
   - 打卡地点（文本）
3. **获取表格信息**：从表格 URL 中提取 `app_token` 和 `table_id`

### 6. 使用方法

在飞书群聊中：
1. 上传打卡图片
2. 发送消息：`打卡 @机器人`
3. 机器人会自动处理并回复：`@用户，✅ 打卡完成！` 或 `@用户，❌ 打卡失败！错误原因！`

## 📁 项目结构

```
skills/clock-in-assistant/
├── README.md              # 本文件 - 项目说明
├── SKILL.md              # Skill 定义和使用说明
├── config.json           # 配置文件
├── scripts/              # 执行脚本目录
│   ├── __init__.py       # 模块初始化
│   ├── clock_in.py       # 主执行脚本
│   ├── ocr_service.py    # OCR 服务封装
│   └── feishu_api.py     # 飞书 API 封装
└── references/           # 参考文档
    ├── agent-config-guide.md       # 智能体配置文件指南
    ├── local-llm-guide.md       # 本地模型配置指南
    └── cloud-llm-guide.md # 云端模型配置指南
```

## 🔧 配置检查清单

- [ ] 图片保存路径已填写，且文件夹存在
- [ ] 飞书 `app_id` 和 `app_secret` 已配置
- [ ] 飞书多维表格 `app_token` 和 `table_id` 已填写
- [ ] 飞书机器人权限已配置
- [ ] Ollama 服务可正常访问
- [ ] 表格列名与配置一致

## ❓ 常见问题

**Q: 打卡失败怎么办？**
A: 检查以下几点：
1. 网络连接是否正常
2. 飞书机器人权限是否完整
3. Ollama 服务是否运行
4. 表格列名是否与配置一致

**Q: 图片没有保存到指定目录？**
A: 检查：
1. 保存路径是否存在且有写入权限
2. 路径格式是否正确（Windows 使用双反斜杠）

**Q: 如何使用云端大模型替代 Ollama？**
A: 参考 `references/cloud-llm-guide.md` 文档

**Q: 提示打卡成功，但是并没有写入表格？**
A: 检查：
1. 飞书多维表格 `app_token` 和 `table_id` 是否填写正确
2. 表格列名是否与配置一致
3. 表格是否有写入权限
4. Ollama 服务是否运行
5. 确保Agent在处理打卡任务时，正确调用了本Skill，Agent可能会自行使用其他工具处理打卡任务，可在Agent的profile.md或者memory.md中进行强制限制。


## 📖 参考文档

- [本地大模型配置指南](references/local-llm-guide.md)
- [云端大模型配置指南](references/cloud-llm-guide.md)
- [智能体配置文件指南](references/agent-config-guide.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 📄 许可证

本项目采用 MIT 许可证。