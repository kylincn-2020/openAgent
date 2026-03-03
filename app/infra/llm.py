"""
LLM 初始化工具
"""
import os
from langchain_openai import ChatOpenAI


def get_llm():
    """
    获取 LLM 实例
    从环境变量读取配置，默认使用 gpt-4o-mini 模型
    temperature=0 确保输出确定性，适合分类任务
    """
    return ChatOpenAI(
        model="glm-4.7",
        base_url="https://coding.dashscope.aliyuncs.com/v1",
        api_key="sk-sp-b6c188b0bd9d478ca5fba8b8b34cc5f1",
        temperature=0
    )
