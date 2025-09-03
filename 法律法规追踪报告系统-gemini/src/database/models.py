import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    JSON
)
from sqlalchemy.orm import declarative_base

# 创建所有数据模型的基类
Base = declarative_base()

class Regulation(Base):
    """
    数据库模型，用于存储跟踪到的法律法规信息。
    """
    __tablename__ = 'regulations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False, index=True)
    url = Column(String(1024), nullable=False, unique=True)
    publish_date = Column(Date, nullable=True)
    source = Column(String(128), index=True)
    category = Column(String(128), index=True)
    
    # 使用Text类型存储可能很长的法规全文
    full_text = Column(Text, nullable=True)
    
    # 使用JSON类型存储关键词列表和AI分析结果，具有更好的扩展性
    keywords = Column(JSON, nullable=True)
    ai_analysis = Column(JSON, nullable=True)

    # 自动管理的时间戳
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Regulation(id={self.id}, title='{self.title[:50]}...')>"
