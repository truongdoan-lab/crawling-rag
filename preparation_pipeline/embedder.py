from dataclasses import dataclass

from FlagEmbedding import BGEM3FlagModel


@dataclass
class EmbeddingResult:
    dense: list[float]
    sparse_indices: list[int]
    sparse_values: list[float]


class BgeM3Embedder:
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu"):
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
