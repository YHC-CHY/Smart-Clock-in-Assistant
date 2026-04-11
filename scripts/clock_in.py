#!/usr/bin/env python3
"""
Clock-in Assistant Main Script
打卡助手主脚本 - 处理打卡图片并写入飞书多维表格
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from ocr_service import create_ocr_service
from feishu_api import create_feishu_api, prepare_record_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_image_directory(save_path: str) -> Path:
    """确保图片保存目录存在"""
    path = Path(save_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def download_image(image_url: str, save_path: str, access_token: str = None, user_name: str = None) -> str:
    """
    下载图片到本地
    
    Args:
        image_url: 图片 URL
        save_path: 保存路径
        access_token: 飞书访问令牌（用于访问飞书临时 URL）
        user_name: 用户姓名（用于图片命名）
        
    Returns:
        本地图片路径
    """
    import httpx
    
    save_dir = ensure_image_directory(save_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if user_name:
        # 移除可能导致文件名问题的字符
        safe_user_name = "".join(c for c in user_name if c.isalnum() or c in "_- ")
        filename = f"clock_in_{timestamp}_{safe_user_name}.jpg"
    else:
        filename = f"clock_in_{timestamp}.jpg"
    file_path = save_dir / filename
    
    # 构建请求头
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    # 禁用 SSL 证书验证（仅用于测试环境）
    client = httpx.Client(timeout=30, headers=headers, verify=False)
    try:
        response = client.get(image_url)
        response.raise_for_status()
        
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        logger.info(f"图片下载成功: {file_path}")
        return str(file_path)
    except Exception as e:
        logger.error(f"图片下载失败: {e}")
        raise
    finally:
        client.close()


def process_clock_in(
    config: Dict[str, Any],
    image_path: str,
    user_name: Optional[str] = None,
    user_department: Optional[str] = None,
    user_id: Optional[str] = None,
    union_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    处理打卡流程
    
    Args:
        config: 配置字典
        image_path: 图片路径
        user_name: 用户姓名 (可选，如果提供 user_id 会从飞书获取)
        user_department: 用户部门 (可选)
        user_id: 飞书用户 open_id (可选，用于获取真实用户信息)
        union_id: 飞书用户 union_id (可选，用于获取真实用户信息)
        
    Returns:
        处理结果
    """
    result = {
        "success": False,
        "message": "",
        "data": {}  # 保持 data 为空，避免机器人生成详细响应
    }
    
    try:
        feishu_api = create_feishu_api(config)
        
        # 如果提供了用户 ID，优先从飞书获取真实用户信息
        if user_id or union_id:
            logger.info("从飞书获取用户信息...")
            user_info = feishu_api.get_user_info(user_id=user_id, union_id=union_id)
            
            if user_info:
                # 使用飞书 API 获取的真实用户姓名
                if not user_name:
                    user_name = user_info.get("name")
                    logger.info(f"获取到用户姓名: {user_name}")
                
                # 获取用户部门信息
                if not user_department:
                    department_ids = user_info.get("department_ids", [])
                    if department_ids:
                        departments = feishu_api.get_user_departments(department_ids)
                        if departments:
                            # 取第一个部门
                            user_department = departments[0].get("name")
                            logger.info(f"获取到用户部门: {user_department}")
                    else:
                        user_department = ""  # 没有部门就留空
        
        # 确保有用户姓名
        if not user_name:
            raise ValueError("无法获取用户姓名，请提供 user_id 或 user_name 参数")
        
        # 部门如果没有就留空
        if not user_department:
            user_department = ""
            logger.warning("未获取到用户部门信息，将留空")
        
        logger.info(f"最终使用 - 用户: {user_name}, 部门: {user_department}")
        
        ocr_service = create_ocr_service(config)
        
        if not ocr_service.test_connection():
            raise ConnectionError("无法连接到 OCR 服务")
        
        logger.info("开始 OCR 识别...")
        ocr_result = ocr_service.extract_text_from_image(image_path)
        logger.info(f"OCR 识别结果: {ocr_result}")
        
        logger.info("上传图片到飞书...")
        image_file_token = feishu_api.upload_file(image_path)
        
        field_mapping = config.get("feishu", {}).get("field_mapping", {})
        record_data = prepare_record_data(
            ocr_result=ocr_result,
            user_name=user_name,
            user_department=user_department,
            image_file_token=image_file_token,
            field_mapping=field_mapping
        )
        
        logger.info("写入多维表格...")
        record = feishu_api.add_record(record_data)
        
        result["success"] = True
        # 飞书群聊中@用户的格式
        if user_id:
            # 使用飞书@用户格式
            at_user = f"<at user_id=\"{user_id}\"></at>"
            result["message"] = f"{at_user}，✅ 打卡成功！"  # 飞书客户端会正确显示符号
        else:
            result["message"] = f"@{user_name}，✅ 打卡成功！"
        # 保持 data 为空，避免机器人生成详细响应
        result["data"] = {}
        
        logger.info("打卡处理完成！")
        
    except Exception as e:
        result["success"] = False
        # 飞书群聊中@用户的格式
        if user_id:
            # 使用飞书@用户格式
            at_user = f"<at user_id=\"{user_id}\"></at>"
            result["message"] = f"{at_user}，❌ 打卡失败！{str(e)}！"  # 飞书客户端会正确显示符号
        else:
            # 回退到普通格式
            result["message"] = f"@{user_name}，❌ 打卡失败！{str(e)}！"
        logger.error(f"打卡处理失败: {e}", exc_info=True)
    
    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="打卡助手 - 处理打卡图片并写入飞书多维表格")
    parser.add_argument(
        "--config",
        "-c",
        default="config.json",
        help="配置文件路径 (默认: config.json)"
    )
    parser.add_argument(
        "--image",
        "-i",
        required=False,
        help="打卡图片路径（如果提供 --image-url 则不需要）"
    )
    parser.add_argument(
        "--image-url",
        "-u",
        help="打卡图片 URL (如果提供，将下载图片)"
    )
    parser.add_argument(
        "--user-name",
        "-n",
        help="打卡人姓名 (可选，如果提供 user-id 会从飞书获取)"
    )
    parser.add_argument(
        "--department",
        "-d",
        help="打卡人部门 (可选)"
    )
    parser.add_argument(
        "--user-id",
        help="飞书用户 open_id (用于获取真实用户信息)"
    )
    parser.add_argument(
        "--union-id",
        help="飞书用户 union_id (用于获取真实用户信息)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="显示详细日志"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / args.config
    if not config_path.exists():
        config_path = Path(args.config)
    
    logger.info(f"加载配置文件: {config_path}")
    config = load_config(str(config_path))
    
    image_path = args.image
    save_path = config.get("image", {}).get("save_path", "./clock_in_images")
    user_name = args.user_name
    
    # 如果提供了 user_id 或 union_id，先获取用户信息以用于图片命名
    if (args.user_id or args.union_id) and not user_name:
        feishu_api = create_feishu_api(config)
        user_info = feishu_api.get_user_info(user_id=args.user_id, union_id=args.union_id)
        if user_info:
            user_name = user_info.get("name")
            logger.info(f"获取到用户姓名: {user_name}")
    
    if args.image_url:
        # 从 URL 下载图片
        feishu_api = create_feishu_api(config)
        access_token = feishu_api.get_tenant_access_token()
        image_path = download_image(args.image_url, save_path, access_token, user_name)
    elif image_path:
        # 复制本地图片到指定目录
        import shutil
        save_dir = ensure_image_directory(save_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if user_name:
            # 移除可能导致文件名问题的字符
            safe_user_name = "".join(c for c in user_name if c.isalnum() or c in "_- ")
            filename = f"clock_in_{timestamp}_{safe_user_name}.jpg"
        else:
            filename = f"clock_in_{timestamp}.jpg"
        dest_path = save_dir / filename
        shutil.copy2(image_path, dest_path)
        image_path = str(dest_path)
        logger.info(f"图片已复制到: {image_path}")
    else:
        parser.error("必须提供 --image 或 --image-url 参数")
    
    # 使用传入的 user_id
    user_id = args.user_id
    
    result = process_clock_in(
        config=config,
        image_path=image_path,
        user_name=user_name,
        user_department=args.department,
        user_id=user_id,
        union_id=args.union_id
    )
    
    # 使用 ensure_ascii=True 避免编码问题，飞书客户端会正确解码显示符号
    print(json.dumps(result, ensure_ascii=True, indent=2))
    
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
