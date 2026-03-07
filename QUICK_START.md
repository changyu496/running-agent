# 快速开始指南

## 1. 安装依赖

### 后端依赖
```bash
cd backend
pip install -r requirements.txt
```

### 前端依赖
```bash
cd frontend
npm install
```

## 2. 初始化数据库

```bash
cd backend
python init_db.py
```

## 3. 启动应用

### 方式1：分别启动（推荐开发）

**终端1 - 启动后端：**
```bash
cd backend
python main.py
```

**终端2 - 启动前端：**
```bash
cd frontend
npm run dev:react
```

**终端3 - 启动Electron：**
```bash
cd frontend
npm run dev:electron
```

### 方式2：一键启动（开发模式）

```bash
cd frontend
npm run dev
```

## 4. 使用说明

1. 打开应用后，点击左侧"新建分析"
2. 输入备忘录文本（可选）
3. 上传高驰截图
4. 点击"开始分析"
5. 查看AI分析结果
6. 点击"保存记录"保存

## 5. 常见问题

### Q: 后端启动失败？
A: 检查Python版本（需要3.10+），确保所有依赖已安装

### Q: 前端启动失败？
A: 检查Node.js版本（需要16+），删除node_modules后重新npm install

### Q: Qwen API调用失败？
A: 检查config.json中的API Key是否正确，确保网络连接正常

### Q: 数据库错误？
A: 运行 `python backend/init_db.py` 重新初始化数据库

## 6. 开发进度

- ✅ 项目基础框架
- ✅ 数据库设计
- ✅ 备忘录分析（基础功能）
- ✅ 历史记录（基础功能）
- 🚧 视频分析（开发中）
- 🚧 数据统计（开发中）
- 🚧 智能指导（开发中）
