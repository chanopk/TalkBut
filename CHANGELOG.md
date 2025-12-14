# Changelog

## [0.2.0] - 2025-12-08

### ✨ New Features

#### ⏰ Automated Scheduling (`talkbut schedule`)
- **Daily Auto-logging**: ตั้งเวลาให้สร้าง daily log อัตโนมัติทุกวัน
- **Cross-platform Support**: รองรับ cron (macOS/Linux) และ Task Scheduler (Windows)
- **Schedule Management**: 
  - `talkbut schedule enable --time 18:00` - เปิดใช้งาน
  - `talkbut schedule status` - ตรวจสอบสถานะ
  - `talkbut schedule disable` - ปิดใช้งาน
- **Status Tracking**: ติดตามการรันล่าสุด, รันถัดไป, และ error history

#### ⚡ Fast Mode (`--fast`)
- **Direct Commit Analysis**: ดึง commits โดยตรงและวิเคราะห์ด้วย AI ในครั้งเดียว
- **Long Period Support**: สร้างรายงานช่วงยาวได้โดยไม่ต้องพึ่ง daily logs
- **Usage Examples**:
  - `talkbut report --fast "1 month"` - รายงาน 1 เดือนย้อนหลัง
  - `talkbut report --fast "3 months"` - รายงาน 3 เดือนย้อนหลัง
- **Cost Efficient**: ประหยัด API calls โดยยิง AI ครั้งเดียวแทนหลายครั้ง

#### 📅 Year-to-Date Mode (`--fast "YTD"`)
- **Annual Overview**: สรุปผลงานตั้งแต่ต้นปีจนถึงปัจจุบัน
- **Monthly Breakdown**: แบ่งวิเคราะห์ทีละเดือนเพื่อหลีกเลี่ยง timeout
- **Comprehensive Report**: รวมสถิติรวม, highlights รายเดือน, และ themes หลัก
- **Smart Processing**: จัดการข้อมูลขนาดใหญ่อย่างมีประสิทธิภาพ

### 🔧 Improvements

#### 🏗️ Architecture Enhancement
- **Modular Design**: ปรับโครงสร้างเป็น modules แยกหน้าที่ชัดเจน
- **Scheduling System**: เพิ่ม `src/talkbut/scheduling/` สำหรับ automation
- **Better Error Handling**: ปรับปรุงการจัดการ errors และ logging

#### 🧪 Testing Framework
- **Property-Based Testing**: เพิ่ม comprehensive test suite ด้วย Hypothesis
- **12 Test Modules**: ครอบคลุมทุกฟีเจอร์หลัก (scheduling, batch processing, validation)
- **Quality Assurance**: ป้องกัน regressions และเพิ่มความมั่นใจในโค้ด

#### 🛠️ Developer Tools
- **Poetry Support**: รองรับ Poetry package manager
- **Code Quality**: Black, Ruff, MyPy, pytest-cov
- **Better Documentation**: เพิ่ม docstrings และ inline comments

### 🚀 Usage Examples

```bash
# ตั้งเวลาสร้าง log อัตโนมัติ
talkbut schedule enable --time 18:00

# สร้างรายงานแบบเร็ว (ประหยัด API)
talkbut report --fast "1 month"

# รายงานสรุปทั้งปี
talkbut report --fast "YTD"

# ตรวจสอบสถานะ schedule
talkbut schedule status
```

---

**Breaking Changes**: ไม่มี - backward compatible กับ v0.1.0

**Full Changelog**: https://github.com/chanopk/TalkBut/compare/v0.1.0...v0.2.0

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