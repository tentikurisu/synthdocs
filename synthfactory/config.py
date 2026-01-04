from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel, Field
import yaml


class MixCfg(BaseModel):
    statement: float = 0.4
    letter: float = 0.6


class StatementCfg(BaseModel):
    min_rows: int = 24
    max_rows: int = 160
    rows_per_page: int = 40
    pages_max: int = 4


class LetterCfg(BaseModel):
    templates: list[str] = Field(default_factory=list)


class DatasetCfg(BaseModel):
    count: int = 40
    out_dir: str = "artifacts"
    group_by_document: bool = True
    prompt: str | None = None
    mix: MixCfg = MixCfg()
    statement: StatementCfg = StatementCfg()
    letter: LetterCfg = LetterCfg()


class OllamaCfg(BaseModel):
    enabled: bool = True
    base_url: str = "http://127.0.0.1:11434"
    model: str = "qwen2.5:1.5b-instruct"
    timeout_s: int = 60


class BedrockCfg(BaseModel):
    enabled: bool = False
    region: str = "eu-west-1"
    model_id: str = "anthropic.claude-3-sonnet-20240307"
    temperature: float = 0.7
    max_tokens: int = 4096


class LLMProviderCfg(BaseModel):
    provider: str = "ollama"
    ollama: OllamaCfg = Field(default_factory=OllamaCfg)
    bedrock: BedrockCfg = Field(default_factory=BedrockCfg)


class LocalOutputCfg(BaseModel):
    destination: str = "./artifacts"


class S3OutputCfg(BaseModel):
    bucket: str = ""


class OutputCfg(BaseModel):
    mode: str = "local"
    local: LocalOutputCfg = Field(default_factory=LocalOutputCfg)
    s3: S3OutputCfg = Field(default_factory=S3OutputCfg)


class JpgCfg(BaseModel):
    width: int = 1654
    height: int = 2339
    quality: int = 85


class RenderCfg(BaseModel):
    watermark_text: str = "SYNTHETIC TEST DOCUMENT • NOT REAL • FOR TESTING ONLY"
    page_size: str = "A4"
    jpg: JpgCfg = JpgCfg()


class NoiseCfg(BaseModel):
    enable: bool = True
    rotate_deg_max: float = 0.6
    blur_radius_max: float = 0.7
    contrast_jitter: float = 0.06
    brightness_jitter: float = 0.05
    speckle_amount: float = 0.0002
    jpeg_recompress: bool = True
    jpeg_quality_min: int = 45
    jpeg_quality_max: int = 85
    partial_crop_prob: float = 0.22
    crop_margin_max: float = 0.08
    smudge_prob: float = 0.35
    smudge_strength: float = 0.25
    downsample_prob: float = 0.35
    downsample_min_scale: float = 0.60
    downsample_max_scale: float = 0.90
    text_damage_prob: float = 0.55
    text_damage_zones_min: int = 2
    text_damage_zones_max: int = 6
    text_damage_strength: float = 0.35
    text_damage_box_min_px: int = 120
    text_damage_box_max_px: int = 620
    font_jitter_prob: float = 0.35
    font_jitter_strength: float = 0.35


class AppCfg(BaseModel):
    dataset: DatasetCfg = DatasetCfg()
    llm: LLMProviderCfg = Field(default_factory=LLMProviderCfg)
    output: OutputCfg = Field(default_factory=OutputCfg)
    render: RenderCfg = Field(default_factory=RenderCfg)
    noise: NoiseCfg = Field(default_factory=NoiseCfg)


def load_config(path: Path) -> AppCfg:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return AppCfg.model_validate(data)
