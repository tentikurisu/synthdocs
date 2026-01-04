from __future__ import annotations
from pathlib import Path
from typing import Optional
from io import BytesIO

import boto3
from botocore.config import Config


class StorageClient:
    def __init__(
        self,
        mode: str = "local",
        local_destination: str = "./artifacts",
        s3_bucket: Optional[str] = None,
        s3_region: str = "eu-west-1",
    ):
        self.mode = mode
        self.local_destination = Path(local_destination)
        self.s3_bucket = s3_bucket
        self.s3_region = s3_region

        if self.mode == "s3" and self.s3_bucket:
            self.s3_client = boto3.client(
                "s3",
                region_name=s3_region,
                config=Config(retries={"max_attempts": 3}),
            )
        else:
            self.s3_client = None

    def save_artifacts(
        self, doc_id: str, files: dict[str, bytes]
    ) -> list[dict[str, str]]:
        if self.mode == "s3" and self.s3_bucket and self.s3_client:
            return self._save_s3(doc_id, files)
        else:
            return self._save_local(doc_id, files)

    def _save_local(self, doc_id: str, files: dict[str, bytes]) -> list[dict[str, str]]:
        output_path = self.local_destination / doc_id
        output_path.mkdir(parents=True, exist_ok=True)
        results = []
        for filename, content in files.items():
            filepath = output_path / filename
            filepath.write_bytes(content)
            results.append(
                {
                    "doc_id": doc_id,
                    "filename": filename,
                    "local_path": str(filepath),
                }
            )
        return results

    def _save_s3(self, doc_id: str, files: dict[str, bytes]) -> list[dict[str, str]]:
        results = []
        for filename, content in files.items():
            s3_key = f"{doc_id}/{filename}"
            self.s3_client.upload_fileobj(
                BytesIO(content),
                self.s3_bucket,
                s3_key,
            )
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.s3_bucket, "Key": s3_key},
                ExpiresIn=3600,
            )
            results.append(
                {
                    "doc_id": doc_id,
                    "filename": filename,
                    "url": url,
                }
            )
        return results
