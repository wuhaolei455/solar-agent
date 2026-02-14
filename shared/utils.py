"""公共工具模块：提供所有 demo 共享的基础功能。"""

import os
from pathlib import Path
from dotenv import load_dotenv


def load_env():
    """加载项目根目录下的 .env 文件。

    无论从哪个 demo 目录运行，都能正确找到根目录的 .env。
    """
    # 向上查找项目根目录的 .env
    current = Path(__file__).resolve().parent.parent
    env_path = current / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # fallback：从当前目录加载


def get_project_root() -> Path:
    """获取项目根目录路径。"""
    return Path(__file__).resolve().parent.parent
