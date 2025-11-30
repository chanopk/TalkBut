"""
TalkBut CLI - Scan command for discovering git repositories
"""
import click
from talkbut.utils.logger import get_logger
from talkbut.collectors.repo_scanner import RepoScanner
from talkbut.core.config import ConfigManager

logger = get_logger(__name__)


@click.command()
@click.option(
    '--path', '-p',
    multiple=True,
    help='Path(s) to scan for git repositories'
)
@click.option(
    '--depth', '-d',
    default=2,
    type=int,
    help='Maximum depth to search (default: 2)'
)
@click.option(
    '--config-paths',
    is_flag=True,
    help='Scan paths from config file instead of --path'
)
def scan(path, depth, config_paths):
    """
    🔍 Scan directories to discover git repositories.
    
    \b
    Examples:
        talkbut scan --path /Users/yourname/projects
        talkbut scan --path ~/Documents/GitHub --depth 3
        talkbut scan --config-paths
    """
    scanner = RepoScanner(max_depth=depth)
    
    if config_paths:
        # Use paths from config
        config = ConfigManager()
        scan_paths = config.get("git.scan_paths", [])
        scan_depth = config.get("git.scan_depth", depth)
        
        if not scan_paths:
            click.echo("❌ No scan_paths configured in config.yaml")
            click.echo("   Add scan_paths under git: section or use --path option")
            return
        
        click.echo(f"📂 Scanning paths from config (depth: {scan_depth})...")
        repos = scanner.scan_multiple(scan_paths, scan_depth)
    elif path:
        # Use provided paths
        click.echo(f"📂 Scanning {len(path)} path(s) (depth: {depth})...")
        repos = scanner.scan_multiple(list(path), depth)
    else:
        click.echo("❌ Please provide --path or use --config-paths")
        click.echo("   Example: talkbut scan --path ~/projects")
        return
    
    if not repos:
        click.echo("📭 No git repositories found")
        return
    
    click.echo(f"\n✅ Found {len(repos)} git repositories:\n")
    for i, repo in enumerate(repos, 1):
        click.echo(f"  {i}. {repo['name']}")
        click.echo(f"     📁 {repo['path']}")
    
    click.echo(f"\n💡 Tip: Add these to config.yaml under git.repositories")
    click.echo("   Or use git.scan_paths to auto-discover them")
