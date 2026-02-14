"""shared - 项目公共模块

提供所有 demo 共享的初始化和工具函数。
"""

import os
from pathlib import Path
from dotenv import load_dotenv


def setup():
    """项目初始化：加载 .env 环境变量并校验必要配置。

    每个 demo 只需在开头调用一次：
        from shared import setup; setup()
    """
    # 加载项目根目录的 .env
    root = Path(__file__).resolve().parent.parent
    load_dotenv(root / ".env")

    assert os.getenv("OPENAI_API_KEY"), "请先在 .env 中配置 OPENAI_API_KEY"
