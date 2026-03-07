"""
视频分析服务 - MediaPipe集成
生成带骨架+角度标签的视频（参考 code-reference Ochy 风格）
"""
import json
import logging
import subprocess
import cv2

logger = logging.getLogger(__name__)
import numpy as np
import mediapipe as mp
import os
from pathlib import Path
import math

from app.pose.visualizer import draw_pose_with_angles

# 采样策略：短视频逐帧，中视频 1 秒/帧，长视频 2 秒/帧
SAMPLE_INTERVAL_SHORT_SEC = 1.0   # 6-30 秒视频：每 1 秒 1 帧
SAMPLE_INTERVAL_LONG_SEC = 2.0    # >30 秒视频：每 2 秒 1 帧
OUTPUT_VIDEO_FPS = 10  # 采样后输出视频的帧率

class VideoAnalyzer:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def calculate_angle(self, point1, point2, point3):
        """计算三点之间的角度"""
        a = np.array(point1)
        b = np.array(point2)
        c = np.array(point3)
        
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
        
        return angle

    def calculate_distance(self, point1, point2):
        """计算两点之间的距离"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    def analyze_side_view(self, landmarks, frame_width, frame_height):
        """分析侧面视角"""
        results = {}
        
        # 关键点索引（MediaPipe Pose）
        # 头部关键点
        nose = [landmarks[0].x * frame_width, landmarks[0].y * frame_height]
        left_shoulder = [landmarks[11].x * frame_width, landmarks[11].y * frame_height]
        right_shoulder = [landmarks[12].x * frame_width, landmarks[12].y * frame_height]
        shoulder_center = [(left_shoulder[0] + right_shoulder[0]) / 2, 
                          (left_shoulder[1] + right_shoulder[1]) / 2]
        
        # 躯干关键点
        left_hip = [landmarks[23].x * frame_width, landmarks[23].y * frame_height]
        right_hip = [landmarks[24].x * frame_width, landmarks[24].y * frame_height]
        hip_center = [(left_hip[0] + right_hip[0]) / 2, 
                      (left_hip[1] + right_hip[1]) / 2]
        
        # 腿部关键点
        left_knee = [landmarks[25].x * frame_width, landmarks[25].y * frame_height]
        right_knee = [landmarks[26].x * frame_width, landmarks[26].y * frame_height]
        left_ankle = [landmarks[27].x * frame_width, landmarks[27].y * frame_height]
        right_ankle = [landmarks[28].x * frame_width, landmarks[28].y * frame_height]
        
        # 手臂关键点
        left_elbow = [landmarks[13].x * frame_width, landmarks[13].y * frame_height]
        left_wrist = [landmarks[15].x * frame_width, landmarks[15].y * frame_height]
        
        # 计算角度
        # 头部倾斜（基于鼻子和肩膀）
        if nose[1] < shoulder_center[1]:
            head_tilt = math.degrees(math.atan2(nose[0] - shoulder_center[0], 
                                               shoulder_center[1] - nose[1])) - 90
        else:
            head_tilt = 0
        
        # 躯干前倾（肩膀中心到髋部中心）
        torso_lean = math.degrees(math.atan2(hip_center[0] - shoulder_center[0],
                                             hip_center[1] - shoulder_center[1])) - 90
        
        # 膝关节角度（使用左腿作为主要分析）
        knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
        
        # 踝关节角度
        ankle_angle = self.calculate_angle(left_knee, left_ankle, 
                                           [left_ankle[0], left_ankle[1] + 50])
        
        # 手臂角度
        arm_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
        
        # 步幅（左右脚踝之间的距离）
        stride_length = self.calculate_distance(left_ankle, right_ankle)
        
        results = {
            "head_tilt": round(head_tilt, 1),
            "torso_lean": round(torso_lean, 1),
            "knee_angle": round(knee_angle, 1),
            "ankle_angle": round(ankle_angle, 1),
            "arm_angle": round(arm_angle, 1),
            "stride_length": round(stride_length, 1),
        }
        
        return results

    def analyze_back_view(self, landmarks, frame_width, frame_height):
        """分析背面视角"""
        results = {}
        
        # 关键点
        left_shoulder = [landmarks[11].x * frame_width, landmarks[11].y * frame_height]
        right_shoulder = [landmarks[12].x * frame_width, landmarks[12].y * frame_height]
        left_hip = [landmarks[23].x * frame_width, landmarks[23].y * frame_height]
        right_hip = [landmarks[24].x * frame_width, landmarks[24].y * frame_height]
        left_ankle = [landmarks[27].x * frame_width, landmarks[27].y * frame_height]
        right_ankle = [landmarks[28].x * frame_width, landmarks[28].y * frame_height]
        
        # 左右平衡（肩膀高度差）
        shoulder_balance = abs(left_shoulder[1] - right_shoulder[1])
        shoulder_balance_angle = math.degrees(math.atan2(shoulder_balance, 
                                                          abs(left_shoulder[0] - right_shoulder[0])))
        
        # 骨盆倾斜
        hip_balance = abs(left_hip[1] - right_hip[1])
        hip_tilt_angle = math.degrees(math.atan2(hip_balance, 
                                                 abs(left_hip[0] - right_hip[0])))
        
        # 身体中心线对齐（基于肩膀和髋部中心）
        shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
        hip_center_x = (left_hip[0] + right_hip[0]) / 2
        center_alignment = abs(shoulder_center_x - hip_center_x)
        
        # 脚落地位置（左右脚踝的Y坐标差）
        foot_balance = abs(left_ankle[1] - right_ankle[1])
        
        results = {
            "shoulder_balance": round(shoulder_balance, 1),
            "shoulder_balance_angle": round(shoulder_balance_angle, 1),
            "hip_tilt": round(hip_balance, 1),
            "hip_tilt_angle": round(hip_tilt_angle, 1),
            "center_alignment": round(center_alignment, 1),
            "foot_balance": round(foot_balance, 1),
        }
        
        return results

    def extract_keypoints(self, landmarks, frame_width, frame_height):
        """提取所有关键点坐标"""
        keypoints = []
        for landmark in landmarks:
            keypoints.append({
                "x": landmark.x * frame_width,
                "y": landmark.y * frame_height,
                "z": landmark.z,
                "visibility": landmark.visibility
            })
        return keypoints

    def _draw_frame(self, frame, landmarks, angle, results):
        """使用 Ochy 风格绘制：橙色骨架 + 关节附近橙色数值标签"""
        return draw_pose_with_angles(frame, landmarks.landmark, angle, results or {})

    def _get_video_rotation(self, video_path):
        """获取视频旋转元数据（手机竖拍常见 90/270），返回需逆旋转的角度 0/90/180/270"""
        # 1. ffprobe stream_tags.rotate（旧版格式）
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                 "-show_entries", "stream_tags=rotate", "-of", "json", str(video_path)],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for stream in data.get("streams", []):
                    tags = stream.get("tags", {})
                    rot = tags.get("rotate")
                    if rot is not None:
                        r = int(rot) % 360
                        if r in (90, 180, 270):
                            return r
        except Exception as e:
            logger.debug("ffprobe stream_tags 旋转失败: %s", e)

        # 2. ffprobe stream_side_data.rotation（新版 ffprobe 5+）
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                 "-show_entries", "stream_side_data=rotation", "-of", "json", str(video_path)],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for stream in data.get("streams", []):
                    side_data = stream.get("side_data", [])
                    if isinstance(side_data, list):
                        for sd in side_data:
                            rot = sd.get("rotation") if isinstance(sd, dict) else None
                            if rot is not None:
                                r = int(float(rot)) % 360
                                if r in (90, 180, 270):
                                    return r
                    elif isinstance(side_data, dict) and "rotation" in side_data:
                        r = int(float(side_data["rotation"])) % 360
                        if r in (90, 180, 270):
                            return r
        except Exception as e:
            logger.debug("ffprobe side_data 旋转失败: %s", e)

        # 3. ffprobe side_data=rotation（部分格式）
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                 "-show_entries", "side_data=rotation", "-of", "json", str(video_path)],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for stream in data.get("streams", []):
                    side_data = stream.get("side_data", [])
                    if isinstance(side_data, list):
                        for sd in side_data:
                            rot = sd.get("rotation") if isinstance(sd, dict) else None
                            if rot is not None:
                                r = int(float(rot)) % 360
                                if r in (90, 180, 270):
                                    return r
        except Exception:
            pass

        # 4. OpenCV CAP_PROP_ORIENTATION_META（部分版本支持）
        try:
            cap = cv2.VideoCapture(str(video_path))
            if hasattr(cv2, "CAP_PROP_ORIENTATION_META"):
                meta = cap.get(cv2.CAP_PROP_ORIENTATION_META)
                cap.release()
                if meta and meta != -1:
                    r = int(meta) % 360
                    if r in (90, 180, 270):
                        return r
            else:
                cap.release()
        except Exception:
            pass
        return 0

    def _rotate_frame(self, frame, rotation_deg):
        """根据旋转角度修正帧方向"""
        if rotation_deg == 0:
            return frame
        if rotation_deg == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        if rotation_deg == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        if rotation_deg == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        return frame

    def _preprocess_rotation(self, video_path, force_flip_180):
        """
        用 ffmpeg 预处理视频：ffmpeg 会应用 rotate 元数据，输出标准方向供 OpenCV 读取。
        避免 OpenCV 各版本/后端旋转行为不一致（参考代码能正常显示同一视频即因环境不同）。
        """
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.close()
        try:
            cmd = ["ffmpeg", "-y", "-i", str(video_path)]
            if force_flip_180:
                cmd.extend(["-vf", "vflip,hflip"])
                logger.info("[姿态分析] ffmpeg 预处理: 应用元数据旋转 + 用户勾选 180°")
            else:
                logger.info("[姿态分析] ffmpeg 预处理: 应用视频旋转元数据")
            cmd.extend(["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-an", tmp.name])
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            if r.returncode == 0 and Path(tmp.name).exists():
                return Path(tmp.name)
        except Exception as e:
            logger.warning("[姿态分析] ffmpeg 预处理失败: %s，使用原视频", e)
        return Path(video_path)

    def analyze_video(self, video_path, angle="side", force_flip_180=False, output_dir=None, log_cb=None):
        """
        分析视频
        
        Args:
            video_path: 视频文件路径
            angle: 拍摄角度 ("side" 或 "back")
            force_flip_180: 画面倒置时设为 True，强制旋转 180°
            output_dir: 可视化输出目录，None 时从 video_path 推导（临时文件时需传入）
            log_cb: 可选，日志回调函数，用于前端实时展示进度
        
        Returns:
            dict: 包含关键点数据、角度数据、可视化图路径等
        """
        def _log(msg):
            if log_cb:
                try:
                    log_cb(msg)
                except Exception:
                    pass

        _log("ffmpeg 预处理视频...")
        work_path = self._preprocess_rotation(video_path, force_flip_180)
        rotation_deg = 0  # 预处理后无需再旋转
        cleanup_work = work_path != Path(video_path)

        cap = cv2.VideoCapture(str(work_path))
        if not cap.isOpened():
            raise Exception("无法打开视频文件")

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if rotation_deg in (90, 270):
            frame_width, frame_height = frame_height, frame_width
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = total_frames / fps if fps else 0
        # 短视频(<6秒)逐帧，中视频(6-30秒)每1秒1帧，长视频(>30秒)每2秒1帧
        if duration_sec <= 6:
            sample_interval_frames = 1
            interval_sec = 0
        elif duration_sec <= 30:
            sample_interval_frames = max(1, int(SAMPLE_INTERVAL_SHORT_SEC * fps))
            interval_sec = SAMPLE_INTERVAL_SHORT_SEC
        else:
            sample_interval_frames = max(1, int(SAMPLE_INTERVAL_LONG_SEC * fps))
            interval_sec = SAMPLE_INTERVAL_LONG_SEC
        estimated_samples = max(1, total_frames // sample_interval_frames)
        _log(f"视频 {total_frames} 帧, {duration_sec:.1f}秒 | 预计分析 {estimated_samples} 帧")
        logger.info("[姿态分析] 视频: %d 帧, %.1f fps, %.1f秒 | 采样间隔 %d 帧(约%.1f秒), 预计分析 %d 帧",
                    total_frames, fps, duration_sec,
                    sample_interval_frames, interval_sec, estimated_samples)

        if output_dir:
            vis_dir = Path(output_dir)
        else:
            base_dir = Path(video_path).parent.parent.parent
            vis_dir = base_dir / "uploads" / "visualizations"
        vis_dir.mkdir(parents=True, exist_ok=True)
        vis_video_path = vis_dir / f"{Path(video_path).stem}_vis.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_fps = fps if sample_interval_frames == 1 else OUTPUT_VIDEO_FPS
        out_writer = cv2.VideoWriter(str(vis_video_path), fourcc, out_fps, (frame_width, frame_height))

        all_keypoints = []
        all_angles = []
        all_symmetry = []
        frame_count = 0
        out_frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = self._rotate_frame(frame, rotation_deg)
            frame_count += 1

            # 采样：仅处理每 SAMPLE_INTERVAL_SEC 秒的第一帧
            if (frame_count - 1) % sample_interval_frames != 0:
                continue

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results_pose = self.pose.process(frame_rgb)

            if results_pose.pose_landmarks:
                landmarks = results_pose.pose_landmarks.landmark

                keypoints = self.extract_keypoints(landmarks, frame_width, frame_height)
                all_keypoints.append(keypoints)

                current_results = None
                if angle == "side":
                    angles = self.analyze_side_view(landmarks, frame_width, frame_height)
                    all_angles.append(angles)
                    current_results = angles
                else:
                    symmetry = self.analyze_back_view(landmarks, frame_width, frame_height)
                    all_symmetry.append(symmetry)
                    current_results = symmetry

                # 绘制骨架+角度标签并写入输出视频
                frame_drawn = self._draw_frame(
                    frame.copy(),
                    results_pose.pose_landmarks,
                    angle,
                    current_results
                )
                out_writer.write(frame_drawn)
                out_frame_count += 1
            else:
                out_writer.write(frame)

            if out_frame_count > 0 and out_frame_count % 30 == 0:
                _log(f"已采样分析 {out_frame_count} 帧...")
                logger.info("[姿态分析] 已采样分析 %d 帧 (总帧 %d)", out_frame_count, frame_count)

        cap.release()
        out_writer.release()
        if cleanup_work and work_path.exists():
            try:
                work_path.unlink()
            except Exception:
                pass

        # 使用 ffmpeg 转码为 H.264，确保浏览器/Electron 可播放（mp4v 在 Chromium 中不支持）
        final_vis_path = vis_video_path
        try:
            vis_h264 = vis_dir / f"{Path(video_path).stem}_vis_h264.mp4"
            ffmpeg_cmd = ["ffmpeg", "-y", "-i", str(vis_video_path),
                         "-c:v", "libx264", "-preset", "fast",
                         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(vis_h264)]
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and vis_h264.exists():
                final_vis_path = vis_h264
                logger.info("[姿态分析] 已转码为 H.264: %s", final_vis_path)
            else:
                logger.warning("[姿态分析] ffmpeg 转码失败，使用原始 mp4v（可能无法在浏览器播放）")
        except FileNotFoundError:
            logger.warning("[姿态分析] 未找到 ffmpeg，跳过 H.264 转码。请安装 ffmpeg 以改善视频兼容性")
        except Exception as e:
            logger.warning("[姿态分析] ffmpeg 转码异常: %s", e)

        _log("姿态检测完成，正在转码...")
        logger.info("[姿态分析] 完成，共 %d 帧，输出可视化视频: %s", out_frame_count, final_vis_path)

        # 保存一帧图片供 Qwen AI 分析（Qwen 只接受图片，不接受视频）
        vis_img_path = vis_dir / f"{Path(video_path).stem}_vis.jpg"
        cap_thumb = cv2.VideoCapture(str(final_vis_path))
        ret_thumb, frame_thumb = cap_thumb.read()
        cap_thumb.release()
        if ret_thumb:
            cv2.imwrite(str(vis_img_path), frame_thumb)
            logger.info("[姿态分析] 已保存 AI 分析用缩略图: %s", vis_img_path)

        # 计算平均值
        avg_angles = {}
        avg_symmetry = {}
        
        if angle == "side":
            if all_angles:
                for key in all_angles[0].keys():
                    avg_angles[key] = round(sum(a[key] for a in all_angles) / len(all_angles), 1)
        else:
            if all_symmetry:
                for key in all_symmetry[0].keys():
                    avg_symmetry[key] = round(sum(s[key] for s in all_symmetry) / len(all_symmetry), 1)
        
        return {
            "keypoints_data": json.dumps(all_keypoints[0] if all_keypoints else []),
            "angles_data": json.dumps(avg_angles if angle == "side" else {}),
            "symmetry_data": json.dumps(avg_symmetry if angle == "back" else {}),
            "visualization_path": str(final_vis_path),
            "visualization_image_path": str(vis_img_path) if vis_img_path.exists() else None,
            "frame_count": out_frame_count,
            "fps": fps
        }
