import unittest
import os
from pathlib import Path
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Adjust path to import from src
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.models import Base, Regulation

# Use a separate in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

class TestDatabase(unittest.TestCase):
    """对数据库模块进行单元测试"""

    @classmethod
    def setUpClass(cls):
        """在所有测试开始前，创建数据库引擎和表"""
        cls.engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        """在所有测试结束后，可以进行清理（内存数据库不需要文件清理）"""
        pass

    def setUp(self):
        """在每个测试方法开始前，创建一个新的会话"""
        self.db = self.SessionLocal()

    def tearDown(self):
        """在每个测试方法结束后，回滚所有未提交的更改并关闭会话"""
        self.db.rollback()
        self.db.close()

    def test_1_create_regulation(self):
        """测试能否成功创建一条法规记录"""
        new_reg = Regulation(
            title="测试法规标题",
            url="http://example.com/test1",
            publish_date=date(2025, 9, 1),
            source="测试源",
            category="测试分类",
            ai_analysis={"summary": "这是一个测试摘要"}
        )
        self.db.add(new_reg)
        self.db.commit()

        # 从数据库中把它找回来，验证它确实存在
        retrieved_reg = self.db.query(Regulation).filter_by(url="http://example.com/test1").first()
        self.assertIsNotNone(retrieved_reg)
        self.assertEqual(retrieved_reg.title, "测试法规标题")
        self.assertEqual(retrieved_reg.source, "测试源")

    def test_2_read_regulation(self):
        """测试能否成功读取一条法规记录"""
        # 首先确保有一条记录存在
        reg = self.db.query(Regulation).filter_by(url="http://example.com/test1").first()
        if not reg:
            # 如果第一条测试因为某种原因失败了，这里再创建一次
            self.test_1_create_regulation()
            reg = self.db.query(Regulation).filter_by(url="http://example.com/test1").first()
        
        self.assertIsNotNone(reg)
        self.assertEqual(reg.title, "测试法规标题")

    def test_3_update_regulation(self):
        """测试能否成功更新一条法规记录"""
        reg_to_update = self.db.query(Regulation).filter_by(url="http://example.com/test1").first()
        self.assertIsNotNone(reg_to_update, "Update test requires the record to exist.")

        reg_to_update.source = "更新后的测试源"
        self.db.commit()

        updated_reg = self.db.query(Regulation).filter_by(url="http://example.com/test1").first()
        self.assertEqual(updated_reg.source, "更新后的测试源")

    def test_4_uniqueness_constraint(self):
        """测试URL的唯一性约束是否生效"""
        # 尝试创建一个与test_1中URL相同的记录
        duplicate_reg = Regulation(
            title="重复的法规标题",
            url="http://example.com/test1", # Same URL
            publish_date=date(2025, 9, 2),
            source="重复源",
            category="重复分类"
        )
        self.db.add(duplicate_reg)

        # 断言（Assert）当我们尝试提交时，会因为违反唯一性约束而抛出IntegrityError
        with self.assertRaises(IntegrityError):
            self.db.commit()

    def test_5_delete_regulation(self):
        """测试能否成功删除一条法规记录"""
        reg_to_delete = self.db.query(Regulation).filter_by(url="http://example.com/test1").first()
        self.assertIsNotNone(reg_to_delete, "Delete test requires the record to exist.")

        self.db.delete(reg_to_delete)
        self.db.commit()

        deleted_reg = self.db.query(Regulation).filter_by(url="http://example.com/test1").first()
        self.assertIsNone(deleted_reg)

if __name__ == '__main__':
    unittest.main()
