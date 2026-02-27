# DevOps Agent 扩展指南

本文档说明如何扩展 DevOps Agent 系统，包括添加新的子 Agent、新的语言支持和自定义 LLM 端点。

## 概述

DevOps Agent 采用高度可扩展的架构设计，通过装饰器注册模式和策略模式，使得添加新功能变得简单。

### 核心扩展点

1. **Agent 系统**：添加新的功能 Agent（如部署 Agent、监控 Agent）
2. **语言解析器**：支持新的编程语言（如 Rust、Ruby）
3. **配置模板**：自定义 CI/CD 流程模板
4. **意图识别**：添加新的意图关键词
5. **LLM 端点**：配置自定义 LLM API 端点

## Adding Custom LLM Endpoints

The framework supports any OpenAI-compatible LLM endpoint out of the box. To use a custom endpoint:

### Step 1: Configure the endpoint in config.yaml

```yaml
llm:
  provider: custom
  api_key: your-custom-endpoint-key
  model: your-model-name
  base_url: https://your-endpoint.com/v1
  max_retries: 3
  timeout: 30
```

**Key fields:**
- `provider: custom` - Tells the framework to use custom endpoint mode
- `base_url` - Your endpoint's base URL (must start with http:// or https://)
- `api_key` - Your endpoint's API key
- `model` - The model identifier your endpoint uses

### Step 2: Framework automatically handles the rest

The framework will:
1. Pass the `api_base` parameter to LiteLLM for all requests
2. Apply standard retry and timeout logic
3. Enable streaming support (if your endpoint supports it)
4. Log all requests with provider, model, and base_url information
5. Provide clear error messages with fix suggestions

### Step 3: Verify your configuration

```bash
# Test the configuration
devops-agent analyze

# Check logs for any errors
tail -f ~/logs/devops-agent.log
```

### For non-OpenAI-compatible endpoints

If your endpoint doesn't follow the OpenAI API format, extend the `LLMClient` class:

```python
# src/devops_agent/llm/custom_client.py

from devops_agent.llm.client import LLMClient, LLMCallError
from typing import Any

class CustomEndpointClient(LLMClient):
    """Custom endpoint client for non-OpenAI-compatible APIs."""

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Call custom endpoint with provider-specific logic."""
        try:
            # Implement your provider-specific API call logic
            response = await self._call_custom_api(prompt, **kwargs)
            return response.text
        except Exception as e:
            raise LLMCallError(
                f"Custom endpoint error: {str(e)}",
                fix_suggestions=(
                    "1. Check your endpoint documentation\n"
                    "2. Verify API key and model name\n"
                    "3. Ensure endpoint is accessible"
                ),
            ) from e

    async def _call_custom_api(self, prompt: str, **kwargs: Any) -> Any:
        """Implement provider-specific API call."""
        # Your custom API call logic here
        pass
```

Then register your custom client in the application initialization.

### Best practices for custom endpoints

1. **API format compatibility**: Ensure your endpoint is compatible with OpenAI API format
2. **Error handling**: Always wrap errors in `LLMCallError` with helpful fix suggestions
3. **Logging**: Use structured logging with provider, model, and base_url fields
4. **Testing**: Test your endpoint connectivity before using in production
5. **Security**: Never log or expose API keys in error messages

## 添加新的子 Agent

子 Agent 是扩展系统功能的主要方式。通过添加新的 Agent，可以支持更多的 DevOps 场景。

### 步骤 1：创建 Agent 类

创建新的 Agent 类，继承自 `Agent` 基类，并使用 `@AgentRegistry.register()` 装饰器注册。

```python
# src/devops_agent/agent/deploy_agent.py

from typing import Dict, Any
from langgraph.types import RunnableConfig
from devops_agent.agent.base import Agent, AgentRegistry
from devops_agent.agent.state import AgentState


@AgentRegistry.register("deploy")
class DeployAgent(Agent):
    """部署 Agent

    负责将应用部署到目标环境（如云平台、服务器）。
    """

    name = "Deploy Agent"
    description = "部署应用到目标环境"

    async def execute(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """执行部署逻辑

        Args:
            state: Agent 状态
            config: LangGraph 配置

        Returns:
            更新后的 AgentState
        """
        # 1. 从 state 获取输入
        user_input = state.get("user_input", "")
        project_path = state.get("project_path", "")

        # 2. 获取上下文（如果需要）
        deployment_config = self.get_context("deployment_config", {})

        # 3. 执行业务逻辑
        try:
            result = await self._deploy_application(project_path, deployment_config)

            # 4. 更新 state
            state["response"] = f"部署成功：{result}"
            state["last_agent"] = self.name
            self.add_result("deploy", result)

        except Exception as e:
            # 5. 错误处理
            self.add_error(f"部署失败：{str(e)}")
            state["response"] = f"部署失败：{str(e)}"

        return state

    async def _deploy_application(
        self, project_path: str, config: Dict[str, Any]
    ) -> str:
        """实际部署逻辑

        Args:
            project_path: 项目路径
            config: 部署配置

        Returns:
            部署结果
        """
        # 实现你的部署逻辑
        # 例如：调用云平台 API、执行部署脚本等
        return "部署到生产环境"
```

**关键点**：
- 使用 `@AgentRegistry.register("deploy")` 注册 Agent
- `name` 和 `description` 属性用于日志和调试
- `execute()` 方法是核心逻辑，必须返回 `AgentState`
- 使用 `self.get_context()` 获取会话上下文
- 使用 `self.add_error()` 添加错误信息
- 使用 `self.add_result()` 记录执行结果

### 步骤 2：定义意图关键词

在 Agent 文件中定义意图关键词，用于规则匹配。

```python
# src/devops_agent/agent/deploy_agent.py

INTENT_KEYWORDS = [
    r"部署",
    r"deploy",
    r"发布",
    r"release",
]
```

**说明**：
- 这些关键词会在 `IntentRouter.route_by_rules()` 中使用
- 使用正则表达式支持更复杂的模式
- 关键词会在规则匹配阶段预筛选

### 步骤 3：在 graph.py 中添加节点

在 `src/devops_agent/agent/graph.py` 中创建节点函数。

```python
# src/devops_agent/agent/graph.py

from devops_agent.agent.deploy_agent import DeployAgent


def deploy_agent_node(state: AgentState, config: dict) -> AgentState:
    """部署 Agent 节点

    LangGraph 节点函数签名。

    Args:
        state: Agent 状态
        config: 配置字典（包含 llm_client）

    Returns:
        更新后的 AgentState
    """
    # 从 config 中获取 llm_client
    llm_client = config.get('configurable', {}).get('llm_client')
    agent = DeployAgent(state, llm_client)

    # 执行 Agent（同步包装异步执行）
    import asyncio
    return asyncio.run(agent.execute())
```

### 步骤 4：在工作流中注册节点

在 `create_agent_graph()` 函数中添加节点。

```python
# src/devops_agent/agent/graph.py

def create_agent_graph() -> StateGraph:
    """构建 LangGraph 工作流"""
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("main_agent", main_agent_node)
    graph.add_node("project_agent", project_agent_node)
    graph.add_node("build_agent", build_agent_node)
    graph.add_node("deploy_agent", deploy_agent_node)  # 新增

    # 设置入口点
    graph.set_entry_point("main_agent")

    # ... 其余代码
```

### 步骤 5：添加条件边路由

在 `route_by_intent()` 函数中添加路由逻辑。

```python
# src/devops_agent/agent/graph.py

def route_by_intent(state: AgentState) -> str:
    """根据意图路由到不同的 Agent"""
    intent = state.get("intent", "unknown")

    if intent == "analyze_project":
        return "project_agent"
    elif intent == "generate_ci":
        return "build_agent"
    elif intent == "deploy":  # 新增
        return "deploy_agent"
    else:
        return END
```

同时需要在条件边配置中添加：

```python
# src/devops_agent/agent/graph.py

graph.add_conditional_edges(
    "main_agent",
    route_by_intent,
    {
        "project_agent": "project_agent",
        "build_agent": "build_agent",
        "deploy_agent": "deploy_agent",  # 新增
        END: END,
    },
)
```

### 步骤 6：添加结束边

如果 Agent 完成后需要结束，添加边到 `END`。

```python
# src/devops_agent/agent/graph.py

# 添加边：deploy_agent 结束
graph.add_edge("deploy_agent", END)
```

### 步骤 7：更新意图识别

在 `main_agent.py` 中添加意图关键词。

```python
# src/devops_agent/agent/main_agent.py

class IntentRouter:
    """意图识别器"""

    RULES = {
        "generate_ci": [
            r"generate.*ci",
            r"generate.*workflow",
            r"create.*github.*actions",
        ],
        "analyze_project": [
            r"analyze.*project",
            r"what.*is.*this.*project",
            r"project.*info",
        ],
        "deploy": [  # 新增
            r"部署",
            r"deploy",
            r"发布",
            r"release",
        ],
        # ... 其他意图
    }
```

### 步骤 8：测试新 Agent

创建测试文件验证功能。

```python
# tests/test_deploy_agent.py

import pytest
from devops_agent.agent.deploy_agent import DeployAgent
from devops_agent.agent.state import AgentState


@pytest.mark.asyncio
async def test_deploy_agent():
    """测试部署 Agent"""
    # 创建测试状态
    state: AgentState = {
        "user_input": "部署到生产环境",
        "intent": "deploy",
        "project_path": "/test/project",
        "context": {"deployment_config": {"env": "production"}},
        "agent_results": [],
        "errors": [],
        "response": "",
    }

    # 创建 Mock LLM 客户端
    from unittest.mock import Mock
    llm_client = Mock()

    # 创建 Agent 并执行
    agent = DeployAgent(state, llm_client)
    result = await agent.execute()

    # 验证结果
    assert "部署" in result["response"]
    assert len(result["errors"]) == 0
```

## 添加新的语言支持

添加新的编程语言支持包括创建解析器、配置模板和语言特定逻辑。

### 步骤 1：创建解析器类

创建新的解析器类，继承自 `BaseParser`。

```python
# src/devops_agent/analyzer/parsers/rust.py

from pathlib import Path
from typing import List, Dict, Any, Optional
from devops_agent.analyzer.parsers.base import BaseParser
from devops_agent.analyzer.models import ProjectInfo


class RustParser(BaseParser):
    """Rust 项目解析器

    解析 Cargo.toml 文件，提取依赖、构建命令和测试命令。
    """

    def can_parse(self, project_path: Path) -> bool:
        """检查是否可以解析该项目

        Args:
            project_path: 项目路径

        Returns:
            如果存在 Cargo.toml 则返回 True
        """
        return (project_path / "Cargo.toml").exists()

    def parse(self, project_path: Path) -> ProjectInfo:
        """解析 Rust 项目

        Args:
            project_path: 项目路径

        Returns:
            项目信息

        Raises:
            ProjectAnalysisError: 解析失败时抛出
        """
        try:
            import toml

            cargo_toml = project_path / "Cargo.toml"

            # 读取 Cargo.toml
            with open(cargo_toml, "r", encoding="utf-8") as f:
                cargo_config = toml.load(f)

            # 提取基本信息
            package = cargo_config.get("package", {})
            name = package.get("name", "unknown")
            version = package.get("version", "0.1.0")

            # 提取依赖
            dependencies = self._extract_dependencies(cargo_config)

            # 检测框架
            framework = self._detect_framework(cargo_config)

            # 构建元数据
            metadata = {
                "package_name": name,
                "version": version,
                "edition": cargo_config.get("package", {}).get("edition", "2021"),
            }

            return ProjectInfo(
                language="Rust",
                framework=framework,
                dependencies=dependencies,
                build_command="cargo build --release",
                test_command="cargo test",
                metadata=metadata,
            )

        except Exception as e:
            from devops_agent.analyzer.exceptions import ProjectAnalysisError
            raise ProjectAnalysisError(
                f"解析 Rust 项目失败：{str(e)}",
                project_path=str(project_path),
                fix_suggestions="确保 Cargo.toml 文件存在且格式正确",
            ) from e

    def _extract_dependencies(self, cargo_config: Dict[str, Any]) -> List[str]:
        """提取依赖列表

        Args:
            cargo_config: Cargo.toml 配置

        Returns:
            依赖名称列表
        """
        dependencies = cargo_config.get("dependencies", {})
        return list(dependencies.keys())

    def _detect_framework(self, cargo_config: Dict[str, Any]) -> Optional[str]:
        """检测使用的框架

        Args:
            cargo_config: Cargo.toml 配置

        Returns:
            框架名称（如果检测到）
        """
        dependencies = cargo_config.get("dependencies", {})

        # 检测常见 Web 框架
        if "actix-web" in dependencies:
            return "Actix Web"
        if "rocket" in dependencies:
            return "Rocket"
        if "warp" in dependencies:
            return "Warp"

        return None
```

**关键点**：
- 继承 `BaseParser` 抽象基类
- 实现 `can_parse()` 方法，判断是否可以解析
- 实现 `parse()` 方法，返回 `ProjectInfo`
- 抛出 `ProjectAnalysisError` 处理解析错误
- 提取依赖、构建命令、测试命令

### 步骤 2：注册解析器

在 `src/devops_agent/analyzer/parsers/__init__.py` 中导入解析器。

```python
# src/devops_agent/analyzer/parsers/__init__.py

"""语言特定解析器模块"""

from devops_agent.analyzer.parsers.python import PythonParser
from devops_agent.analyzer.parsers.nodejs import NodeJSParser
from devops_agent.analyzer.parsers.go import GoParser
from devops_agent.analyzer.parsers.java import JavaParser
from devops_agent.analyzer.parsers.rust import RustParser  # 新增

__all__ = [
    "PythonParser",
    "NodeJSParser",
    "GoParser",
    "JavaParser",
    "RustParser",  # 新增
]
```

**说明**：
- 系统会自动检测所有 `__all__` 中的解析器
- 无需手动注册，自动集成到 `ProjectAnalyzer`

### 步骤 3：创建配置模板

创建语言特定的配置模板。

```bash
mkdir -p templates/github-actions/rust
```

```yaml
# templates/github-actions/rust/ci.yml.template

name: CI for {language}

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test_and_build:
    name: Test and Build
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Install Rust toolchain
        uses: actions-rs/toolchain@v1
        with:
          profile: minimal
          toolchain: {rust_version}
          override: true
          components: rustfmt, clippy

      - name: Cache cargo registry
        uses: actions/cache@v3
        with:
          path: ~/.cargo/registry
          key: ${{{{ runner.os }}}}-cargo-registry-${{{{ hashFiles('**/Cargo.lock') }}}}

      - name: Cache cargo index
        uses: actions/cache@v3
        with:
          path: ~/.cargo/git
          key: ${{{{ runner.os }}}}-cargo-index-${{{{ hashFiles('**/Cargo.lock') }}}}

      - name: Cache cargo build
        uses: actions/cache@v3
        with:
          path: target
          key: ${{{{ runner.os }}}}-cargo-build-target-${{{{ hashFiles('**/Cargo.lock') }}}}

      - name: Build
        run: cargo build --verbose

      - name: Run tests
        run: cargo test --verbose

      - name: Run clippy
        run: cargo clippy -- -D warnings

      - name: Check formatting
        run: cargo fmt -- --check
```

**关键点**：
- 使用 `{variable}` 语法引用变量
- 包含依赖缓存以加快构建速度
- 包含测试、构建、格式检查步骤

### 步骤 4：添加语言特定逻辑

在 `ConfigGenerator` 中添加 Rust 特定的变量构建。

```python
# src/devops_agent/config/generator.py

class ConfigGenerator:
    # ... 现有代码

    def _get_language_specific_vars(
        self, project_info: ProjectInfo
    ) -> Dict[str, Any]:
        """获取语言特定变量

        Args:
            project_info: 项目信息

        Returns:
            语言特定变量字典
        """
        language = project_info.language

        if language == "Python":
            return self._get_python_vars(project_info)
        elif language == "Node.js":
            return self._get_nodejs_vars(project_info)
        elif language == "Go":
            return self._get_go_vars(project_info)
        elif language == "Java":
            return self._get_java_vars(project_info)
        elif language == "Rust":  # 新增
            return self._get_rust_vars(project_info)
        else:
            return {}

    def _get_rust_vars(self, project_info: ProjectInfo) -> Dict[str, Any]:
        """获取 Rust 特定变量

        Args:
            project_info: 项目信息

        Returns:
            Rust 变量字典
        """
        return {
            "rust_version": project_info.metadata.get("edition", "2021"),
            "language": "Rust",
            "runs_on": "ubuntu-latest",
            "setup_action": "actions-rs/toolchain@v1",
        }
```

**关键点**：
- 在 `_get_language_specific_vars()` 中添加 Rust 分支
- 创建 `_get_rust_vars()` 方法构建变量
- 变量会传递给模板进行渲染

### 步骤 5：更新语言名称规范化

确保语言名称正确规范化。

```python
# src/devops_agent/config/generator.py

class ConfigGenerator:
    def _normalize_language_name(self, language: str) -> str:
        """规范化语言名称用于模板目录

        Args:
            language: 原始语言名称

        Returns:
            规范化后的语言名称
        """
        mapping = {
            "Node.js": "nodejs",
            "C++": "cpp",
            "C#": "csharp",
            "Rust": "rust",  # 新增（如果需要）
        }
        return mapping.get(language, language.lower())
```

### 步骤 6：测试新解析器

创建测试验证功能。

```python
# tests/test_rust_parser.py

import pytest
from pathlib import Path
from devops_agent.analyzer.parsers.rust import RustParser
from devops_agent.analyzer.models import ProjectInfo


def test_rust_parser_can_parse():
    """测试 Rust 解析器 can_parse 方法"""
    parser = RustParser()

    # 创建测试项目
    test_project = Path("/tmp/test_rust_project")
    test_project.mkdir(exist_ok=True)
    (test_project / "Cargo.toml").touch()

    # 验证
    assert parser.can_parse(test_project) is True


def test_rust_parser_parse():
    """测试 Rust 解析器 parse 方法"""
    parser = RustParser()

    # 创建测试项目
    test_project = Path("/tmp/test_rust_project_full")
    test_project.mkdir(exist_ok=True)

    # 创建 Cargo.toml
    cargo_toml_content = """
[package]
name = "test-project"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = "1.0"
tokio = "1.0"
"""
    (test_project / "Cargo.toml").write_text(cargo_toml)

    # 解析
    result = parser.parse(test_project)

    # 验证
    assert result.language == "Rust"
    assert "serde" in result.dependencies
    assert "tokio" in result.dependencies
    assert result.build_command == "cargo build --release"
    assert result.test_command == "cargo test"
```

### 步骤 7：集成到项目分析器

解析器会自动被 `ProjectAnalyzer` 检测和使用，无需额外配置。

```python
# 自动集成 - 无需修改
from devops_agent.analyzer.parsers import RustParser  # 自动注册

analyzer = ProjectAnalyzer()
result = analyzer.analyze("/path/to/rust/project")
# RustParser 会被自动调用
```

## 添加自定义配置模板

用户可以通过提供自定义模板覆盖默认模板。

### 创建自定义模板目录

```bash
mkdir -p ~/.devops-agent/templates/python
```

### 创建自定义模板

```yaml
# ~/.devops-agent/templates/python/ci.yml.template

name: Custom CI for Python

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  custom_test:
    name: Custom Test
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: {python_version}

      # 自定义步骤
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run linting
        run: flake8 src tests

      - name: Run type checking
        run: mypy src

      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=xml
```

**说明**：
- 自定义模板会自动覆盖默认模板
- 使用相同的变量语法（`{variable}`）
- 可以添加任何自定义步骤

### 验证自定义模板

```bash
# 生成配置时使用自定义模板
devops-agent build

# 系统会自动使用 ~/.devops-agent/templates/ 中的模板
```

## 添加新的意图识别

### 方式 1：添加规则关键词

在 `main_agent.py` 的 `RULES` 字典中添加。

```python
# src/devops_agent/agent/main_agent.py

class IntentRouter:
    RULES = {
        "generate_ci": [...],
        "analyze_project": [...],
        "monitor": [  # 新增
            r"监控",
            r"monitor",
            r"查看.*状态",
            r"check.*status",
        ],
        # ... 其他意图
    }
```

### 方式 2：更新 LLM 提示

在 `INTENT_RECOGNITION_PROMPT` 中添加意图描述。

```python
# src/devops_agent/llm/prompts.py

INTENT_RECOGNITION_PROMPT = """
你是一个意图识别助手。根据用户输入，识别用户想要执行的操作。

支持的意图：
- generate_ci: 生成 CI/CD 配置
- analyze_project: 分析项目
- deploy: 部署应用
- monitor: 监控应用状态  # 新增

用户输入：{user_input}

请返回意图名称（generate_ci/analyze_project/deploy/monitor/unknown）。
"""
```

## 最佳实践

### 1. Agent 设计

**单一职责**：每个 Agent 只负责一个功能域

```python
# 好的设计
class DeployAgent(Agent):
    """只负责部署"""

class MonitorAgent(Agent):
    """只负责监控"""

# 不好的设计
class DevOpsAgent(Agent):
    """负责所有 DevOps 操作（太复杂）"""
```

**错误处理**：统一使用 `add_error()` 记录错误

```python
try:
    result = await self._do_something()
    state["response"] = f"成功：{result}"
except Exception as e:
    self.add_error(f"操作失败：{str(e)}")
    state["response"] = f"操作失败：{str(e)}"
```

**上下文管理**：使用 `update_context()` 和 `get_context()`

```python
# 保存上下文供其他 Agent 使用
self.update_context("deployment_env", "production")

# 获取其他 Agent 保存的上下文
env = self.get_context("deployment_env", "staging")
```

### 2. 解析器设计

**依赖提取**：只读取直接依赖，不递归解析

```python
# 好的设计
def _extract_dependencies(self, config):
    # 只读取直接依赖
    return list(config.get("dependencies", {}).keys())

# 不好的设计
def _extract_dependencies(self, config):
    # 递归解析所有传递依赖（性能差）
    return self._recursive_parse(config)
```

**错误处理**：抛出 `ProjectAnalysisError` 而非通用异常

```python
try:
    with open(config_file) as f:
        config = toml.load(f)
except Exception as e:
    raise ProjectAnalysisError(
        f"解析配置文件失败：{str(e)}",
        project_path=str(project_path),
        fix_suggestions="确保文件存在且格式正确",
    ) from e
```

### 3. 模板设计

**变量命名**：使用清晰、一致的变量名

```yaml
# 好的设计
name: CI for {language}
runs-on: {runs_on}
python-version: {python_version}

# 不好的设计
name: CI for {lang}
runs-on: {os}
python-version: {py_ver}
```

**缓存策略**：包含依赖缓存以加快构建

```yaml
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{{{ runner.os }}}}-pip-${{{{ hashFiles('**/requirements.txt') }}}}
```

### 4. 测试策略

**单元测试**：测试单个组件

```python
def test_parser_can_parse():
    parser = RustParser()
    assert parser.can_parse(project_path) is True

def test_parser_parse():
    parser = RustParser()
    result = parser.parse(project_path)
    assert result.language == "Rust"
```

**集成测试**：测试组件协作

```python
def test_project_analyzer_with_rust():
    analyzer = ProjectAnalyzer()
    result = analyzer.analyze(rust_project)
    assert result.primary_language == "Rust"
```

## 扩展示例

### 示例 1：添加 Docker 支持 Agent

```python
# src/devops_agent/agent/docker_agent.py

from devops_agent.agent.base import Agent, AgentRegistry
from devops_agent.agent.state import AgentState


@AgentRegistry.register("docker")
class DockerAgent(Agent):
    """Docker Agent - 生成 Dockerfile 和 docker-compose.yml"""

    name = "Docker Agent"
    description = "生成 Docker 配置"

    async def execute(self, state: AgentState, config) -> AgentState:
        project_path = state.get("project_path")
        # 生成 Dockerfile
        # 生成 docker-compose.yml
        state["response"] = "Docker 配置已生成"
        return state
```

### 示例 2：添加 Ruby 语言支持

```python
# src/devops_agent/analyzer/parsers/ruby.py

class RubyParser(BaseParser):
    def can_parse(self, project_path: Path) -> bool:
        return (project_path / "Gemfile").exists()

    def parse(self, project_path: Path) -> ProjectInfo:
        # 解析 Gemfile
        return ProjectInfo(
            language="Ruby",
            framework=self._detect_framework(),
            dependencies=self._extract_gems(),
            build_command="bundle exec rake build",
            test_command="bundle exec rake test",
            metadata={},
        )
```

## 常见问题

### Q1: 如何调试 Agent？

使用日志记录和调试输出：

```python
from loguru import logger

class MyAgent(Agent):
    async def execute(self, state: AgentState, config) -> AgentState:
        logger.info(f"执行 {self.name}")
        logger.debug(f"状态：{state}")
        # Agent 逻辑
        return state
```

### Q2: 如何 Mock LLM 进行测试？

使用 `unittest.mock.Mock`：

```python
from unittest.mock import Mock

llm_client = Mock()
llm_client.generate.return_value = "测试响应"

agent = MyAgent(state, llm_client)
result = await agent.execute()
```

### Q3: 如何处理复杂的业务逻辑？

将复杂逻辑提取到单独的服务模块：

```python
# src/devops_agent/services/deployment_service.py

class DeploymentService:
    async def deploy_to_cloud(self, config):
        # 复杂的部署逻辑
        pass

# 在 Agent 中使用
class DeployAgent(Agent):
    def __init__(self, state, llm_client):
        super().__init__(state, llm_client)
        self.deployment_service = DeploymentService()

    async def execute(self, state, config):
        result = await self.deployment_service.deploy_to_cloud(config)
        return state
```

### Q4: 如何共享代码逻辑？

创建基类或混入类：

```python
# src/devops_agent/agent/mixins.py

class ConfigWriterMixin:
    def write_config(self, path, content):
        # 通用配置写入逻辑
        pass

# 在 Agent 中使用
class BuildAgent(ConfigWriterMixin, Agent):
    async def execute(self, state, config):
        self.write_config(path, content)
        return state
```

---

**文档版本**：1.0.0
**最后更新**：2026-02-26
**维护者**：DevOps Agent Team
