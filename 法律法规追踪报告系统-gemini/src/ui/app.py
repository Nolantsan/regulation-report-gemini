import customtkinter as ctk
import asyncio
import threading
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

# 导入核心服务和数据库模块
from src.core.scraper import AsyncLegalScraper
from src.core.ai_service import ai_service
from src.database.connection import get_db # 使用get_db
from src.database.models import Regulation
from sqlalchemy import desc

class LegalTrackerApp(ctk.CTk):
    """主应用窗口 - 采用现代化设计语言和健壮的后台任务架构"""
    def __init__(self):
        super().__init__()
        self.title("智能法规追踪系统 v2.0")
        self.geometry("1200x800")
        self.minsize(1000, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._create_sidebar()
        self._create_main_content()
        self._create_status_bar()
        self.update_time()

    def _set_ui_busy(self):
        """锁定UI，防止并发操作"""
        self.scan_button.configure(state="disabled")
        self.generate_button.configure(state="disabled")
        self.web_search_switch.configure(state="disabled")
        self.status_label.configure(text="正在处理，请稍候...")

    def _set_ui_idle(self):
        """解锁UI，恢复正常状态"""
        self.scan_button.configure(state="normal")
        self.generate_button.configure(state="normal")
        self.web_search_switch.configure(state="normal")
        self.status_label.configure(text="系统就绪")

    def log_to_ui(self, message: str, level: str = "INFO"):
        def _add_log():
            color_map = {"INFO": "#FFFFFF", "SUCCESS": "#2ECC71", "ERROR": "#E74C3C", "WARNING": "#F1C40F"}
            log_entry = ctk.CTkLabel(self.monitor_frame, text=f"[{datetime.now().strftime('%H:%M:%S')}] [{level}] {message}", text_color=color_map.get(level, "#FFFFFF"), wraplength=self.monitor_frame.winfo_width() - 40)
            log_entry.pack(anchor="w", padx=5, pady=2)
            self.monitor_frame._parent_canvas.yview_moveto(1.0)
        self.after(0, _add_log)

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.logo_label = ctk.CTkLabel(self.sidebar,text="📊 Legal Tracker",font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)
        nav_items = [("🏠 主页", self.show_dashboard),("🔍 数据源", self.show_sources),("📈 分析", self.show_analysis),("📄 报告", self.show_reports),("⚙️ 设置", self.show_settings)]
        for i, (text, command) in enumerate(nav_items, 1):
            btn = ctk.CTkButton(self.sidebar,text=text,command=command,height=40,font=ctk.CTkFont(size=14))
            btn.grid(row=i, column=0, padx=20, pady=10, sticky="ew")

    def _create_main_content(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.title_label = ctk.CTkLabel(self.main_frame,text="法规监控仪表板",font=ctk.CTkFont(size=28, weight="bold"))
        self.title_label.grid(row=0, column=0, sticky="w", padx=20, pady=20)
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.action_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.scan_button = ctk.CTkButton(self.action_frame,text="🚀 立即扫描",command=self.start_scan_thread,height=50,font=ctk.CTkFont(size=16, weight="bold"),fg_color="#2ECC71",hover_color="#27AE60")
        self.scan_button.pack(side="left", padx=0)
        self.web_search_switch = ctk.CTkSwitch(self.action_frame, text="启用网络搜索", onvalue=True, offvalue=False)
        self.web_search_switch.pack(side="left", padx=10)
        self.generate_button = ctk.CTkButton(self.action_frame,text="📊 生成报告",command=self.start_report_generation_thread,height=50,font=ctk.CTkFont(size=16, weight="bold"))
        self.generate_button.pack(side="left", padx=10)
        self.monitor_frame = ctk.CTkScrollableFrame(self.main_frame,label_text="实时监控日志")
        self.monitor_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)

    def _create_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=30)
        self.status_bar.grid(row=1, column=1, sticky="ew", padx=20, pady=(0, 10))
        self.status_bar.grid_column_configure(1, weight=1)
        self.status_label = ctk.CTkLabel(self.status_bar,text="系统就绪",font=ctk.CTkFont(size=12))
        self.status_label.grid(row=0, column=0, padx=10)
        self.progress_bar = ctk.CTkProgressBar(self.status_bar, orientation="horizontal", mode="determinate")
        self.progress_bar.set(0)
        self.time_label = ctk.CTkLabel(self.status_bar,text="",font=ctk.CTkFont(size=12))
        self.time_label.grid(row=0, column=2, padx=10)

    def show_dashboard(self):
        self.title_label.configure(text="法规监控仪表板")
    def show_sources(self):
        self.title_label.configure(text="数据源管理")
    def show_analysis(self):
        self.title_label.configure(text="数据分析与可视化")
    def show_reports(self):
        self.title_label.configure(text="合规报告中心")
    def show_settings(self):
        self.title_label.configure(text="系统设置")

    def start_scan_thread(self):
        self.log_to_ui("请求启动扫描任务...", "INFO")
        self._set_ui_busy()
        scan_thread = threading.Thread(target=self._run_scan_in_thread)
        scan_thread.daemon = True
        scan_thread.start()

    def _run_scan_in_thread(self):
        try:
            asyncio.run(self.run_scan_async())
        except Exception as e:
            logger.error(f"扫描线程发生严重错误: {e}", exc_info=True)
            self.log_to_ui(f"扫描线程发生严重错误: {e}", "ERROR")
        finally:
            self.after(0, self._set_ui_idle)

    async def run_web_search_async(self) -> list:
        """Execute web searches when enabled and return regulation list."""
        if not self.web_search_switch.get():
            self.log_to_ui("网络搜索未启用，跳过。", "WARNING")
            return []

        self.log_to_ui("启动网络搜索...", "INFO")
        # 初始进度反馈
        self.after(0, self.progress_bar.set, 0.1)

        results = []
        try:
            async with AsyncLegalScraper() as scraper:
                results = await scraper.fetch_all_sources()
            self.log_to_ui(f"网络搜索完成，获取到 {len(results)} 条法规。", "SUCCESS")
        except Exception as e:
            logger.error(f"网络搜索失败: {e}", exc_info=True)
            self.log_to_ui(f"网络搜索失败: {e}", "ERROR")

        # 更新进度条
        self.after(0, self.progress_bar.set, 0.3)
        return results

    async def run_scan_async(self):
        """Coordinate scraping, AI analysis and DB persistence."""
        self.after(0, self.progress_bar.grid, {"row": 0, "column": 1, "sticky": "ew", "padx": 10})
        self.after(0, self.progress_bar.set, 0)
        self.log_to_ui("开始扫描法规数据源...", "INFO")

        try:
            regulations = await self.run_web_search_async()

            if not regulations:
                self.log_to_ui("未获取到任何法规。", "WARNING")
                return

            self.after(0, self.progress_bar.set, 0.4)
            analyzed = await ai_service.batch_analyze(regulations)
            self.log_to_ui(f"AI分析完成，共 {len(analyzed)} 条法规相关。", "INFO")

            self.after(0, self.progress_bar.set, 0.7)
            with next(get_db()) as db_session:
                for reg in analyzed:
                    # 解析发布日期
                    publish_date = None
                    if reg.get('publish_date'):
                        try:
                            publish_date = datetime.strptime(str(reg['publish_date']).strip('[]'), "%Y-%m-%d").date()
                        except Exception:
                            publish_date = None

                    existing = db_session.query(Regulation).filter_by(url=reg['url']).first()
                    if existing:
                        existing.title = reg.get('title', existing.title)
                        existing.publish_date = publish_date or existing.publish_date
                        existing.source = reg.get('source', existing.source)
                        existing.category = reg.get('category', existing.category)
                        existing.full_text = reg.get('full_text', existing.full_text)
                        existing.keywords = reg.get('keywords', existing.keywords)
                        existing.ai_analysis = reg.get('ai_analysis', existing.ai_analysis)
                    else:
                        db_session.add(Regulation(
                            title=reg.get('title'),
                            url=reg.get('url'),
                            publish_date=publish_date,
                            source=reg.get('source'),
                            category=reg.get('category'),
                            full_text=reg.get('full_text'),
                            keywords=reg.get('keywords'),
                            ai_analysis=reg.get('ai_analysis')
                        ))
                db_session.commit()

            self.after(0, self.progress_bar.set, 1)
            self.log_to_ui("扫描流程完成，数据已保存。", "SUCCESS")
        except Exception as e:
            logger.error(f"扫描流程失败: {e}", exc_info=True)
            self.log_to_ui(f"扫描流程失败: {e}", "ERROR")
        finally:
            self.after(0, self.progress_bar.grid_forget)

    def start_report_generation_thread(self):
        self.log_to_ui("请求生成合规报告...", "INFO")
        self._set_ui_busy()
        report_thread = threading.Thread(target=self._run_report_in_thread)
        report_thread.daemon = True
        report_thread.start()

    def _run_report_in_thread(self):
        try:
            self.after(0, self.progress_bar.grid, {"row": 0, "column": 1, "sticky": "ew", "padx": 10})
            self.after(0, self.progress_bar.set, 0)
            asyncio.run(self.run_report_generation_async())
        except Exception as e:
            logger.error(f"报告生成线程发生严重错误: {e}", exc_info=True)
            self.log_to_ui(f"报告生成线程发生严重错误: {e}", "ERROR")
        finally:
            self.after(0, self.progress_bar.grid_forget)
            self.after(0, self._set_ui_idle)

    async def run_report_generation_async(self):
        """Generate executive report from analyzed regulations."""
        self.log_to_ui("开始生成合规报告...", "INFO")
        self.after(0, self.progress_bar.set, 0.1)

        try:
            with next(get_db()) as db_session:
                regs = (
                    db_session.query(Regulation)
                    .filter(Regulation.ai_analysis.isnot(None))
                    .order_by(desc(Regulation.publish_date))
                    .all()
                )

            self.after(0, self.progress_bar.set, 0.4)
            reg_dicts = []
            for r in regs:
                reg_dicts.append({
                    'title': r.title,
                    'url': r.url,
                    'publish_date': r.publish_date.isoformat() if r.publish_date else None,
                    'source': r.source,
                    'category': r.category,
                    'full_text': r.full_text,
                    'keywords': r.keywords,
                    'ai_analysis': r.ai_analysis,
                })

            report_content = await ai_service.generate_executive_report(reg_dicts)

            report_dir = Path(__file__).resolve().parent.parent.parent / "reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            report_path = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            report_path.write_text(report_content, encoding="utf-8")

            self.after(0, self.progress_bar.set, 1)
            self.log_to_ui(f"报告生成完成: {report_path}", "SUCCESS")
            return str(report_path)
        except Exception as e:
            logger.error(f"报告生成失败: {e}", exc_info=True)
            self.log_to_ui(f"报告生成失败: {e}", "ERROR")
            return ""

    def update_time(self):
        self.time_label.configure(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.after(1000, self.update_time)

if __name__ == "__main__":
    app = LegalTrackerApp()
    app.mainloop()
