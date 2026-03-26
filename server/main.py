from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import httpx
import asyncio
import os
import json
import yaml
import uuid
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()
CONFIG_FILE = os.environ.get("CONFIG_PATH", "/app/config/config.yaml")
executor = ThreadPoolExecutor(max_workers=3)

jobs = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    seed: int = -1
    output_path: str = ""
    width: int = 1024
    height: int = 1024
    steps: int = 8
    guidance_scale: float = 1.0
    sampler: str = "UniPC Trailing"
    model: str = ""
    batch_count: int = 1

class Img2ImgRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    image: str
    denoising_strength: float = 0.6
    seed: int = -1
    output_path: str = ""
    width: int = 1024
    height: int = 1024
    steps: int = 8
    guidance_scale: float = 1.0
    sampler: str = "UniPC Trailing"
    model: str = ""

class ConfigRequest(BaseModel):
    output_path: str
    api_base: str = "http://localhost:7860"

def load_config():
    global config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = yaml.safe_load(f)
                config["output_path"] = os.path.expanduser(loaded.get("storage", {}).get("output_path", "~/Workspace/drawthings-ui/images"))
                config["read_path"] = loaded.get("storage", {}).get("read_path", "/app/images")
                config["api_base"] = loaded.get("backend", {}).get("api_base", "http://localhost:7860")
        except Exception as e:
            print(f"Error loading config: {e}")

def save_config():
    try:
        with open(CONFIG_FILE, 'w') as f:
            yaml.safe_dump(config, f, default_flow_style=False)
    except Exception as e:
        print(f"Error saving config: {e}")

config = {
    "output_path": os.path.expanduser("~/Workspace/drawthings-ui/images"),
    "read_path": "/app/images",
    "api_base": "http://localhost:7860"
}

load_config()

@app.get("/api/config")
async def get_config():
    return {
        "output_path": config["output_path"],
        "read_path": config["read_path"],
        "api_base": config["api_base"]
    }

@app.post("/api/config")
async def update_config(req: ConfigRequest):
    config["output_path"] = os.path.expanduser(req.output_path)
    config["api_base"] = req.api_base
    save_config()
    return {"status": "ok", "config": config}

@app.get("/api/models")
async def get_models():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{config['api_base']}/sdapi/v1/options")
            if response.status_code == 200:
                options = response.json()
                current_model = options.get("model", "")
                return {"models": [current_model], "current": current_model}
    except:
        pass
    return {"models": [], "current": ""}

@app.get("/api/samplers")
async def get_samplers():
    samplers = [
        "UniPC Trailing",
        "Euler",
        "Euler a",
        "DPM++ 2M Karras",
        "DPM++ SDE Karras",
        "DDIM",
        "PLMS"
    ]
    return {"samplers": samplers}

def run_generate_sync(job_id: str, req_data: dict):
    import base64
    try:
        payload = {
            "prompt": req_data["prompt"],
            "negative_prompt": req_data.get("negative_prompt", ""),
            "seed": req_data.get("seed", -1),
            "width": req_data.get("width", 1024),
            "height": req_data.get("height", 1024),
            "steps": req_data.get("steps", 8),
            "guidance_scale": req_data.get("guidance_scale", 1.0),
            "sampler": req_data.get("sampler", "UniPC Trailing"),
            "batch_count": req_data.get("batch_count", 1)
        }
        if req_data.get("model"):
            payload["model"] = req_data["model"]

        jobs[job_id]["status"] = "processing"

        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{config['api_base']}/sdapi/v1/txt2img",
                json=payload
            )

            if response.status_code != 200:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = response.text
                return

            result = response.json()

            if "images" in result and len(result["images"]) > 0:
                image_data = result["images"][0]
                filename = f"drawthings_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(req_data["output_path"], filename)

                img_bytes = base64.b64decode(image_data)
                Path(filepath).parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)

                jobs[job_id]["status"] = "completed"
                jobs[job_id]["result"] = {
                    "filename": filename,
                    "filepath": filepath,
                    "url": f"/api/image/{filename}"
                }
            else:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = "No image in response"

    except httpx.ConnectError:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = "Cannot connect to Draw Things API"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.post("/api/generate")
async def generate_image(req: GenerateRequest):
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    output_path = req.output_path or config["output_path"]
    output_path = os.path.join(output_path, "txt2img")
    Path(output_path).mkdir(parents=True, exist_ok=True)

    job_id = str(uuid.uuid4())[:8]
    req_data = req.model_dump()
    req_data["output_path"] = output_path

    jobs[job_id] = {
        "status": "pending",
        "type": "txt2img",
        "prompt": req.prompt,
        "created": datetime.now().isoformat(),
        "result": None,
        "error": None
    }

    executor.submit(run_generate_sync, job_id, req_data)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Task submitted, use /api/job/{job_id} to check status"
    }

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]

@app.get("/api/jobs")
async def list_jobs():
    return list(jobs.values())[-20:]

def run_img2img_sync(job_id: str, req_data: dict):
    import base64
    try:
        payload = {
            "prompt": req_data["prompt"],
            "negative_prompt": req_data.get("negative_prompt", ""),
            "init_images": [req_data["image"]],
            "denoising_strength": req_data.get("denoising_strength", 0.6),
            "seed": req_data.get("seed", -1),
            "width": req_data.get("width", 1024),
            "height": req_data.get("height", 1024),
            "steps": req_data.get("steps", 8),
            "guidance_scale": req_data.get("guidance_scale", 1.0),
            "sampler": req_data.get("sampler", "UniPC Trailing")
        }
        if req_data.get("model"):
            payload["model"] = req_data["model"]

        jobs[job_id]["status"] = "processing"

        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{config['api_base']}/sdapi/v1/img2img",
                json=payload
            )

            if response.status_code != 200:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = response.text
                return

            result = response.json()

            if "images" in result and len(result["images"]) > 0:
                image_data = result["images"][0]
                filename = f"drawthings_img2img_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(req_data["output_path"], filename)

                img_bytes = base64.b64decode(image_data)
                Path(filepath).parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)

                jobs[job_id]["status"] = "completed"
                jobs[job_id]["result"] = {
                    "filename": filename,
                    "filepath": filepath,
                    "url": f"/api/image/{filename}"
                }
            else:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = "No image in response"

    except httpx.ConnectError:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = "Cannot connect to Draw Things API"
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

@app.post("/api/img2img")
async def img2img(req: Img2ImgRequest):
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    if not req.image:
        raise HTTPException(status_code=400, detail="Image is required")

    output_path = req.output_path or config["output_path"]
    output_path = os.path.join(output_path, "img2img")
    Path(output_path).mkdir(parents=True, exist_ok=True)

    job_id = str(uuid.uuid4())[:8]
    req_data = req.model_dump()
    req_data["output_path"] = output_path

    jobs[job_id] = {
        "status": "pending",
        "type": "img2img",
        "prompt": req.prompt,
        "created": datetime.now().isoformat(),
        "result": None,
        "error": None
    }

    executor.submit(run_img2img_sync, job_id, req_data)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Task submitted, use /api/job/{job_id} to check status"
    }

@app.get("/api/image/{filepath:path}")
async def get_image(filepath: str):
    from fastapi.responses import FileResponse
    safe_path = os.path.normpath(filepath)
    full_path = os.path.join(config["read_path"], safe_path)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"Image not found: {full_path}")

    return FileResponse(full_path, media_type="image/png")

@app.delete("/api/image/{filepath:path}")
async def delete_image(filepath: str):
    safe_path = os.path.normpath(filepath)
    full_path = os.path.join(config["read_path"], safe_path)

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        os.remove(full_path)
        return {"status": "success", "deleted": safe_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images")
async def list_images(type: str = "all"):
    read_path = config["read_path"]
    if not os.path.exists(read_path):
        return []

    images = []
    image_exts = ('.png', '.jpg', '.jpeg', '.webp', '.gif')

    for f in Path(read_path).rglob('*'):
        if f.is_file() and f.suffix.lower() in image_exts:
            rel_path = f.relative_to(read_path)
            rel_path_str = str(rel_path).replace('\\', '/')

            if type != "all" and not rel_path_str.startswith(type):
                continue

            images.append({
                "filename": rel_path_str,
                "url": f"/api/image/{rel_path_str}",
                "name": f.name,
                "type": rel_path_str.split('/')[0] if '/' in rel_path_str else "root",
                "created": f.stat().st_ctime,
                "size": f.stat().st_size
            })
    images.sort(key=lambda x: x["created"], reverse=True)
    return images[:50]

@app.get("/api/health")
async def health_check():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{config['api_base']}/")
            if response.status_code == 200:
                return {"status": "ok", "drawthings": "connected"}
    except:
        pass
    return {"status": "ok", "drawthings": "disconnected"}
