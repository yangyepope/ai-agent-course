from app.context import ContextBuilder
from app.elasticsearch_client import ElasticsearchClient
from app.embedding import EmbeddingService
from app.llm import LLMService
from app.logging_config import get_logger, new_request_id
from app.models import RAGRequest, RAGResponse
from app.rag_service import RAGService
from app.reranker import SimpleReranker
from app.retriever import Retriever
from fastapi import APIRouter

logger = get_logger(__name__)

router = APIRouter()


# =========================
# 初始化基础组件
# =========================

es_client = ElasticsearchClient()

embedding_service = EmbeddingService()

retriever = Retriever(
    client=es_client.get_client(),
    embedding_service=embedding_service,
)

reranker = SimpleReranker()

context_builder = ContextBuilder()

llm_service = LLMService()


# =========================
# RAG Service
# =========================

rag_service = RAGService(
    retriever=retriever,
    reranker=reranker,
    context_builder=context_builder,
    llm=llm_service,
)


# =========================
# API
# =========================


@router.post(
    "/chat",
    response_model=RAGResponse,
)
def chat(
    request: RAGRequest,
):

    # 一次问答会穿过 5 个模块，靠这个 id 才能把日志串起来
    request_id = new_request_id()

    try:
        result = rag_service.answer(
            query=request.query,
            tenant_id=request.tenant_id,
            top_k=request.top_k,
            debug=request.debug,
        )
    except Exception:
        logger.exception("请求处理失败")
        raise

    # 把 id 回给调用方，出问题时能凭它到日志里定位
    result["request_id"] = request_id

    return result
