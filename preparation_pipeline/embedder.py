"""
Sinh dense + sparse embedding bằng BGE-M3 (BAAI/bge-m3), tự host.

Lý do chọn BGE-M3 thay vì text-embedding-004 (đã bị Google khai tử 14/1/2026)
đã trình bày trong review: tự host được, hỗ trợ tiếng Việt tốt, và quan
trọng nhất - xuất được CẢ dense lẫn sparse vector trong 1 lần encode, dùng
chung cho cả 2 nhánh của hybrid search ở Pipeline 2 mà không cần dựng thêm
hệ BM25 riêng.
"""
from dataclasses import dataclass

from FlagEmbedding import BGEM3FlagModel


@dataclass
class EmbeddingResult:
    dense: list[float]
    sparse_indices: list[int]
    sparse_values: list[float]


class BgeM3Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
        # use_fp16=True chỉ nên bật khi chạy trên GPU (device != "cpu")
        self._model = BGEM3FlagModel(model_name, use_fp16=(device != "cpu"), device=device)

    def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        output = self._model.encode(
            texts,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
            batch_size=8,
            max_length=8192,
        )
        results = []
        for dense_vec, lexical_weights in zip(output["dense_vecs"], output["lexical_weights"]):
            indices = [int(k) for k in lexical_weights.keys()]
            values = [float(v) for v in lexical_weights.values()]
            results.append(
                EmbeddingResult(dense=dense_vec.tolist(), sparse_indices=indices, sparse_values=values)
            )
        return results

    def embed_one(self, text: str) -> EmbeddingResult:
        return self.embed([text])[0]
