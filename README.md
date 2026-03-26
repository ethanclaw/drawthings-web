# Draw Things Web

移动端友好的 Web 界面，用于调用本地 Draw Things API 生成图片。

## 功能特点

- 📱 移动端优化的响应式界面
- 🎨 文本生成图片 (txt2img)
- 🔄 图生图 (img2img)
- 📁 可配置的输出路径
- 🖼️ 图片预览和下载
- ⚙️ Draw Things API 地址配置
- 🐳 Docker 部署支持

## 快速开始

### 1. 安装依赖

```bash
# 安装 Node.js 依赖 (前端)
npm install

# 安装 Python 依赖 (后端)
cd server
pip install -r requirements.txt
cd ..
```

### 2. 配置 Draw Things

1. 在 Mac/iPad 上打开 Draw Things 应用
2. 进入 Settings → Server → 启用 HTTP Server
3. 确认端口为 7860（默认）

### 3. 启动服务

```bash
# 终端 1: 启动 FastAPI 后端
cd server
python -m uvicorn main:app --reload --port 8002

# 终端 2: 启动 Express 前端
npm start
```

### 4. 访问页面

- 本地访问: http://localhost:3002
- 同一网络下其他设备: http://YOUR_IP:3002

## Docker 部署

### 目录结构

```
~/Workspace/drawthings-ui/
├── config/
│   └── config.yaml     # 配置文件
├── images/             # 图片目录
│   ├── txt2img/
│   └── img2img/
├── public/
├── server/
│   ├── main.py
│   └── requirements.txt
├── server.js
├── Dockerfile
├── docker-compose.yml
└── package.json
```

### 配置文件 (config/config.yaml)

```yaml
app:
  port: 3002

backend:
  port: 8002
  api_base: "http://host.docker.internal:7860"

storage:
  output_path: "~/Workspace/drawthings-ui/images"  # 宿主机路径 (Draw Things 用)
  read_path: "/app/images"                          # 容器内路径 (Express 用)
```

### 启动 Docker

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### 端口

| 服务 | Docker 端口 |
|------|-------------|
| Express | 3002 |
| FastAPI | 8002 |

## 使用说明

1. **生成** - 输入提示词生成图片
2. **图生图** - 上传参考图片生成
3. **画廊** - 查看已生成图片并下载
4. **设置** - 配置输出路径和 API 地址

## 项目结构

```
drawthings-web/
├── config/
│   └── config.yaml     # 配置文件
├── images/              # 图片目录 (挂载点)
│   ├── txt2img/
│   └── img2img/
├── public/
│   └── index.html      # 前端页面
├── server/
│   ├── main.py        # FastAPI 后端
│   └── requirements.txt
├── server.js          # Express 前端服务器
├── Dockerfile         # Express 镜像构建
├── docker-compose.yml # Docker 部署配置
└── package.json
```

## API 端点

- `POST /api/generate` - 生成图片
- `POST /api/img2img` - 图生图
- `GET /api/images` - 获取图片列表
- `GET /api/image/:filepath` - 获取图片
- `DELETE /api/image/:filepath` - 删除图片
- `GET /api/config` - 获取配置
- `POST /api/config` - 更新配置
- `GET /api/health` - 健康检查
- `GET /api/job/:job_id` - 获取任务状态
- `GET /api/models` - 获取可用模型
- `GET /api/samplers` - 获取采样器列表

## 云端部署

通过 Cloudflare Tunnel 暴露服务：

```yaml
# ~/.cloudflared/config.yml
ingress:
  - hostname: drawthings.qinxincan.com
    service: http://localhost:3002
  - service: http_status:404
```

## License

MIT
