"""
智能法律法规追踪系统 - 常量定义模块
定义系统中使用的所有常量
"""

from enum import Enum, IntEnum
from typing import Dict, List


# ================== 系统基本常量 ==================
APP_NAME = "智能法律法规追踪系统"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Legal AI Team"
APP_DESCRIPTION = "基于智谱GLM-4.5的企业级法规合规管理平台"


# ================== 法规类别定义 ==================
class RegulationCategory(Enum):
    """法规类别枚举"""
    
    LAW = "法律"                    # 全国人大制定
    ADMINISTRATIVE_REGULATION = "行政法规"    # 国务院制定
    DEPARTMENT_RULE = "部门规章"           # 部委制定
    LOCAL_REGULATION = "地方性法规"        # 地方人大制定
    LOCAL_RULE = "地方政府规章"            # 地方政府制定
    JUDICIAL_INTERPRETATION = "司法解释"   # 最高法院、检察院制定
    NORMATIVE_DOCUMENT = "规范性文件"      # 其他规范性文件
    INTERNATIONAL_TREATY = "国际条约"      # 国际条约和协定


# ================== 数据源配置 ==================
class DataSource:
    """数据源常量类"""
    
    # 国家级数据源
    NPC_DATABASE = {
        "name": "国家法律法规数据库",
        "base_url": "https://flk.npc.gov.cn",
        "api_endpoint": "https://flk.npc.gov.cn/api/v1/laws",
        "encoding": "utf-8",
        "rate_limit": 60,  # 每分钟请求数限制
        "priority": 1
    }
    
    MOJ_WEBSITE = {
        "name": "司法部",
        "base_url": "https://www.moj.gov.cn",
        "search_url": "https://www.moj.gov.cn/search",
        "regulation_section": "/regulations",
        "encoding": "utf-8",
        "rate_limit": 30,
        "priority": 2
    }
    
    GOV_CN = {
        "name": "中国政府网",
        "base_url": "https://www.gov.cn",
        "policy_section": "/zhengce",
        "search_api": "https://sousuo.gov.cn/s.htm",
        "encoding": "utf-8",
        "rate_limit": 100,
        "priority": 3
    }
    
    NDRC_WEBSITE = {
        "name": "国家发展改革委",
        "base_url": "https://www.ndrc.gov.cn",
        "policy_section": "/fggz/fgzy",
        "encoding": "utf-8",
        "rate_limit": 20,
        "priority": 4
    }


# ================== AI模型配置 ==================
class AIModelConfig:
    """AI模型配置常量"""
    
    # 智谱AI模型
    ZHIPU_MODELS = {
        "GLM_4_5": "glm-4.5",
        "GLM_4": "glm-4",
        "GLM_3_TURBO": "glm-3-turbo"
    }
    
    # 分析任务配置
    ANALYSIS_CONFIG = {
        "max_tokens": 2000,
        "temperature": 0.3,
        "top_p": 0.8,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    }
    
    # 批量处理配置
    BATCH_CONFIG = {
        "default_size": 10,
        "max_size": 50,
        "timeout": 300  # 5分钟
    }


# ================== 影响等级定义 ==================
class ImpactLevel(Enum):
    """影响等级枚举"""
    
    HIGH = "high"          # 高影响 - 需要立即关注
    MEDIUM = "medium"      # 中影响 - 需要关注
    LOW = "low"           # 低影响 - 一般关注


# ================== 行业分类 ==================
class IndustryCategory(Enum):
    """行业分类枚举"""
    
    TECHNOLOGY = "科技"
    FINANCE = "金融"
    HEALTHCARE = "医疗"
    EDUCATION = "教育"
    MANUFACTURING = "制造业"
    REAL_ESTATE = "房地产"
    ENERGY = "能源"
    TRANSPORTATION = "交通运输"
    RETAIL = "零售"
    AGRICULTURE = "农业"
    ENVIRONMENTAL = "环保"
    TELECOMMUNICATION = "电信"
    CONSTRUCTION = "建筑"
    FOOD_BEVERAGE = "食品饮料"
    TOURISM = "旅游"
    MEDIA = "传媒"
    INSURANCE = "保险"
    LOGISTICS = "物流"
    CHEMICAL = "化工"
    PHARMACEUTICAL = "医药"


# ================== 部门映射 ==================
DEPARTMENT_MAPPING = {
    "人力资源": ["人事部", "HR部门", "人力资源部"],
    "财务": ["财务部", "会计部", "审计部"],
    "法务": ["法务部", "合规部", "风控部"],
    "运营": ["运营部", "业务部", "营销部"],
    "技术": ["技术部", "研发部", "IT部门"],
    "采购": ["采购部", "供应链部"],
    "安全": ["安全部", "保卫部", "安环部"],
    "质量": ["质量部", "质检部", "QA部门"],
    "行政": ["行政部", "总务部", "办公室"],
    "销售": ["销售部", "市场部", "商务部"]
}


# ================== 合规行动模板 ==================
COMPLIANCE_ACTION_TEMPLATES = {
    "policy_update": "更新内部政策文件",
    "training": "组织相关培训",
    "system_upgrade": "升级相关系统",
    "process_review": "审查现有流程",
    "document_prepare": "准备相关文档",
    "risk_assessment": "进行风险评估",
    "compliance_check": "开展合规检查",
    "report_submission": "提交合规报告",
    "audit_preparation": "准备审计工作",
    "emergency_plan": "制定应急预案"
}


# ================== 状态码定义 ==================
class StatusCode(Enum):
    """系统状态码"""
    
    SUCCESS = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# ================== 缓存键前缀 ==================
CACHE_KEYS = {
    "regulation": "regulation:",
    "analysis": "analysis:",
    "report": "report:",
    "user_session": "session:",
    "api_limit": "limit:",
    "search_result": "search:"
}


# ================== 文件类型支持 ==================
SUPPORTED_FILE_TYPES = {
    "document": [".pdf", ".doc", ".docx", ".txt", ".md"],
    "spreadsheet": [".xls", ".xlsx", ".csv"],
    "image": [".png", ".jpg", ".jpeg", ".gif", ".bmp"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz"]
}


# ================== 日志等级映射 ==================
class LogLevel(IntEnum):
    """Loguru supported log levels"""

    TRACE = 5
    DEBUG = 10
    INFO = 20
    SUCCESS = 25
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


LOG_LEVELS: Dict[str, int] = {level.name: level.value for level in LogLevel}


# ================== 邮件模板 ==================
EMAIL_TEMPLATES = {
    "daily_report": {
        "subject": "【法规监控】每日更新报告 - {date}",
        "template_file": "daily_report.html"
    },
    "weekly_report": {
        "subject": "【法规监控】周度分析报告 - 第{week}周",
        "template_file": "weekly_report.html"
    },
    "alert": {
        "subject": "【紧急】重要法规变更提醒",
        "template_file": "alert.html"
    },
    "system_error": {
        "subject": "【系统告警】法规监控系统异常",
        "template_file": "error.html"
    }
}


# ================== API限制配置 ==================
API_LIMITS = {
    "zhipu_ai": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "requests_per_day": 10000
    },
    "scraper": {
        "requests_per_second": 5,
        "concurrent_sessions": 20,
        "retry_delays": [1, 2, 4, 8, 16]  # 指数退避
    }
}


# ================== 正则表达式模式 ==================
REGEX_PATTERNS: Dict[str, str] = {
    "chinese_text": r"[\u4e00-\u9fff]+",
    "date": r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?",
    "regulation_number": r"[A-Za-z0-9]{1,10}〔\d{4}〕第?\d{1,4}号?",
    "phone": r"1[3-9]\d{9}",
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "url": r"https?://[^\s<>\"{}|\\^`\[\]]+",
}


# ================== 用户界面常量 ==================
UI_CONSTANTS = {
    "colors": {
        "primary": "#1f538d",
        "secondary": "#2ECC71",
        "success": "#27AE60",
        "warning": "#F39C12",
        "error": "#E74C3C",
        "info": "#3498DB",
        "dark": "#2C3E50",
        "light": "#ECF0F1"
    },
    "fonts": {
        "default": ("Microsoft YaHei", 12),
        "title": ("Microsoft YaHei", 16, "bold"),
        "subtitle": ("Microsoft YaHei", 14, "bold"),
        "small": ("Microsoft YaHei", 10)
    },
    "padding": {
        "small": 5,
        "medium": 10,
        "large": 20,
        "xlarge": 30
    }
}


# ================== 系统限制 ==================
SYSTEM_LIMITS = {
    "max_file_size_mb": 100,
    "max_concurrent_tasks": 50,
    "max_cache_items": 10000,
    "max_log_files": 10,
    "max_database_size_gb": 5,
    "session_timeout_minutes": 30,
    "max_search_results": 1000
}


# ================== 功能开关 ==================
FEATURE_FLAGS = {
    "ai_analysis": True,
    "email_notifications": True,
    "cache_system": True,
    "auto_scheduling": True,
    "data_export": True,
    "advanced_search": True,
    "user_management": False,  # 暂未实现
    "api_access": False,       # 暂未实现
    "mobile_app": False        # 暂未实现
}


# ================== 错误消息 ==================
ERROR_MESSAGES = {
    "network_error": "网络连接失败，请检查网络设置",
    "api_key_invalid": "API密钥无效，请检查配置",
    "database_error": "数据库操作失败",
    "file_not_found": "文件未找到",
    "permission_denied": "权限不足",
    "invalid_format": "文件格式不支持",
    "service_unavailable": "服务暂时不可用",
    "rate_limit_exceeded": "请求频率超限，请稍后重试",
    "parsing_error": "数据解析失败",
    "validation_error": "数据验证失败"
}