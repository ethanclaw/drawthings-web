# Draw Things Web

移动端友好的 Web 界面，用于调用本地 Draw Things API 生成图片。

## 功能特点

- 📱 移动端优化的响应式界面
- 🎨 文本生成图片 (txt2img)
- 📁 可配置的输出路径
- 🖼️ 图片预览和下载
- ⚙️ Draw Things API 地址配置

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
python -m uvicorn main:app --reload --port 8000

# 终端 2: 启动 Express 前端
npm start
```

### 4. 访问页面

- 本地访问: http://localhost:3000
- 同一网络下其他设备: http://YOUR_IP:3000

## 使用说明

1. **Generate** - 输入提示词生成图片
2. **Gallery** - 查看已生成图片并下载
3. **Settings** - 配置输出路径和 API 地址

## 项目结构

```
drawthings-web/
├── public/
│   └── index.html      # 前端页面
├── server/
│   ├── main.py        # FastAPI 后端
│   └── requirements.txt
├── server.js          # Express 前端服务器
└── package.json
```

## API 端点

- `POST /api/generate` - 生成图片
- `GET /api/images` - 获取图片列表
- `GET /api/image/:filename` - 下载图片
- `GET /api/config` - 获取配置
- `POST /api/config` - 更新配置
- `GET /api/health` - 健康检查
