"""
项目检测器和语言识别模块

提供项目根目录查找、语言类型检测、Monorepo 结构识别等功能。
"""

from pathlib import Path
from typing import Dict, List, Optional


# 语言标记文件定义
LANGUAGE_MARKERS = {
    "python": [
        "requirements.txt",
        "setup.py",
        "pyproject.toml",
        "Pipfile",
        "poetry.lock",
    ],
    "nodejs": [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "tsconfig.json",
    ],
    "go": [
        "go.mod",
        "go.sum",
    ],
    "java": [
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
    ],
}

# Monorepo 常见子项目目录
MONOREPO_PATTERNS = [
    "packages/*",
    "apps/*",
    "services/*",
    "modules/*",
]

# 需要排除的依赖目录
EXCLUDED_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "dist",
    "build",
    "target",
}


def find_project_root(cwd: Path) -> Optional[Path]:
    """从当前目录向上查找项目根目录（包含 .git 的目录）

    Args:
        cwd: 当前工作目录

    Returns:
        项目根目录路径，如果未找到则返回 None
    """
    current = cwd.resolve()
    # 遍历到文件系统根目录，最多100次防止无限循环
    for _ in range(100):
        if (current / ".git").exists():
            return current
        parent = current.parent
        if parent == current:  # 已到达根目录
            break
        current = parent
    return None


def detect_languages(project_root: Path) -> Dict[str, List[str]]:
    """检测项目中所有存在的语言类型

    扫描所有标记文件，不返回第一个匹配，支持多语言项目。

    Args:
        project_root: 项目根目录

    Returns:
        字典：{语言名: [找到的标记文件列表]}
    """
    detected = {}
    for language, markers in LANGUAGE_MARKERS.items():
        found = [m for m in markers if (project_root / m).exists()]
        if found:
            detected[language] = found
    return detected


def determine_primary_language(detected: Dict[str, List[str]]) -> str:
    """根据标记文件数量决定主语言

    Args:
        detected: detect_languages 的返回值

    Returns:
        主语言名称，无语言时返回 "unknown"
    """
    if not detected:
        return "unknown"
    # 按标记文件数量排序
    counter = {lang: len(files) for lang, files in detected.items()}
    return max(counter.items(), key=lambda x: x[1])[0]


def is_valid_project(project_root: Path) -> bool:
    """检查路径是否是有效的项目根目录

    必须存在 .git 目录（CONTEXT.md 锁定决策）。

    Args:
        project_root: 要检查的路径

    Returns:
        是否是有效的项目根目录
    """
    return (project_root / ".git").exists()


def detect_monorepo(project_root: Path) -> List[Path]:
    """检测 Monorepo 结构中的子项目

    检测常见的 Monorepo 目录模式（packages/, apps/ 等），返回包含子项目的路径列表。
    每个子项目必须包含自己的依赖标记文件或 .git 目录。

    Args:
        project_root: 项目根目录

    Returns:
        子项目路径列表，不是 Monorepo 时返回空列表
    """
    subprojects = []

    for pattern in MONOREPO_PATTERNS:
        # 展开glob模式
        for subproject_dir in project_root.glob(pattern):
            if not subproject_dir.is_dir():
                continue

            # 排除依赖目录
            if subproject_dir.name in EXCLUDED_DIRS:
                continue

            # 检查是否有 .git 目录
            if (subproject_dir / ".git").exists():
                subprojects.append(subproject_dir)
                continue

            # 检查是否有项目标记文件
            has_markers = False
            for markers in LANGUAGE_MARKERS.values():
                for marker in markers:
                    if (subproject_dir / marker).exists():
                        has_markers = True
                        break
                if has_markers:
                    break

            if has_markers:
                subprojects.append(subproject_dir)

    return subprojects
