# DevAgent MVP

基于 LangChain + LangGraph + FastAPI 的 Agent 路由系统（内存存储版本）。

## 功能特性

- **意图识别**: 自动识别用户意图（代码生成、文档问答、任务查询）
- **Agent 路由**: 根据意图将请求路由到对应的 Agent
- **会话隔离**: 基于内存实现多租户会话隔离（线程安全）
- **规则 + LLM 混合路由**: 支持命令前缀快速路由和 LLM 智能识别

## 目录结构

```
app/
  main.py              # FastAPI 入口
  core/
    models.py          # 数据模型定义
    context.py         # 上下文工具
    registry.py        # Agent 注册中心
  infra/
    llm.py             # LLM 初始化
  memory/
    session_store.py   # 内存会话存储
  agents/
    base.py            # Agent 基类
    code_agent.py      # 代码生成 Agent
    doc_agent.py       # 文档问答 Agent
    task_agent.py      # 任务查询 Agent
  router/
    prompts.py         # Prompt 定义
    policy.py          # 路由策略
    nodes.py           # LangGraph 节点
    graph.py           # 路由图构建
```

## 快速开始

### 1. 安装依赖

```bash
pip install -e .
```

或使用 uv：

```bash
uv pip install -e .
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. 测试接口

健康检查：
```bash
curl http://127.0.0.1:8000/healthz
```

聊天接口：
```bash
curl -X POST "http://127.0.0.1:8000/v1/chat" \
-H "Content-Type: application/json" \
-d '{
  "tenant_id":"t1",
  "channel":"web",
  "user_id":"u1",
  "session_id":"s1",
  "text":"/code 帮我写一个 fastapi 健康检查接口"
}'
```

## 路由流程

```
用户请求
    ↓
preprocess (预处理)
    ↓
rule_route (规则路由：/code, /doc, /task)
    ↓
llm_intent (LLM 意图识别)
    ↓
policy (路由策略决策)
    ↓
invoke_agent (调用对应 Agent)
    ↓
返回响应
```

## 意图类型

| 意图 | 说明 | 对应 Agent |
|------|------|-----------|
| code_gen | 代码生成、重构、调试 | CodeAgent |
| doc_qa | 文档解释、知识问答 | DocAgent |
| task_query | 任务进度、工单查询 | TaskAgent |
| unknown | 无法判断 | DocAgent (fallback) |

## 路由策略

- 置信度 >= 0.75: 直接路由到对应 Agent
- 置信度 0.5-0.75: 返回澄清问题
- 置信度 < 0.5: 降级到 DocAgent

## 内存存储 vs Redis

当前版本使用**内存存储**，特点：

| 特性 | 内存存储 | Redis |
|------|----------|-------|
| 部署 | 无需额外服务 | 需要 Redis 服务 |
| 性能 | 最快（无网络开销） | 快（网络开销小） |
| 持久化 | 进程重启后丢失 | 支持持久化 |
| 多实例 | 不支持（数据隔离） | 支持（共享数据） |
| 适用场景 | 开发、测试、单机部署 | 生产环境、分布式部署 |

如需切换到 Redis 版本，可参考 DESIGN.md 中的 Redis 实现。

## 下一步增强

- [ ] 流式输出（SSE）
- [ ] LangGraph checkpointer（持久化状态）
- [ ] Agent Manifest 动态注册
- [ ] 机器人签名验签中间件
- [ ] 路由评测脚本
