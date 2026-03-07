# 跑步Agent 云端部署指南

从 [GitHub](https://github.com/changyu496/running-agent) 构建部署的快速流程：

```bash
# 1. 克隆代码
git clone https://github.com/changyu496/running-agent.git
cd running-agent

# 2. 配置环境变量
cp deploy/.env.example deploy/.env
nano deploy/.env   # 填写 MYSQL_PASSWORD、SECRET_KEY、QWEN_API_KEY

# 3. 启动服务
cd deploy && docker compose up -d --build
```

---

## 架构概览

```
阿里云 ECS
├── Docker Compose
│   ├── backend (FastAPI)
│   └── mysql (数据库)
├── 数据卷: uploads, database
└── 定时任务: 备份到 OSS
```

---

## 第一步：准备阿里云 ECS

1. 登录 [阿里云控制台](https://ecs.console.aliyun.com)
2. 创建实例：**共享型 t6**，1核2G，约 50-80 元/月
3. 镜像：**Ubuntu 22.04**
4. 安全组：开放 **22**（SSH）、**80**（HTTP）、**8000**（API，可选）
5. 绑定弹性公网 IP

---

## 第二步：服务器初始化

```bash
# SSH 登录
ssh root@你的公网IP

# 安装 Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker && systemctl start docker

# 安装 Docker Compose 插件
apt install docker-compose-plugin -y
```

---

## 第三步：获取代码

### 方式 A：从 GitHub 克隆（推荐）

在**服务器**执行：

```bash
# 创建目录并克隆
mkdir -p /opt
cd /opt
git clone https://github.com/changyu496/running-agent.git
cd running-agent
```

### 方式 B：本地 SCP 上传

在**本地**执行：

```bash
cd /path/to/running-agent

# 上传 deploy、backend 目录
scp -r deploy backend root@你的公网IP:/opt/running-agent/

# 复制环境变量模板
scp deploy/.env.example root@你的公网IP:/opt/running-agent/deploy/.env
```

---

## 第四步：配置环境变量

在服务器创建并编辑 `.env`：

```bash
cd /opt/running-agent
cp deploy/.env.example deploy/.env
nano deploy/.env
```

必填项：

| 变量 | 说明 | 示例 |
|------|------|------|
| MYSQL_ROOT_PASSWORD | MySQL root 密码 | 随机强密码 |
| MYSQL_PASSWORD | 应用数据库密码 | 随机强密码 |
| SECRET_KEY | JWT 密钥 | `openssl rand -hex 32` 生成 |

可选项：

| 变量 | 说明 |
|------|------|
| QWEN_API_KEY | 通义千问 API Key（AI 分析） |
| CORS_ORIGINS | 允许的跨域源，默认 `*` |

**OSS 存储**（生产环境建议开启，用户上传和生成的文件存到 OSS）：

| 变量 | 说明 |
|------|------|
| STORAGE_TYPE | `oss` 启用 OSS，不设或 `local` 用本地目录 |
| OSS_BUCKET | OSS 桶名 |
| OSS_ENDPOINT | 地域节点，如 `oss-cn-shanghai.aliyuncs.com` |
| OSS_ACCESS_KEY_ID | 阿里云 AccessKey ID |
| OSS_ACCESS_KEY_SECRET | 阿里云 AccessKey Secret |

OSS 桶需设置为**公共读**，或使用签名 URL（当前为公共读直链）。

**默认登录账号**：`changyu496` / `31Eq845F`（首次启动时自动创建）

---

## 第五步：启动服务

```bash
ssh root@你的公网IP
cd /opt/running-agent/deploy
docker compose up -d --build
```

（.env 需在 deploy/ 目录下，docker compose 会自动读取）

等待 1-2 分钟，检查：

```bash
curl http://localhost:8000/api/health
# 应返回 {"status":"healthy"}
```

如需外网访问，确保安全组开放 8000 端口，然后访问 `http://你的公网IP:8000`。

---

## 第六步：客户端连接云端

### 方式 A：修改 config.json（推荐）

在 `frontend/public/config.json` 中设置云端 API 地址：

```json
{
  "apiUrl": "http://你的公网IP:8000"
}
```

然后重新构建前端：`cd frontend && npm run build`。

### 方式 B：构建时指定

```bash
cd frontend
REACT_APP_API_URL=http://你的公网IP:8000 npm run build
```

---

## 第七步：配置备份到 OSS（可选）

1. 在 deploy/.env 中添加：
   ```
   OSS_BUCKET=你的桶名
   OSS_PREFIX=running-agent-backup
   ```

2. 安装 ossutil：<https://help.aliyun.com/document_detail/120075.html>

3. 配置 crontab：
   ```bash
   crontab -e
   # 每天凌晨 2 点备份
   0 2 * * * /opt/running-agent/deploy/scripts/backup-to-oss.sh
   ```

---

## 常见问题

**Q: 拉取 mysql:8.0 超时（dial tcp ... i/o timeout）？**  
A: 国内访问 Docker Hub 易超时。已改用 DaoCloud 镜像 `docker.m.daocloud.io/library/mysql:8.0`。若仍有问题，可配置 Docker 镜像加速：

```bash
# 编辑 /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.nju.edu.cn"
  ]
}
# 重启 Docker: systemctl restart docker
```

**Q: 如何配置 HTTPS？**  
A: 可使用 Nginx 反向代理 + Let's Encrypt，或阿里云 SLB + 证书。

**Q: 数据库迁移？**  
A: 当前为 MySQL，表结构自动创建。从 SQLite 迁移需手动导出导入。
