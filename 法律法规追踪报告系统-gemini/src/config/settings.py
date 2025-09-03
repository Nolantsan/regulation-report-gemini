import os
from pathlib import Path
from functools import lru_cache
from dotenv import load_dotenv
from pydantic import BaseModel

# 构建 .env 文件的绝对路径
# __file__ -> /home/nolantsan/法律法规追踪报告系统-gemini/src/config/settings.py
# .parent -> .../src/config/
# .parent -> .../src/
# .parent -> .../
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class AppSettings(BaseModel):
    """
    使用 Pydantic 管理和验证应用配置。
    配置值从环境变量（通过 .env 文件加载）中读取。
    """

    class LoggingSettings(BaseModel):
        """日志相关配置"""
        level: str = os.getenv("LOG_LEVEL", "INFO").upper()
        file_path: str = os.getenv("LOG_FILE_PATH", "logs/app_{time}.log")
        console_output: bool = str(os.getenv("LOG_CONSOLE_OUTPUT", "True")).lower() in (
            "true",
            "1",
            "t",
        )
        rotation: str = os.getenv("LOG_ROTATION", "1 week")
        retention: str = os.getenv("LOG_RETENTION", "1 month")

    # 智谱AI配置
    # .env 文件中应包含 ZHIPU_API_KEY=your_actual_api_key
    zhipu_api_key: str = os.getenv("ZHIPU_API_KEY", "default_key_if_not_set")

    # Redis 缓存配置
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # 爬虫配置
    max_concurrent_scrapers: int = int(os.getenv("MAX_CONCURRENT_SCRAPERS", 20))

    # 日志配置
    logging: LoggingSettings = LoggingSettings()

    # 爬虫SSL验证配置
    scraper_verify_ssl: bool = str(os.getenv("SCRAPER_VERIFY_SSL", "True")).lower() in (
        "true",
        "1",
        "t",
    )


@lru_cache()
def get_settings() -> AppSettings:
    """返回单例配置实例"""
    return AppSettings()


# 兼容旧的导入方式
settings = get_settings()
