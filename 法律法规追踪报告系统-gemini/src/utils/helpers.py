"""
智能法律法规追踪系统 - 辅助函数模块
提供系统中使用的各种工具函数
"""

import re
import hashlib
import json
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
import pandas as pd
import pendulum
from urllib.parse import urlparse, urljoin, quote, unquote
from selectolax.parser import HTMLParser
import unicodedata

from ..config.constants import REGEX_PATTERNS, SUPPORTED_FILE_TYPES


class TextUtils:
    """文本处理工具类"""
    
    @staticmethod
    def clean_text(text: str, remove_extra_spaces: bool = True) -> str:
        """清理文本，移除无用字符"""
        if not text:
            return ""
        
        # 移除控制字符和格式字符
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
        
        # 标准化Unicode
        text = unicodedata.normalize('NFKC', text)
        
        # 移除多余空格
        if remove_extra_spaces:
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @staticmethod
    def extract_chinese_text(text: str) -> str:
        """提取中文文本"""
        if not text:
            return ""
        
        chinese_pattern = re.compile(REGEX_PATTERNS['chinese_text'])
        chinese_chars = chinese_pattern.findall(text)
        return ''.join(chinese_chars)
    
    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """从文本中提取日期"""
        if not text:
            return []
        
        date_pattern = re.compile(REGEX_PATTERNS['date'])
        dates = date_pattern.findall(text)
        return list(set(dates))  # 去重
    
    @staticmethod
    def extract_regulation_numbers(text: str) -> List[str]:
        """提取法规编号"""
        if not text:
            return []
        
        reg_pattern = re.compile(REGEX_PATTERNS['regulation_number'])
        numbers = reg_pattern.findall(text)
        return list(set(numbers))
    
    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """计算文本相似度（基于字符集合的Jaccard相似度）"""
        if not text1 or not text2:
            return 0.0
        
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """截断文本"""
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 2, max_count: int = 20) -> List[str]:
        """提取关键词（简单实现）"""
        if not text:
            return []
        
        # 移除标点符号和特殊字符
        clean_text = re.sub(r'[^\w\s]', ' ', text)
        words = clean_text.split()
        
        # 过滤短词和常用词
        stopwords = {'的', '了', '是', '在', '有', '和', '与', '及', '或', '但', '而', '因', '由', '为', '以'}
        keywords = [word for word in words if len(word) >= min_length and word not in stopwords]
        
        # 统计词频
        word_count = {}
        for word in keywords:
            word_count[word] = word_count.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:max_count]]


class DateUtils:
    """日期处理工具类"""
    
    @staticmethod
    def parse_chinese_date(date_str: str) -> Optional[datetime]:
        """解析中文日期格式"""
        if not date_str:
            return None
        
        try:
            # 标准化日期格式
            date_str = re.sub(r'[年月日]', '-', date_str)
            date_str = re.sub(r'-$', '', date_str)  # 移除末尾的-
            date_str = re.sub(r'--+', '-', date_str)  # 合并多个-
            
            # 尝试解析
            return pendulum.parse(date_str, strict=False).to_date_string()
        except:
            return None
    
    @staticmethod
    def format_date_range(start_date: datetime, end_date: datetime) -> str:
        """格式化日期范围"""
        if not start_date or not end_date:
            return ""
        
        start_str = pendulum.instance(start_date).format('YYYY年MM月DD日')
        end_str = pendulum.instance(end_date).format('YYYY年MM月DD日')
        
        return f"{start_str} - {end_str}"
    
    @staticmethod
    def get_date_range(days: int = 7) -> Tuple[datetime, datetime]:
        """获取指定天数的日期范围"""
        end_date = pendulum.now()
        start_date = end_date.subtract(days=days)
        
        return start_date.to_date_string(), end_date.to_date_string()
    
    @staticmethod
    def is_recent(date: datetime, days: int = 30) -> bool:
        """判断日期是否为最近指定天数内"""
        if not date:
            return False
        
        now = pendulum.now()
        target_date = pendulum.instance(date)
        
        return (now - target_date).days <= days


class FileUtils:
    """文件处理工具类"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """确保目录存在"""
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    @staticmethod
    def get_file_hash(file_path: Union[str, Path]) -> str:
        """计算文件哈希值"""
        file_path = Path(file_path)
        if not file_path.exists():
            return ""
        
        hash_obj = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """获取文件大小（字节）"""
        file_path = Path(file_path)
        return file_path.stat().st_size if file_path.exists() else 0
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        
        size = float(size_bytes)
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        return f"{size:.1f} {units[unit_index]}"
    
    @staticmethod
    def is_supported_file_type(file_path: Union[str, Path], category: str = None) -> bool:
        """检查文件类型是否支持"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if category:
            return extension in SUPPORTED_FILE_TYPES.get(category, [])
        
        # 检查所有支持的类型
        for file_types in SUPPORTED_FILE_TYPES.values():
            if extension in file_types:
                return True
        
        return False
    
    @staticmethod
    def create_backup(file_path: Union[str, Path], backup_dir: str = "backups") -> Path:
        """创建文件备份"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # 创建备份目录
        backup_path = file_path.parent / backup_dir
        FileUtils.ensure_directory(backup_path)
        
        # 生成备份文件名
        timestamp = pendulum.now().format('YYYYMMDD_HHmmss')
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_file = backup_path / backup_name
        
        # 复制文件
        import shutil
        shutil.copy2(file_path, backup_file)
        
        return backup_file
    
    @staticmethod
    def compress_files(file_paths: List[Union[str, Path]], output_path: Union[str, Path]) -> bool:
        """压缩文件列表"""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_paths:
                    file_path = Path(file_path)
                    if file_path.exists():
                        zipf.write(file_path, file_path.name)
            return True
        except Exception:
            return False


class URLUtils:
    """URL处理工具类"""
    
    @staticmethod
    def normalize_url(url: str, base_url: str = None) -> str:
        """标准化URL"""
        if not url:
            return ""
        
        # 处理相对URL
        if base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        # 解析URL组件
        parsed = urlparse(url)
        
        # 重建URL，确保格式统一
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """提取域名"""
        if not url:
            return ""
        
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """验证URL格式"""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            return all([parsed.scheme, parsed.netloc])
        except:
            return False
    
    @staticmethod
    def encode_url_params(params: Dict[str, Any]) -> str:
        """编码URL参数"""
        if not params:
            return ""
        
        encoded_params = []
        for key, value in params.items():
            if value is not None:
                encoded_key = quote(str(key))
                encoded_value = quote(str(value))
                encoded_params.append(f"{encoded_key}={encoded_value}")
        
        return "&".join(encoded_params)


class HTMLUtils:
    """HTML处理工具类"""
    
    @staticmethod
    def extract_text(html: str, clean: bool = True) -> str:
        """从HTML中提取纯文本"""
        if not html:
            return ""
        
        try:
            parser = HTMLParser(html)
            text = parser.text()
            
            if clean:
                text = TextUtils.clean_text(text)
            
            return text
        except:
            return ""
    
    @staticmethod
    def extract_links(html: str, base_url: str = None) -> List[Dict[str, str]]:
        """提取HTML中的链接"""
        if not html:
            return []
        
        links = []
        try:
            parser = HTMLParser(html)
            
            for link in parser.css('a[href]'):
                href = link.attributes.get('href', '')
                text = link.text(strip=True)
                
                if href:
                    # 标准化URL
                    if base_url:
                        href = URLUtils.normalize_url(href, base_url)
                    
                    links.append({
                        'url': href,
                        'text': text,
                        'title': link.attributes.get('title', '')
                    })
        except:
            pass
        
        return links
    
    @staticmethod
    def extract_images(html: str, base_url: str = None) -> List[Dict[str, str]]:
        """提取HTML中的图片"""
        if not html:
            return []
        
        images = []
        try:
            parser = HTMLParser(html)
            
            for img in parser.css('img[src]'):
                src = img.attributes.get('src', '')
                alt = img.attributes.get('alt', '')
                
                if src:
                    # 标准化URL
                    if base_url:
                        src = URLUtils.normalize_url(src, base_url)
                    
                    images.append({
                        'src': src,
                        'alt': alt,
                        'title': img.attributes.get('title', '')
                    })
        except:
            pass
        
        return images
    
    @staticmethod
    def remove_tags(html: str, tags: List[str] = None) -> str:
        """移除指定的HTML标签"""
        if not html:
            return ""
        
        default_tags = ['script', 'style', 'nav', 'aside', 'footer', 'header']
        tags_to_remove = tags or default_tags
        
        try:
            parser = HTMLParser(html)
            
            for tag in tags_to_remove:
                for element in parser.css(tag):
                    element.decompose()
            
            return str(parser.html)
        except:
            return html


class DataUtils:
    """数据处理工具类"""
    
    @staticmethod
    def safe_get(data: Dict, key: str, default: Any = None) -> Any:
        """安全获取字典值，支持嵌套键"""
        if not isinstance(data, dict):
            return default
        
        keys = key.split('.')
        current_data = data
        
        try:
            for k in keys:
                if isinstance(current_data, dict) and k in current_data:
                    current_data = current_data[k]
                else:
                    return default
            return current_data
        except:
            return default
    
    @staticmethod
    def merge_dicts(dict1: Dict, dict2: Dict, deep: bool = True) -> Dict:
        """合并字典"""
        if not deep:
            result = dict1.copy()
            result.update(dict2)
            return result
        
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataUtils.merge_dicts(result[key], value, deep=True)
            else:
                result[key] = value
        
        return result
    
    @staticmethod
    def flatten_dict(data: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """展平嵌套字典"""
        items = []
        
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(DataUtils.flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    @staticmethod
    def to_dataframe(data: List[Dict]) -> pd.DataFrame:
        """将字典列表转换为DataFrame"""
        if not data:
            return pd.DataFrame()
        
        try:
            return pd.DataFrame(data)
        except Exception:
            # 如果直接转换失败，尝试标准化数据
            normalized_data = []
            all_keys = set()
            
            # 收集所有键
            for item in data:
                if isinstance(item, dict):
                    all_keys.update(item.keys())
            
            # 标准化每个项目
            for item in data:
                if isinstance(item, dict):
                    normalized_item = {key: item.get(key, None) for key in all_keys}
                    normalized_data.append(normalized_item)
            
            return pd.DataFrame(normalized_data)
    
    @staticmethod
    def filter_data(data: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """根据条件过滤数据"""
        if not data or not filters:
            return data
        
        filtered_data = []
        
        for item in data:
            match = True
            
            for key, value in filters.items():
                item_value = DataUtils.safe_get(item, key)
                
                if isinstance(value, (list, tuple)):
                    # 包含匹配
                    if item_value not in value:
                        match = False
                        break
                elif isinstance(value, dict):
                    # 范围匹配
                    if 'min' in value and item_value < value['min']:
                        match = False
                        break
                    if 'max' in value and item_value > value['max']:
                        match = False
                        break
                else:
                    # 精确匹配
                    if item_value != value:
                        match = False
                        break
            
            if match:
                filtered_data.append(item)
        
        return filtered_data


class CryptoUtils:
    """加密工具类"""
    
    @staticmethod
    def hash_string(text: str, algorithm: str = 'sha256') -> str:
        """对字符串进行哈希"""
        if not text:
            return ""
        
        hash_func = getattr(hashlib, algorithm, hashlib.sha256)
        return hash_func(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """生成随机令牌"""
        import secrets
        return secrets.token_urlsafe(length)[:length]


# 便捷函数
def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """安全JSON解析"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: Any = None) -> str:
    """安全JSON序列化"""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return json.dumps(default or {}, ensure_ascii=False, indent=2)


def chunks(lst: List, size: int) -> List[List]:
    """将列表分割成指定大小的块"""
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def remove_duplicates(lst: List, key: str = None) -> List:
    """移除列表中的重复项"""
    if not lst:
        return []
    
    if key is None:
        # 简单去重
        return list(set(lst))
    
    # 基于键去重
    seen = set()
    result = []
    
    for item in lst:
        if isinstance(item, dict):
            item_key = item.get(key)
            if item_key not in seen:
                seen.add(item_key)
                result.append(item)
        else:
            attr_value = getattr(item, key, None)
            if attr_value not in seen:
                seen.add(attr_value)
                result.append(item)
    
    return result


def format_number(number: Union[int, float], decimal_places: int = 2) -> str:
    """格式化数字显示"""
    if isinstance(number, (int, float)):
        if isinstance(number, int) or number.is_integer():
            return f"{int(number):,}"
        else:
            return f"{number:,.{decimal_places}f}"
    return str(number)
