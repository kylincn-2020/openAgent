# 贡献指南

感谢你考虑为 DevOps Agent 做出贡献！本文档将帮助你了解如何参与项目开发。

## 概述

DevOps Agent 是一个开源项目，我们欢迎所有形式的贡献，包括但不限于：

- 报告 Bug
- 讨论代码状态
- 提交修复
- 提出新功能
- 成为维护者

我们使用 GitHub 来托管代码、跟踪问题和功能请求，以及接受 Pull Request。

## 行为准则

参与本项目意味着你同意遵守我们的行为准则：

- 尊重所有贡献者
- 使用包容和友好的语言
- 乐于接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

## 开发环境设置

### 前置要求

- Python 3.11 或更高版本
- Git
- pip 或 Poetry

### Fork 和克隆仓库

1. Fork 项目仓库到你的 GitHub 账户
2. 克隆你的 Fork：

```bash
git clone https://github.com/your-username/devops-agent.git
cd devops-agent
```

3. 添加上游远程仓库：

```bash
git remote add upstream https://github.com/original-owner/devops-agent.git
```

### 安装依赖

使用 pip 安装开发依赖：

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装项目及其开发依赖
pip install -e .[dev]
```

或使用 Poetry：

```bash
poetry install --with dev
```

### 配置开发环境

1. 复制环境变量示例文件：

```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，添加你的配置：

```bash
# LLM 配置
ANTHROPIC_API_KEY=your_api_key_here
DEVOPS_AGENT_CONFIG=/path/to/config.yaml
```

### 验证安装

运行测试确保一切正常：

```bash
pytest
```

## 代码风格

### Python 代码规范

我们遵循 PEP 8 编码规范，并使用以下工具确保代码质量：

### 格式化代码

使用 Black 自动格式化代码：

```bash
black .
```

### 排序导入

使用 isort 自动排序导入：

```bash
isort .
```

### 类型检查

使用 mypy 进行类型检查：

```bash
mypy src/
```

### 代码检查

使用 ruff 进行代码检查：

```bash
ruff check src/
```

### 自动修复

许多工具可以自动修复问题：

```bash
# Black 自动格式化
black .

# isort 自动排序
isort .

# ruff 自动修复
ruff check --fix src/
```

### Pre-commit 钩子（可选）

安装 pre-commit 钩子自动运行检查：

```bash
pip install pre-commit
pre-commit install
```

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范来格式化提交消息。

### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构（既不是新功能也不是修复）
- `perf`: 性能优化
- `test`: 添加测试
- `chore`: 构建过程或辅助工具的变动
- `ci`: CI 配置文件和脚本的变动
- `revert`: 回退之前的 commit

### Scope 范围

- `cli`: CLI 命令和交互
- `agent`: Agent 系统和逻辑
- `analyzer`: 项目分析器
- `config`: 配置生成器
- `llm`: LLM 客户端
- `session`: 会话管理
- `docs`: 文档

### 示例

```bash
feat(agent): 添加部署 Agent

- 实现 DeployAgent 类
- 支持部署到云平台
- 添加部署配置验证

Closes #123
```

```bash
fix(analyzer): 修复 Go 解析器依赖提取

- 正确解析 indirect 依赖
- 添加单元测试

Fixes #456
```

```bash
docs(readme): 更新安装说明

- 添加 Poetry 安装方法
- 更新依赖版本
```

## 测试指南

### 编写测试

我们使用 pytest 作为测试框架。所有新功能都应该包含相应的测试。

### 单元测试

测试单个函数或类的行为：

```python
# tests/test_agent.py

import pytest
from devops_agent.agent.base import Agent, AgentRegistry
from devops_agent.agent.state import AgentState


def test_agent_registry_register():
    """测试 Agent 注册"""
    @AgentRegistry.register('test_agent')
    class TestAgent(Agent):
        async def execute(self, state, config):
            return state

    assert 'test_agent' in AgentRegistry.list_agents()


@pytest.mark.asyncio
async def test_agent_execute():
    """测试 Agent 执行"""
    state: AgentState = {
        "user_input": "test",
        "intent": "test",
        "project_path": "/test",
        "context": {},
        "agent_results": [],
        "errors": [],
        "response": "",
    }

    from unittest.mock import Mock
    llm_client = Mock()

    @AgentRegistry.register('test_agent')
    class TestAgent(Agent):
        async def execute(self, state, config):
            state["response"] = "test response"
            return state

    agent = TestAgent(state, llm_client)
    result = await agent.execute()

    assert result["response"] == "test response"
```

### 集成测试

测试多个组件的协作：

```python
# tests/test_integration.py

import pytest
from pathlib import Path
from devops_agent.analyzer import ProjectAnalyzer


def test_project_analyzer_python_project():
    """测试 Python 项目分析"""
    # 创建测试项目
    test_project = Path("/tmp/test_python_project")
    test_project.mkdir(exist_ok=True)
    (test_project / "pyproject.toml").write_text("""
[project]
name = "test-project"
version = "0.1.0"
dependencies = ["requests"]
""")

    # 分析项目
    analyzer = ProjectAnalyzer()
    result = analyzer.analyze(str(test_project))

    # 验证结果
    assert result.primary_language == "Python"
    assert "requests" in result.languages[0].dependencies
```

### 运行测试

运行所有测试：

```bash
pytest
```

运行特定测试文件：

```bash
pytest tests/test_agent.py
```

运行特定测试：

```bash
pytest tests/test_agent.py::test_agent_registry_register
```

运行测试并显示覆盖率：

```bash
pytest --cov=src/devops_agent --cov-report=html
```

### 测试覆盖率要求

我们要求新代码的测试覆盖率至少达到 80%。

查看覆盖率报告：

```bash
pytest --cov=src/devops_agent --cov-report=term-missing
```

## Pull Request 流程

### 1. 创建功能分支

从 `main` 分支创建新分支：

```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

分支命名规范：

- `feature/` - 新功能
- `fix/` - Bug 修复
- `docs/` - 文档更新
- `refactor/` - 重构
- `test/` - 添加测试

### 2. 进行更改

- 编写代码
- 添加测试
- 更新文档（如需要）
- 运行格式化工具
- 运行测试确保通过

### 3. 提交更改

使用 Conventional Commits 规范提交：

```bash
git add .
git commit -m "feat(agent): 添加新功能描述"
```

### 4. 推送到你的 Fork

```bash
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

1. 访问 GitHub 上的你的 Fork
2. 点击 "New Pull Request"
3. 提供清晰的 PR 描述：
   - **标题**：使用 Conventional Commits 格式
   - **描述**：
     - 这个 PR 做什么？
     - 为什么需要这个更改？
     - 如何测试这些更改？
     - 相关 Issue 链接
   - **检查清单**：
     - [ ] 代码遵循项目风格指南
     - [ ] 已进行自我审查
     - [ ] 已添加注释（特别是难以理解的代码）
     - [ ] 已更新文档
     - [ ] 已添加测试
     - [ ] 所有测试通过

### 6. 代码审查

维护者会审查你的 PR，可能会：

- 请求更改
- 提出改进建议
- 询问设计决策

请保持开放和友好的态度讨论反馈。

### 7. 合并

一旦 PR 被批准并通过所有 CI 检查，维护者会将其合并到 `main` 分支。

## 报告 Bug

### 在提交 Bug 之前

1. 检查是否已存在相同的 Issue
2. 确认这是一个 Bug 而非问题请求
3. 收集必要的信息

### Bug 报告应包含

- **标题**：简短描述 Bug
- **描述**：详细说明问题
- **重现步骤**：
  1. 执行 '...'
  2. 点击 '....'
  3. 滚动到 '....'
  4. 看到错误
- **预期行为**：应该发生什么
- **实际行为**：实际发生了什么
- **环境**：
  - 操作系统：
  - Python 版本：
  - 项目版本：
- **日志**：相关错误日志
- **截图**：如果有帮助

## 功能请求

### 功能请求应包含

- **标题**：简短描述功能
- **问题描述**：这个功能解决什么问题？
- **建议的解决方案**：你希望如何实现？
- **替代方案**：你考虑过的其他解决方案
- **附加信息**：任何其他相关信息

## 开发指南

### 项目结构

```
devops-agent/
├── src/devops_agent/
│   ├── agent/          # Agent 系统
│   ├── analyzer/       # 项目分析器
│   ├── config/         # 配置生成器
│   ├── llm/            # LLM 客户端
│   ├── session/        # 会话管理
│   └── cli.py          # CLI 入口
├── tests/              # 测试
├── docs/               # 文档
├── templates/          # 配置模板
└── pyproject.toml      # 项目配置
```

### 添加新功能

1. 阅读相关文档（ARCHITECTURE.md、EXTENSIBILITY.md）
2. 创建 Issue 讨论设计（如果是重大功能）
3. 创建功能分支
4. 实现功能并编写测试
5. 更新文档
6. 提交 Pull Request

### 代码审查要点

- 代码是否遵循项目风格？
- 是否有足够的测试？
- 是否处理了错误情况？
- 是否有文档说明？
- 是否会影响现有功能？

## 发布流程

### 版本号

我们遵循 [语义化版本](https://semver.org/)：

- **主版本号**：不兼容的 API 变更
- **次版本号**：向下兼容的功能新增
- **修订号**：向下兼容的问题修正

### 发布步骤

维护者执行以下步骤发布新版本：

1. 更新 `pyproject.toml` 中的版本号
2. 更新 `CHANGELOG.md`
3. 创建 Git tag
4. 构建 Distribution 包
5. 发布到 PyPI

## 社区

### 获取帮助

- GitHub Issues：报告 Bug 和功能请求
- Discussions：提问和讨论
- Wiki：详细文档和教程

### 成为维护者

活跃的贡献者可能被邀请成为维护者。维护者负责：

- 审查和合并 Pull Request
- 维护 Issue 跟踪
- 发布新版本
- 引导新贡献者

## 许可证

通过贡献代码，你同意你的贡献将使用与项目相同的 [MIT 许可证](LICENSE)。

## 致谢

感谢所有贡献者！你的贡献让 DevOps Agent 变得更好。

---

**文档版本**：1.0.0
**最后更新**：2026-02-26
**维护者**：DevOps Agent Team
