# 开发计划与技术设计

## 快速确认（基于已有信息）

### ✅ 已确认
- 技术栈：Electron + React + Python FastAPI + SQLite
- 功能优先级：先做备忘录分析，再做视频分析
- 数据存储：SQLite + 本地文件系统
- API调用：Qwen API（已配置）
- 不需要：导出、批量上传、实时预览

### 📋 开发假设
1. **功能优先级**：备忘录分析 → 历史记录 → 视频分析 → 数据统计 → 智能指导
2. **记录关联**：AI自动判断（时间间隔<30分钟 + 距离/配速相似），用户可手动调整
3. **错误处理**：图片识别失败提供重试，视频分析失败仅提示
4. **UI框架**：React + Tailwind CSS（简洁风格）
5. **后端通信**：Electron主进程调用Python子进程（通过stdin/stdout或HTTP）

---

## 技术架构

### 项目结构
```
runningAgent/
├── frontend/              # Electron + React
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── pages/         # 页面组件
│   │   ├── services/     # API服务
│   │   └── utils/         # 工具函数
│   ├── public/
│   └── package.json
├── backend/               # Python FastAPI
│   ├── app/
│   │   ├── api/           # API路由
│   │   ├── services/      # 业务逻辑
│   │   ├── models/        # 数据模型
│   │   └── utils/         # 工具函数
│   ├── requirements.txt
│   └── main.py
├── database/              # SQLite数据库
├── uploads/               # 上传文件存储
├── config.json            # 配置文件
└── README.md
```

### 技术选型
- **前端**：Electron 28+ + React 18 + Tailwind CSS
- **后端**：Python 3.10+ + FastAPI + SQLAlchemy
- **AI**：Qwen API (dashscope) + MediaPipe
- **数据库**：SQLite
- **文件处理**：Pillow, OpenCV, mediapipe

---

## 开发任务分解

### Phase 1: 项目基础搭建 (2小时)
- [x] 创建项目结构
- [ ] 配置Electron + React环境
- [ ] 配置Python FastAPI环境
- [ ] 创建数据库模型和初始化
- [ ] 配置文件读取模块

### Phase 2: 备忘录分析核心功能 (3小时)
- [ ] 前端：文本输入 + 图片上传组件
- [ ] 前端：分析结果展示组件
- [ ] 后端：Qwen API调用服务
- [ ] 后端：图片处理（base64编码）
- [ ] 后端：AI分析结果解析
- [ ] 数据库：保存记录功能

### Phase 3: 历史记录功能 (2小时)
- [ ] 前端：记录列表页面
- [ ] 前端：记录详情页面
- [ ] 前端：搜索和筛选功能
- [ ] 后端：记录查询API
- [ ] 后端：记录详情API

### Phase 4: 视频分析功能 (4小时)
- [ ] 后端：MediaPipe集成
- [ ] 后端：视频处理（关键点提取）
- [ ] 后端：角度计算（侧面/背面）
- [ ] 后端：可视化图生成
- [ ] 前端：视频上传组件
- [ ] 前端：拍摄角度选择
- [ ] 前端：分析结果展示

### Phase 5: 数据统计和智能指导 (2小时)
- [ ] 后端：统计数据计算
- [ ] 前端：图表展示（Chart.js）
- [ ] 后端：智能指导生成
- [ ] 前端：智能指导页面

### Phase 6: 记录关联功能 (1小时)
- [ ] 后端：AI自动关联算法
- [ ] 前端：手动关联UI
- [ ] 后端：关联记录查询

### Phase 7: 完善和优化 (1小时)
- [ ] 错误处理完善
- [ ] UI细节优化
- [ ] 性能优化
- [ ] 测试和调试

---

## 关键实现细节

### 1. Electron与Python通信
```javascript
// Electron主进程
const { spawn } = require('child_process');
const pythonProcess = spawn('python', ['backend/main.py']);

// 通过HTTP通信（更简单）
// Python FastAPI运行在localhost:8000
```

### 2. Qwen API调用
```python
from dashscope import MultiModalConversation

def analyze_coros_image(image_path, memo_text):
    # 读取图片并转换为base64
    # 调用Qwen视觉模型
    # 解析返回结果
```

### 3. MediaPipe视频分析
```python
import mediapipe as mp
import cv2

def analyze_video(video_path, angle):
    # 提取关键点
    # 计算角度/对称性
    # 生成可视化图
    # 返回结构化数据
```

### 4. 数据库设计
- records表：主记录
- coros_data表：高驰数据
- video_analysis表：视频分析数据
- 使用SQLAlchemy ORM

---

## 开发顺序

1. **先搭建基础框架**（Electron + React + FastAPI）
2. **实现备忘录分析**（最核心功能）
3. **实现历史记录**（数据积累）
4. **实现视频分析**（高级功能）
5. **实现统计和指导**（增值功能）
6. **完善细节**（错误处理、UI优化）

---

## 预计完成时间

总计：约15小时
- 基础搭建：2小时
- 备忘录分析：3小时
- 历史记录：2小时
- 视频分析：4小时
- 统计指导：2小时
- 关联功能：1小时
- 完善优化：1小时

---

**开始开发！**
