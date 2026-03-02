# 多 Agent 系统

基于 **LangGraph 1.0+** 的多 Agent 系统，支持意图识别、自动路由和会话管理。

## 功能特性

### ✅ 已实现

1. **意图识别主 Agent**
   - 基于 LangGraph StateGraph 实现
   - 自动分析用户意图，路由到合适的子 agent
   - 支持关键词快速匹配 + LLM 语义识别

2. **装饰器注册系统**
   - 使用 `@registry.register` 装饰器自动注册子 agent
   - 支持按分类、关键词索引
   - 无需手动维护 agent 列表

3. **会话管理**
   - 自动为用户创建/复用会话
   - 30 分钟无活动自动释放
   - 保持对话历史上下文

4. **FastAPI 服务**
   - RESTful API 接口
   - 会话管理接口
   - 健康检查和统计信息

## 项目结构

```
multi_agent_system/
├── core/                      # 核心模块
│   ├── registry.py           # 装饰器注册系统
│   ├── session_manager.py    # 会话管理器
│   └── base_agent.py         # Agent 基类
├── agents/                    # Agent 实现
│   ├── intent_agent.py       # 意图识别主 Agent
│   ├── coding_agent.py       # 编程助手（示例）
│   ├── writing_agent.py      # 写作助手（示例）
│   └── analysis_agent.py     # 数据分析（示例）
├── api/                       # API 服务层
│   └── server.py             # FastAPI 服务
├── config.py                  # 配置管理
├── main.py                    # 入口
├── requirements.txt           # 依赖
└── .env.example              # 环境变量示例
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动。

### 4. 测试 API

#### 聊天接口

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "帮我写一个 Python 函数计算斐波那契数列",
    "user_id": "user123"
  }'
```

#### 查看已注册的 Agents

```bash
curl http://localhost:8000/agents
```

#### 查看会话统计

```bash
curl http://localhost:8000/sessions
```

## 添加新的子 Agent

### 步骤

1. 在 `agents/` 目录创建新文件，例如 `translation_agent.py`

2. 使用装饰器注册：

```python
from core.base_agent import BaseAgent
from core.registry import registry


@registry.register(
    name="translation_agent",
    description="翻译助手，支持多语言互译",
    category="translation",
    keywords=["翻译", "语言", "english", "中文", "日语", "韩语"]
)
class TranslationAgent(BaseAgent):
    def get_system_prompt(self) -> str:
        return """你是一位专业翻译..."""
    
    async def act(self, user_input: str, context=None) -> str:
        # 实现翻译逻辑
        response = await self._invoke_llm(...)
        return response
```

3. 在 `agents/__init__.py` 中导入：

```python
from .translation_agent import TranslationAgent
```

4. 重启服务，新 agent 自动生效！

## API 文档

启动服务后访问 `http://localhost:8000/docs` 查看完整的 API 文档。

### 主要接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/chat` | POST | 聊天接口 |
| `/session/{session_id}` | GET | 获取会话信息 |
| `/session/{session_id}` | DELETE | 删除会话 |
| `/sessions` | GET | 获取会话统计 |
| `/agents` | GET | 获取所有 agent |
| `/health` | GET | 健康检查 |

## 技术栈

- **LangGraph 1.0+**: Agent 编排和状态管理
- **LangChain**: LLM 抽象和工具链
- **FastAPI**: Web 框架
- **Pydantic**: 数据验证
- **Loguru**: 日志管理

## 会话管理说明

- **会话创建**: 首次请求自动创建，返回 `session_id`
- **会话复用**: 后续请求携带 `session_id` 或 `user_id`
- **会话过期**: 30 分钟无活动自动释放
- **对话历史**: 每个会话保留最近 20 条消息

## 自定义配置

编辑 `.env` 文件：

```bash
# 修改会话超时时间（分钟）
SESSION_TIMEOUT_MINUTES=60

# 修改默认模型
DEFAULT_MODEL=gpt-4o

# 使用其他 LLM 服务
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

## 开发计划

- [ ] 支持流式响应
- [ ] 添加更多示例子 agent
- [ ] 支持自定义工具（Tools）
- [ ] 会话持久化（Redis）
- [ ] Agent 间协作（多轮路由）
- [ ] 监控和指标收集

## License

MIT
