# 跑步Agent 打包说明

## 一、打包步骤（在当前 Mac 上）

### 1. 环境要求

- **Node.js 18+**（electron-builder 需要）
- **Python 3.9+**（仅打包时需要）
- ffmpeg（`brew install ffmpeg`）
- 已安装依赖：`cd frontend && npm install`、`cd backend && pip install -r requirements.txt`

### 2. 一键打包（推荐）

```bash
./package-all.sh
```

该脚本会：打包 Python 后端为独立可执行文件 → 打包 React 前端 → 生成 Electron .app

### 3. 输出位置

- `frontend/dist/` 目录下会生成：
  - `跑步Agent.app` - **可直接双击运行，无需安装 Python**
  - `跑步Agent-1.0.0.dmg` - 安装镜像
  - `跑步Agent-1.0.0-mac.zip` - 压缩包

---

## 二、在另一台 Mac 上使用

1. 将 `跑步Agent.app` 复制到目标 Mac
2. 双击即可运行
3. **视频分析**需目标 Mac 已安装 ffmpeg：`brew install ffmpeg`

> 无需安装 Python，后端已打包为独立可执行文件。

---

## 三、ffmpeg 说明

视频跑姿分析依赖 ffmpeg 做旋转和转码。目标 Mac 需安装：`brew install ffmpeg`。若未安装，视频分析可能失败，其他功能正常。

---

## 四、图标

- 当前图标：`frontend/public/icon.png`（512x512）
- 替换：用任意 512x512 或 1024x1024 的 PNG 覆盖该文件后重新打包即可

### 图标设计建议

1. **跑步剪影**：橙色/深色跑者轮廓，简洁现代（当前已采用）
2. **鞋印**：抽象跑鞋或脚印，体现运动感
3. **数据图表**：折线/柱状图元素，体现数据分析
4. **品牌色**：橙色 (#f97316) 为主，与界面一致

---

## 五、常见问题

- **Q: 双击 .app 后无法启动？**  
  A: 检查是否已安装 Python 3 和依赖。可在终端运行：`python3 跑步Agent.app/Contents/Resources/backend/main.py` 测试后端是否正常。

- **Q: 视频分析失败？**  
  A: 目标 Mac 需安装 ffmpeg：`brew install ffmpeg`。

- **Q: 如何打包成不需要 Python 的独立应用？**  
  A: 需用 PyInstaller 将 backend 打成可执行文件，再通过 extraResources 打包进 .app，配置较复杂，可后续单独实现。
