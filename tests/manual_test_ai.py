import os
import sys
from datetime import datetime, date
from talkbut.processors.ai_analyzer import AIAnalyzer
from talkbut.models.commit import Commit
from talkbut.processors.formatter import ReportFormatter

# Set the API key provided by the user
# NOTE: In production, this should be loaded from a secure .env file
os.environ["GEMINI_API_KEY"] = "AIzaSyBzwUpmU_Yq9DIbfmmG4Ztjm-ptrkYXt5U"

def run_test():
    print("🚀 Starting Manual AI Integration Test...")
    
    # 1. Create sample commits (simulating a day's work)
    commits = [
        Commit(
            hash="a1b2c3d",
            author="Dev",
            email="dev@example.com",
            date=datetime.now(),
            message="feat: implement login page\n\n- Added login form\n- Integrated with auth service",
            files_changed=["src/auth/login.py", "src/ui/login.html"],
            insertions=50,
            deletions=0
        ),
        Commit(
            hash="e5f6g7h",
            author="Dev",
            email="dev@example.com",
            date=datetime.now(),
            message="fix: resolve crash on startup\n\nFixed null pointer exception in config loader",
            files_changed=["src/config/loader.py"],
            insertions=2,
            deletions=1
        ),
        Commit(
            hash="i8j9k0l",
            author="Dev",
            email="dev@example.com",
            date=datetime.now(),
            message="refactor: optimize database query\n\nReduced query time by 50%",
            files_changed=["src/db/query.py"],
            insertions=10,
            deletions=20
        )
    ]
    
    print(f"📝 Created {len(commits)} sample commits.")

    # 2. Initialize Analyzer
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        print("📋 Available Models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
        
        analyzer = AIAnalyzer()
        print("✅ AIAnalyzer initialized.")
    except Exception as e:
        print(f"❌ Failed to initialize AIAnalyzer: {e}")
        return

    # 3. Analyze Commits
    print("🤖 Sending commits to Gemini API for analysis...")
    try:
        report = analyzer.analyze_commits(commits, date.today())
        print("✅ Analysis complete!")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Format and Print Report
    formatter = ReportFormatter()
    print("\n" + "="*50)
    print("📄 GENERATED REPORT")
    print("="*50)
    print(formatter.format_markdown(report))
    print("="*50)

if __name__ == "__main__":
    # Ensure src is in path
    sys.path.append(os.path.join(os.getcwd(), "src"))
    run_test()
