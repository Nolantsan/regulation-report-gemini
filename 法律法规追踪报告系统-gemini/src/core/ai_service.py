from zhipuai import ZhipuAI
from typing import List, Dict, Optional
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from pydantic import BaseModel, Field, ValidationError

# 导入全局配置实例
from ..config.settings import settings

class RegulationAnalysis(BaseModel):
    """用于验证和规范AI分析结果的数据模型"""
    relevance_score: float = Field(..., description="与企业运营的相关度评分(0-1)", ge=0, le=1)
    impact_level: str = Field(..., description="影响等级(high|medium|low)", pattern="^(high|medium|low)$")
    affected_departments: List[str] = Field(..., description="受影响的部门列表")
    compliance_actions: List[str] = Field(..., description="需要采取的合规行动列表")
    risk_assessment: str = Field(..., description="风险评估说明")
    summary: str = Field(..., description="核心要点总结(200字以内)")

class EnhancedAIService:
    """
    增强版AI服务，封装了与智谱AI模型的交互逻辑。
    """
    def __init__(self):
        """初始化时，从全局配置加载API Key并创建客户端"""
        self.model = "glm-4.5"
        self._cache = {}  # 简单的内存缓存

        api_key = settings.zhipu_api_key
        if not api_key or api_key == "default_key_if_not_set":
            logger.warning("智谱AI的API Key未配置在.env文件中，AI服务将不可用。")
            self.client = None
        else:
            self.client = ZhipuAI(api_key=api_key)
            logger.info("AI服务已成功初始化。")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def analyze_regulation(self, regulation: Dict) -> Optional[RegulationAnalysis]:
        """使用AI深度分析单条法规，返回结构化的Pydantic模型"""
        if not self.client:
            return None

        cache_key = f"{regulation.get('title', '')}_{regulation.get('publish_date', '')}"
        if cache_key in self._cache:
            logger.info(f"命中AI分析缓存: {regulation.get('title')}")
            return self._cache[cache_key]

        prompt = f"""
        你是一位资深的企业法务专家和合规顾问。请对以下法规进行深度分析：

        法规标题：{regulation.get('title')}
        发布日期：{regulation.get('publish_date')}
        来源机构：{regulation.get('source')}
        法规类别：{regulation.get('category', '未分类')}

        请从以下维度进行分析并以JSON格式返回：
        1. relevance_score: 与通用企业运营的相关度评分(0.0-1.0)
        2. impact_level: 对通用企业的影响等级(high/medium/low)
        3. affected_departments: 可能受影响的企业部门列表
        4. compliance_actions: 企业需要采取的通用合规行动列表
        5. risk_assessment: 简要的风险评估说明
        6. summary: 核心要点总结(200字以内)

        输出格式要求：必须是纯JSON对象，不包含任何额外文本或Markdown标记。
        """

        try:
            logger.info(f"发送至AI进行分析: {regulation.get('title')}")
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result_data = json.loads(result_text)

            analysis = RegulationAnalysis(**result_data)
            self._cache[cache_key] = analysis  # 缓存成功的结果
            return analysis

        except ValidationError as e:
            logger.error(f"AI返回内容的格式不符合Pydantic模型要求: {e}。返回内容: {result_text}")
        except Exception as e:
            logger.error(f"调用AI分析API时出错: {e}")
        
        return None  # 失败时返回None

    async def batch_analyze(self, regulations: List[Dict], threshold: float = 0.5) -> List[Dict]:
        """批量分析法规，并根据相关度阈值进行筛选"""
        if not self.client:
            return []

        tasks = [self.analyze_regulation(reg) for reg in regulations]
        analyses = await asyncio.gather(*tasks)

        relevant_results = []
        for reg, analysis in zip(regulations, analyses):
            if analysis and analysis.relevance_score >= threshold:
                reg['ai_analysis'] = analysis.model_dump()  # Pydantic v2使用.model_dump()
                relevant_results.append(reg)
        
        logger.info(f"AI分析完成。在{len(regulations)}条法规中，筛选出{len(relevant_results)}条相关法规。")
        return relevant_results

    def _prepare_report_context(self, regulations: List[Dict]) -> Dict:
        """为报告生成准备上下文信息"""
        categories = set()
        high_impact_count = 0
        regulations_detail = []

        for reg in regulations[:20]:  # 限制最多20条法规进入报告以控制篇幅
            analysis = reg.get('ai_analysis', {})
            categories.add(reg.get('category', '其他'))

            if analysis.get('impact_level') == 'high':
                high_impact_count += 1

            regulations_detail.extend([
                "".join([
                    f"- 【{reg['title']}】",
                    f"\n  - 影响等级：{analysis.get('impact_level', '未知')}",
                    f"\n  - 核心要点：{analysis.get('summary', '待分析')}",
                ])
            ])

        return {
            'categories': ', '.join(categories) or '无',
            'high_impact_count': high_impact_count,
            'regulations_detail': '\n'.join(regulations_detail) or '无相关法规详情。'
        }

    async def generate_executive_report(self, regulations: List[Dict]) -> str:
        """调用AI，生成给管理层的摘要报告"""
        if not self.client:
            return "# AI服务未配置\n\n无法生成报告，因为AI服务未被正确初始化。"

        if not regulations:
            return "# 本期无相关法规更新\n\n系统未在数据库中发现需要报告的已分析法规。"

        context = self._prepare_report_context(regulations)

        prompt = f"""
        作为首席合规官（CCO），请基于以下近期分析的法规更新，撰写一份专业的管理层合规报告。

        本期法规更新总数：{len(regulations)}
        涉及领域：{context['categories']}
        高影响法规数量：{context['high_impact_count']}

        详细法规列表摘要：
        {context['regulations_detail']}

        报告要求：
        1.  **格式**: 使用Markdown格式，结构清晰，包含标题、章节和列表。
        2.  **内容**: 必须包含**执行摘要**、**详细分析**、**行动建议**和**风险矩阵**四个部分。
        3.  **风格**: 专业、简洁、直接，重点突出，量化影响。
        4.  **目标读者**: 公司管理层，他们需要快速了解核心影响和应采取的行动。
        5.  **输出**: 直接输出Markdown原文，不要包含任何额外的解释或标记。
        """

        try:
            logger.info("Generating executive report with AI...")
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=3500 # 增加token限制以生成更详细的报告
            )
            report_content = response.choices[0].message.content
            logger.success("Successfully generated executive report.")
            return report_content
        except Exception as e:
            logger.error(f"Failed to generate executive report: {e}", exc_info=True)
            return f"# 报告生成失败\n\n在调用AI生成报告时发生错误: {e}"

# 创建一个全局可引用的AI服务实例
ai_service = EnhancedAIService()
