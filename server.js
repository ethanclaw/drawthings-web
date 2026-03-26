const express = require('express');
const path = require('path');
const http = require('http');
const yaml = require('js-yaml');
const fs = require('fs');

const app = express();

const CONFIG_PATH = process.env.CONFIG_PATH || path.join(__dirname, 'config', 'config.yaml');
const config = yaml.load(fs.readFileSync(CONFIG_PATH, 'utf8'));

const PORT = config.app.port;
const BACKEND_PORT = config.backend.port;
const API_BASE = config.backend.api_base;

app.use(express.json({ limit: '50mb' }));
app.use(express.static(path.join(__dirname, 'public')));

const backendUrl = `http://localhost:${BACKEND_PORT}`;

app.get('/api/health', (req, res) => {
    http.get(`${backendUrl}/api/health`, (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => res.json(JSON.parse(data)));
    }).on('error', () => res.json({ status: 'ok', drawthings: 'disconnected' }));
});

app.get('/api/config', (req, res) => {
    http.get(`${backendUrl}/api/config`, (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => res.json(JSON.parse(data)));
    }).on('error', () => res.status(500).json({ error: 'Backend offline' }));
});

app.post('/api/config', (req, res) => {
    const body = [];
    req.on('data', chunk => body.push(chunk));
    req.on('end', () => {
        const postData = Buffer.concat(body).toString();
        const options = {
            hostname: 'localhost',
            port: BACKEND_PORT,
            path: '/api/config',
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': postData.length }
        };
        const proxyReq = http.request(options, (proxyRes) => {
            let data = '';
            proxyRes.on('data', chunk => data += chunk);
            proxyRes.on('end', () => res.json(JSON.parse(data)));
        });
        proxyReq.write(postData);
        proxyReq.end();
    });
});

app.get('/api/images', (req, res) => {
    const queryParams = new URLSearchParams(req.query).toString();
    const path = queryParams ? `/api/images?${queryParams}` : '/api/images';
    http.get(`${backendUrl}${path}`, (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => res.json(JSON.parse(data)));
    }).on('error', () => res.json([]));
});

app.get('/api/models', (req, res) => {
    http.get(`${backendUrl}/api/models`, (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => res.json(JSON.parse(data)));
    }).on('error', () => res.json({ models: [], current: '' }));
});

app.get('/api/samplers', (req, res) => {
    http.get(`${backendUrl}/api/samplers`, (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => res.json(JSON.parse(data)));
    }).on('error', () => res.json({ samplers: [] }));
});

app.post('/api/generate', (req, res) => {
    const body = JSON.stringify(req.body);
    const options = {
        hostname: 'localhost',
        port: BACKEND_PORT,
        path: '/api/generate',
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) }
    };
    const proxyReq = http.request(options, (proxyRes) => {
        let data = '';
        proxyRes.on('data', chunk => data += chunk);
        proxyRes.on('end', () => {
            res.status(proxyRes.statusCode).json(JSON.parse(data));
        });
    });
    proxyReq.on('error', (e) => res.status(500).json({ error: e.message }));
    proxyReq.write(body);
    proxyReq.end();
});

app.post('/api/img2img', (req, res) => {
    const body = JSON.stringify(req.body);
    const options = {
        hostname: 'localhost',
        port: BACKEND_PORT,
        path: '/api/img2img',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(body)
        }
    };
    const proxyReq = http.request(options, (proxyRes) => {
        const dataChunks = [];
        proxyRes.on('data', chunk => dataChunks.push(chunk));
        proxyRes.on('end', () => {
            const data = Buffer.concat(dataChunks);
            try {
                res.status(proxyRes.statusCode).json(JSON.parse(data));
            } catch (e) {
                res.status(500).json({ error: 'Parse error', detail: e.message });
            }
        });
    });
    proxyReq.on('error', (e) => {
        res.status(500).json({ error: 'Proxy error', detail: e.message });
    });
    proxyReq.write(body);
    proxyReq.end();
});

app.get('/api/image/*', (req, res) => {
    const filepath = req.params[0];
    http.get(`${backendUrl}/api/image/${filepath}`, (apiRes) => {
        res.setHeader('Content-Type', apiRes.headers['content-type'] || 'image/png');
        apiRes.pipe(res);
    }).on('error', () => res.status(404).json({ error: 'Not found' }));
});

app.delete('/api/image/*', (req, res) => {
    const filepath = req.params[0];
    const options = {
        hostname: 'localhost',
        port: BACKEND_PORT,
        path: `/api/image/${filepath}`,
        method: 'DELETE'
    };
    const proxyReq = http.request(options, (proxyRes) => {
        let data = '';
        proxyRes.on('data', chunk => data += chunk);
        proxyRes.on('end', () => {
            try {
                res.status(proxyRes.statusCode).json(JSON.parse(data));
            } catch {
                res.status(proxyRes.statusCode).send(data);
            }
        });
    });
    proxyReq.on('error', () => res.status(500).json({ error: 'Proxy error' }));
    proxyReq.end();
});

app.get('/api/job/:job_id', (req, res) => {
    http.get(`${backendUrl}/api/job/${req.params.job_id}`, (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => {
            try {
                res.status(apiRes.statusCode).json(JSON.parse(data));
            } catch {
                res.status(apiRes.statusCode).send(data);
            }
        });
    }).on('error', () => res.status(500).json({ error: 'Backend error' }));
});

app.get('/api/jobs', (req, res) => {
    http.get(`${backendUrl}/api/jobs`, (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => {
            try {
                res.json(JSON.parse(data));
            } catch {
                res.status(500).json([]);
            }
        });
    }).on('error', () => res.json([]));
});

app.listen(PORT, () => {
    console.log(`Draw Things Web running at http://localhost:${PORT}`);
    console.log(`FastAPI backend running at http://localhost:${BACKEND_PORT}`);
});
