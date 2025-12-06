"""
TalkBut CLI - Main entry point
"""
import click
from talkbut.utils.logger import get_logger
from talkbut.cli.config import config
from talkbut.cli.log import log
from talkbut.cli.report import report
from talkbut.cli.scan import scan
from talkbut.cli.schedule import schedule

logger = get_logger(__name__)

@click.group()
@click.version_option(version="0.1.0", prog_name="talkbut")
def cli():
    """
    🗣️  TalkBut - สรุปผลงานจาก Git ด้วย AI
    
    \b
    ⚡ Quick Start:
       talkbut config init     สร้าง config
       talkbut scan --path ~   ค้นหา git repos
       talkbut log             เก็บ + วิเคราะห์ commits
       talkbut report          สรุป daily logs
    
    \b
    📖 Examples:
       talkbut scan --path ~/Documents/GitHub
       talkbut log --since "3 days ago"
       talkbut report --days 7
       talkbut report --start 2025-11-01 --end 2025-11-30
       talkbut report --fast "1 month"    # ⚡ สรุปแบบเร็ว ยิง AI ครั้งเดียว
       talkbut report --fast "YTD"        # 📅 สรุปทั้งปี แบ่งทีละเดือน
    """
    pass

# Register commands
cli.add_command(log)
cli.add_command(config)
cli.add_command(report)
cli.add_command(scan)
cli.add_command(schedule)

if __name__ == "__main__":
    cli()
