# DevOps Agent 架构文档

## 系统概述

### 核心价值

**让 DevOps 像对话一样简单** — 用户用自然语言描述需求，系统通过智能分析和多 Agent 协作自动完成 DevOps 任务。

### 主要功能

1. **项目分析**：自动识别项目类型、编程语言、依赖关系和构建命令
2. **CI/CD 配置生成**：根据项目特征自动生成 GitHub Actions 工作流配置
3. **对话式交互**：通过自然语言与系统交互，无需记忆复杂命令

### 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| CLI 框架 | Typer + Rich | 命令行界面和美化输出 |
| 工作流编排 | LangGraph | 多 Agent 协作和状态管理 |
| LLM 集成 | LiteLLM | 多模型支持（Claude、OpenAI 等） |
| 数据验证 | Pydantic v2 | 类型安全和数据验证 |
| 配置管理 | YAML | 配置文件格式 |
| 异步处理 | asyncio | 高性能异步 Agent 执行 |

## 系统架构

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI 层                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  REPL 循环   │  │  命令解析    │  │  Rich 输出   │      │
│  │  (cli.py)    │  │  (Typer)     │  │  (Panel)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent 系统层                            │
│  ┌────────────────────────────────────────────────────┐     │
│  │           LangGraph StateGraph                     │     │
│  │  ┌──────────────┐       ┌──────────────┐          │     │
│  │  │ Main Agent   │──▶    │ Intent Router│          │     │
│  │  │ (唯一入口)   │       │ (意图识别)   │          │     │
│  │  └──────┬───────┘       └──────┬───────┘          │     │
│  │         │                       │                   │     │
│  │         ▼                       ▼                   │     │
│  │  ┌─────────────────────────────────────────┐       │     │
│  │  │     条件边路由 (route_by_intent)        │       │     │
│  │  └──┬─────────────┬────────────────────────┘       │     │
│  │     │             │                                  │     │
│  │     ▼             ▼                                  │     │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │     │
│  │  │ Project  │ │  Build   │ │   ...    │            │     │
│  │  │  Agent   │ │  Agent   │ │  Agents  │            │     │
│  │  └──────────┘ └──────────┘ └──────────┘            │     │
│  └────────────────────────────────────────────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      核心服务层                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  ProjectAnalyzer │  │ ConfigGenerator  │                │
│  │  (项目分析器)     │  │  (配置生成器)     │                │
│  │                  │  │                  │                │
│  │  - 检测器        │  │  - 模板引擎      │                │
│  │  - 解析器        │  │  - YAML 验证     │                │
│  │  - 协调器        │  │  - 输出管理      │                │
│  └──────────────────┘  └──────────────────┘                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据层                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 文件系统      │  │ 配置文件      │  │ 会话上下文    │      │
│  │ (项目分析)    │  │ (YAML)       │  │ (内存)       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 模块说明

#### 1. CLI 模块 (`cli.py`)

**职责**：提供命令行接口和 REPL 循环

**核心功能**：
- `start()`：启动对话模式
- `build()`：直接生成配置（无需 LLM）
- `analyze()`：分析项目（无需 LLM）
- `_start_async()`：异步 REPL 循环实现
- Rich Status/Panel：美化的输出显示

**技术特点**：
- 使用 Typer 实现声明式 CLI
- 使用 Rich 提供美观的终端输出
- 集成 SessionManager 管理会话
- 集成 LangGraph 处理用户输入

#### 2. Agent 系统 (`agent/`)

**设计模式**：装饰器注册模式

##### 2.1 Agent 基类 (`base.py`)

**核心组件**：
- `AgentRegistry`：全局注册表，使用装饰器注册 Agent
- `Agent`：抽象基类，定义统一接口

```python
@AgentRegistry.register('my_agent')
class MyAgent(Agent):
    async def execute(self, state: AgentState, config: RunnableConfig) -> AgentState:
        # Agent 逻辑
        return state
```

**工具方法**：
- `update_context()`：更新会话上下文
- `get_context()`：获取上下文值
- `add_error()`：添加错误信息
- `add_result()`：添加执行结果

##### 2.2 LangGraph State (`state.py`)

**状态结构**：
```python
class AgentState(TypedDict):
    user_input: str          # 用户输入
    intent: str              # 识别的意图
    project_path: str        # 项目路径
    context: Dict[str, Any]  # 会话上下文
    agent_results: List[Dict]  # 子 Agent 结果
    errors: List[str]        # 错误列表
    response: str            # 最终响应
```

##### 2.3 主 Agent (`main_agent.py`)

**职责**：系统唯一入口，负责意图识别和任务分发

**意图识别**：混合模式（规则预筛选 + LLM 确认）
- **第一阶段**：规则匹配（正则表达式）
  - 覆盖 80% 常见场景
  - 毫秒级响应
- **第二阶段**：LLM 确认
  - 处理复杂场景
  - 智能灵活性

**支持意图**：
- `generate_ci`：生成 CI/CD 配置
- `analyze_project`：分析项目
- `unknown`：未知意图

##### 2.4 LangGraph 工作流 (`graph.py`)

**工作流构建**：
```python
def create_agent_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("main_agent", main_agent_node)
    graph.add_node("project_agent", project_agent_node)
    graph.add_node("build_agent", build_agent_node)
    graph.set_entry_point("main_agent")
    graph.add_conditional_edges("main_agent", route_by_intent, {...})
    return graph.compile()
```

**路由逻辑**：
- `route_by_intent()`：根据 intent 路由到不同 Agent
- 支持：project_agent、build_agent、END

##### 2.5 子 Agent

**ProjectAgent** (`project_agent.py`)：
- 调用 ProjectAnalyzer 分析项目
- 不使用 LLM（纯逻辑）
- 返回项目分析结果

**BuildAgent** (`build_agent.py`)：
- 调用 ConfigGenerator 生成配置
- 不使用 LLM（纯逻辑）
- 支持配置预览和确认

#### 3. 项目分析器 (`analyzer/`)

**设计模式**：策略模式

##### 3.1 数据模型 (`models.py`)

**Pydantic 模型**：
```python
class ProjectInfo(BaseModel):
    language: str
    framework: Optional[str]
    dependencies: List[str]
    build_command: str
    test_command: str
    metadata: Dict[str, Any]

class ProjectAnalysisResult(BaseModel):
    project_path: str
    primary_language: str
    languages: List[ProjectInfo]
    subprojects: List[str]
```

##### 3.2 项目检测器 (`detector.py`)

**核心功能**：
- `find_project_root()`：向上递归查找 .git 目录
- `detect_languages()`：扫描所有标记文件
- `determine_primary_language()`：决定主语言
- `is_valid_project()`：检查项目有效性
- `detect_monorepo()`：检测 Monorepo 结构

**支持的标记文件**：
- Python: `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`
- Node.js: `package.json`
- Go: `go.mod`
- Java: `pom.xml`, `build.gradle`, `build.gradle.kts`

##### 3.3 语言解析器 (`parsers/`)

**策略模式实现**：
```python
class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, project_path: Path) -> bool:
        pass

    @abstractmethod
    def parse(self, project_path: Path) -> ProjectInfo:
        pass
```

**支持的解析器**：
- `PythonParser`：Python 项目（requirements.txt, pyproject.toml）
- `NodeJSParser`：Node.js 项目（package.json）
- `GoParser`：Go 项目（go.mod）
- `JavaParser`：Java 项目（pom.xml, build.gradle）

**解析器特性**：
- 框架检测（Flask, Django, React, Vue 等）
- 构建命令推断
- 测试命令推断
- 依赖提取（只读取直接依赖）

##### 3.4 协调器 (`analyzer.py`)

**ProjectAnalyzer 类**：
- 整合检测器和解析器
- 统一的项目分析接口
- 异常驱动的错误处理

#### 4. 配置生成器 (`config/`)

##### 4.1 模板系统 (`templates.py`)

**模板引擎**：Python f-string（轻量级，无额外依赖）

**模板目录结构**：
```
templates/github-actions/
├── python/ci.yml.template
├── nodejs/ci.yml.template
├── go/ci.yml.template
└── java/ci.yml.template
```

**模板特性**：
- 支持用户自定义覆盖（`~/.devops-agent/templates/`）
- 使用 `lru_cache` 缓存模板（maxsize=32）
- 跨平台路径处理（pathlib）

##### 4.2 配置生成器 (`generator.py`)

**ConfigGenerator 类**：
- `generate()`：生成 YAML 配置
- `generate_and_validate()`：生成并验证配置
- 语言特定变量构建
- 语言名称规范化（Node.js → nodejs）

**生成的配置包含**：
- 依赖安装步骤
- GitHub Actions 缓存
- 测试运行步骤
- 项目构建步骤

##### 4.3 YAML 验证器 (`validator.py`)

**验证逻辑**：
- 验证必需字段（name, on, jobs, runs-on, steps）
- 处理 PyYAML 保留字问题（`on` → `True`）
- 人类可读的错误格式化

##### 4.4 输出管理 (`output.py`)

**用户交互**：
- `confirm_write()`：确认是否写入配置
- `confirm_save_draft()`：确认是否保存草稿
- 备份文件名包含时间戳（`.bak.YYYYMMDD_HHMMSS`）

#### 5. LLM 客户端 (`llm/`)

##### 5.1 LLM 客户端 (`client.py`)

**核心功能**：
- 统一的 LLM 调用接口
- 重试逻辑（tenacity）
- 错误处理和格式化
- 敏感信息过滤

**支持的提供商**：
- Claude (Anthropic)
- OpenAI (GPT-4, GPT-3.5)
- 其他 LiteLLM 支持的提供商

#### 6. 会话管理 (`session/`)

##### 6.1 会话管理器 (`manager.py`)

**SessionManager 类**：
- 内存存储会话数据（非持久化）
- 支持多会话并发
- 管理会话上下文
- 记录对话历史

**会话生命周期**：
```python
session_id = session_manager.create_session()
session_manager.update_context(session_id, key, value)
session_manager.add_to_history(session_id, user_input, response)
session_manager.cleanup_session(session_id)
```

##### 6.2 清理钩子 (`cleanup.py`)

**atexit 钩子**：
- 使用 `atexit.register()` 注册清理函数
- 程序退出时自动清理所有会话
- 避免内存泄漏

## 数据流

### 1. 用户输入流程

```
用户输入
    │
    ▼
CLI REPL (create AgentState)
    │
    ▼
LangGraph ainvoke(state, config)
    │
    ▼
main_agent_node(state, config)
    │
    ▼
MainAgent.execute()
    │
    ├─▶ IntentRouter.route()
    │       ├─▶ route_by_rules()  [规则匹配]
    │       └─▶ route_by_llm()    [LLM 确认]
    │
    ├─▶ Format Response
    │
    └─▶ Return AgentState
    │
    ▼
Rich Panel Display
    │
    ▼
SessionManager.add_to_history()
```

### 2. 项目分析流程

```
项目路径
    │
    ▼
ProjectAnalyzer.analyze()
    │
    ├─▶ find_project_root()
    ├─▶ detect_languages()
    │       │
    │       ├─▶ PythonParser.can_parse()
    │       ├─▶ NodeJSParser.can_parse()
    │       ├─▶ GoParser.can_parse()
    │       └─▶ JavaParser.can_parse()
    │
    ├─▶ parsers[].parse()
    │       │
    │       ├─▶ 提取依赖
    │       ├─▶ 检测框架
    │       ├─▶ 推断构建命令
    │       └─▶ 推断测试命令
    │
    └─▶ ProjectAnalysisResult
```

### 3. 配置生成流程

```
ProjectAnalysisResult
    │
    ▼
ConfigGenerator.generate()
    │
    ├─▶ _normalize_language_name()
    ├─▶ _get_language_specific_vars()
    ├─▶ _load_template()
    ├─▶ _render_template()
    │
    ▼
YAML 配置字符串
    │
    ▼
validate_yaml_config()
    │
    ├─▶ 验证必需字段
    └─▶ YAML 结构检查
    │
    ▼
用户确认
    │
    ├─▶ 接受 → 写入 .github/workflows/ci.yml
    └─▶ 拒绝 → 保存草稿（可选）
```

## 关键设计模式

### 1. 装饰器注册模式 (AgentRegistry)

**目的**：简化 Agent 扩展

**实现**：
```python
class AgentRegistry:
    _agents: Dict[str, Type['Agent']] = {}

    @classmethod
    def register(cls, name: str) -> Callable:
        def decorator(agent_class: Type['Agent']) -> Type['Agent']:
            cls._agents[name] = agent_class
            return agent_class
        return decorator

# 使用
@AgentRegistry.register('my_agent')
class MyAgent(Agent):
    pass
```

**优势**：
- 符合开闭原则（对扩展开放，对修改封闭）
- 添加新 Agent 无需修改路由代码
- 代码简洁，易于维护

### 2. 策略模式 (BaseParser)

**目的**：支持多种语言解析器

**实现**：
```python
class BaseParser(ABC):
    @abstractmethod
    def can_parse(self, project_path: Path) -> bool:
        pass

    @abstractmethod
    def parse(self, project_path: Path) -> ProjectInfo:
        pass

# 具体策略
class PythonParser(BaseParser):
    def can_parse(self, project_path: Path) -> bool:
        return (project_path / "pyproject.toml").exists()

    def parse(self, project_path: Path) -> ProjectInfo:
        # 解析逻辑
        pass
```

**优势**：
- 统一的解析器接口
- 添加新语言只需创建新解析器类
- 易于测试和维护

### 3. 模板模式 (配置模板)

**目的**：生成标准化的 CI/CD 配置

**实现**：
```python
# 模板文件
name: CI for {language}
on: [push, pull_request]
jobs:
  build:
    runs-on: {runs_on}
    steps:
      - uses: actions/checkout@v4
      - name: Setup {language}
        uses: {setup_action}
```

**优势**：
- 配置结构标准化
- 易于维护和更新
- 支持用户自定义

### 4. 工作流编排 (LangGraph)

**目的**：多 Agent 协作和状态管理

**实现**：
```python
graph = StateGraph(AgentState)
graph.add_node("main_agent", main_agent_node)
graph.add_node("project_agent", project_agent_node)
graph.add_conditional_edges("main_agent", route_by_intent, {...})
return graph.compile()
```

**优势**：
- 类型安全的状态管理
- 可视化工作流
- 支持复杂的条件路由

## 技术决策

### 1. 为什么选择 LangGraph？

**决策**：使用 LangGraph 进行多 Agent 工作流编排

**理由**：
- **类型安全**：TypedDict 状态定义，编译时检查
- **可扩展**：轻松添加新 Agent 和条件边
- **可视化**：支持工作流图可视化
- **异步支持**：原生支持异步 Agent 执行

**替代方案**：
- 硬编码路由：不灵活，难以扩展
- 自研框架：开发成本高，维护复杂

**影响**：Positive - 高扩展性，易于维护

### 2. 为什么选择 Pydantic？

**决策**：使用 Pydantic v2 进行数据验证

**理由**：
- **类型安全**：自动类型检查和转换
- **自动验证**：字段验证和错误提示
- **JSON 序列化**：`model_dump_json()` 方法
- **文档化**：自动生成 JSON Schema

**替代方案**：
- dataclasses：更轻量但缺少自动验证
- 手动验证：代码冗余，易出错

**影响**：Positive - 减少错误，提高代码质量

### 3. 为什么选择 Rich？

**决策**：使用 Rich 进行 CLI 输出美化

**理由**：
- **美观输出**：Panel、Syntax、Table 等组件
- **颜色高亮**：语法高亮和状态指示
- **进度显示**：Status 组件显示处理进度
- **用户友好**：提升用户体验

**替代方案**：
- 标准输出：功能单调，用户体验差
- colorama：功能有限，需要手动实现

**影响**：Positive - 提升用户体验

### 4. 为什么使用 f-string 而非 Jinja2？

**决策**：使用 Python f-string 作为模板引擎

**理由**：
- **轻量级**：零额外依赖，Python 内置
- **简单**：语法简单，易于理解
- **满足需求**：v1 阶段模板复杂度不高
- **性能好**：无需额外解析开销

**替代方案**：
- Jinja2：功能强大但增加依赖
- Mako：过时，社区不活跃

**影响**：Positive - 减少依赖，满足 v1 需求

### 5. 为什么使用混合意图识别？

**决策**：规则预筛选 + LLM 确认的两阶段模式

**理由**：
- **速度快**：规则匹配毫秒级响应
- **成本低**：大部分场景不调用 LLM
- **灵活性**：LLM 处理复杂场景
- **可扩展**：易于添加新规则

**替代方案**：
- 纯 LLM 识别：成本高，速度慢
- 纯规则识别：不够智能，难以扩展

**影响**：Positive - 平衡速度和准确性

### 6. 为什么会话级上下文（非持久化）？

**决策**：会话数据仅在内存中存储

**理由**：
- **简化架构**：降低 v1 复杂度
- **自动清理**：会话结束自动清理
- **避免一致性问题**：无需管理数据同步

**替代方案**：
- 数据持久化：增加复杂度，依赖外部存储
- 文件存储：状态管理复杂，并发问题

**影响**：Positive - 简化架构，专注核心功能

## 扩展点

### 1. 添加新的子 Agent

**步骤**：
1. 创建 Agent 类，继承 `Agent` 基类
2. 使用 `@AgentRegistry.register()` 装饰器注册
3. 实现 `execute()` 方法
4. 在 `graph.py` 中添加节点
5. 在 `route_by_intent()` 中添加路由逻辑

**示例**：
```python
@AgentRegistry.register('deploy')
class DeployAgent(Agent):
    async def execute(self, state: AgentState, config: RunnableConfig) -> AgentState:
        # 部署逻辑
        return state
```

### 2. 添加新的语言支持

**步骤**：
1. 创建解析器类，继承 `BaseParser`
2. 实现 `can_parse()` 和 `parse()` 方法
3. 在 `parsers/__init__.py` 中导入
4. 创建配置模板文件
5. 在 `ConfigGenerator` 中添加语言特定逻辑

**示例**：
```python
class RustParser(BaseParser):
    def can_parse(self, project_path: Path) -> bool:
        return (project_path / "Cargo.toml").exists()

    def parse(self, project_path: Path) -> ProjectInfo:
        # 解析 Cargo.toml
        return ProjectInfo(...)
```

### 3. 添加自定义配置模板

**步骤**：
1. 创建 `~/.devops-agent/templates/{language}/ci.yml.template`
2. 使用 f-string 语法
3. 系统自动使用自定义模板覆盖默认模板

### 4. 添加新的意图识别

**步骤**：
1. 在 `main_agent.py` 的 `RULES` 字典中添加正则规则
2. 或在 `INTENT_RECOGNITION_PROMPT` 中添加意图描述

## 性能考虑

### 1. 模板缓存

使用 `lru_cache` 缓存模板，减少文件 I/O：
```python
@lru_cache(maxsize=32)
def _load_template(language: str) -> str:
    # 模板加载逻辑
```

### 2. LLM 调用优化

- 规则预筛选减少 LLM 调用
- 重试逻辑避免临时失败
- 敏感信息过滤减少 Token 消耗

### 3. 异步处理

- Agent 执行使用 `async/await`
- LangGraph 原生支持异步
- 提高并发性能

## 安全考虑

### 1. 敏感信息过滤

- API Key、Token 等不写入日志
- 错误消息中过滤敏感信息
- 配置文件权限控制

### 2. 输入验证

- Pydantic 模型自动验证
- 项目路径验证（防止路径遍历）
- YAML 配置验证

### 3. 错误处理

- 统一的错误格式化
- 友好的错误消息
- 修复建议提示

## 测试策略

### 1. 单元测试

- Agent 逻辑测试
- 解析器功能测试
- 配置生成测试
- LLM 客户端 Mock 测试

### 2. 集成测试

- CLI 命令测试
- Agent 协作测试
- 端到端流程测试

### 3. 测试覆盖率

- 目标：> 80%
- 工具：pytest + pytest-cov

## 部署考虑

### 1. 安装方式

```bash
# 从 PyPI 安装
pip install devops-agent

# 从源码安装
pip install -e .
```

### 2. 配置文件

```yaml
# ~/config/devops-agent/config.yaml
llm:
  provider: claude
  api_key: your_api_key_here
  model: claude-3-5-sonnet-20241022
```

### 3. 环境变量

```bash
export DEVOPS_AGENT_CONFIG=/path/to/config.yaml
export ANTHROPIC_API_KEY=your_api_key_here
```

## 未来方向

### v1.1 规划

- 更多语言支持（Rust, Ruby, PHP）
- 配置模板优化
- 性能优化
- 更多测试覆盖

### v2.0 规划

- 持久化会话历史
- Web UI
- 更多 DevOps 工具支持（Docker, Kubernetes）
- 团队协作功能

---

**文档版本**：1.0.0
**最后更新**：2026-02-26
**维护者**：DevOps Agent Team
