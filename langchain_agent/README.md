# LangChain 意图识别 Agent 系统

基于 LangChain v1.0+ 的智能意图识别 Agent 系统，支持多子 Agent 并行执行和结果汇总。

## 功能特性

1. **意图识别**: 使用 LangChain v1.0+ 最新 API 自动识别用户意图
2. **并行执行**: 支持多个子 Agent 并行处理独立任务
3. **结果汇总**: 自动汇总所有 Agent 的执行结果
4. **装饰器注册**: 提供便捷的装饰器快速注册子 Agent
5. **Client 缓存**: 按用户+入口维度缓存 Client，30分钟自动过期

## LangChain v1.0+ API 更新

本项目已更新为使用 LangChain v1.0+ 最新 API：
- 使用 `with_structured_output()` 替代 `PydanticOutputParser`
- 更新导入路径为 `langchain_core.prompts`
- 简化了意图识别流程

- 详见 [API_UPDATE.md](./API_UPDATE.md) 文档。

基于 LangChain 的智能意图识别 Agent 系统，支持多子 Agent 并行执行和结果汇总。
n
**本系统已更新为使用 LangChain v1.0+ 最新 API**
- 使用 `with_structured_output()` 替代 `PydanticOutputParser`
- 更新导入路径为 `langchain_core.prompts`
- 详见 [API_UPDATE.md](./API_UPDATE.md) 文档


## 功能特性

1. **意图识别**: 使用 LangChain 自动识别用户意图
2. **并行执行**: 支持多个子 Agent 并行处理独立任务
3. **结果汇总**: 自动汇总所有 Agent 的执行结果
4. **装饰器注册**: 提供便捷的装饰器快速注册子 Agent
5. **Client 缓存**: 按用户+入口维度缓存 Client，30分钟自动过期

## 项目结构

```
langchain_agent/
├── agents/
│   ├── __init__.py
│   ├── agent_registry.py      # Agent 注册表和装饰器
│   ├── intent_agent.py        # 意图识别 Agent
│   ├── client_manager.py      # Client 管理器
│   └── example_agents.py      # 示例子 Agent
├── cache/
│   ├── __init__.py
│   └── client_cache.py        # Client 缓存管理器
├── examples/
│   ├── quick_start.py         # 快速开始示例
│   ├── usage_example.py       # 完整使用示例
│   └── custom_agent.py        # 自定义 Agent 示例
├── requirements.txt           # 依赖包
├── .env.example              # 环境变量示例
└── README.md                 # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的 OpenAI API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_MODEL=gpt-4o-mini
```

### 3. 运行快速开始示例

```bash
python examples/quick_start.py
```

## 核心使用方式

### 基础使用

```python
import asyncio
from langchain_agent.agents.example_agents import WeatherAgent, TimeAgent
from langchain_agent.agents.client_manager import get_client_manager

async def main():
    # 获取 Client 管理器
    client_manager = get_client_manager()
    
    # 获取或创建 Client（会自动缓存）
    client = client_manager.get_client(
        user_id="user_001",
        entry_point="web_chat"
    )
    
    # 处理用户请求
    result = await client.process("北京今天的天气怎么样？")
    print(result)

asyncio.run(main())
```

### 添加自定义子 Agent

使用装饰器快速注册新 Agent：

```python
from langchain_agent.agents.agent_registry import BaseSubAgent, AgentMetadata, register_agent
from typing import Any, Dict, Optional

@register_agent(AgentMetadata(
    name="my_agent",
    description="我的自定义 Agent",
    intent_keywords=["关键词1", "关键词2"],
    priority=10,
    parallel_allowed=True,
    category="custom"
))
class MyAgent(BaseSubAgent):
    """自定义 Agent"""
    
    async def execute(
        self,
        input_data: Any,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """执行任务"""
        # 实现你的逻辑
        return {"result": "处理结果"}
```

### Client 缓存机制

系统按 `user_id + entry_point` 维度缓存 Client 实例：

```python
# 同一用户同一入口 - 使用缓存的 Client
client1 = client_manager.get_client("user_001", "web")
client2 = client_manager.get_client("user_001", "web")  # 返回同一个实例

# 同一用户不同入口 - 创建新的 Client
client3 = client_manager.get_client("user_001", "mobile")  # 新实例

# 不同用户同一入口 - 创建新的 Client
client4 = client_manager.get_client("user_002", "web")  # 新实例

# Client 会在 30 分钟后自动释放过期
```

## API 文档

### AgentClient

`AgentClient` 是对应用户和入口的客户端实例。

**方法:**

- `async process(user_input: str, input_data: Any = None, context: Optional[Dict] = None) -> Dict[str, Any]`
  - 处理用户请求
  - `user_input`: 用户输入文本
  - `input_data`: 传递给 Agent 的输入数据（默认为 user_input）
  - `context`: 上下文信息
  - 返回包含所有 Agent 执行结果的字典

### ClientManager

`ClientManager` 管理 Client 的创建和缓存。

**方法:**

- `get_client(user_id: str, entry_point: str, model_name: Optional[str] = None, temperature: float = 0.0) -> AgentClient`
  - 获取或创建 Client

- `remove_client(user_id: str, entry_point: str) -> bool`
  - 移除指定的 Client

- `clear_expired_clients() -> int`
  - 清理过期的 Client，返回清理数量

- `get_stats() -> Dict[str, Any]`
  - 获取缓存统计信息

### AgentMetadata

`AgentMetadata` 定义 Agent 的元数据。

**参数:**

- `name`: Agent 名称（唯一标识）
- `description`: Agent 描述
- `intent_keywords`: 意图关键词列表
- `priority`: 优先级（数字越大优先级越高，默认 0）
- `parallel_allowed`: 是否允许并行执行（默认 True）
- `category`: Agent 类别（可选）

### BaseSubAgent

所有子 Agent 的基类。

**必须实现的方法:**

- `async execute(input_data: Any, context: Optional[Dict] = None) -> Any`
  - 执行 Agent 任务

## 示例

### 示例 1: 基础使用

```bash
python examples/quick_start.py
```

### 示例 2: 完整功能展示

```bash
python examples/usage_example.py
```

### 示例 3: 自定义 Agent

```bash
python examples/custom_agent.py
```

## 工作原理

1. **意图识别**: 系统使用 LangChain 分析用户输入，识别最匹配的子 Agent
2. **并行执行**: 如果识别到多个独立任务，系统会并行执行相应的子 Agent
3. **结果汇总**: 所有 Agent 的执行结果会被汇总到一个字典中返回
4. **Client 缓存**: 每个 `(user_id, entry_point)` 组合对应一个 Client 实例，30分钟后自动过期

## 执行流程

```
用户输入
    ↓
意图识别（LangChain）
    ↓
识别主 Agent + 次要 Agent（可并行）
    ↓
并行执行所有 Agent
    ↓
汇总结果
    ↓
返回结果
```

## 注意事项

1. 确保 `.env` 文件中配置了正确的 OpenAI API Key
2. 子 Agent 的 `execute` 方法必须是异步的
3. 意图关键词要尽量具体，避免误识别
4. 不同 Agent 处理的任务必须完全独立才能并行执行

## 扩展建议

1. **添加更多子 Agent**: 使用装饰器轻松添加新功能
2. **集成更多 LLM**: 支持其他大语言模型
3. **持久化存储**: 将对话历史和结果保存到数据库
4. **监控和日志**: 添加详细的执行日志和监控
5. **限流和重试**: 添加 API 调用限流和重试机制

## 许可证

MIT License
