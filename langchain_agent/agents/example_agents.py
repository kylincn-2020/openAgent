"""
示例子 Agent
展示如何使用装饰器注册子 Agent
"""

import asyncio
from typing import Any, Dict, Optional
from datetime import datetime

from langchain_agent.agents.agent_registry import (
    BaseSubAgent,
    AgentMetadata,
    register_agent,
)


@register_agent(
    AgentMetadata(
        name="weather_agent",
        description="查询天气信息",
        intent_keywords=["天气", "气温", "下雨", "晴", "阴", "雪", "风"],
        priority=10,
        parallel_allowed=False,
        category="information",
    )
)
class WeatherAgent(BaseSubAgent):
    """天气查询 Agent"""

    async def execute(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        执行天气查询

        Args:
            input_data: 用户输入
            context: 上下文信息

        Returns:
            天气信息
        """
        # 模拟天气查询（实际应用中应该调用天气 API）
        await asyncio.sleep(0.5)

        # 简单的关键词匹配
        input_str = str(input_data).lower()

        if "北京" in input_str:
            return {
                "location": "北京",
                "temperature": "22°C",
                "weather": "晴",
                "humidity": "45%",
                "wind": "东南风 3级",
            }
        elif "上海" in input_str:
            return {
                "location": "上海",
                "temperature": "25°C",
                "weather": "多云",
                "humidity": "65%",
                "wind": "东风 2级",
            }
        else:
            # 默认返回通用天气信息
            return {
                "location": "当前位置",
                "temperature": "20°C",
                "weather": "晴",
                "humidity": "50%",
                "wind": "微风",
                "note": "请指定城市获取更准确的信息",
            }


@register_agent(
    AgentMetadata(
        name="time_agent",
        description="查询当前时间、日期等信息",
        intent_keywords=["时间", "几点", "日期", "今天", "明天", "现在"],
        priority=20,
        parallel_allowed=True,
        category="information",
    )
)
class TimeAgent(BaseSubAgent):
    """时间查询 Agent"""

    async def execute(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        执行时间查询

        Args:
            input_data: 用户输入
            context: 上下文信息

        Returns:
            时间信息
        """
        await asyncio.sleep(0.3)

        now = datetime.now()

        return {
            "current_time": now.strftime("%H:%M:%S"),
            "current_date": now.strftime("%Y年%m月%d日"),
            "weekday": now.strftime("%A"),
            "timezone": "Asia/Shanghai",
        }


@register_agent(
    AgentMetadata(
        name="calculation_agent",
        description="执行数学计算",
        intent_keywords=["计算", "加", "减", "乘", "除", "等于", "+", "-", "*", "/"],
        priority=15,
        parallel_allowed=False,
        category="tool",
    )
)
class CalculationAgent(BaseSubAgent):
    """计算 Agent"""

    async def execute(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        执行计算

        Args:
            input_data: 用户输入
            context: 上下文信息

        Returns:
            计算结果
        """
        await asyncio.sleep(0.4)

        input_str = str(input_data)

        # 简单的数学表达式解析
        try:
            # 提取数字和运算符
            import re

            numbers = re.findall(r"\d+\.?\d*", input_str)
            operators = re.findall(r"[+\-*/]", input_str)

            if len(numbers) >= 2 and operators:
                # 执行计算
                num1 = float(numbers[0])
                num2 = float(numbers[1])
                op = operators[0]

                if op == "+":
                    result = num1 + num2
                elif op == "-":
                    result = num1 - num2
                elif op == "*":
                    result = num1 * num2
                elif op == "/":
                    result = num1 / num2 if num2 != 0 else "除数不能为0"
                else:
                    result = "不支持的运算符"

                return {
                    "expression": f"{num1} {op} {num2}",
                    "result": result,
                    "success": True,
                }
            else:
                return {
                    "error": "无法识别的表达式",
                    "input": input_str,
                    "success": False,
                }
        except Exception as e:
            return {"error": str(e), "success": False}


@register_agent(
    AgentMetadata(
        name="news_agent",
        description="查询新闻资讯",
        intent_keywords=["新闻", "头条", "资讯", "消息"],
        priority=8,
        parallel_allowed=True,
        category="information",
    )
)
class NewsAgent(BaseSubAgent):
    """新闻查询 Agent"""

    async def execute(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        执行新闻查询

        Args:
            input_data: 用户输入
            context: 上下文信息

        Returns:
            新闻信息
        """
        await asyncio.sleep(0.5)

        # 模拟新闻数据（实际应用中应该调用新闻 API）
        return {
            "news": [
                {
                    "title": "AI技术持续突破，多模态模型迎来新进展",
                    "time": "10分钟前",
                    "source": "科技日报",
                },
                {
                    "title": "新能源汽车销量创历史新高",
                    "time": "30分钟前",
                    "source": "财经网",
                },
                {
                    "title": "国际航天合作项目取得重大成果",
                    "time": "1小时前",
                    "source": "新华网",
                },
            ],
            "count": 3,
        }


@register_agent(
    AgentMetadata(
        name="translation_agent",
        description="翻译文本",
        intent_keywords=["翻译", "英文", "中文", "translate", "英语"],
        priority=12,
        parallel_allowed=False,
        category="tool",
    )
)
class TranslationAgent(BaseSubAgent):
    """翻译 Agent"""

    async def execute(
        self, input_data: Any, context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        执行翻译

        Args:
            input_data: 用户输入
            context: 上下文信息

        Returns:
            翻译结果
        """
        await asyncio.sleep(0.6)

        input_str = str(input_data)

        # 简单的翻译模拟
        # 实际应用中应该使用翻译 API 或 LLM
        return {
            "original": input_str,
            "translated": f"[翻译结果] {input_str}",
            "language_pair": "中文 -> 英文",
            "note": "这是模拟翻译，实际应用中需要集成翻译服务",
        }
