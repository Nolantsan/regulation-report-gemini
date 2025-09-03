import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from types import SimpleNamespace

# Adjust path to import from src
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ui.app import LegalTrackerApp


class DummySwitch:
    def __init__(self, value=True):
        self._value = value

    def get(self):
        return self._value


class DummyProgressBar:
    def __init__(self):
        self.value = 0
        self.grid_called = False
        self.grid_forget_called = False

    def set(self, v):
        self.value = v

    def grid(self, *args, **kwargs):
        self.grid_called = True

    def grid_forget(self):
        self.grid_forget_called = True


class DummyApp:
    def __init__(self):
        self.web_search_switch = DummySwitch(True)
        self.progress_bar = DummyProgressBar()
        self.logs = []

    def log_to_ui(self, message, level="INFO"):
        self.logs.append((level, message))

    def after(self, delay, func, *args, **kwargs):
        func(*args, **kwargs)

    run_web_search_async = LegalTrackerApp.run_web_search_async
    run_scan_async = LegalTrackerApp.run_scan_async
    run_report_generation_async = LegalTrackerApp.run_report_generation_async


class TestAppWorkflows(unittest.TestCase):
    def test_run_web_search_async(self):
        sample_result = [{
            'title': 'Test Law',
            'url': 'http://example.com',
            'publish_date': '2025-01-01',
            'source': 'UnitTest',
            'category': 'Test'
        }]

        mock_scraper = MagicMock()
        mock_scraper.fetch_all_sources = AsyncMock(return_value=sample_result)

        async def run_test():
            app = DummyApp()
            with patch('src.ui.app.AsyncLegalScraper') as MockScraper:
                MockScraper.return_value.__aenter__.return_value = mock_scraper
                results = await app.run_web_search_async()
            self.assertEqual(results, sample_result)
            self.assertTrue(app.progress_bar.value >= 0.3)

        asyncio.run(run_test())

    def test_run_scan_async(self):
        sample_reg = {
            'title': 'Test',
            'url': 'http://example.com',
            'publish_date': '2025-01-01',
            'source': 'UnitTest',
            'category': 'Test'
        }
        analyzed_reg = {**sample_reg, 'ai_analysis': {'summary': 'ok'}}

        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = False
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        def fake_get_db():
            yield mock_session

        async def run_test():
            app = DummyApp()
            with patch.object(app, 'run_web_search_async', AsyncMock(return_value=[sample_reg])):
                with patch('src.ui.app.ai_service.batch_analyze', AsyncMock(return_value=[analyzed_reg])):
                    with patch('src.ui.app.get_db', fake_get_db):
                        await app.run_scan_async()

            mock_session.add.assert_called()
            mock_session.commit.assert_called_once()
            self.assertTrue(app.progress_bar.grid_called)
            self.assertTrue(app.progress_bar.grid_forget_called)

        asyncio.run(run_test())

    def test_run_report_generation_async(self):
        record = SimpleNamespace(
            title='Test',
            url='http://example.com',
            publish_date=__import__('datetime').date(2025, 1, 1),
            source='UnitTest',
            category='Test',
            full_text='',
            keywords=[],
            ai_analysis={'summary': 'ok'}
        )

        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_session.__exit__.return_value = False
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_order = mock_filter.order_by.return_value
        mock_order.all.return_value = [record]

        def fake_get_db():
            yield mock_session

        async def run_test():
            app = DummyApp()
            with patch('src.ui.app.get_db', fake_get_db):
                with patch('src.ui.app.ai_service.generate_executive_report', AsyncMock(return_value='# report')) as mock_gen:
                    path = await app.run_report_generation_async()
                    self.assertTrue(Path(path).exists())
                    mock_gen.assert_called_once()
                    Path(path).unlink()

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()

