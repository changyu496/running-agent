# 步知 API 列表

## 基础

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务状态 |
| GET | `/api/health` | 健康检查 |

---

## 备忘录分析 `/api/memo`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/memo/analyze` | 分析备忘录 + 高驰截图 |
| POST | `/api/memo/save` | 保存备忘录分析记录 |

**analyze** 请求：`multipart/form-data`
- `memo_text` (string, 可选)：备忘录文字
- `image` (file, 必填)：高驰数据截图

**save** 请求：`multipart/form-data`
- `memo_text` (string)
- `image_path` (string)
- `analysis_result` (string, JSON)
- `run_date` (string, 可选)：YYYY-MM-DD
- `run_type` (string, 可选)：recovery/aerobic/long/pace/interval/other

---

## 视频分析 `/api/video`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/video/analyze` | 分析跑步视频 |
| POST | `/api/video/save` | 保存视频分析记录 |

**analyze** 请求：`multipart/form-data`
- `video` (file, 必填)
- `angle` (string, 必填)：`side` 或 `back`
- `force_flip_180` (string, 可选)：`true` 或 `false`，画面倒置时用

**save** 请求：`multipart/form-data`
- `record_id` (int)
- `video_path` (string)
- `video_angle` (string)
- `keypoints_data` (string, JSON)
- `angles_data` (string, JSON)
- `symmetry_data` (string, JSON, 可选)
- `visualization_path` (string)
- `overall_score` (int)
- `analysis_text` (string)

---

## 历史记录 `/api/records`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/records/list` | 记录列表 |
| GET | `/api/records/{record_id}` | 记录详情 |
| PATCH | `/api/records/{record_id}` | 更新记录 |
| DELETE | `/api/records/{record_id}` | 删除记录 |
| POST | `/api/records/link` | 关联记录 |
| POST | `/api/records/unlink/{record_id}` | 取消关联 |
| POST | `/api/records/auto-link` | 自动关联 |

**list** 查询参数：
- `skip` (int, 默认 0)
- `limit` (int, 默认 20, 最大 100)
- `record_type` (string, 可选)：memo/video/both
- `search` (string, 可选)：搜索备忘录内容

**patch** 请求体：`{ "run_date": "YYYY-MM-DD", "run_type": "aerobic" }`

**link** 请求体：`[record_id1, record_id2, ...]` (JSON array)

---

## 数据统计 `/api/stats`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stats/overview` | 统计概览 |
| GET | `/api/stats/trends` | 趋势数据 |

**overview** 查询参数：
- `days` (int, 默认 30, 范围 1–365)

**trends** 查询参数：
- `metric` (string, 默认 pace)：pace/heart_rate/distance/cadence
- `days` (int, 默认 90, 范围 7–365)

---

## 智能指导 `/api/guidance`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/guidance/` | 获取个性化训练建议 |

---

## 文件服务 `/api/files`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/files/{filename}` | 获取上传的图片/视频/可视化文件 |
