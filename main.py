"""
多 Agent 系统入口
"""

import asyncio
from loguru import logger
from config import settings

# 导入 agents 触发装饰器注册
from agents import (
    IntentAgent,
    CodingAgent,
    WritingAgent,
    AnalysisAgent,
)
from core.session_manager import session_manager
from api.server import app


async def main():
    """主函数"""
    logger.info("启动多 Agent 系统...")
    logger.info(f"调试模式：查看所有注册的 agents")

    # 显示所有注册的 agents
    from core.registry import registry

    agents = registry.get_all_agents()
    logger.info(f"已注册 {len(agents)} 个 agent:")
    for name, metadata in agents.items():
        logger.info(f"  - {name}: {metadata.description}")

    # 启动 API 服务
    import uvicorn

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
    )


if __name__ == "__main__":
    asyncio.run(main())
