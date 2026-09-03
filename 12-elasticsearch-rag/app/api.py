from app.elasticsearch_client import ElasticsearchClient
from app.embedding import EmbeddingService
from app.reranker import Reranker
from app.search_service import SearchService
from fastapi import APIRouter

router = APIRouter()

es_client = ElasticsearchClient()

embedding_service = EmbeddingService()

search_service = SearchService(
    es_client.get_client()
)

# 模型是懒加载的，这行不会真的把 1.1GB 权重读进内存，
# 等第一个 rerank=true 的请求来了才加载
reranker = Reranker()


def build_results(
    hits: list[dict],
) -> list[dict]:
    """
    把 ES 原样返回的 hit 整理成对外的结果项。

    三个检索路由共用。rerank_score 用 .get() 取：
    只有走过精排的 hit 才有这个键，其余为 null，
    这样三个接口的响应结构保持一致，方便横向对比。
    """

    return [
        {
            "id": hit["_source"]["chunk_id"],
            "score": hit["_score"],
            "rerank_score": hit.get("_rerank_score"),
            "content": hit["_source"]["content"],
            "source": hit["_source"]["source"],
            "page": hit["_source"]["page"],
        }
        for hit in hits
    ]


@router.post("/search")
def search(
    query: str,
    tenant_id: str,
    top_k: int = 5,
    rerank: bool = True,
    candidate_k: int = 50,
):
    """
    rerank=true （默认）：
        ES 先出 candidate_k 条候选（RRF 融合过），
        再由 CrossEncoder 在 Python 里精排到 top_k 条。

    rerank=false：
        ES 直接出 top_k 条，跟加精排之前的行为一致。
        用来对比精排到底改变了什么。
    """

    if rerank:

        hits = search_service.hybrid_search(
            query=query,
            embedding_service=embedding_service,
            tenant_id=tenant_id,
            top_k=top_k,
            candidate_k=candidate_k,
        )

        results = reranker.rerank(
            query=query,
            hits=hits,
            top_k=top_k,
        )

    else:

        results = search_service.hybrid_search(
            query=query,
            embedding_service=embedding_service,
            tenant_id=tenant_id,
            top_k=top_k,
        )

    return {
        "query": query,
        "mode": "hybrid",
        "reranked": rerank,
        "results": build_results(results),
    }


# 以下两个路由是「对照用」入口：
# /search 是完整链路（BM25 + kNN + RRF + 精排），
# 想看清某一路单独的表现，就打这两个。
# 它们都不走精排，看到的就是检索器的原始输出。


@router.post("/search/keyword")
def search_keyword(
    query: str,
    tenant_id: str,
    top_k: int = 5,
):
    """
    纯 BM25（字面匹配）。不需要 Embedding —— 这一路不算向量。

    擅长：专有名词、错误码、型号，比如 maxmemory-policy
    不擅长：换个说法就搜不到

    注意本课 ES 没装 IK 分词器，中文被切成单字，
    所以这一路的中文精度会比看起来差不少。
    """

    hits = search_service.keyword_search(
        query=query,
        tenant_id=tenant_id,
        top_k=top_k,
    )

    return {
        "query": query,
        "mode": "keyword",
        "reranked": False,
        "results": build_results(hits),
    }


@router.post("/search/vector")
def search_vector(
    query: str,
    tenant_id: str,
    top_k: int = 5,
    num_candidates: int = 50,
):
    """
    纯 kNN（语义相近）。query 会先过 Embedding 变成 512 维向量。

    擅长：同义词、换句话说
    不擅长：专有名词、缩写、编号

    num_candidates 是 HNSW 的候选池大小，必须大于 top_k：
        整个索引 ──► 粗捞 num_candidates 条 ──► 精算排序 ──► 取 top_k
    调大召回更准但更慢，一般取 top_k 的 5~10 倍。
    """

    hits = search_service.vector_search(
        query=query,
        embedding_service=embedding_service,
        tenant_id=tenant_id,
        top_k=top_k,
        num_candidates=num_candidates,
    )

    return {
        "query": query,
        "mode": "vector",
        "reranked": False,
        "results": build_results(hits),
    }
