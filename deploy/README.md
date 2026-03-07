# 跑步Agent 云端部署指南

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

## 第三步：上传代码

在**本地**执行：

```bash
cd /Users/changyu/Project/runningAgent

# 上传 deploy、backend 目录
scp -r deploy backend root@你的公网IP:/opt/running-agent/

# 复制环境变量模板并编辑
scp deploy/.env.example root@你的公网IP:/opt/running-agent/deploy/.env
```

---

## 第四步：配置环境变量

在服务器编辑 `/opt/running-agent/deploy/.env`：

```bash
ssh root@你的公网IP
nano /opt/running-agent/deploy/.env
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

**Q: 如何配置 HTTPS？**  
A: 可使用 Nginx 反向代理 + Let's Encrypt，或阿里云 SLB + 证书。

**Q: 数据库迁移？**  
A: 当前为 MySQL，表结构自动创建。从 SQLite 迁移需手动导出导入。
