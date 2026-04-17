# 部署指南

## 目录
- [环境准备](#环境准备)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [Nginx 配置](#nginx-配置)
- [安全加固](#安全加固)
- [监控与日志](#监控与日志)

---

## 环境准备

### 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Windows 10, Ubuntu 20.04+, macOS 11+ | Ubuntu 22.04 LTS |
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 10 GB | 50 GB+ |
| Python | 3.8+ | 3.10+ |
| Node.js | 16+ | 18+ |

### 端口要求

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8000 | FastAPI 服务 |
| 前端开发 | 5175 | Vite 开发服务器 |
| 前端生产 | 80/443 | Nginx 或其他 Web 服务器 |

---

## 开发环境部署

### 后端部署

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd 实验室Agent
   ```

2. **创建虚拟环境**
   ```bash
   cd backend
   python -m venv .venv
   
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   
   创建 `.env` 文件：
   ```env
   DATABASE_URL=sqlite:///./data/lab_agent.db
   SECRET_KEY=your-secret-key-change-this-in-production
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_BASE_URL=https://api.openai.com/v1
   ```

5. **初始化数据库**
   ```bash
   cd scripts
   python init_db.py create
   ```

6. **启动开发服务器**
   ```bash
   cd ..
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 前端部署

1. **安装依赖**
   ```bash
   cd frontend
   npm install
   ```

2. **启动开发服务器**
   ```bash
   npm run dev
   ```

3. **访问应用**
   - 前端: http://localhost:5175
   - 后端 API: http://localhost:8000
   - API 文档: http://localhost:8000/docs

---

## 生产环境部署

### 后端生产部署

#### 1. 使用 Gunicorn + Uvicorn Workers

安装 Gunicorn：
```bash
pip install gunicorn
```

创建启动脚本 `start_backend.sh`：
```bash
#!/bin/bash
cd /path/to/backend
source .venv/bin/activate
export PYTHONPATH=/path/to/backend

gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 600 \
    --access-logfile /var/log/lab_agent/access.log \
    --error-logfile /var/log/lab_agent/error.log
```

#### 2. 使用 Systemd 管理服务

创建服务文件 `/etc/systemd/system/lab-agent-backend.service`：
```ini
[Unit]
Description=Lab Agent Backend Service
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
Environment="PATH=/path/to/backend/.venv/bin"
ExecStart=/path/to/backend/.venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 600
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable lab-agent-backend
sudo systemctl start lab-agent-backend
sudo systemctl status lab-agent-backend
```

### 前端生产部署

#### 1. 构建生产版本

```bash
cd frontend
npm run build
```

构建产物将输出到 `frontend/dist` 目录。

#### 2. 使用 Nginx 部署

创建 Nginx 配置文件 `/etc/nginx/sites-available/lab-agent`：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持（如需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /path/to/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 安全头部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/lab-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Docker 部署

### Docker Compose

创建 `docker-compose.yml`：
```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: lab-agent-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/lab_agent.db
      - SECRET_KEY=${SECRET_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_BASE_URL=${OPENAI_BASE_URL}
    volumes:
      - ./data:/app/data
      - ./config.json:/app/config.json
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: lab-agent-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  data:
```

### 后端 Dockerfile

创建 `backend/Dockerfile`：
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 前端 Dockerfile

创建 `frontend/Dockerfile`：
```dockerfile
# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
```

创建 `frontend/nginx.conf`：
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json application/javascript;
}
```

### 启动容器

创建 `.env` 文件：
```env
SECRET_KEY=your-secret-key
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

启动服务：
```bash
docker-compose up -d
```

查看日志：
```bash
docker-compose logs -f
```

---

## Nginx 配置

### HTTPS 配置

使用 Let's Encrypt 免费证书：

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Certbot 会自动更新 Nginx 配置。

### 完整 HTTPS 配置

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
    }

    # 限流配置
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    location /api {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        # ... 其他配置
    }
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 安全加固

### 1. 环境变量安全

- 永远不要将 `.env` 文件提交到版本控制
- 使用强密码和密钥
- 定期轮换密钥
- 使用密钥管理服务（如 AWS Secrets Manager, HashiCorp Vault）

### 2. 数据库安全

- 生产环境使用 PostgreSQL/MySQL 替代 SQLite
- 定期备份数据库
- 使用数据库用户权限最小化原则
- 启用数据库连接加密

### 3. API 安全

- 使用 HTTPS
- 实现速率限制（已内置）
- 验证所有输入
- 使用 JWT 认证
- 实现 CORS 限制

### 4. 文件上传安全

- 限制文件大小
- 验证文件类型
- 扫描上传的文件（使用 ClamAV 等）
- 隔离上传目录

### 5. 系统安全

- 定期更新系统和依赖
- 使用防火墙限制访问
- 启用日志监控
- 使用非 root 用户运行服务

---

## 监控与日志

### 日志配置

后端日志配置（使用 Python logging）：

```python
# backend/app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler
import sys

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件输出（轮转）
    file_handler = RotatingFileHandler(
        '/var/log/lab_agent/app.log',
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(console_formatter)
    logger.addHandler(file_handler)
    
    return logger
```

### 健康检查端点

后端已内置根路径健康检查：
```
GET /
```

响应：
```json
{
  "message": "实验室智能助手 - 后端 API",
  "version": "2.0"
}
```

### 监控工具推荐

- **应用监控**: Prometheus + Grafana
- **日志聚合**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **错误追踪**: Sentry
- **性能监控**: New Relic, Datadog

---

## 下一步

- 查看 [常见问题解答](./faq.md) 解决部署问题
- 查看 [配置指南](../backend/README.md#配置指南) 了解配置详情
