# 跑步Agent

基于AI的跑步数据分析与指导工具，帮助用户记录、分析和改进跑步表现。

## ✨ 功能特性

- 📝 **备忘录分析**：通过文本备忘录 + 高驰数据截图，AI评价跑步情况
- 🎥 **视频跑姿分析**：上传跑步视频，AI分析跑姿并提供改进建议（支持侧面/背面）
- 📊 **历史数据积累**：自动保存所有分析记录，支持关联和统计
- 💡 **智能指导**：基于历史数据提供个性化跑步建议

## 🛠️ 技术栈

- **前端**：Electron + React + Tailwind CSS
- **后端**：Python + FastAPI
- **AI模型**：Qwen（视觉分析）+ MediaPipe（姿态估计）
- **存储**：SQLite + 本地文件系统

## 🚀 快速开始

### 1. 安装依赖

**后端：**
```bash
cd backend
pip install -r requirements.txt
```

**前端：**
```bash
cd frontend
npm install
```

### 2. 初始化数据库

```bash
cd backend
python init_db.py
```

### 3. 启动应用

**方式1：分别启动（推荐）**

终端1 - 启动后端：
```bash
cd backend
python main.py
```

终端2 - 启动前端：
```bash
cd frontend
npm run dev
```

**方式2：一键启动（本地模式）**

连接本地后端时，使用 `start.sh` 一键启动后端 + 前端 + Electron：

```bash
# 1. 确保使用本地配置（apiUrl 指向 localhost）
cp frontend/public/config.local.json frontend/public/config.json

# 2. 一键启动
./start.sh
```

启动后，侧边栏会显示 **「本地」** 绿色标签，表示已连接本地后端。

**云端模式**：将 `config.cloud.json` 复制为 `config.json`，或修改 `apiUrl` 为云端地址。页面会显示 **「云端」** 蓝色标签。

详细安装说明请参考：`INSTALL.md`

## 📖 使用说明

### 备忘录分析
1. 点击"新建分析" → 输入备忘录文本
2. 上传高驰截图
3. 点击"开始分析"
4. 查看AI分析结果
5. 点击"保存记录"

### 视频跑姿分析
1. 点击"新建分析" → 选择"分析视频"
2. 上传跑步视频
3. 选择拍摄角度（侧面/背面）
4. 点击"开始分析"
5. 查看分析结果（可视化图 + 数值指标 + AI评价）
6. 点击"保存记录"

### 历史记录
- 查看所有记录列表
- 搜索和筛选记录
- 点击记录查看详情
- 自动关联同一次跑步的记录

### 数据统计
- 查看总览指标
- 查看趋势图表

### 智能指导
- 查看本周训练总结
- 查看趋势分析
- 获取下周训练建议

## 📁 项目结构

```
runningAgent/
├── frontend/          # Electron + React前端
├── backend/           # Python FastAPI后端
├── database/          # SQLite数据库
├── uploads/           # 上传文件存储
├── config.json        # 配置文件（已配置你的信息）
└── README.md
```

## ⚙️ 配置

配置文件：`config.json`

已包含你的个人信息：
- 姓名、年龄、身高、体重
- 心率数据
- 训练目标
- 个人最佳成绩
- Qwen API配置

## 📝 文档

- `INSTALL.md` - 详细安装指南
- `QUICK_START.md` - 快速开始指南
- `FINAL_STATUS.md` - 功能完成状态
- `COMPLETE.md` - 完成总结
- `requirements.md` - 产品需求文档

## 🎯 功能清单

- ✅ 备忘录分析（完整）
- ✅ 视频跑姿分析（完整，MediaPipe + Qwen）
- ✅ 历史记录（完整）
- ✅ 数据统计（完整）
- ✅ 智能指导（完整）
- ✅ 记录关联（完整）

## 📌 注意事项

1. **Qwen API**：确保config.json中的API Key正确
2. **MediaPipe**：首次使用会下载模型，需要一些时间
3. **文件存储**：所有上传文件保存在 `uploads/` 目录
4. **数据库**：SQLite文件在 `database/running_agent.db`

## 🐛 问题排查

遇到问题请参考 `INSTALL.md` 中的常见问题部分。

---

**版本**：v1.0.0  
**状态**：✅ 全部完成，可以直接使用！
