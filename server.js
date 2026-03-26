const express = require('express');
const path = require('path');
const http = require('http');

const app = express();
const PORT = 3000;

app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/health', (req, res) => {
    http.get('http://localhost:8000/api/health', (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => res.json(JSON.parse(data)));
    }).on('error', () => res.json({ status: 'ok', drawthings: 'disconnected' }));
});

app.get('/api/config', (req, res) => {
    http.get('http://localhost:8000/api/config', (apiRes) => {
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
            port: 8000,
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
    http.get('http://localhost:8000/api/images', (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => res.json(JSON.parse(data)));
    }).on('error', () => res.json([]));
});

app.get('/api/models', (req, res) => {
    http.get('http://localhost:8000/api/models', (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => res.json(JSON.parse(data)));
    }).on('error', () => res.json({ models: [], current: '' }));
});

app.get('/api/samplers', (req, res) => {
    http.get('http://localhost:8000/api/samplers', (apiRes) => {
        let data = '';
        apiRes.on('data', chunk => data += chunk);
        apiRes.on('end', () => res.json(JSON.parse(data)));
    }).on('error', () => res.json({ samplers: [] }));
});

app.post('/api/generate', (req, res) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
        const options = {
            hostname: 'localhost',
            port: 8000,
            path: '/api/generate',
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': body.length }
        };
        const proxyReq = http.request(options, (proxyRes) => {
            let data = '';
            proxyRes.on('data', chunk => data += chunk);
            proxyRes.on('end', () => {
                res.status(proxyRes.statusCode).json(JSON.parse(data));
            });
        });
        proxyReq.write(body);
        proxyReq.end();
    });
});

app.post('/api/img2img', (req, res) => {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
        const options = {
            hostname: 'localhost',
            port: 8000,
            path: '/api/img2img',
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Content-Length': body.length }
        };
        const proxyReq = http.request(options, (proxyRes) => {
            let data = '';
            proxyRes.on('data', chunk => data += chunk);
            proxyRes.on('end', () => {
                res.status(proxyRes.statusCode).json(JSON.parse(data));
            });
        });
        proxyReq.write(body);
        proxyReq.end();
    });
});

app.get('/api/image/:filename', (req, res) => {
    http.get(`http://localhost:8000/api/image/${req.params.filename}`, (apiRes) => {
        res.setHeader('Content-Type', apiRes.headers['content-type'] || 'image/png');
        apiRes.pipe(res);
    }).on('error', () => res.status(404).json({ error: 'Not found' }));
});

app.listen(PORT, () => {
    console.log(`Draw Things Web running at http://localhost:${PORT}`);
    console.log(`FastAPI backend should be running on port 8000`);
});
