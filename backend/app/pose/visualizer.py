"""
姿态可视化 - 在图像/视频上绘制骨架和角度标签（参考 code-reference）
骨架橙色、关节点白色、角度标签橙色背景
"""
import cv2
import numpy as np
from typing import Tuple, List, Optional

# MediaPipe Pose 关键点索引（与 solutions.pose 一致）
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
LEFT_HEEL = 29
RIGHT_HEEL = 30
LEFT_FOOT_INDEX = 31
RIGHT_FOOT_INDEX = 32

POSE_CONNECTIONS = [
    (LEFT_SHOULDER, RIGHT_SHOULDER),
    (LEFT_SHOULDER, LEFT_HIP),
    (RIGHT_SHOULDER, RIGHT_HIP),
    (LEFT_HIP, RIGHT_HIP),
    (LEFT_HIP, LEFT_KNEE),
    (LEFT_KNEE, LEFT_ANKLE),
    (LEFT_ANKLE, LEFT_HEEL),
    (LEFT_HEEL, LEFT_FOOT_INDEX),
    (LEFT_ANKLE, LEFT_FOOT_INDEX),
    (RIGHT_HIP, RIGHT_KNEE),
    (RIGHT_KNEE, RIGHT_ANKLE),
    (RIGHT_ANKLE, RIGHT_HEEL),
    (RIGHT_HEEL, RIGHT_FOOT_INDEX),
    (RIGHT_ANKLE, RIGHT_FOOT_INDEX),
]

COLOR_SKELETON = (0, 165, 255)  # BGR 橙色
COLOR_JOINT = (255, 255, 255)   # BGR 白色
COLOR_ANGLE_BG = (0, 100, 255)  # BGR 橙色背景
COLOR_ANGLE_TEXT = (255, 255, 255)


def landmarks_to_numpy(landmarks) -> np.ndarray:
    """将 MediaPipe solutions 的 landmarks 转为 (33, 4) numpy"""
    arr = []
    for lm in landmarks:
        vis = getattr(lm, 'visibility', 1.0)
        arr.append([lm.x, lm.y, lm.z, vis])
    return np.array(arr)


def calculate_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    """计算三点角度（p2 为顶点）"""
    v1 = p1 - p2
    v2 = p3 - p2
    cos_a = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
    return np.degrees(np.arccos(np.clip(cos_a, -1.0, 1.0)))


def draw_skeleton(
    image: np.ndarray,
    landmarks: np.ndarray,
    line_thickness: int = 3,
    joint_radius: int = 6,
) -> np.ndarray:
    """在图像上绘制骨架"""
    output = image.copy()
    h, w = output.shape[:2]

    for start_idx, end_idx in POSE_CONNECTIONS:
        if start_idx >= len(landmarks) or end_idx >= len(landmarks):
            continue
        if landmarks[start_idx][3] < 0.5 or landmarks[end_idx][3] < 0.5:
            continue
        sp = (int(landmarks[start_idx][0] * w), int(landmarks[start_idx][1] * h))
        ep = (int(landmarks[end_idx][0] * w), int(landmarks[end_idx][1] * h))
        cv2.line(output, sp, ep, COLOR_SKELETON, line_thickness)

    for i, lm in enumerate(landmarks):
        if lm[3] < 0.5:
            continue
        pt = (int(lm[0] * w), int(lm[1] * h))
        cv2.circle(output, pt, joint_radius, COLOR_JOINT, -1)
        cv2.circle(output, pt, joint_radius, COLOR_SKELETON, 2)

    return output


def draw_angle_label(
    image: np.ndarray,
    position: Tuple[int, int],
    value: float,
    font_scale: float = 0.6,
) -> np.ndarray:
    """在指定位置绘制橙色背景的数值标签"""
    output = image.copy()
    text = f"{value:.0f}" if abs(value) >= 1 else f"{value:.2f}"

    (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
    padding = 5
    cv2.rectangle(
        output,
        (position[0] - padding, position[1] - text_h - padding),
        (position[0] + text_w + padding, position[1] + padding),
        COLOR_ANGLE_BG,
        -1,
    )
    cv2.putText(
        output, text, position,
        cv2.FONT_HERSHEY_SIMPLEX, font_scale, COLOR_ANGLE_TEXT, 2
    )
    return output


def draw_pose_with_angles(
    frame: np.ndarray,
    landmarks,
    angle: str,
    results: dict,
    line_thickness: int = 3,
    joint_radius: int = 6,
) -> np.ndarray:
    """
    在帧上绘制骨架 + 关节附近的橙色数值标签
    angle: "side" | "back"
    results: 当前帧的分析结果（角度/对称性数据）
    """
    if landmarks is None or len(landmarks) < 33:
        return frame

    lm_arr = landmarks_to_numpy(landmarks) if hasattr(landmarks[0], 'x') else np.array(landmarks)
    if lm_arr.shape[0] < 33:
        return frame

    output = draw_skeleton(frame, lm_arr, line_thickness, joint_radius)
    h, w = output.shape[:2]

    # 根据视角显示不同指标
    if angle == "side":
        # 左膝角度
        if all(lm_arr[i][3] > 0.5 for i in [LEFT_HIP, LEFT_KNEE, LEFT_ANKLE]):
            a = calculate_angle(
                lm_arr[LEFT_HIP][:2], lm_arr[LEFT_KNEE][:2], lm_arr[LEFT_ANKLE][:2]
            )
            pos = (int(lm_arr[LEFT_KNEE][0] * w) - 60, int(lm_arr[LEFT_KNEE][1] * h))
            output = draw_angle_label(output, pos, a)

        # 右膝角度
        if all(lm_arr[i][3] > 0.5 for i in [RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE]):
            a = calculate_angle(
                lm_arr[RIGHT_HIP][:2], lm_arr[RIGHT_KNEE][:2], lm_arr[RIGHT_ANKLE][:2]
            )
            pos = (int(lm_arr[RIGHT_KNEE][0] * w) + 10, int(lm_arr[RIGHT_KNEE][1] * h))
            output = draw_angle_label(output, pos, a)

        # 躯干前倾
        if "torso_lean" in results:
            sm = (lm_arr[LEFT_SHOULDER][:2] + lm_arr[RIGHT_SHOULDER][:2]) / 2
            pos = (int(sm[0] * w), int(sm[1] * h) - 20)
            output = draw_angle_label(output, pos, results["torso_lean"])

    else:  # back
        # 骨盆倾斜
        if "hip_tilt_angle" in results:
            hm = (lm_arr[LEFT_HIP][:2] + lm_arr[RIGHT_HIP][:2]) / 2
            pos = (int(hm[0] * w) + 15, int(hm[1] * h))
            output = draw_angle_label(output, pos, results["hip_tilt_angle"])

        # 肩膀平衡
        if "shoulder_balance_angle" in results:
            sm = (lm_arr[LEFT_SHOULDER][:2] + lm_arr[RIGHT_SHOULDER][:2]) / 2
            pos = (int(sm[0] * w), int(sm[1] * h) - 25)
            output = draw_angle_label(output, pos, results["shoulder_balance_angle"])

        # 左右平衡（像素差）
        if "shoulder_balance" in results:
            sm = (lm_arr[LEFT_SHOULDER][:2] + lm_arr[RIGHT_SHOULDER][:2]) / 2
            pos = (int(sm[0] * w) - 50, int(sm[1] * h))
            output = draw_angle_label(output, pos, results["shoulder_balance"])

    return output
