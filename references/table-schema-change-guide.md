# 数据表格式修改指南

本指南说明当飞书多维表格格式发生变化时，需要进行的所有修改。

## 📋 修改清单

### 1. `config.json` - 字段映射配置

**文件路径**：`config.json`

修改 `feishu.field_mapping` 部分：

```json
{
  "feishu": {
    "field_mapping": {
      "clock_in_time": "打卡时间",
      "clock_in_image": "打卡拍照",
      "month": "月度",
      "employee_name": "打卡人",
      "department": "打卡部门",
      "project_name": "打卡项目名称",
      "notes": "其他事项打卡备注",
      "clock_in_location": "打卡地点",
      "新字段key": "新字段名"
    }
  }
}
```

**说明**：
- 左侧为程序内部使用的 key（不要修改）
- 右侧为飞书多维表格的实际字段名（修改此项）
- 新增字段时，添加新的 key-value 对

---

### 2. `scripts/feishu_api.py` - 数据准备函数

**文件路径**：`scripts/feishu_api.py`

修改 `prepare_record_data()` 函数：

```python
def prepare_record_data(
    ocr_result: Dict[str, Any],
    user_name: str,
    user_department: str,
    image_file_token: Optional[str] = None,
    field_mapping: Dict[str, str] = None
) -> Dict[str, Any]:
    # ... 省略 ...
    
    record_data = {
        field_mapping.get("employee_name", "打卡人"): user_name,
        field_mapping.get("department", "打卡部门"): user_department,
        field_mapping.get("clock_in_time", "打卡时间"): clock_in_timestamp,
        field_mapping.get("month", "月度"): month_timestamp,
        field_mapping.get("project_name", "打卡项目名称"): ocr_result.get("打卡项目名称"),
        field_mapping.get("clock_in_location", "打卡地点"): ocr_result.get("打卡地点"),
        field_mapping.get("notes", "其他事项打卡备注"): ocr_result.get("其他事项"),
        # 新增字段
        field_mapping.get("新字段key", "新字段名"): "新字段值",
    }
```

**说明**：
- 只有在新增字段或修改字段逻辑时才需要修改
- 从 OCR 结果或用户信息中获取值
- 确保字段值类型符合飞书多维表格的要求

---

### 3. `scripts/ocr_service.py` - OCR 识别 Prompt（条件修改）

**文件路径**：`scripts/ocr_service.py`

**只有当新增需要从图片提取的字段时才需要修改！**

修改 OCR 识别的 prompt（约第 56-70 行）：

```python
prompt = """请仔细观察这张打卡图片，特别注意图片上的水印、时间戳、拍摄时间、地点、项目名称等信息。

请以 JSON 格式直接返回以下字段，不要有任何其他描述文字：
{
  "打卡时间": "从水印中提取的拍摄时间，格式为 YYYY/MM/DD HH:mm，例如 2026/04/09 10:59",
  "打卡地点": "从水印中提取的地点信息",
  "打卡项目名称": "从水印中提取的项目名称",
  "新字段名": "从水印中提取的新字段信息",  // 新增
  "其他事项": "其他重要信息，如天气等，没有则为空字符串",
  "raw_text": "图片中识别到的所有文字内容"
}

请确保：
- 日期格式转换：如 "2026.04.09 10:59" 转换为 "2026/04/09 10:59"
- 只返回一个纯 JSON 对象，不要有其他文字说明
- 即使某些信息缺失，也要返回完整的 JSON 结构"""
```

**是否需要修改 prompt 的判断标准**：

| 修改类型 | 是否需要改 prompt |
|---------|------------------|
| 只修改表格列名 | ❌ 不需要 |
| 新增从图片提取的字段（如天气、设备等） | ✅ 需要 |
| 新增非图片来源的字段（如用户信息、手动输入） | ❌ 不需要 |
| 删除从图片提取的字段 | ⚠️ 可选（保留不影响） |

---

### 4. `SKILL.md` - 技能配置文件

**文件路径**：`SKILL.md`

检查是否有与数据表相关的配置需要更新：

- 字段名提示
- 数据格式说明
- 示例数据

---

## 🔧 常见修改场景

### 场景 1：修改字段名（最简单）

只需要修改 `config.json`：

```json
{
  "feishu": {
    "field_mapping": {
      "employee_name": "打卡人员",  // 修改字段名
      "department": "所属部门"
    }
  }
}
```

### 场景 2：新增非图片来源字段（如用户信息）

只需修改两个文件：

**步骤 1**：`config.json` 添加映射
```json
{
  "feishu": {
    "field_mapping": {
      "phone": "联系电话"  // 新增字段
    }
  }
}
```

**步骤 2**：`feishu_api.py` 添加字段赋值
```python
record_data = {
    # ... 现有字段 ...
    field_mapping.get("phone", "联系电话"): "从用户信息或其他来源获取",
}
```

### 场景 3：新增从图片提取的字段（如天气）

需要修改三个文件：

**步骤 1**：`ocr_service.py` 修改 prompt
```python
prompt = """...
{
  "打卡时间": "...",
  "打卡地点": "...",
  "打卡项目名称": "...",
  "天气": "从水印中提取的天气信息",  // 新增
  "其他事项": "...",
  "raw_text": "..."
}
..."""
```

**步骤 2**：`config.json` 添加映射
```json
{
  "feishu": {
    "field_mapping": {
      "weather": "天气"  // 新增
    }
  }
}
```

**步骤 3**：`feishu_api.py` 添加字段赋值
```python
record_data = {
    # ... 现有字段 ...
    field_mapping.get("weather", "天气"): ocr_result.get("天气"),
}
```

### 场景 4：删除字段

需要修改两个文件：

**步骤 1**：`config.json` 移除映射
```json
{
  "feishu": {
    "field_mapping": {
      // 删除不需要的字段
    }
  }
}
```

**步骤 2**：`feishu_api.py` 移除字段赋值
```python
record_data = {
    // 删除不需要的字段
}
```

### 场景 5：修改字段类型

需要修改 `feishu_api.py` 中的字段值处理：

```python
# 例如：日期字段需要转换为时间戳
if clock_in_time:
    dt = datetime.strptime(clock_in_time, "%Y/%m/%d %H:%M")
    clock_in_timestamp = int(dt.timestamp() * 1000)
```

### 场景 6：新增特殊类型字段

飞书多维表格支持多种特殊字段类型，需要特殊处理：

#### 6.1 单选/多选字段

**飞书要求**：传入选项文本即可，飞书会自动匹配

```python
# 单选字段
record_data["打卡类型"] = "进场"  # 直接传文本

# 多选字段
record_data["标签"] = ["标签1", "标签2"]  # 传数组
```

#### 6.2 人员字段

**飞书要求**：需要传入用户 ID 格式

```python
# 人员字段
record_data["负责人"] = {
    "id": "ou_xxxxx",  # 用户 open_id
    "type": "open_id"   # ID 类型
}

# 或多人
record_data["参与人员"] = [
    {"id": "ou_xxx1", "type": "open_id"},
    {"id": "ou_xxx2", "type": "open_id"}
]
```

#### 6.3 数字字段

**飞书要求**：传入数字类型，不能是字符串

```python
# 数字字段
record_data["工时"] = 8.5  # 直接传数字，不要传字符串 "8.5"
```

#### 6.4 关联字段

**飞书要求**：需要传入关联记录的 ID

```python
# 关联字段
record_data["关联项目"] = {
    "link_record_ids": ["recXXXXXX"]  # 关联记录的 ID
}
```

### 场景 7：设置字段默认值

当字段可能为空时，需要设置合理的默认值：

```python
# 在 prepare_record_data() 中
record_data = {
    # 方式 1：使用 or 设置默认值
    field_mapping.get("notes", "备注"): ocr_result.get("其他事项") or "",
    
    # 方式 2：条件判断
    field_mapping.get("project_name", "项目名称"): 
        ocr_result.get("打卡项目名称") if ocr_result.get("打卡项目名称") else "未知项目",
}
```

### 场景 8：必填字段处理

如果表格有必填字段，需要确保数据不为空：

```python
def prepare_record_data(...):
    # ... 省略 ...
    
    # 必填字段检查
    if not user_name:
        raise ValueError("打卡人姓名不能为空")
    
    if not clock_in_time:
        # 使用当前时间作为默认值
        clock_in_timestamp = int(datetime.now().timestamp() * 1000)
```

---

## 📊 飞书字段类型对照表

| 字段类型 | 类型代码 | Python 值类型 | 示例 |
|---------|---------|--------------|------|
| 文本 | 1 | str | `"张三"` |
| 数字 | 2 | int/float | `8` 或 `8.5` |
| 单选 | 3 | str | `"进场"` |
| 多选 | 4 | list | `["标签1", "标签2"]` |
| 日期 | 5 | int (时间戳毫秒) | `1712937600000` |
| 复选框 | 7 | bool | `True` |
| 附件 | 17 | list | `[{"file_token": "xxx"}]` |
| 人员 | 11 | dict/list | `{"id": "ou_xxx", "type": "open_id"}` |
| 关联 | 18 | dict | `{"link_record_ids": ["recXXX"]}` |

---

## ✅ 验证修改

修改完成后，请按以下步骤验证：

1. **检查配置文件格式**
   ```bash
   python -m json.tool config.json
   ```

2. **测试运行**
   ```bash
   python scripts/clock_in.py --config config.json --image test.jpg --user-id ou_xxx
   ```

3. **检查飞书多维表格**
   - 确认字段是否正确映射
   - 确认数据格式是否正确
   - 确认附件是否正确上传

---

## 📚 相关文件参考

| 文件 | 说明 | 修改频率 |
|------|------|---------|
| `config.json` | 配置文件，包含字段映射 | 高 |
| `config.example.json` | 配置文件示例 | 低 |
| `scripts/feishu_api.py` | 飞书 API 模块，包含数据准备 | 中 |
| `scripts/clock_in.py` | 主程序 | 低 |
| `scripts/ocr_service.py` | OCR 服务，包含识别 prompt | 低（仅新增图片字段时） |
| `SKILL.md` | 技能配置 | 低 |
| `agent-config-guide.md` | Agent 配置指南 | 低 |

---

## 💡 常见问题

### Q: 只修改字段名需要改代码吗？

A: 不需要，只需要修改 `config.json` 中的 `field_mapping` 即可。

### Q: 新增字段需要改哪些文件？

A: 取决于字段数据来源：
- **非图片来源**（如用户信息）：改 `config.json` + `feishu_api.py`
- **图片来源**（如天气）：改 `ocr_service.py` + `config.json` + `feishu_api.py`

### Q: 字段类型是日期怎么办？

A: 需要在 `prepare_record_data()` 中将日期转换为时间戳（毫秒）。

### Q: 附件字段怎么处理？

A: 参考代码中的 `clock_in_image` 字段处理方式：
```python
record_data["打卡拍照"] = [
    {
        "file_token": image_file_token,
        "name": "打卡图片",
        "type": "file"
    }
]
```

### Q: 如何判断是否需要修改 OCR prompt？

A: 问自己：**这个字段的信息能从打卡图片中提取吗？**
- 能 → 需要修改 `ocr_service.py`
- 不能（如用户信息、手动输入）→ 不需要修改

### Q: 单选字段怎么传值？

A: 直接传选项文本即可，飞书会自动匹配：
```python
record_data["打卡类型"] = "进场"  # 直接传文本
```

### Q: 人员字段怎么传值？

A: 需要传入用户 ID 和类型：
```python
record_data["负责人"] = {"id": "ou_xxx", "type": "open_id"}
```

### Q: 字段为空时怎么办？

A: 设置合理的默认值，避免写入失败：
```python
# 文本字段：空字符串
field_mapping.get("notes", "备注"): ocr_result.get("其他事项") or ""

# 数字字段：0 或 None
field_mapping.get("hours", "工时"): ocr_result.get("工时") or 0
```

---

*最后更新时间：2026-04-12*
