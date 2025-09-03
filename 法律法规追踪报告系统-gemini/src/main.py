import sys
from pathlib import Path
from loguru import logger

# 将项目根目录添加到sys.path，以便应用能正确找到所有模块
# __file__ -> /home/nolantsan/法律法规追踪报告系统-gemini/src/main.py
# .parent -> .../src/
# .parent -> .../
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ui.app import LegalTrackerApp
from src.database.connection import init_db
from src.config.settings import settings


def setup_logger():
    """配置Loguru日志记录器，提供控制台和文件两种输出"""
    logger.remove()  # 移除默认的处理器以进行自定义
    if settings.logging.console_output:
        logger.add(
            sys.stderr,
            level=settings.logging.level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>",
        )
    # 将日志文件保存在项目根目录的指定位置
    logger.add(
        project_root / settings.logging.file_path,
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        level=settings.logging.level,
        encoding="utf-8",
        enqueue=True,  # 使日志写入异步，防止阻塞
        backtrace=True,
        diagnose=True,
    )
    logger.info("日志系统配置完成。")


def main():
    """应用主入口函数，负责初始化和启动"""
    # 1. 配置日志
    setup_logger()

    # 2. 初始化数据库
    try:
        init_db()
    except Exception as e:
        logger.critical(f"数据库初始化失败，应用无法启动: {e}", exc_info=True)
        return  # 关键步骤失败，退出应用

    # 3. 创建并运行主应用窗口
    logger.info("启动 '智能法规追踪系统'...")
    app = LegalTrackerApp()
    app.mainloop()
    logger.info("应用已关闭。")


if __name__ == "__main__":
    main()
