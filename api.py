from __future__ import annotations
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from .config import load_config, AppCfg
from .pipeline import generate_dataset

app = FastAPI(
    title="SynthDocs API",
    description="Generate synthetic documents for testing OCR systems",
    version="1.0.0",
)


class GenerateRequest(BaseModel):
    count: int = 40
    prompt: str = ""
    mix: Optional[dict] = None
    llm_provider: Optional[str] = None
    output_mode: Optional[str] = None
    local_destination: Optional[str] = None
    s3_bucket: Optional[str] = None


class DocumentResult(BaseModel):
    doc_id: str
    filename: str
    local_path: Optional[str] = None
    url: Optional[str] = None


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    documents: list[DocumentResult]


def get_config() -> AppCfg:
    config_path = os.getenv("CONFIG_PATH", "config.yaml")
    if not Path(config_path).exists():
        config_path = "config_dev.yaml"
    return load_config(Path(config_path))


def override_config(cfg: AppCfg, request: GenerateRequest) -> AppCfg:
    cfg_dict = cfg.model_dump()

    if request.count:
        cfg_dict["dataset"]["count"] = request.count

    if request.prompt:
        cfg_dict["dataset"]["prompt"] = request.prompt

    if request.mix:
        cfg_dict["dataset"]["mix"] = request.mix

    if request.llm_provider:
        cfg_dict["llm"]["provider"] = request.llm_provider

    if request.output_mode:
        cfg_dict["output"]["mode"] = request.output_mode

    if request.local_destination:
        cfg_dict["output"]["local"]["destination"] = request.local_destination

    if request.s3_bucket:
        cfg_dict["output"]["s3"]["bucket"] = request.s3_bucket

    return AppCfg.model_validate(cfg_dict)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/generate", response_model=GenerateResponse)
async def generate_documents(request: GenerateRequest):
    job_id = str(uuid.uuid4())[:8]

    try:
        cfg = get_config()
        cfg = override_config(cfg, request)

        output_dir = cfg.output.local.destination
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        generate_dataset(
            cfg, prompt_override=request.prompt, count_override=request.count
        )

        output_path = Path(output_dir)
        results = []

        for doc_dir in sorted(output_path.iterdir()):
            if not doc_dir.is_dir():
                continue

            doc_id = doc_dir.name

            for file_path in doc_dir.rglob("*"):
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(doc_dir))
                    result = {
                        "doc_id": doc_id,
                        "filename": relative_path,
                    }

                    if cfg.output.mode == "s3" and cfg.output.s3.bucket:
                        result["url"] = (
                            f"https://{cfg.output.s3.bucket}.s3.amazonaws.com/{doc_id}/{relative_path}"
                        )
                    else:
                        result["local_path"] = str(file_path)

                    results.append(DocumentResult(**result))

        return GenerateResponse(
            job_id=job_id,
            status="completed",
            documents=results,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "name": "SynthDocs Synthetic Factory",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "generate": "/generate",
        },
    }


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)
