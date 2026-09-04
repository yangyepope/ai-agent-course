from app.api import router
from app.logging_config import setup_logging
from fastapi import FastAPI

# 必须在建 app 之前调用：app.api 在 import 时就会创建
# ElasticsearchClient / EmbeddingService，那些日志也要被接住
setup_logging()
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="RAG Application",
    version="1.0.0",
    # 关掉自带的 /docs，换成下面注入了字体样式的版本
    docs_url=None,
)


app.include_router(
    router,
    prefix="/api/rag",
)


# Swagger UI 自带的 CSS 里写的是 Titillium Web / Open Sans，
# 但 FastAPI 只引了它的 CSS、没引 Google Fonts 的字体文件。
# 浏览器找不到这两个字体，就回退到自己设置里的默认字体
# —— 有些机器上默认是 Comic Sans，页面就变成手写体了。
#
# 这里在 </head> 前插一段 CSS，把字体钉死成各系统都自带的字体，
# 不依赖网络，也不依赖浏览器的字体设置。
SWAGGER_FONT_CSS = """
<style>
.swagger-ui,
.swagger-ui * {
  font-family:
    -apple-system, BlinkMacSystemFont,
    "Segoe UI", "Microsoft YaHei",
    "PingFang SC", "Noto Sans CJK SC",
    Roboto, Arial, sans-serif !important;
}

/* 代码块、示例 JSON、输入框保持等宽字体 */
.swagger-ui pre,
.swagger-ui code,
.swagger-ui .microlight,
.swagger-ui textarea,
.swagger-ui input {
  font-family:
    ui-monospace, Consolas,
    "Cascadia Mono", Menlo,
    "Noto Sans Mono CJK SC",
    monospace !important;
}
</style>
"""


@app.get(
    "/docs",
    include_in_schema=False,
)
def docs() -> HTMLResponse:

    page = get_swagger_ui_html(
        openapi_url=app.openapi_url or "/openapi.json",
        title=f"{app.title} - Swagger UI",
    )

    # .body 的类型是 bytes | memoryview，包一层 bytes() 才能 decode
    html = bytes(page.body).decode()
    return HTMLResponse(
        html.replace(
            "</head>",
            SWAGGER_FONT_CSS + "</head>",
        )
    )


@app.get("/health")
def health():

    return {"status": "ok"}
