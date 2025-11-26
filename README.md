# TalkBut 🎯

> เครื่องมือสร้าง Daily Work Log จาก Git commits ด้วย AI

TalkBut (ล้อเลียนเสียงคำว่า "ตอกบัตร") เป็น CLI tool ที่ช่วยสร้างรายงานสรุปงานประจำวันจาก Git commits โดยใช้ AI วิเคราะห์และสรุปผลงานให้อัตโนมัติ

## ✨ Features

- ⚡ สร้าง daily log ในคำสั่งเดียว
- 🤖 วิเคราะห์และสรุปงานด้วย Google Gemini AI
- 📊 ดึงข้อมูลจาก Git commits อัตโนมัติ
- 📝 Export เป็น JSON, Markdown, Plain Text
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

# Create daily log
talkbut log
```

ผลลัพธ์จะถูกบันทึกที่ `data/logs/daily_log_YYYY-MM-DD.json`

## 📖 Usage

### สร้าง Daily Log

```bash
# สร้าง log วันนี้
talkbut log

# แสดงผลอย่างเดียว ไม่บันทึก
talkbut log --unsave

# ไม่อ่าน diffs อ่านแค่  commits
talkbut log --no-diffs
```

### Export รายงาน

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
  repositories:
    - path: /path/to/your/project
      name: "Project Name"

ai:
  provider: gemini
  api_key_env: GEMINI_API_KEY
  model: gemini-2.0-flash-exp
```

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

## 🛠️ Tech Stack

Python 3.9+ • Click • GitPython • Google Gemini API

---

Made with ❤️ for developers who want to focus on coding, not reporting.
