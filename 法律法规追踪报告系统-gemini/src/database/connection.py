from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# 导入在models.py中定义的Base
from .models import Base

# 将数据库文件定义在项目的根目录下，命名为 legal_tracker.db
DB_PATH = Path(__file__).parent.parent.parent / "legal_tracker.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# 创建SQLAlchemy引擎
# connect_args={"check_same_thread": False} 是SQLite在多线程环境下（例如GUI应用）的推荐配置
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 创建一个配置好的 "Session" 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    获取一个新的数据库会话，并确保使用后能安全关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    初始化数据库。如果表不存在，则会根据模型进行创建。
    这个函数应该在应用启动时被调用一次。
    """
    print(f"Initializing database at: {DB_PATH}")
    # Base.metadata 会收集所有继承自Base的类（即我们的模型）并创建对应的表
    Base.metadata.create_all(bind=engine)
    print("Database initialization complete.")
