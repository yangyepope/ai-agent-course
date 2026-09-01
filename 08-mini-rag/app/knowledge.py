from langchain_core.documents import Document


documents = [
    Document(
        page_content=(
            "Spring Boot 是一个用于快速开发 Java "
            "应用程序的框架。它通过自动配置和 "
            "Starter 简化了 Spring 应用的开发。"
        ),
        metadata={
            "source": "spring-boot.md",
            "category": "java",
        },
    ),

    Document(
        page_content=(
            "Spring Boot 可以通过配置 DataSource "
            "连接 MySQL 数据库。通常需要配置 "
            "数据库 URL、用户名和密码。"
        ),
        metadata={
            "source": "mysql.md",
            "category": "database",
        },
    ),

    Document(
        page_content=(
            "Redis 是一个基于内存的高性能键值数据库，"
            "通常用于缓存、分布式锁、Session "
            "以及其他需要高速访问的数据场景。"
        ),
        metadata={
            "source": "redis.md",
            "category": "database",
        },
    ),

    Document(
        page_content=(
            "Java 是一种面向对象的编程语言，"
            "广泛应用于企业级后端开发。"
        ),
        metadata={
            "source": "java.md",
            "category": "java",
        },
    ),

    Document(
        page_content=(
            "RAG 是一种让大语言模型在回答问题之前，"
            "先从外部知识库中检索相关信息的方法。"
        ),
        metadata={
            "source": "rag.md",
            "category": "ai",
        },
    ),
]