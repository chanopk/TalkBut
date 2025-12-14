# TalkBut 🎯

> เครื่องมือสร้าง Daily Work Log จาก Git commits ด้วย AI

TalkBut (ล้อเลียนเสียงคำว่า "ตอกบัตร") เป็น CLI tool ที่ช่วยสร้างรายงานสรุปงานประจำวันจาก Git commits โดยใช้ AI วิเคราะห์และสรุปผลงานให้อัตโนมัติ

## ✨ Features

- ⚡ สร้าง daily log ในคำสั่งเดียว
- 🤖 วิเคราะห์และสรุปงานด้วย Google Gemini AI
- 📊 ดึงข้อมูลจาก Git commits อัตโนมัติ
- �  Auto-scan หา git repositories จาก path ที่กำหนด
- � Expor้t เป็น JSON, Markdown, Plain Text
- 💾 เก็บข้อมูลปลอดภัยที่เครื่องของคุณ

## 🚀 Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd talkbut

# 2. Create environment file
cp .env.example .env

# 3. Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
npm install

# 5. Install CLI
pip install -e .

# 6. Set API key in .env
echo "GEMINI_API_KEY=your-api-key-here" >> .env
```

## ⚡ Quick Start

```bash
# Activate environment
source venv/bin/activate

# Initialize config (first time)
talkbut config init
```

แก้ไข `config/config.yaml` เพื่อระบุ path ที่เก็บ git repos:

```yaml
git:
  # กรอง commits เฉพาะ author ที่ต้องการ (email หรือชื่อ)
  author: "your.email@example.com"
  
  # ระบุ path ที่เก็บ git projects ของคุณ สามารถระบุได้หลาย path
  scan_paths:
    - /Users/yourname/Documents/GitHub
    - /Users/yourname/projects
  scan_depth: 1 # สามารถสิ่งไปดูลึกๆได้ ยิ่งลึกยิ่งช้า
```

จากนั้นสร้าง daily log:

```bash
# Create daily log
talkbut log
```

ผลลัพธ์จะถูกบันทึกที่ `data/logs/daily_log_YYYY-MM-DD.json`

## 📖 Usage

### สร้าง Daily Log

```bash
# สร้าง log default : วันนี้
talkbut log

# กำหนดช่วงเวลาแบบ relative
talkbut log --since "1 day ago"
talkbut log --since "7 days ago"
talkbut log --since "1 week ago"
talkbut log --since "yesterday"

# กำหนดช่วงเวลาแบบวันที่ (ISO format)
talkbut log --since "2025-11-01"
talkbut log --since "2025-11-25"

# กำหนดทั้ง start และ end date
talkbut log --since "2025-11-01" --until "2025-11-30"

# กรอง commits เฉพาะ author (override config)
talkbut log --author "john@example.com"

# แสดงผลอย่างเดียว ไม่บันทึก
talkbut log --unsave

# ไม่อ่าน diffs อ่านแค่ commits
talkbut log --no-diffs
```

### Export รายงาน (อยู่ระหว่างปรับปรุง)

```bash
# Export เป็น Markdown
talkbut report --format markdown --output report.md

# Export เป็น Plain Text
talkbut report --format text --output report.txt
```

### จัดการ Config

```bash
# แสดง config
talkbut config show

# ตรวจสอบ config
talkbut config check
```

📚 **[ดูคู่มือเพิ่มเติม →](docs/LOG_COMMAND.md)**

### Automated Scheduling

TalkBut รองรับการสร้าง daily log อัตโนมัติทุกวันตามเวลาที่กำหนด โดยใช้ cron (macOS/Linux) หรือ Task Scheduler (Windows)

#### เปิดใช้งาน Automated Logging

```bash
# เปิดใช้งานและกำหนดเวลา (24-hour format)
talkbut schedule enable --time "18:00"

# ตรวจสอบสถานะ
talkbut schedule status
```

#### จัดการ Schedule

```bash
# แก้ไขเวลา
talkbut schedule update --time "20:00"

# ปิดใช้งาน
talkbut schedule disable

# ดูสถานะปัจจุบัน
talkbut schedule status
```

#### ตัวอย่าง Status Output

```
Schedule Status:
  Status: Enabled
  Schedule Time: 18:00 (daily)
  Last Run: 2025-12-06 18:00:15
  Next Run: 2025-12-07 18:00:00
  Platform: cron (macOS)

Recent Runs:
  ✓ 2025-12-06 18:00:15 - Success
  ✓ 2025-12-05 18:00:12 - Success
```

#### Platform-Specific Notes

**macOS/Linux:**
- ใช้ cron สำหรับ scheduling
- ต้องการ permission ในการแก้ไข crontab
- ตรวจสอบ cron jobs ด้วย: `crontab -l`

**Windows:**
- ใช้ Task Scheduler สำหรับ scheduling
- อาจต้องการ administrator privileges
- ตรวจสอบ tasks ด้วย: `schtasks /query /tn TalkButDailyLog`

### Batch Processing

สร้าง daily logs สำหรับหลายวันพร้อมกัน - เหมาะสำหรับการสร้าง logs ย้อนหลังหรือรันสัปดาห์ละครั้ง

#### Basic Batch Processing

```bash
# สร้าง logs สำหรับ 7 วันที่ผ่านมา
talkbut log --since "7 days ago"

# สร้าง logs สำหรับช่วงเวลาที่กำหนด
talkbut log --since "2025-11-01" --until "2025-11-30"

# สร้าง logs สำหรับสัปดาห์ที่แล้ว
talkbut log --since "1 week ago"
```

#### Batch Options

```bash
# แสดง progress bar และสรุปผล
talkbut log --since "7 days ago" --batch

# บังคับสร้างใหม่ทั้งหมด (ข้าม existing logs)
talkbut log --since "7 days ago" --force

# รวมทั้ง batch mode และ force
talkbut log --since "7 days ago" --batch --force
```

#### ตัวอย่าง Batch Output

```
Processing 7 dates...

[1/7] 2025-11-25: ✓ Processed (5 commits)
[2/7] 2025-11-26: ⊘ Skipped (log exists)
[3/7] 2025-11-27: ✓ Processed (3 commits)
[4/7] 2025-11-28: ⊘ Skipped (no commits)
[5/7] 2025-11-29: ✓ Processed (8 commits)
[6/7] 2025-11-30: ✓ Processed (2 commits)
[7/7] 2025-12-01: ✓ Processed (6 commits)

Summary:
  Total: 7 dates
  Processed: 5 dates
  Skipped: 2 dates (1 existing, 1 no commits)
  Failed: 0 dates
  Duration: 45.2s
```

#### Smart Skipping

Batch processing จะข้ามวันที่มี log อยู่แล้วโดยอัตโนมัติ เพื่อ:
- ประหยัดค่า API calls
- ลดเวลาในการประมวลผล
- หลีกเลี่ยงการสร้าง logs ซ้ำ

ใช้ `--force` เพื่อบังคับสร้างใหม่ทั้งหมด

#### Error Handling

หาก batch processing พบ error ในวันใดวันหนึ่ง:
- ระบบจะดำเนินการต่อกับวันอื่นๆ
- Error จะถูกบันทึกและแสดงในสรุปผล
- สามารถ retry เฉพาะวันที่ล้มเหลวได้

## 📋 ตัวอย่าง Output

```json
{
  "date": "2025-11-26",
  "summary": "Implemented CLI interface with collect, analyze, and report commands",
  "stats": {
    "commits": 12,
    "files": 8,
    "insertions": 450,
    "deletions": 23
  },
  "highlights": [
    "Complete CLI interface with Click framework",
    "AI analysis with Google Gemini API",
    "Multiple output formats support"
  ]
}
```

## 🔧 Configuration

แก้ไข `config/config.yaml`:

```yaml
git:
  # กรอง commits เฉพาะ author (email หรือชื่อ)
  # เว้นว่างไว้ = เก็บ commits ของทุกคน
  author: "your.email@example.com"
  
  # วิธีที่ 1: ระบุ repositories ตรงๆ
  repositories:
    - path: /path/to/your/project
      name: "Project Name"
  
  # วิธีที่ 2: Auto-scan หา git repos ใน path ที่กำหนด
  scan_paths:
    - /Users/yourname/Documents/GitHub
    - /Users/yourname/projects

schedule:
  enabled: false  # เปิด/ปิด automated logging
  time: "18:00"  # เวลาที่จะรัน (24-hour format)
  status_file: ./data/schedule_status.json
  error_log: ./data/schedule_errors.log
```

### Auto-scan Repositories

ระบบสามารถค้นหา git repositories อัตโนมัติจาก path ที่กำหนด:

```yaml
git:
  scan_paths:
    - /Users/yourname/Documents/GitHub  # scan ทุก repos ใน GitHub folder
  scan_depth: 2
```

`scan_depth` คือความลึกของ folder ที่จะค้นหา:
- `depth: 1` = หา repos ที่อยู่ตรงๆ ใน path
- `depth: 2` = ลงไปอีก 1 ชั้น (default)
- `depth: 3` = ลงไปอีก 2 ชั้น

## 📦 Development

```bash
# Run tests
pytest

# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

### Release Process

TalkBut uses a simple AI-assisted release process:

#### Steps to Release

1. **Prepare for release**
   ```bash
   # Make sure all changes are committed
   git status
   ```

2. **Ask AI to help with release**
   
   Simply ask: *"Help me release version X.Y.Z"*
   
   The AI will:
   - Analyze all commits since the last release
   - Generate a comprehensive changelog entry
   - Update version numbers in:
     - `package.json`
     - `setup.py`
     - `pyproject.toml`
   - Update `CHANGELOG.md` with the new entry
   - Create a git commit with message "Release vX.Y.Z"
   - Create an annotated git tag `vX.Y.Z`

3. **Review and push**
   ```bash
   # Review the changes
   git show HEAD
   
   # Push to remote
   git push origin main --tags
   ```

4. **Create GitHub Release (optional)**
   - Go to: https://github.com/YOUR_USERNAME/TalkBut/releases/new
   - Select the tag you just created
   - Copy the changelog entry as release notes
   - Publish release

#### Example Conversation

```
You: "Help me release version 0.3.0"

AI: "I'll help you release version 0.3.0. Let me analyze the commits 
     since v0.2.0..."
     
     [AI analyzes commits and generates changelog]
     
     "I've created the release with the following changes:
     - Updated version to 0.3.0 in all files
     - Added changelog entry with 5 new features and 3 bug fixes
     - Created commit and tag v0.3.0
     
     You can now push with: git push origin main --tags"
```

#### Manual Release (if needed)

If you prefer to do it manually:

```bash
# 1. Update version in package.json, setup.py, pyproject.toml
# 2. Update CHANGELOG.md
# 3. Commit changes
git add package.json setup.py pyproject.toml CHANGELOG.md
git commit -m "Release vX.Y.Z"

# 4. Create tag
git tag -a vX.Y.Z -m "Release version X.Y.Z"

# 5. Push
git push origin main --tags
```

## 🛠️ Tech Stack

Python 3.9+ • Click • GitPython • Google Gemini API

---

Made with ❤️ for developers who want to focus on coding, not reporting.
