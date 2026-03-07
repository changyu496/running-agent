# 安装和启动指南

## 📋 前置要求

- **Python**: 3.10 或更高版本
- **Node.js**: 16 或更高版本
- **npm**: 随 Node.js 安装
- **Mac OS**: 10.15 或更高版本

## 🔧 安装步骤

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

**注意**：如果遇到 MediaPipe 安装问题，可以尝试：
```bash
pip install mediapipe --upgrade
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

**注意**：如果遇到 Electron 安装问题，可以尝试：
```bash
npm install electron --save-dev
```

### 3. 初始化数据库

```bash
cd backend
python init_db.py
```

应该看到输出：`数据库初始化完成: ...`

## 🚀 启动应用

### 方式1：分别启动（推荐，便于调试）

**终端1 - 启动后端：**
```bash
cd backend
python main.py
```

看到 `INFO:     Uvicorn running on http://0.0.0.0:8000` 表示后端启动成功。

**终端2 - 启动前端开发服务器：**
```bash
cd frontend
npm run dev:react
```

看到 `Compiled successfully!` 表示前端启动成功。

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

这会自动启动 React 开发服务器和 Electron。

## ✅ 验证安装

1. 后端应该运行在：http://localhost:8000
2. 访问 http://localhost:8000/api/health 应该返回 `{"status": "healthy"}`
3. Electron 应用窗口应该自动打开

## 🐛 常见问题

### Q: pip install 失败？
A: 尝试使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: npm install 失败？
A: 尝试清除缓存：
```bash
rm -rf node_modules package-lock.json
npm install
```

### Q: MediaPipe 安装失败？
A: 确保 Python 版本 >= 3.10，然后：
```bash
pip install --upgrade pip
pip install mediapipe
```

### Q: Electron 启动失败？
A: 检查 Node.js 版本，确保 >= 16

### Q: 后端启动失败？
A: 检查端口 8000 是否被占用：
```bash
lsof -i :8000
```

### Q: 数据库初始化失败？
A: 确保有写入权限，手动创建 database 目录：
```bash
mkdir -p database
```

## 📝 下一步

安装完成后，参考 `QUICK_START.md` 开始使用应用。
