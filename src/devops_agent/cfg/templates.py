"""
GitHub Actions 模板系统

提供模板加载和管理功能，支持用户自定义模板覆盖。
"""

from pathlib import Path
from typing import List


# 模板目录常量
# 模板文件位于项目根目录的 templates/github-actions/
# 从 src/devops_agent/config/templates.py 向上三级到达项目根目录
TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "templates" / "github-actions"
USER_TEMPLATE_DIR = Path.home() / ".devops-agent" / "templates" / "github-actions"


def get_template(language: str) -> str:
    """获取指定语言的模板

    优先使用用户自定义模板，如果不存在则使用默认模板。

    Args:
        language: 编程语言（python, nodejs, go, java）

    Returns:
        模板内容字符串

    Raises:
        FileNotFoundError: 模板文件不存在
        ValueError: 不支持的语言
    """
    # 标准化语言名称
    language = language.lower()

    # 验证语言支持
    supported_languages = ["python", "nodejs", "go", "java"]
    if language not in supported_languages:
        raise ValueError(
            f"不支持的语言: {language}。支持的语言: {', '.join(supported_languages)}"
        )

    # 构建模板路径
    user_template_path = USER_TEMPLATE_DIR / language / "ci.yml.template"
    default_template_path = TEMPLATE_DIR / language / "ci.yml.template"

    # 优先使用用户模板
    if user_template_path.exists():
        template_path = user_template_path
    else:
        template_path = default_template_path

    # 检查模板是否存在
    if not template_path.exists():
        raise FileNotFoundError(f"模板文件不存在: {template_path}")

    # 读取模板内容
    return template_path.read_text(encoding="utf-8")


def list_templates() -> List[str]:
    """列出所有支持的语言模板

    Returns:
        语言列表
    """
    supported_languages = ["python", "nodejs", "go", "java"]

    # 只返回实际存在的模板
    available = []
    for lang in supported_languages:
        default_path = TEMPLATE_DIR / lang / "ci.yml.template"
        if default_path.exists():
            available.append(lang)

    return available


def ensure_user_template_dir() -> Path:
    """确保用户模板目录存在

    如果用户模板目录不存在，则创建它。

    Returns:
        用户模板目录路径
    """
    USER_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    return USER_TEMPLATE_DIR
