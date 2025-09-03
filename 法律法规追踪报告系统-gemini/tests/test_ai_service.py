import unittest
from unittest.mock import patch, MagicMock
import asyncio
import json
from pathlib import Path

# Adjust path to import from src
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.ai_service import EnhancedAIService, RegulationAnalysis

# --- Sample Data ---

SAMPLE_REGULATION_INPUT = {
    'title': '关于测试AI服务的规定',
    'publish_date': '2025-09-01',
    'source': '测试部门',
    'category': '测试类型'
}

VALID_AI_RESPONSE_JSON = {
    "relevance_score": 0.9,
    "impact_level": "high",
    "affected_departments": ["法务部", "财务部"],
    "compliance_actions": ["更新内部合规手册", "组织相关人员培训"],
    "risk_assessment": "该规定对公司的核心业务有重大影响，不遵守将面临高额罚款。",
    "summary": "这是一条关于测试AI服务的重要规定，要求各部门高度重视。"
}

INVALID_AI_RESPONSE_JSON = {
    "relevance_score": 0.9,
    "impact_level": "very_high", # Invalid value
    "affected_departments": ["法务部", "财务部"]
}

class TestAIService(unittest.TestCase):
    """对AI核心服务进行单元测试"""

    @patch('src.core.ai_service.settings')
    @patch('src.core.ai_service.ZhipuAI')
    def test_analyze_regulation_success(self, MockZhipuAI, mock_settings):
        """测试AI分析成功返回并被正确解析的场景"""
        mock_settings.zhipu_api_key = "DUMMY_KEY_FOR_TESTING"
        mock_client = MockZhipuAI.return_value
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps(VALID_AI_RESPONSE_JSON)
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        ai_service = EnhancedAIService()
        result = asyncio.run(ai_service.analyze_regulation(SAMPLE_REGULATION_INPUT))

        self.assertIsInstance(result, RegulationAnalysis)
        self.assertEqual(result.impact_level, "high")
        self.assertEqual(result.summary, "这是一条关于测试AI服务的重要规定，要求各部门高度重视。")
        mock_client.chat.completions.create.assert_called_once()

    @patch('src.core.ai_service.settings')
    @patch('src.core.ai_service.ZhipuAI')
    def test_analyze_regulation_api_failure(self, MockZhipuAI, mock_settings):
        """测试AI接口调用失败时，程序能否优雅处理"""
        mock_settings.zhipu_api_key = "DUMMY_KEY_FOR_TESTING"
        mock_client = MockZhipuAI.return_value
        mock_client.chat.completions.create.side_effect = Exception("Simulated API Error")

        ai_service = EnhancedAIService()
        result = asyncio.run(ai_service.analyze_regulation(SAMPLE_REGULATION_INPUT))

        self.assertIsNone(result)

    @patch('src.core.ai_service.settings')
    @patch('src.core.ai_service.ZhipuAI')
    def test_analyze_regulation_validation_failure(self, MockZhipuAI, mock_settings):
        """测试AI返回了不规范的JSON时，Pydantic验证能否捕获"""
        mock_settings.zhipu_api_key = "DUMMY_KEY_FOR_TESTING"
        mock_client = MockZhipuAI.return_value
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = json.dumps(INVALID_AI_RESPONSE_JSON)
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        ai_service = EnhancedAIService()
        result = asyncio.run(ai_service.analyze_regulation(SAMPLE_REGULATION_INPUT))

        self.assertIsNone(result)

    @patch('src.core.ai_service.settings')
    @patch('src.core.ai_service.ZhipuAI')
    def test_generate_executive_report(self, MockZhipuAI, mock_settings):
        """测试报告生成功能"""
        mock_settings.zhipu_api_key = "DUMMY_KEY_FOR_TESTING"
        mock_client = MockZhipuAI.return_value
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "# 测试报告\n\n这是一个测试报告。"
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        ai_service = EnhancedAIService()
        report = asyncio.run(ai_service.generate_executive_report([SAMPLE_REGULATION_INPUT]))

        self.assertIn("# 测试报告", report)
        mock_client.chat.completions.create.assert_called_once()

if __name__ == '__main__':
    unittest.main()
