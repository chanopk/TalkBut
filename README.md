# TalkBut 🎯

> เครื่องมือเก็บและวิเคราะห์ข้อมูลการทำงานจาก Git สำหรับ Software Developers

TalkBut (ล้อเลียนเสียงคำว่า "ตอกบัตร") เป็น CLI tool ที่ช่วยให้คุณเก็บรวบรวมข้อมูลการทำงานจาก Git commits และใช้ AI ในการวิเคราะห์และสรุปผลงานประจำวัน ทำให้การเขียนรายงานสรุปงานเป็นเรื่องง่ายและรวดเร็ว

## ✨ Features

- ⚡ **Daily Log Generator** - สร้าง JSON log ในคำสั่งเดียว (collect + analyze)
- 🤖 **AI Analysis** - วิเคราะห์และสรุปงานด้วย Google Gemini
- � **Gาit Integration** - ดึงข้อมูล commits, changes, file diffs อัตโนมัติ
- 📝 **รายงานหลากหลายรูปแบบ** - Markdown, JSON, Plain Text
- 💾 **Local Storage** - เก็บข้อมูลปลอดภัยที่เครื่องของคุณ

## 🚀 Quick Start

```bash
# 1. Install
pip install -e .

# 2. ตั้งค่า API key
export GEMINI_API_KEY="your-api-key-here"

# 3. สร้าง daily log (คำสั่งเดียวจบ! บันทึกอัตโนมัติ)
talkbut log
```

## 📖 คำสั่งหลัก

### `talkbut log` - สร้าง Daily Log (แนะนำ) ⭐

คำสั่งหลักที่รวม collect + analyze ในคำสั่งเดียว สร้าง JSON log ที่กระชับ และบันทึกอัตโนมัติ

```bash
# พื้นฐาน - บันทึกอัตโนมัติที่ data/logs/daily_log_YYYY-MM-DD.json
talkbut log

# แสดงผลบนหน้าจอเท่านั้น ไม่บันทึกไฟล์
talkbut log --unsave

# รวม file diffs
talkbut log --include-diffs
```

📚 **[ดูคู่มือฉบับเต็ม →](docs/LOG_COMMAND.md)**

### คำสั่งอื่นๆ

```bash
# เก็บข้อมูลจาก Git
talkbut collect --since "1 week ago"

# วิเคราะห์ด้วย AI
talkbut analyze --date today

# สร้างรายงาน
talkbut report --format markdown --output report.md

# จัดการ config
talkbut config show
```

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
  "categories": {
    "feature": 8,
    "documentation": 3,
    "refactor": 1
  },
  "highlights": [
    "Complete CLI interface with Click framework",
    "AI analysis with Google Gemini API",
    "Multiple output formats support"
  ],
  "commits": [...]
}
```

## 🛠️ Technology Stack

- **Python 3.10+** - Core language
- **Click** - CLI framework
- **GitPython** - Git integration
- **Google Gemini API** - AI analysis

## 📚 เอกสารเพิ่มเติม

- **[คู่มือคำสั่ง `talkbut log`](docs/LOG_COMMAND.md)** - คำสั่งหลักที่ใช้บ่อยที่สุด
- [Architecture MVP](docs/architecture_mvp.md) - ระบบสถาปัตยกรรม
- [Project Idea](idea.txt) - แนวคิดและวิสัยทัศน์

## 🔧 Configuration

```bash
# ตรวจสอบ config
talkbut config check

# สร้าง config file
talkbut config init
```

Config file: `config/config.yaml`

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

## 💡 Use Cases

- **Daily Standup** - สร้าง log สำหรับ standup meeting
- **Personal Work Log** - เก็บบันทึกงานของตัวเอง
- **Code Review** - สร้าง log พร้อม diffs สำหรับ review
- **Weekly Summary** - สรุปงานประจำสัปดาห์
- **Automated Backup** - ตั้ง cron job เก็บ log อัตโนมัติ

## 🎯 Roadmap

**MVP (Current)**
- ✅ Git data collection
- ✅ AI analysis with Gemini
- ✅ Daily log generator
- ✅ CLI interface

**Next Phase**
- [ ] Multiple repository support
- [ ] Custom report templates
- [ ] Integration with Jira/Linear
- [ ] Web dashboard

---

Made with ❤️ for developers who want to focus on coding, not reporting.
