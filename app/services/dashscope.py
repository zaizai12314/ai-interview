import dashscope
from http import HTTPStatus
from app.config import settings

dashscope.api_key = settings.dashscope_api_key


async def embed_text(text: str) -> list[float]:
    """将文本向量化为 1536 维向量"""
    return _embed(text)


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """批量向量化"""
    resp = dashscope.TextEmbedding.call(
        model=settings.dashscope_embedding_model,
        input=texts,
    )
    if resp.status_code == HTTPStatus.OK:
        return [e["embedding"] for e in resp.output["embeddings"]]
    raise RuntimeError(f"Batch embedding failed: {resp.code} - {resp.message}")


def embed_text_sync(text: str) -> list[float]:
    """同步向量化（供 Celery 使用）"""
    return _embed(text)


def _embed(text: str) -> list[float]:
    """embed_text 底层实现（同步，DashScope SDK 本身就是同步的）"""
    resp = dashscope.TextEmbedding.call(
        model=settings.dashscope_embedding_model,
        input=text,
    )
    if resp.status_code == HTTPStatus.OK:
        return resp.output["embeddings"][0]["embedding"]
    raise RuntimeError(f"Embedding failed: {resp.code} - {resp.message}")
