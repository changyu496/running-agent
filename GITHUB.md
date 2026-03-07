# 上传到 GitHub 与克隆

## 一、在 GitHub 创建仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角 **+** → **New repository**
3. 填写：
   - **Repository name**：`buzhi` 或 `running-agent`（自定）
   - **Description**：步知 - 跑步数据分析与指导工具
   - **Visibility**：Private 或 Public
   - **不要**勾选 "Add a README file"（本地已有）
4. 点击 **Create repository**

---

## 二、推送本地代码

在项目根目录执行（将 `你的用户名` 和 `仓库名` 替换为实际值）：

```bash
cd /Users/changyu/Project/runningAgent

# 添加远程仓库
git remote add origin https://github.com/你的用户名/仓库名.git

# 推送
git push -u origin main
```

若使用 SSH：

```bash
git remote add origin git@github.com:你的用户名/仓库名.git
git push -u origin main
```

---

## 三、从 GitHub 获取代码（新机器/部署）

```bash
git clone https://github.com/你的用户名/仓库名.git
cd 仓库名
```

---

## 四、日常更新流程

**本地修改后推送：**
```bash
git add -A
git commit -m "描述本次修改"
git push
```

**服务器/另一台机器拉取最新代码：**
```bash
cd /opt/running-agent   # 或你的项目路径
git pull
```

---

## 已忽略的文件（不会上传）

- `config.json`（含 API Key 等敏感信息）
- `deploy/.env`（部署环境变量）
- `node_modules/`、`frontend/build/`、`frontend/dist/`
- `backend/dist/`、`backend/build/`（打包输出）
- `uploads/`、`*.db`、`*.log`
