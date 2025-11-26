"""
TalkBut CLI - Main entry point
"""
import click
from talkbut.utils.logger import get_logger
from talkbut.cli.collect import collect
from talkbut.cli.analyze import analyze
from talkbut.cli.report import report
from talkbut.cli.config import config
from talkbut.cli.log import log

logger = get_logger(__name__)

@click.group()
@click.version_option(version="0.1.0", prog_name="talkbut")
def cli():
    """
    TalkBut - เครื่องมือเก็บและวิเคราะห์ข้อมูลการทำงานจาก Git
    
    ใช้สำหรับ developers ที่ต้องการสรุปผลงานประจำวัน
    
    \b
    Quick Start:
        1. talkbut config init          # สร้าง config file
        2. talkbut log                   # เก็บข้อมูล + วิเคราะห์ในคำสั่งเดียว
        3. talkbut report                # สร้างรายงาน
    
    \b
    Examples:
        talkbut log --output daily_log.json
        talkbut log --include-diffs --no-compact
        talkbut collect --repo ./myproject
        talkbut analyze --date today
        talkbut report --format markdown --output report.md
        talkbut config show
    """
    pass

# Register commands
cli.add_command(log)
cli.add_command(collect)
cli.add_command(analyze)
cli.add_command(report)
cli.add_command(config)

if __name__ == "__main__":
    cli()
