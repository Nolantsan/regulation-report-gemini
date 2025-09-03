import asyncio
import aiohttp
import httpx
from typing import List, Dict, Optional, Callable
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
from loguru import logger
from selectolax.parser import HTMLParser

# 导入全局配置
from src.config.settings import settings

class AsyncLegalScraper:
    """高性能异步法规爬虫，支持API和HTML两种类型的数据源"""

    def __init__(self, max_concurrent: int = 20):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None

        if not settings.scraper_verify_ssl:
            logger.warning("Scraper SSL verification is disabled. This is not recommended for production.")

        # 可配置的数据源列表
        self.sources = [
            {
                'name': '国家法律法规数据库',
                'url': 'https://flk.npc.gov.cn/api/v1/laws',
                'type': 'api',
                'parser': self._parse_npc_api
            },
            {
                'name': '司法部',
                'url': 'https://www.moj.gov.cn/regulations',
                'type': 'html',
                'parser': self._parse_moj_html
            },
            {
                'name': '国务院',
                'url': 'https://www.gov.cn/zhengce',
                'type': 'html',
                'parser': self._parse_gov_html
            }
        ]

    async def __aenter__(self):
        """异步上下文管理器入口，创建aiohttp会话"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        connector = aiohttp.TCPConnector(limit_per_host=30, ssl=settings.scraper_verify_ssl)
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口，关闭会话"""
        if self.session:
            await self.session.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_url(self, url: str) -> str:
        """使用aiohttp异步获取URL内容，并添加重试机制"""
        async with self.semaphore:
            logger.info(f"Fetching HTML from: {url}")
            try:
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
            except Exception as e:
                logger.error(f"Error fetching {url} with aiohttp: {e}")
                raise

    async def fetch_all_sources(self) -> List[Dict]:
        """并发获取所有数据源的内容"""
        tasks = []
        for source in self.sources:
            task = asyncio.create_task(self.process_source(source))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_regulations = []
        for result in results:
            if isinstance(result, list):
                all_regulations.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"A source failed to fetch: {result}")
        return all_regulations

    async def process_source(self, source: Dict) -> List[Dict]:
        """根据数据源类型（API或HTML）处理单个数据源"""
        logger.info(f"Processing source: {source['name']}")
        if source['type'] == 'api':
            return await self.fetch_api_data(source)
        else:
            return await self.fetch_html_data(source)

    async def fetch_api_data(self, source: Dict) -> List[Dict]:
        """使用httpx获取API数据，支持HTTP/2"""
        try:
            async with httpx.AsyncClient(http2=True, verify=settings.scraper_verify_ssl) as client:
                logger.info(f"Fetching API from: {source['url']}")
                response = await client.get(source['url'], params={'searchType': 'all', 'sort': 'false', 'is_nd': 'false', 'type': 'fl', 'page': 1, 'size': 100}) # 获取数量提升到100
                response.raise_for_status()
                data = response.json()
                return source['parser'](data)
        except Exception as e:
            logger.error(f"API fetch error for {source['name']}: {e}")
            return []

    async def fetch_html_data(self, source: Dict) -> List[Dict]:
        """获取并解析HTML数据"""
        try:
            html = await self.fetch_url(source['url'])
            return source['parser'](html)
        except Exception as e:
            logger.error(f"HTML fetch error for {source['name']}: {e}")
            return []

    def _parse_npc_api(self, data: Dict) -> List[Dict]:
        """解析国家法律法规数据库API的数据"""
        regulations = []
        items = data.get('result', {}).get('data', [])
        for item in items:
            regulations.append({
                'title': item.get('title'),
                'url': f"https://flk.npc.gov.cn/law/{item.get('id')}",
                'publish_date': item.get('publishDate'),
                'source': '国家法律法规数据库',
                'category': item.get('cat'),
                'full_text': item.get('content', ''),
                'keywords': item.get('keywords', [])
            })
        logger.info(f"Parsed {len(regulations)} regulations from NPC API.")
        return regulations

    def _parse_moj_html(self, html: str) -> List[Dict]:
        """使用selectolax解析司法部HTML"""
        parser = HTMLParser(html)
        regulations = []
        for item in parser.css('div.law-item'):
            title_elem = item.css_first('h3 a')
            date_elem = item.css_first('span.date')
            if title_elem and date_elem:
                regulations.append({
                    'title': title_elem.text(strip=True),
                    'url': title_elem.attributes.get('href', ''),
                    'publish_date': date_elem.text(strip=True),
                    'source': '司法部',
                    'category': '部门规章'
                })
        logger.info(f"Parsed {len(regulations)} regulations from MOJ HTML.")
        return regulations

    def _parse_gov_html(self, html: str) -> List[Dict]:
        """解析国务院HTML"""
        parser = HTMLParser(html)
        regulations = []
        for item in parser.css('li.xxgk_li'):
            link = item.css_first('a')
            date = item.css_first('span')
            if link and date:
                regulations.append({
                    'title': link.text(strip=True),
                    'url': f"https://www.gov.cn{link.attributes.get('href', '')}",
                    'publish_date': date.text(strip=True),
                    'source': '国务院',
                    'category': '行政法规'
                })
        logger.info(f"Parsed {len(regulations)} regulations from GOV HTML.")
        return regulations
