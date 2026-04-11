"""
Feishu API Module
飞书 API 模块 - 封装飞书多维表格操作
"""
import json

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeishuBitableAPI:
    """飞书多维表格 API 类"""

    def __init__(
        self, 
        app_token: str, 
        table_id: str, 
        view_id: Optional[str] = None,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None
    ):
        self.app_token = app_token
        self.table_id = table_id
        self.view_id = view_id
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = "https://open.feishu.cn/open-apis/bitable/v1"
        self.client = httpx.Client(timeout=30)
        self.access_token = None
        self._token_expire_time = 0

    def __del__(self):
        self.client.close()

    def get_tenant_access_token(self) -> str:
        """
        自动获取 tenant_access_token
        
        Returns:
            tenant_access_token
        """
        if not self.app_id or not self.app_secret:
            raise ValueError("未配置 app_id 或 app_secret，无法自动获取令牌")
        
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        
        if result.get("code") != 0:
            raise ValueError(f"获取令牌失败: {result.get('msg')}")
        
        token = result.get("tenant_access_token")
        expire = result.get("expire", 7200)
        
        logger.info(f"成功获取 tenant_access_token，有效期 {expire} 秒")
        
        return token

    def ensure_access_token(self):
        """确保有有效的访问令牌"""
        if not self.access_token:
            self.access_token = self.get_tenant_access_token()
            logger.info("已自动获取访问令牌")

    def set_access_token(self, token: str):
        """设置访问令牌"""
        self.access_token = token

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        self.ensure_access_token()
        if not self.access_token:
            raise ValueError("未设置 access_token，请先调用 set_access_token 或配置 app_id/app_secret")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_table_fields(self) -> List[Dict[str, Any]]:
        """获取表格字段列表"""
        url = f"{self.base_url}/apps/{self.app_token}/tables/{self.table_id}/fields"
        response = self.client.get(url, headers=self._get_headers())
        response.raise_for_status()
        result = response.json()
        return result.get("data", {}).get("items", [])

    def create_field(self, field_name: str, field_type: int = 1) -> Dict[str, Any]:
        """
        创建新字段
        
        Args:
            field_name: 字段名称
            field_type: 字段类型 (1=文本, 2=数字, 3=单选, 4=多选, 5=日期, 7=复选框, 
                                  11=人员, 13=电话号码, 15=URL, 17=附件, 18=关联, 
                                  19=公式, 20=双向关联, 21=位置, 22=群组, 1001=创建时间,
                                  1002=修改时间, 1003=创建人, 1004=修改人, 1005=自动编号)
        """
        url = f"{self.base_url}/apps/{self.app_token}/tables/{self.table_id}/fields"
        payload = {
            "field_name": field_name,
            "type": field_type
        }
        response = self.client.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info(f"创建字段成功: {field_name}")
        return result.get("data", {})

    def add_record(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加一条记录
        
        Args:
            fields: 字段值字典，key 为字段名，value 为字段值
        """
        url = f"{self.base_url}/apps/{self.app_token}/tables/{self.table_id}/records"
        
        field_values = {}
        for field_name, field_value in fields.items():
            if field_value is not None:
                field_values[field_name] = field_value
        
        payload = {
            "fields": field_values
        }
        
        response = self.client.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"添加记录成功: {result.get('data', {}).get('record', {}).get('record_id')}")
        return result.get("data", {})


    def upload_file(self, file_path: str) -> str:
        """
        上传文件到飞书
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件 token
        """
        self.ensure_access_token()
        url = "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all"
        
        import os
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f, "image/jpeg")}
            data = {
                "parent_type": "bitable_image",
                "parent_node": self.app_token,
                "size": str(file_size),
                "file_name": file_name
            }
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.client.post(url, headers=headers, files=files, data=data)
            try:
                response.raise_for_status()
            except Exception as e:
                logger.error(f"文件上传失败: {response.text}")
                raise
            result = response.json()
            
        file_token = result.get("data", {}).get("file_token")
        logger.info(f"文件上传成功: {file_token}")
        return file_token

    def get_user_info(self, user_id: Optional[str] = None, union_id: Optional[str] = None, user_id_type: str = "open_id") -> Dict[str, Any]:
        """
        获取飞书用户信息
        
        Args:
            user_id: 用户 open_id (可选)
            union_id: 用户 union_id (可选)
            user_id_type: 用户 ID 类型，"open_id" 或 "union_id"
            
        Returns:
            用户信息字典，包含 name, en_name, avatar_url, department_ids 等字段
        """
        self.ensure_access_token()
        
        if not user_id and not union_id:
            raise ValueError("必须提供 user_id 或 union_id")
        
        if user_id:
            target_id = user_id
            id_type = user_id_type  # 默认为 "open_id"
        elif union_id:
            target_id = union_id
            id_type = "union_id"
        else:
            raise ValueError("必须提供 user_id 或 union_id")
        
        user_info = {}
        
        # 步骤 1：尝试使用单个用户信息 API（可能获取到最新信息）
        single_user_url = f"https://open.feishu.cn/open-apis/contact/v3/users/{target_id}"
        single_user_params = {"user_id_type": id_type}
        
        try:
            single_response = self.client.get(single_user_url, headers=self._get_headers(), params=single_user_params)
            single_response.raise_for_status()
            single_result = single_response.json()
            
            if single_result.get("code") == 0:
                user_info = single_result.get("data", {}).get("user", {})
                if user_info:
                    logger.info(f"成功获取用户信息（单个 API）: {user_info.get('name')}")
        except Exception as e:
            logger.warning(f"单个用户 API 失败: {e}")
        
        # 步骤 2：如果单个 API 失败，尝试使用 batch API
        if not user_info:
            batch_url = "https://open.feishu.cn/open-apis/contact/v3/users/batch"
            # 飞书 API 要求 user_ids 是逗号分隔的字符串
            batch_params = {"user_ids": target_id, "user_id_type": id_type}
            
            try:
                logger.info(f"批量用户 API 请求: {batch_url}, 参数: {batch_params}")
                batch_response = self.client.get(batch_url, headers=self._get_headers(), params=batch_params)
                logger.info(f"批量用户 API 响应状态: {batch_response.status_code}")
                if batch_response.status_code != 200:
                    logger.error(f"批量用户 API 响应内容: {batch_response.text}")
                batch_response.raise_for_status()
                batch_result = batch_response.json()
                
                if batch_result.get("code") == 0:
                    users = batch_result.get("data", {}).get("items", [])
                    if users:
                        user_info = users[0]
                        logger.info(f"成功获取用户信息（批量 API）: {user_info.get('name')}")
                else:
                    logger.error(f"批量用户 API 错误: {batch_result.get('msg')}")
            except Exception as e:
                logger.error(f"批量用户 API 失败: {e}")
        
        if user_info:
            return user_info
        
        logger.warning("未找到用户信息")
        return {}

    def get_user_departments(self, department_ids: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取部门信息
        
        Args:
            department_ids: 部门 ID 列表
            
        Returns:
            部门信息列表
        """
        if not department_ids:
            return []
        
        self.ensure_access_token()
        departments = []
        
        for dept_id in department_ids:
            url = f"https://open.feishu.cn/open-apis/contact/v3/departments/{dept_id}"
            response = self.client.get(url, headers=self._get_headers(), params={"department_id_type": "open_department_id"})
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    dept_data = result.get("data", {}).get("department", {})
                    departments.append(dept_data)
        
        return departments


def prepare_record_data(
    ocr_result: Dict[str, Any],
    user_name: str,
    user_department: str,
    image_file_token: Optional[str] = None,
    field_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    准备要写入多维表格的记录数据
    
    Args:
        ocr_result: OCR 识别结果
        user_name: 用户姓名
        user_department: 用户部门
        image_file_token: 图片文件 token
        field_mapping: 字段映射配置
        
    Returns:
        准备好的字段数据字典
    """
    if field_mapping is None:
        field_mapping = {
            "clock_in_time": "打卡时间",
            "clock_in_image": "打卡拍照",
            "month": "月度",
            "employee_name": "打卡人",
            "department": "打卡部门",
            "project_name": "打卡项目名称",
            "notes": "其他事项打卡备注",
            "clock_in_location": "打卡地点"
        }

    clock_in_time = ocr_result.get("打卡时间")
    
    clock_in_timestamp = None
    month_timestamp = None
    if clock_in_time:
        try:
            dt = datetime.strptime(clock_in_time, "%Y/%m/%d %H:%M")
            clock_in_timestamp = int(dt.timestamp() * 1000)
            month_dt = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_timestamp = int(month_dt.timestamp() * 1000)
        except:
            dt = datetime.now()
            clock_in_timestamp = int(dt.timestamp() * 1000)
            month_dt = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_timestamp = int(month_dt.timestamp() * 1000)
    else:
        dt = datetime.now()
        clock_in_timestamp = int(dt.timestamp() * 1000)
        month_dt = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_timestamp = int(month_dt.timestamp() * 1000)

    record_data = {
        field_mapping.get("employee_name", "打卡人"): user_name,
        field_mapping.get("department", "打卡部门"): user_department,
        field_mapping.get("clock_in_time", "打卡时间"): clock_in_timestamp,
        field_mapping.get("month", "月度"): month_timestamp,
        field_mapping.get("project_name", "打卡项目名称"): ocr_result.get("打卡项目名称"),
        field_mapping.get("clock_in_location", "打卡地点"): ocr_result.get("打卡地点"),
        field_mapping.get("notes", "其他事项打卡备注"): ocr_result.get("其他事项"),
    }

    if image_file_token:
        record_data[field_mapping.get("clock_in_image", "打卡拍照")] = [
            {
                "file_token": image_file_token,
                "name": "打卡图片",
                "type": "file"
            }
        ]

    record_data = {k: v for k, v in record_data.items() if v is not None}
    
    logger.info(f"准备记录数据: {record_data}")
    return record_data


def create_feishu_api(config: Dict[str, Any]) -> FeishuBitableAPI:
    """根据配置创建飞书 API 实例"""
    feishu_config = config.get("feishu", {})
    bitable_config = feishu_config.get("bitable", {})
    return FeishuBitableAPI(
        app_token=bitable_config.get("app_token", ""),
        table_id=bitable_config.get("table_id", ""),
        view_id=bitable_config.get("view_id"),
        app_id=feishu_config.get("app_id"),
        app_secret=feishu_config.get("app_secret")
    )
