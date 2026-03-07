"""
Qwen API服务
"""
import base64
import json
from pathlib import Path
try:
    from dashscope import MultiModalConversation
except ImportError:
    # 如果dashscope未安装，使用占位
    class MultiModalConversation:
        @staticmethod
        def call(*args, **kwargs):
            raise ImportError("请安装dashscope: pip install dashscope")
from app.utils.config import get_api_config

def _image_mime_type(image_path):
    """根据文件扩展名返回 MIME 类型"""
    p = Path(image_path)
    ext = (p.suffix or "").lower()
    if ext in (".png",):
        return "image/png"
    if ext in (".gif",):
        return "image/gif"
    return "image/jpeg"  # jpg, jpeg, 及其他

def image_to_base64(image_path):
    """将图片转换为base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def _extract_text_from_content(item):
    """从 content 项提取文本，兼容 object.text 与 dict['text']"""
    if item is None:
        return ""
    if isinstance(item, dict):
        return item.get("text", "")
    return getattr(item, "text", "")

def _extract_text_from_response(response):
    """从 Qwen API 响应中提取文本，兼容多种返回格式"""
    if not hasattr(response, 'output'):
        return str(response)
    out = response.output
    content = []
    try:
        if isinstance(out, dict):
            ch = out.get('choices', [{}])
            msg = ch[0].get('message', {}) if ch else {}
            content = msg.get('content', []) if isinstance(msg, dict) else getattr(msg, 'content', [])
        elif hasattr(out, 'choices') and out.choices:
            msg = out.choices[0].message if hasattr(out.choices[0], 'message') else out.choices[0].get('message', {})
            content = getattr(msg, 'content', []) if not isinstance(msg, dict) else msg.get('content', [])
    except (IndexError, AttributeError, KeyError):
        pass
    for item in (content if isinstance(content, list) else [content]):
        text = _extract_text_from_content(item)
        if text:
            return text
    return str(out)

def analyze_coros_image(image_path, memo_text=""):
    """
    分析高驰截图
    
    Args:
        image_path: 图片路径
        memo_text: 备忘录文本
    
    Returns:
        dict: 分析结果
    """
    api_config = get_api_config()
    api_key = api_config.get("qwen_api_key")
    
    if not api_key:
        raise ValueError("Qwen API Key未配置")
    
    # 读取图片
    image_base64 = image_to_base64(image_path)
    mime = _image_mime_type(image_path)
    
    # 构建提示词
    prompt = f"""请分析这张高驰跑步数据截图，提取关键数据并给出专业评价。

截图可能包含高驰手表数据和 Stryd 功率计数据。请提取所有可见数据。

要求：
1. 提取所有关键数据，包括：
   - 基础：距离、配速、心率、步频、步幅
   - Stryd 功率：平均功率(avg_power, W)、最高功率(max_power, W)、姿势功率(form_power, W)、姿势功率比(form_power_ratio, %，理想 20-30%)
   - Stryd 跑步经济性：触地时间(avg_gct, ms)、垂直振幅(vertical_oscillation_cm 或 vertical_oscillation_ratio)
2. 分析跑步表现：整体评价、优点、需要改进的地方
3. 若有 Stryd 数据，结合功率和跑步经济性指标进行分析（如姿势功率比是否理想、触地时间是否偏长等）
4. 给出改进建议：基于数据的针对性建议，若有功率数据可给出功率训练相关建议
5. 如果提供了备忘录文本，请结合备忘录内容进行分析

备忘录内容：
{memo_text if memo_text else "无"}

请以JSON格式返回，包含以下字段：
- data_overview: 数据概览（距离、配速、心率、步频、avg_power、max_power、form_power、form_power_ratio、avg_gct、vertical_oscillation 等，有则提取）
- performance_evaluation: 表现评价（整体评价、优点、需要改进）
- improvement_suggestions: 改进建议（具体建议列表，可包含功率训练、跑步经济性相关建议）
"""
    
    try:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "image": f"data:{mime};base64,{image_base64}"
                    },
                    {
                        "text": prompt
                    }
                ]
            }
        ]
        
        response = MultiModalConversation.call(
            model="qwen-vl-plus",
            messages=messages,
            api_key=api_key
        )
        
        if response.status_code == 200:
            result_text = _extract_text_from_response(response)
            # 去除 markdown 代码块（AI 可能返回 ```json ... ```）
            text_to_parse = result_text.strip()
            if text_to_parse.startswith("```"):
                lines = text_to_parse.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text_to_parse = "\n".join(lines)
            # 尝试解析JSON
            try:
                result = json.loads(text_to_parse)
            except:
                # 如果不是JSON，返回文本
                result = {
                    "raw_text": result_text,
                    "data_overview": {},
                    "performance_evaluation": result_text,
                    "improvement_suggestions": []
                }
            return result
        else:
            raise Exception(f"Qwen API调用失败: {response.message}")
    
    except Exception as e:
        raise Exception(f"分析失败: {str(e)}")

def analyze_video_pose(keypoints_data, angles_data, visualization_path, video_angle, symmetry_data=None):
    """
    分析视频跑姿数据
    
    Args:
        keypoints_data: 关键点数据（JSON字符串）
        angles_data: 角度数据（JSON字符串）
        visualization_path: 可视化图路径
        video_angle: 拍摄角度（side/back）
        symmetry_data: 对称性数据（仅背面，JSON字符串）
    
    Returns:
        dict: 分析结果
    """
    api_config = get_api_config()
    api_key = api_config.get("qwen_api_key")
    
    if not api_key:
        raise ValueError("Qwen API Key未配置")
    
    # 读取可视化图
    vis_base64 = image_to_base64(visualization_path)
    mime = _image_mime_type(visualization_path)
    
    # 解析数据
    keypoints = json.loads(keypoints_data) if isinstance(keypoints_data, str) else keypoints_data
    angles = json.loads(angles_data) if isinstance(angles_data, str) else angles_data
    
    # 构建提示词
    if video_angle == "side":
        prompt = f"""请分析这张跑步视频的姿态分析结果（侧面拍摄）。

关键点数据：
{json.dumps(keypoints, ensure_ascii=False, indent=2)}

角度数据：
{json.dumps(angles, ensure_ascii=False, indent=2)}

请分析：
1. 关键角度评估：头部倾斜、躯干前倾、膝关节角度、踝关节角度等
2. 步态分析：步幅、落地方式、触地时间、垂直振幅
3. 整体评分（0-100分）
4. 优点和需要改进的地方
5. 针对性训练建议

请以JSON格式返回。
"""
    else:  # back
        symmetry = json.loads(symmetry_data) if symmetry_data and isinstance(symmetry_data, str) else {}
        prompt = f"""请分析这张跑步视频的姿态分析结果（背面拍摄）。

关键点数据：
{json.dumps(keypoints, ensure_ascii=False, indent=2)}

对称性数据：
{json.dumps(symmetry, ensure_ascii=False, indent=2)}

请分析：
1. 对称性评估：左右平衡、骨盆倾斜、肩膀对称性
2. 对齐度分析：身体中心线对齐、脚落地位置、膝盖对齐
3. 整体评分（0-100分）
4. 对称性问题和需要改进的地方
5. 针对性训练建议

请以JSON格式返回。
"""
    
    try:
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "image": f"data:{mime};base64,{vis_base64}"
                    },
                    {
                        "text": prompt
                    }
                ]
            }
        ]
        
        response = MultiModalConversation.call(
            model="qwen-vl-plus",
            messages=messages,
            api_key=api_key
        )
        
        if response.status_code == 200:
            result_text = _extract_text_from_response(response)
            # 去除 markdown 代码块（AI 可能返回 ```json ... ```）
            text_to_parse = result_text.strip()
            if text_to_parse.startswith("```"):
                lines = text_to_parse.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text_to_parse = "\n".join(lines)
            try:
                result = json.loads(text_to_parse)
            except:
                result = {
                    "raw_text": result_text,
                    "overall_score": 85,
                    "evaluation": result_text,
                    "suggestions": []
                }
            return result
        else:
            raise Exception(f"Qwen API调用失败: {response.message}")
    
    except Exception as e:
        raise Exception(f"分析失败: {str(e)}")
