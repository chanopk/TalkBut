from talkbut.collectors.parser import DataParser
from talkbut.models.commit import Commit
from datetime import datetime

def test_parse_commit_message():
    parser = DataParser()
    message = "feat: add login feature [FEATURE]\n\nImplemented login with OAuth.\nRelates to JIRA-123 and #456"
    
    parsed = parser.parse_commit_message(message)
    
    assert parsed['subject'] == "feat: add login feature [FEATURE]"
    assert "Implemented login" in parsed['body']
    assert "JIRA-123" in parsed['ticket_refs']
    assert "#456" in parsed['ticket_refs']
    assert "FEATURE" in parsed['tags']

def test_categorize_commit():
    parser = DataParser()
    
    c1 = Commit("hash", "author", "email", datetime.now(), "feat: new feature")
    assert parser.categorize_commit(c1) == "feature"
    
    c2 = Commit("hash", "author", "email", datetime.now(), "fix: bug fix")
    assert parser.categorize_commit(c2) == "bugfix"
    
    c3 = Commit("hash", "author", "email", datetime.now(), "chore: cleanup")
    assert parser.categorize_commit(c3) == "chore"
    
    c4 = Commit("hash", "author", "email", datetime.now(), "random message")
    assert parser.categorize_commit(c4) == "other"

def test_enrich_commit():
    parser = DataParser()
    commit = Commit(
        "hash", "author", "email", datetime.now(), 
        "feat: add feature [BETA]\n\nRef JIRA-999"
    )
    
    enriched = parser.enrich_commit(commit)
    
    assert "JIRA-999" in enriched.ticket_refs
    assert "BETA" in enriched.tags
