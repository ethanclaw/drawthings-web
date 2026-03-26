from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx
import os
import json
import uuid
from pathlib import Path

app = FastAPI()

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

config = {
    "output_path": os.path.expanduser("~/Downloads"),
    "api_base": "http://localhost:7860"
}

@app.get("/api/config")
async def get_config():
    return config

@app.post("/api/config")
async def update_config(req: ConfigRequest):
    config["output_path"] = req.output_path
    config["api_base"] = req.api_base
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

@app.post("/api/generate")
async def generate_image(req: GenerateRequest):
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    output_path = req.output_path or config["output_path"]
    Path(output_path).mkdir(parents=True, exist_ok=True)

    payload = {
        "prompt": req.prompt,
        "negative_prompt": req.negative_prompt,
        "seed": req.seed,
        "width": req.width,
        "height": req.height,
        "steps": req.steps,
        "guidance_scale": req.guidance_scale,
        "sampler": req.sampler,
        "batch_count": req.batch_count
    }

    if req.model:
        payload["model"] = req.model

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{config['api_base']}/sdapi/v1/txt2img",
                json=payload
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            result = response.json()

            if "images" in result and len(result["images"]) > 0:
                image_data = result["images"][0]
                filename = f"drawthings_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(output_path, filename)

                import base64
                img_bytes = base64.b64decode(image_data)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)

                return {
                    "status": "success",
                    "filename": filename,
                    "filepath": filepath,
                    "url": f"/api/image/{filename}"
                }
            else:
                raise HTTPException(status_code=500, detail="No image in response")

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot connect to Draw Things API. Make sure it's running on this device.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/img2img")
async def img2img(req: Img2ImgRequest):
    if not req.prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    if not req.image:
        raise HTTPException(status_code=400, detail="Image is required")

    output_path = req.output_path or config["output_path"]
    Path(output_path).mkdir(parents=True, exist_ok=True)

    payload = {
        "prompt": req.prompt,
        "negative_prompt": req.negative_prompt,
        "init_images": [req.image],
        "denoising_strength": req.denoising_strength,
        "seed": req.seed,
        "width": req.width,
        "height": req.height,
        "steps": req.steps,
        "guidance_scale": req.guidance_scale,
        "sampler": req.sampler
    }

    if req.model:
        payload["model"] = req.model

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{config['api_base']}/sdapi/v1/img2img",
                json=payload
            )

            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            result = response.json()

            if "images" in result and len(result["images"]) > 0:
                image_data = result["images"][0]
                filename = f"drawthings_img2img_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(output_path, filename)

                import base64
                img_bytes = base64.b64decode(image_data)
                with open(filepath, "wb") as f:
                    f.write(img_bytes)

                return {
                    "status": "success",
                    "filename": filename,
                    "filepath": filepath,
                    "url": f"/api/image/{filename}"
                }
            else:
                raise HTTPException(status_code=500, detail="No image in response")

    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot connect to Draw Things API. Make sure it's running on this device.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/image/{filename}")
async def get_image(filename: str):
    from fastapi.responses import FileResponse
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(config["output_path"], safe_filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(filepath, media_type="image/png")

@app.get("/api/images")
async def list_images():
    output_path = config["output_path"]
    if not os.path.exists(output_path):
        return []

    images = []
    for f in sorted(Path(output_path).glob("drawthings_*.png"), key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
        images.append({
            "filename": f.name,
            "url": f"/api/image/{f.name}",
            "created": f.stat().st_ctime
        })
    return images

@app.delete("/api/image/{filename}")
async def delete_image(filename: str):
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(config["output_path"], safe_filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        os.remove(filepath)
        return {"status": "success", "deleted": safe_filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
