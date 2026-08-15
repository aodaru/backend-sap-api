"""Cliente frontend simulado para descargas binarias de templates."""

from dataclasses import dataclass
from re import search


@dataclass
class DownloadedBlob:
    filename: str
    content_type: str
    blob: bytes


def download_template(client, path: str, api_key: str) -> DownloadedBlob:
    """Envía API key, consume bytes como Blob y nunca llama ``response.json``."""
    response = client.get(path, headers={"X-API-Key": api_key})
    response.raise_for_status()
    disposition = response.headers["content-disposition"]
    match = search(r"filename=([^;]+)", disposition)
    if not match:
        raise ValueError("Content-Disposition sin nombre de archivo")
    return DownloadedBlob(match.group(1), response.headers["content-type"], bytes(response.content))
