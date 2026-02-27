"""
Java 项目解析器

解析 pom.xml、build.gradle 等依赖文件。
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from devops_agent.analyzer.models import ProjectInfo
from devops_agent.analyzer.parsers.python import BaseParser


class JavaParser(BaseParser):
    """Java 项目解析器"""

    MARKER_FILES = ["pom.xml", "build.gradle", "build.gradle.kts"]

    def can_parse(self, marker_file: Path) -> bool:
        """判断是否能解析该文件"""
        return marker_file.name in self.MARKER_FILES

    def parse(self, project_root: Path, marker_file: Path) -> ProjectInfo:
        """解析 Java 项目"""
        if marker_file.name == "pom.xml":
            return self._parse_pom(project_root, marker_file)
        elif marker_file.name == "build.gradle":
            return self._parse_gradle(project_root, marker_file)
        elif marker_file.name == "build.gradle.kts":
            return self._parse_gradle_kts(project_root, marker_file)
        else:
            return ProjectInfo(
                language="Java",
                dependency_file=str(marker_file.name),
            )

    def _parse_pom(self, project_root: Path, file: Path) -> ProjectInfo:
        """解析 Maven pom.xml"""
        try:
            tree = ET.parse(file)
            root = tree.getroot()

            # 处理命名空间
            namespace = {"maven": "http://maven.apache.org/POM/4.0.0"}

            # 提取 groupId, artifactId, version
            group_id = self._find_text(root, "maven:groupId", namespace) or self._find_text(
                root, "groupId", namespace
            )
            artifact_id = (
                self._find_text(root, "maven:artifactId", namespace)
                or self._find_text(root, "artifactId", namespace)
            )
            version = (
                self._find_text(root, "maven:version", namespace)
                or self._find_text(root, "version", namespace)
            )

            # 提取依赖
            deps = []
            # 尝试带命名空间查找
            dependencies_el = root.find(".//maven:dependencies", namespace)
            if dependencies_el is None:
                # 尝试不带命名空间查找
                dependencies_el = root.find(".//dependencies")

            if dependencies_el is not None:
                # 尝试带命名空间查找所有 dependency
                dependency_els = dependencies_el.findall("maven:dependency", namespace)
                if not dependency_els:
                    # 尝试不带命名空间查找
                    dependency_els = dependencies_el.findall("dependency")

                for dep in dependency_els:
                    dep_artifact_id = dep.find("maven:artifactId", namespace) if namespace else dep.find("artifactId")
                    if dep_artifact_id is None:
                        dep_artifact_id = dep.find("artifactId")
                    if dep_artifact_id is not None and dep_artifact_id.text:
                        deps.append(dep_artifact_id.text)

            return ProjectInfo(
                language="Java",
                framework=self._detect_framework(deps),
                dependency_file=str(file.name),
                dependencies=deps,
                build_command="mvn clean package - 构建 Maven 项目",
                test_command="mvn test - 运行 Maven 测试",
                metadata={
                    "groupId": group_id or "",
                    "artifactId": artifact_id or "",
                    "version": version or "",
                },
            )
        except ET.ParseError as e:
            print(f"[red]错误: {file} XML 格式无效[/red]")
            print(f"[red]位置: 第 {e.position[0]} 行[/red]")
            print(f"[yellow]建议: 检查 XML 语法和标签闭合[/yellow]")
            return ProjectInfo(
                language="Java",
                dependency_file=str(file.name),
            )
        except FileNotFoundError:
            return ProjectInfo(
                language="Java",
                dependency_file=str(file.name),
            )
        except Exception as e:
            print(f"[yellow]警告: 无法解析 {file}: {e}[/yellow]")
            return ProjectInfo(
                language="Java",
                dependency_file=str(file.name),
            )

    def _parse_gradle(self, project_root: Path, file: Path) -> ProjectInfo:
        """解析 Gradle build.gradle（简化版）"""
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取 dependencies 块中的依赖
            deps = []
            # 匹配 implementation 'group:name:version' 或 "group:name:version"
            for match in re.finditer(
                r'implementation\s+[\'"]([^:]+):([^:]+):[^\']+[\'"]', content
            ):
                group, name = match.groups()
                deps.append(f"{group}:{name}")

            # 匹配 testImplementation
            for match in re.finditer(
                r'testImplementation\s+[\'"]([^:]+):([^:]+):[^\']+[\'"]', content
            ):
                group, name = match.groups()
                deps.append(f"{group}:{name}")

            return ProjectInfo(
                language="Java",
                framework=self._detect_framework(deps),
                dependency_file=str(file.name),
                dependencies=deps,
                build_command="./gradlew build - 构建 Gradle 项目",
                test_command="./gradlew test - 运行 Gradle 测试",
                metadata={},
            )
        except FileNotFoundError:
            return ProjectInfo(
                language="Java",
                dependency_file=str(file.name),
            )
        except Exception as e:
            print(f"[yellow]警告: 无法解析 {file}: {e}[/yellow]")
            return ProjectInfo(
                language="Java",
                dependency_file=str(file.name),
            )

    def _parse_gradle_kts(self, project_root: Path, file: Path) -> ProjectInfo:
        """解析 Gradle Kotlin build.gradle.kts（简化版）"""
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取 dependencies（Kotlin 语法）
            deps = []
            # 匹配 implementation("group:name:version")
            for match in re.finditer(
                r'implementation\s*\(\s*"([^:]+):([^:]+):[^"]+"\s*\)', content
            ):
                group, name = match.groups()
                deps.append(f"{group}:{name}")

            # 匹配 testImplementation
            for match in re.finditer(
                r'testImplementation\s*\(\s*"([^:]+):([^:]+):[^"]+"\s*\)', content
            ):
                group, name = match.groups()
                deps.append(f"{group}:{name}")

            return ProjectInfo(
                language="Java",
                framework=self._detect_framework(deps),
                dependency_file=str(file.name),
                dependencies=deps,
                build_command="./gradlew build - 构建 Gradle 项目",
                test_command="./gradlew test - 运行 Gradle 测试",
                metadata={},
            )
        except FileNotFoundError:
            return ProjectInfo(
                language="Java",
                dependency_file=str(file.name),
            )
        except Exception as e:
            print(f"[yellow]警告: 无法解析 {file}: {e}[/yellow]")
            return ProjectInfo(
                language="Java",
                dependency_file=str(file.name),
            )

    def _find_text(self, element, tag, namespace=None):
        """查找元素的文本内容"""
        if namespace:
            child = element.find(tag, namespace)
        else:
            child = element.find(tag)
        return child.text if child is not None else None

    def _detect_framework(self, deps: list) -> str:
        """检测 Java 框架"""
        deps_str = " ".join(deps).lower()

        if "spring-boot" in deps_str or "spring" in deps_str:
            return "Spring Boot"
        elif "junit" in deps_str:
            return "JUnit"
        elif "mockito" in deps_str:
            return "Mockito"
        else:
            return "unknown"
