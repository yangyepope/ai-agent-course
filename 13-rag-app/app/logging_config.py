"""
日志系统。

设计要点：

1. 一次问答会穿过 5 个模块，光看日志行分不清哪几行属于同一次请求，
   所以用 contextvar 存一个 request_id，靠 Filter 自动注入到每一行。
   contextvar 的好处是不用把 request_id 一层层当参数传下去。

2. RAG 最值得记的不是"发生了什么"，而是"每一步花了多久"：
   embedding、ES 检索、精排、LLM 生成的耗时差好几个数量级，
   出问题时第一件事就是看这四个数。

3. Context 原文和 Prompt 只在 DEBUG 级别打。
   它们又长又可能含敏感内容，不该出现在生产日志里。
"""

import logging
import logging.handlers
import sys
import uuid
from contextvars import ContextVar
from pathlib import Path

from app.config import LOG_FILE, LOG_LEVEL

# 当前请求的 id。脚本里没有请求，就是那串短横线
_request_id: ContextVar[str] = ContextVar("request_id", default="--------")

_configured = False


def new_request_id() -> str:
    """开启一次新的追踪，返回生成的 id。"""

    request_id = uuid.uuid4().hex[:8]

    _request_id.set(request_id)

    return request_id


def get_request_id() -> str:
    return _request_id.get()


class RequestIdFilter(logging.Filter):
    """把当前 request_id 塞进每条日志记录。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()

        return True


FORMAT = "%(asctime)s %(levelname)-5s [%(request_id)s] %(name)-20s %(message)s"

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str | None = None) -> None:
    """
    配置根 logger。重复调用只生效一次。

    在两个地方调用：
        main.py         —— 服务启动时
        scripts/*.py    —— 脚本入口
    """

    global _configured

    if _configured:
        return

    formatter = logging.Formatter(FORMAT, DATE_FORMAT)

    request_id_filter = RequestIdFilter()

    handlers: list[logging.Handler] = []

    # 控制台
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(formatter)
    console.addFilter(request_id_filter)
    handlers.append(console)

    # 文件（LOG_FILE 为空则不写文件）
    # 按大小滚动，单文件 10MB，留 5 个历史文件
    if LOG_FILE:
        log_path = Path(LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(request_id_filter)
        handlers.append(file_handler)

    root = logging.getLogger()
    root.setLevel(level or LOG_LEVEL)

    for handler in root.handlers[:]:
        root.removeHandler(handler)

    for handler in handlers:
        root.addHandler(handler)

    # 第三方库的日志太吵，单独压一档：
    #   elastic_transport 会把每个 ES 请求的完整 URL 打成 INFO
    #   httpx 会把每次 LLM 调用打成 INFO
    #   sentence_transformers 启动时打一堆模型加载信息
    for name in (
        "elastic_transport.transport",
        "elasticsearch",
        # openai 3.x 用的是 vendored 的 httpx2，不是 httpx，
        # 两个名字都要压，否则每次 LLM 调用会多打一行 HTTP 日志
        "httpx",
        "httpx2",
        "httpcore",
        "httpcore2",
        "sentence_transformers",
        "urllib3",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)

    _configured = True

    logging.getLogger(__name__).info(
        "日志已初始化：level=%s file=%s",
        root.level and logging.getLevelName(root.level),
        LOG_FILE or "（不写文件）",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
