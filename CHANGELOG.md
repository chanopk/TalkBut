# Changelog


## [0.2.0] - 2025-12-08

### ✨ Features
- Automated release process with version management
- Property-based testing for core functionality
- Comprehensive test suite with unit and property tests

### 🔧 Improvements
- Enhanced error handling and logging
- Improved code organization and documentation

### 📚 Documentation
- Added release process documentation
- Updated README with release instructions

## [0.1.0] - 2025-12-02

### 🎉 MVP Release

TalkBut v0.1.0 เป็น MVP (Minimum Viable Product) แรกที่พร้อมใช้งาน!

### ✨ Features

#### Core Functionality
- **Daily Work Log Generation**: สร้างรายงานสรุปงานประจำวันจาก Git commits อัตโนมัติ
- **AI-Powered Analysis**: ใช้ Google Gemini AI วิเคราะห์และสรุปผลงานอย่าง intelligent
- **Auto Repository Scanner**: สแกนหา Git repositories อัตโนมัติจาก path ที่กำหนด

#### CLI Commands
- `talkbut log`: สร้าง daily log พร้อม options ต่างๆ
  - `--since`: กำหนดช่วงเวลา (เช่น "7 days ago", "1 week ago")
  - `--author`: กรอง commits ตาม author
  - `--unsave`: แสดงผลอย่างเดียวไม่บันทึก
  - `--no-diffs`: ไม่อ่าน code diffs เพื่อความเร็ว
- `talkbut config`: จัดการ configuration
  - `init`: สร้าง config เริ่มต้น
  - `show`: แสดง config ปัจจุบัน
  - `check`: ตรวจสอบความถูกต้องของ config
- `talkbut report`: Export รายงานเป็น Markdown format

#### Data Collection
- **Git Integration**: ดึงข้อมูล commits, diffs, และ statistics จาก Git
- **Multi-Repository Support**: รองรับหลาย repositories พร้อมกัน
- **Flexible Time Ranges**: กำหนดช่วงเวลาได้อย่างยืดหยุ่น
- **Author Filtering**: กรอง commits ตาม author email หรือชื่อ

#### Storage & Export
- **JSON Storage**: บันทึกข้อมูลเป็น JSON ที่ `data/logs/`
- **Markdown Export**: Export รายงานเป็น Markdown format ด้วยคำสั่ง `talkbut report`
- **Local Storage**: เก็บข้อมูลปลอดภัยที่เครื่องของคุณ

#### Configuration
- **YAML Configuration**: ใช้ `config/config.yaml` สำหรับตั้งค่า
- **Flexible Setup**: รองรับทั้งการระบุ repos ตรงๆ และ auto-scan
- **Customizable Prompts**: ปรับแต่ง AI prompts ได้ที่ `config/prompts/`

### 🛠️ Technical Stack
- Python 3.9+
- Click (CLI framework)
- GitPython (Git integration)
- Google Gemini API (AI analysis)
- PyYAML (Configuration)

### 📦 Installation
```bash
pip install -e .
```

### 🚀 Quick Start
```bash
# Initialize config
talkbut config init

# Edit config/config.yaml with your settings

# Create daily log
talkbut log
```

### 📝 Notes
- ต้องมี Google Gemini API key (ฟรี)
- รองรับ Python 3.9 ขึ้นไป
- ทำงานบน macOS, Linux, และ Windows

### 🔮 Coming Soon
- Enhanced report generation
- More export formats
- Weekly/Monthly summaries
- Team collaboration features
- Custom templates

---

**Full Changelog**: https://github.com/chanopk/TalkBut/commits/v0.1.0
