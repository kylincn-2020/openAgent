## LangChain v1.0+ API 更新说明（2025年2月）

### 主要变化

1. **移除 PydanticOutputParser**
   - 旧方式：`PydanticOutputParser(pydantic_object=Schema)`
   - 新方式：使用 `llm.with_structured_output(Schema)` 方法
   - 优势：更简洁，自动处理格式说明

2. **更新导入路径**
   - 旧方式：`from langchain.prompts import ChatPromptTemplate`
   - 新方式：`from langchain_core.prompts import ChatPromptTemplate`
   - 原因：LangChain v1 重构了包结构

3. **简化意图识别流程**
   - 移除了 `format_instructions` 参数
   - 移除了 `ChatPromptTemplate.from_messages` 后的 LCEL 链式调用
   - 直接使用消息列表调用 `structured_llm.ainvoke(messages)`

### 迁移指南

如果从旧版本 LangChain 迁移：

1. 删除 `from langchain.output_parsers import PydanticOutputParser`
2. 将 `from langchain.prompts` 改为 `from langchain_core.prompts`
3. 将 `PydanticOutputParser` 替换为 `llm.with_structured_output(Schema)`
4. 移除 `format_instructions` 相关代码
5. 直接构建消息列表并传递给 `ainvoke`

### 示例对比

#### 旧代码 (LangChain < 1.0)
```python
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=MySchema)
prompt = ChatPromptTemplate.from_messages([...])
chain = prompt | llm | parser
result = await chain.ainvoke(input_data)
```

#### 新代码 (LangChain 1.0+)
```python
from langchain_core.prompts import ChatPromptTemplate

structured_llm = llm.with_structured_output(MySchema)
messages = [
    ("system", system_prompt),
    ("human", user_input),
]
result = await structured_llm.ainvoke(messages)
```

### 依赖版本要求

```txt
langchain>=1.0.0
langchain-openai>=0.2.0
langchain-core>=0.3.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```

### 示例对比
- [LangChain v1 Migration Guide](https://docs.langchain.com/oss/python/migrate/langchain-v1)
- [ChatOpenAI Integration](https://docs.langchain.com/oss/python/integrations/chat/openai)
- [Structured Output](https://docs.langchain.com/oss/python/structured-output)
LangChain 意图识别 Agent 系统 - 使用最新 API

更新说明（2025年）：
- 使用 LangChain v1.0+ API
- 移除了 PydanticOutputParser，改用 with_structured_output 方法
- 更新导入路径：langchain_core.prompts 替代 langchain.prompts
- 简化了意图识别流程，无需手动处理格式说明
"""
