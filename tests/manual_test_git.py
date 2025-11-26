import sys
import os
from talkbut.collectors.git_collector import GitCollector
from talkbut.core.config import ConfigManager

def run_test():
    print("🚀 Starting Manual Git Collector Test...")
    
    # Load config
    config = ConfigManager()
    repos = config.get("git.repositories", [])
    
    if not repos:
        print("❌ No repositories configured.")
        return

    for repo_conf in repos:
        path = repo_conf.get("path")
        name = repo_conf.get("name")
        print(f"\n📂 Checking repository: {name} ({path})")
        
        try:
            collector = GitCollector(path)
            # Collect commits from the last 24 hours
            commits = collector.collect_commits(since="24 hours ago")
            
            print(f"✅ Successfully connected to repo.")
            print(f"📊 Found {len(commits)} commits in the last 24 hours.")
            
            for c in commits:
                print(f"  - [{c.short_hash}] {c.author}: {c.message.splitlines()[0]}")
                
        except Exception as e:
            print(f"❌ Failed to collect from {name}: {e}")

if __name__ == "__main__":
    sys.path.append(os.path.join(os.getcwd(), "src"))
    run_test()
