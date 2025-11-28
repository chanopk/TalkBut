"""
TalkBut CLI - Main entry point
"""
import click
from talkbut.utils.logger import get_logger
from talkbut.cli.config import config
from talkbut.cli.log import log

logger = get_logger(__name__)

@click.group()
@click.version_option(version="0.1.0", prog_name="talkbut")
def cli():
    """
    🗣️  TalkBut - สรุปผลงานจาก Git ด้วย AI
    
    \b
    ⚡ Quick Start:
       talkbut config init     สร้าง config
       talkbut log             เก็บ + วิเคราะห์ commits
    
    \b
    📖 Examples:
       talkbut log --since "3 days ago"
       talkbut log --unsave
       talkbut config show
    """
    pass

# Register commands
cli.add_command(log)
cli.add_command(config)

if __name__ == "__main__":
    cli()
