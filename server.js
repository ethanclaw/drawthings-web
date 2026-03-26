const express = require('express');
const path = require('path');
const http = require('http');

const app = express();
const PORT = 3000;

app.use(express.json({ limit: '50mb' }));
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
    const queryParams = new URLSearchParams(req.query).toString();
    const path = queryParams ? `/api/images?${queryParams}` : '/api/images';
    http.get(`http://localhost:8000${path}`, (apiRes) => {
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
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => {
        const body = Buffer.concat(chunks);
        const options = {
            hostname: 'localhost',
            port: 8000,
            path: '/api/img2img',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': body.length
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
});

app.get('/api/image/*', (req, res) => {
    const filepath = req.params[0];
    http.get(`http://localhost:8000/api/image/${filepath}`, (apiRes) => {
        res.setHeader('Content-Type', apiRes.headers['content-type'] || 'image/png');
        apiRes.pipe(res);
    }).on('error', () => res.status(404).json({ error: 'Not found' }));
});

app.delete('/api/image/*', (req, res) => {
    const filepath = req.params[0];
    const options = {
        hostname: 'localhost',
        port: 8000,
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

app.listen(PORT, () => {
    console.log(`Draw Things Web running at http://localhost:${PORT}`);
    console.log(`FastAPI backend should be running on port 8000`);
});
