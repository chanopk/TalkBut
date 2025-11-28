"""
Config command - จัดการ configuration
"""
import click
import os
from pathlib import Path
from talkbut.core.config import ConfigManager
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)

@click.group()
def config():
    """จัดการ config"""
    pass

@config.command('show')
def show_config():
    """
    แสดง configuration ปัจจุบัน
    
    Example:
        talkbut config show
    """
    try:
        cfg = ConfigManager()
        
        click.echo("⚙️  Current Configuration:")
        click.echo("")
        
        # Git settings
        click.echo("📁 Git Settings:")
        repos = cfg.git_repos
        if repos:
            for repo in repos:
                click.echo(f"   • {repo.get('name', 'Unnamed')}: {repo.get('path', 'N/A')}")
        else:
            click.echo("   (No repositories configured)")
        click.echo(f"   Default branch: {cfg.get('git.default_branch', 'main')}")
        click.echo("")
        
        # AI settings
        click.echo("🤖 AI Settings:")
        click.echo(f"   Provider: {cfg.get('ai.provider', 'gemini')}")
        click.echo(f"   Model: {cfg.get('ai.model', 'gemini-1.5-flash')}")
        api_key = cfg.ai_api_key
        if api_key:
            click.echo(f"   API Key: {'*' * 20} (configured)")
        else:
            click.echo("   API Key: ⚠️  Not configured")
        click.echo("")
        
        # Report settings
        click.echo("📄 Report Settings:")
        click.echo(f"   Format: {cfg.get('report.default_format', 'markdown')}")
        click.echo(f"   Include stats: {cfg.get('report.include_stats', True)}")
        click.echo(f"   Sort order: {cfg.get('report.sort_order', 'asc')}")
        click.echo("")
        
        # Storage settings
        click.echo("💾 Storage Settings:")
        click.echo(f"   Log dir: ./data/logs/")
        click.echo("")
        
    except Exception as e:
        logger.error(f"Failed to show config: {e}", exc_info=True)
        click.echo(f"❌ Failed to show config: {e}", err=True)
        raise click.Abort()

@config.command('init')
@click.option('--force', is_flag=True, help='Overwrite existing config')
def init_config(force):
    """
    สร้าง configuration file เริ่มต้น
    
    Example:
        talkbut config init
        talkbut config init --force
    """
    try:
        config_path = Path("config/config.yaml")
        example_path = Path("config/config.yaml.example")
        
        if config_path.exists() and not force:
            click.echo("⚠️  Config file already exists. Use --force to overwrite.")
            return
        
        if not example_path.exists():
            click.echo("❌ Example config file not found.")
            return
        
        # Copy example to actual config
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(example_path, 'r', encoding='utf-8') as src:
            content = src.read()
        
        with open(config_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        
        click.echo(f"✅ Created config file: {config_path}")
        click.echo("💡 Edit the file to customize your settings.")
        click.echo("💡 Set your API key: export GEMINI_API_KEY='your-key'")
        
    except Exception as e:
        logger.error(f"Failed to init config: {e}", exc_info=True)
        click.echo(f"❌ Failed to init config: {e}", err=True)
        raise click.Abort()

@config.command('set-key')
@click.argument('api_key')
@click.option('--provider', default='gemini', help='AI provider (gemini/openai)')
def set_api_key(api_key, provider):
    """
    ตั้งค่า API key (บันทึกใน environment)
    
    Example:
        talkbut config set-key YOUR_API_KEY
        talkbut config set-key YOUR_API_KEY --provider openai
    """
    try:
        # Determine env var name
        if provider == 'gemini':
            env_var = 'GEMINI_API_KEY'
        elif provider == 'openai':
            env_var = 'OPENAI_API_KEY'
        else:
            env_var = f'{provider.upper()}_API_KEY'
        
        click.echo(f"💡 To set API key, add this to your shell profile:")
        click.echo(f"   export {env_var}='{api_key}'")
        click.echo("")
        click.echo("Or for current session only:")
        click.echo(f"   export {env_var}='{api_key}'")
        
    except Exception as e:
        logger.error(f"Failed to set API key: {e}", exc_info=True)
        click.echo(f"❌ Failed: {e}", err=True)
        raise click.Abort()

@config.command('check')
def check_config():
    """
    ตรวจสอบ configuration และ dependencies
    
    Example:
        talkbut config check
    """
    try:
        click.echo("🔍 Checking configuration...")
        click.echo("")
        
        cfg = ConfigManager()
        issues = []
        
        # Check API key
        if not cfg.ai_api_key:
            issues.append("⚠️  AI API key not configured")
        else:
            click.echo("✅ API key configured")
        
        # Check storage directories
        log_dir = Path("./data/logs")
        if not log_dir.exists():
            click.echo(f"⚠️  Log directory doesn't exist: {log_dir}")
            log_dir.mkdir(parents=True, exist_ok=True)
            click.echo(f"   Created: {log_dir}")
        else:
            click.echo(f"✅ Log directory exists: {log_dir}")
        
        # Check git
        try:
            import git
            click.echo("✅ GitPython installed")
        except ImportError:
            issues.append("❌ GitPython not installed")
        
        # Check AI library
        try:
            import google.generativeai
            click.echo("✅ Google Generative AI installed")
        except ImportError:
            issues.append("❌ Google Generative AI not installed")
        
        click.echo("")
        
        if issues:
            click.echo("Issues found:")
            for issue in issues:
                click.echo(f"   {issue}")
        else:
            click.echo("🎉 All checks passed!")
        
    except Exception as e:
        logger.error(f"Config check failed: {e}", exc_info=True)
        click.echo(f"❌ Check failed: {e}", err=True)
        raise click.Abort()
