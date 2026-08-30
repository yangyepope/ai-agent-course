1. LangChain 是什么
2. ChatModel 是什么
3. Message 是什么
4. PromptTemplate 是什么
5. Output Parser 是什么
6. Runnable 是什么
7. LCEL 是什么
8. LangChain 如何把这些东西串起来


chain = prompt | llm | parser


但是当你的应用越来越复杂：
Prompt
 ↓
LLM
 ↓
Parser
 ↓
Tool
 ↓
Retriever
 ↓
LLM
 ↓
Parser


LangChain 的目标之一就是提供统一的抽象，把：
Model
Prompt
Parser
Tool
Retriever
Document


所以你可以先记：
LangChain = LLM 应用开发的组件和编排框架。


为什么现在安装三个 LangChain 包？
langchain
langchain-openai
langchain-core


langchain
    ↓
LangChain 的高级能力

langchain-core
    ↓
核心抽象
Prompt / Runnable / Message 等

langchain-openai
    ↓
OpenAI / OpenAI-compatible ChatModel