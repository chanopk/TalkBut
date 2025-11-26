# คำสั่ง `talkbut log` - Daily Log Generator

## 📖 ภาพรวม

คำสั่ง `talkbut log` เป็นคำสั่งหลักของ TalkBut ที่รวม `collect` และ `analyze` เข้าด้วยกัน เพื่อสร้าง daily log แบบ JSON ที่กระชับและประหยัดพื้นที่ในคำสั่งเดียว

### ทำไมต้องใช้ `talkbut log`?

- **รวดเร็ว** - ทำงานในคำสั่งเดียว ไม่ต้องรันหลายขั้นตอน
- **กระชับ** - JSON format ที่ประหยัดพื้นที่
- **ครบถ้วน** - มีทั้งข้อมูล commits และการวิเคราะห์ AI
- **ยืดหยุ่น** - ปรับแต่งได้ตามความต้องการ

## ✨ ความสามารถ

✅ **เก็บข้อมูล commits** จาก Git repository  
✅ **วิเคราะห์ด้วย AI** เพื่อสรุปและจัดหมวดหมู่งาน  
✅ **ดึง file diffs** (ถ้าต้องการ) เพื่อดูรายละเอียดการเปลี่ยนแปลง  
✅ **สร้าง JSON log** ที่กระชับและอ่านง่าย  
✅ **ทำงานในคำสั่งเดียว** ไม่ต้องรันหลายขั้นตอน  
✅ **กรองข้อมูล** ตาม author, branch, date range

## 🚀 การใช้งานพื้นฐาน

```bash
# สร้าง daily log แบบ compact (แสดงบนหน้าจอ)
talkbut log

# บันทึกเป็นไฟล์ (แนะนำ)
talkbut log --output daily_log.json

# รวม file diffs ด้วย (ดูรายละเอียดการเปลี่ยนแปลง)
talkbut log --include-diffs --output detailed_log.json

# JSON แบบอ่านง่าย (มี indent)
talkbut log --no-compact --output readable_log.json

# กรองเฉพาะงานของตัวเอง
talkbut log --author "your-email@example.com" --output my_work.json

# เก็บข้อมูลย้อนหลัง 1 สัปดาห์
talkbut log --since "1 week ago" --output weekly_log.json
```

## ⚙️ Options

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--repo` | `-r` | Path to git repository | current directory | `-r /path/to/project` |
| `--since` | `-s` | Start date/time | "1 day ago" | `-s "2025-11-20"` |
| `--until` | `-u` | End date/time | now | `-u "2025-11-25"` |
| `--author` | `-a` | Filter by author email/name | None | `-a "john@example.com"` |
| `--branch` | `-b` | Filter by branch | current branch | `-b main` |
| `--output` | `-o` | Save to file | print to console | `-o daily.json` |
| `--include-diffs` | - | Include file diffs | no | `--include-diffs` |
| `--no-diffs` | - | Exclude file diffs | - | `--no-diffs` |
| `--compact` | - | Use compact JSON | yes | `--compact` |
| `--no-compact` | - | Use readable JSON | - | `--no-compact` |

### รายละเอียด Options

#### `--since` และ `--until`
รองรับหลายรูปแบบ:
- **Relative**: `"1 day ago"`, `"2 weeks ago"`, `"yesterday"`
- **Absolute**: `"2025-11-20"`, `"2025-11-20 14:30"`
- **Git format**: `"@{2.days.ago}"`, `"@{yesterday}"`

#### `--author`
กรองตาม author email หรือชื่อ:
```bash
# ตาม email
talkbut log --author "john@example.com"

# ตามชื่อ (บางส่วนก็ได้)
talkbut log --author "John"
```

#### `--include-diffs` vs `--no-diffs`
- `--include-diffs`: รวม file diffs ทั้งหมด (ไฟล์จะใหญ่มาก)
- `--no-diffs` (default): ไม่รวม diffs (ประหยัดพื้นที่)

#### `--compact` vs `--no-compact`
- `--compact` (default): JSON แบบบรรทัดเดียว ประหยัดพื้นที่
- `--no-compact`: JSON แบบมี indent อ่านง่าย

## 📋 โครงสร้าง Output

### JSON Schema

```json
{
  "date": "string (ISO 8601)",
  "summary": "string (AI-generated summary)",
  "stats": {
    "commits": "number",
    "files": "number",
    "insertions": "number",
    "deletions": "number"
  },
  "categories": {
    "category_name": "number (count)"
  },
  "highlights": ["string"],
  "commits": [
    {
      "hash": "string (short hash)",
      "time": "string (HH:MM)",
      "message": "string (first line only)",
      "files": ["string"],
      "changes": "string (+X/-Y)",
      "tickets": ["string"] (optional),
      "diffs": {"filename": "string"} (optional, if --include-diffs)
    }
  ]
}
```

### ตัวอย่าง Output

#### 1. แบบ Compact (ประหยัดพื้นที่)

```bash
talkbut log --output compact.json
```

```json
{"date":"2025-11-25","summary":"Refactored coach service with improved orchestration","stats":{"commits":1,"files":7,"insertions":35,"deletions":147},"categories":{"refactor":1},"highlights":["Simplified coach orchestrator logic","Updated AI coach simulator"],"commits":[{"hash":"d7911c7","time":"16:48","message":"refactor coach service","files":["README.md","config/coach_settings.json"],"changes":"+35/-147","tickets":[]}]}
```

**ขนาดไฟล์**: ~300-500 bytes ต่อ commit

#### 2. แบบ Readable (อ่านง่าย)

```bash
talkbut log --no-compact --output readable.json
```

```json
{
  "date": "2025-11-25",
  "summary": "Refactored coach service with improved orchestration and updated AI coach simulator",
  "stats": {
    "commits": 1,
    "files": 7,
    "insertions": 35,
    "deletions": 147
  },
  "categories": {
    "refactor": 1
  },
  "highlights": [
    "Simplified coach orchestrator logic",
    "Updated AI coach simulator"
  ],
  "commits": [
    {
      "hash": "d7911c7",
      "time": "16:48",
      "message": "refactor coach service (Reviewed by Chanop K.)",
      "files": [
        "README.md",
        "config/coach_settings.json",
        "libs/ai_components/orchestrators/coach_orchestrator.py",
        "libs/ai_components/personas/ai_coach_simulator.py",
        "libs/ai_components/prompts/coach_prompts.py",
        "libs/services/coach_service.py",
        "libs/shared/models/coach.py"
      ],
      "changes": "+35/-147",
      "tickets": []
    }
  ]
}
```

**ขนาดไฟล์**: ~800-1200 bytes ต่อ commit

#### 3. แบบรวม Diffs (ละเอียดสุด)

```bash
talkbut log --include-diffs --no-compact --output detailed.json
```

```json
{
  "date": "2025-11-25",
  "summary": "...",
  "stats": {...},
  "commits": [
    {
      "hash": "d7911c7",
      "time": "16:48",
      "message": "refactor coach service",
      "files": ["README.md", "config/coach_settings.json"],
      "changes": "+35/-147",
      "diffs": {
        "README.md": "diff --git a/README.md b/README.md\nindex 1234567..abcdefg 100644\n--- a/README.md\n+++ b/README.md\n@@ -1,3 +1,4 @@\n # Project\n+New line added\n...",
        "config/coach_settings.json": "diff --git a/config/coach_settings.json..."
      }
    }
  ]
}
```

**ขนาดไฟล์**: ~5-50 KB ต่อ commit (ขึ้นกับขนาดของ diffs)

## 💼 Use Cases และตัวอย่างการใช้งาน

### 1. Daily Standup Report
สร้าง log สำหรับ standup meeting ทุกเช้า

```bash
# แบบง่าย
talkbut log --since "yesterday" --output standup.json

# แบบมีชื่อไฟล์ตามวันที่
talkbut log --since "yesterday" --output standup-$(date +%Y-%m-%d).json

# แบบอ่านง่าย สำหรับนำเสนอ
talkbut log --since "yesterday" --no-compact --output standup-readable.json
```

**ผลลัพธ์**: ไฟล์ JSON ที่มีสรุปงานเมื่อวาน พร้อม AI summary

### 2. Personal Work Log
เก็บ log งานของตัวเองแยกจากทีม

```bash
# กรองเฉพาะงานของตัวเอง
talkbut log --author "john@example.com" --output my-work.json

# เก็บงานของตัวเองย้อนหลัง 1 สัปดาห์
talkbut log --author "john@example.com" --since "1 week ago" --output my-weekly-work.json

# เก็บงานในช่วงเวลาที่กำหนด
talkbut log --author "john@example.com" \
  --since "2025-11-01" \
  --until "2025-11-30" \
  --output november-work.json
```

**ผลลัพธ์**: ไฟล์ JSON ที่มีเฉพาะ commits ของคุณ

### 3. Code Review Preparation
สร้าง log พร้อม diffs สำหรับ code review

```bash
# รวม diffs ทั้งหมด
talkbut log --include-diffs --no-compact --output review-log.json

# กรองเฉพาะ branch ที่จะ review
talkbut log --branch feature/new-feature \
  --include-diffs \
  --no-compact \
  --output feature-review.json

# รวม diffs และกรองตาม author
talkbut log --author "john@example.com" \
  --include-diffs \
  --since "1 week ago" \
  --output john-review.json
```

**ผลลัพธ์**: ไฟล์ JSON ที่มีรายละเอียดการเปลี่ยนแปลงทั้งหมด

### 4. Weekly Summary
สร้าง log สำหรับสรุปสัปดาห์

```bash
# สรุปสัปดาห์ปัจจุบัน
talkbut log --since "1 week ago" --output weekly-$(date +%Y-W%V).json

# สรุปสัปดาห์ที่แล้ว
talkbut log --since "2 weeks ago" --until "1 week ago" --output last-week.json

# สรุปสัปดาห์แบบละเอียด
talkbut log --since "1 week ago" \
  --no-compact \
  --output weekly-detailed.json
```

**ผลลัพธ์**: ไฟล์ JSON ที่รวมงานทั้งสัปดาห์

### 5. Automated Daily Backup
ตั้ง cron job เพื่อสร้าง log อัตโนมัติทุกวัน

```bash
# เพิ่มใน crontab (crontab -e)
# รันทุกวันเวลา 18:00 น.
0 18 * * * cd /path/to/project && talkbut log --output ~/logs/daily-$(date +\%Y-\%m-\%d).json

# หรือใช้ script
#!/bin/bash
# save-daily-log.sh
cd /path/to/project
talkbut log --output ~/logs/daily-$(date +%Y-%m-%d).json
echo "Daily log saved at $(date)"
```

**ผลลัพธ์**: ไฟล์ JSON ใหม่ทุกวันใน `~/logs/`

### 6. Team Report
สร้างรายงานสำหรับทีม

```bash
# รายงานทั้งทีม
talkbut log --since "1 day ago" --output team-daily.json

# รายงานแต่ละคน
for email in john@example.com jane@example.com; do
  talkbut log --author "$email" --output "logs/$(echo $email | cut -d@ -f1).json"
done
```

### 7. Sprint Summary
สรุปงานในแต่ละ sprint

```bash
# Sprint 2 สัปดาห์
talkbut log --since "2 weeks ago" --output sprint-summary.json

# Sprint ที่กำหนดวันเริ่มต้น-สิ้นสุด
talkbut log --since "2025-11-01" \
  --until "2025-11-14" \
  --output sprint-1.json
```

### 8. Monthly Report
สรุปงานประจำเดือน

```bash
# เดือนปัจจุบัน
talkbut log --since "$(date +%Y-%m-01)" --output monthly-$(date +%Y-%m).json

# เดือนที่แล้ว
talkbut log --since "$(date -d 'last month' +%Y-%m-01)" \
  --until "$(date +%Y-%m-01)" \
  --output monthly-$(date -d 'last month' +%Y-%m).json
```

## 🎯 ข้อดีของ JSON Format

### 1. ประหยัดพื้นที่
- **Compact mode**: ~300-500 bytes ต่อ commit
- **Readable mode**: ~800-1200 bytes ต่อ commit
- เหมาะสำหรับเก็บ log ระยะยาว

### 2. ง่ายต่อการ Parse
```python
import json

# อ่านและประมวลผล
with open('daily.json') as f:
    data = json.load(f)
    print(f"Total commits: {data['stats']['commits']}")
    print(f"Summary: {data['summary']}")
```

```javascript
// ใช้ใน JavaScript/Node.js
const data = require('./daily.json');
console.log(`Total commits: ${data.stats.commits}`);
```

### 3. รองรับ Unicode
- แสดงภาษาไทยได้ถูกต้อง
- รองรับ emoji และ special characters
- ไม่มีปัญหา encoding

### 4. Structured Data
- มีโครงสร้างชัดเจน
- ง่ายต่อการ validate
- สามารถใช้ JSON Schema ได้

### 5. Machine Readable
- เหมาะสำหรับ automation
- ใช้กับ CI/CD pipeline ได้
- ง่ายต่อการ integrate กับระบบอื่น

### 6. ตัวอย่างการใช้งาน

#### วิเคราะห์ข้อมูล
```python
import json
from collections import Counter

# รวม categories จากหลายวัน
categories = Counter()
for file in ['day1.json', 'day2.json', 'day3.json']:
    with open(file) as f:
        data = json.load(f)
        categories.update(data['categories'])

print("Top categories:", categories.most_common(3))
```

#### สร้างรายงาน
```python
import json

with open('daily.json') as f:
    data = json.load(f)

# สร้าง Markdown report
print(f"# Daily Report: {data['date']}")
print(f"\n## Summary\n{data['summary']}")
print(f"\n## Stats")
print(f"- Commits: {data['stats']['commits']}")
print(f"- Files: {data['stats']['files']}")
```

#### ส่งไปยัง API
```python
import json
import requests

with open('daily.json') as f:
    data = json.load(f)

# ส่งไปยัง webhook
requests.post('https://api.example.com/logs', json=data)
```

## เปรียบเทียบกับคำสั่งอื่น

| Feature | `talkbut log` | `talkbut collect` + `talkbut analyze` |
|---------|---------------|---------------------------------------|
| จำนวนคำสั่ง | 1 | 2 |
| รวม AI analysis | ✅ | ✅ |
| รวม file diffs | ✅ | ✅ |
| Output format | JSON | Cache + Report |
| ความเร็ว | เร็ว | ช้ากว่า |
| ประหยัดพื้นที่ | ✅ | ❌ |

## 💡 Tips และ Best Practices

### 1. เลือก Format ให้เหมาะสม

```bash
# Compact - สำหรับ backup ระยะยาว
talkbut log --compact --output backup.json

# Readable - สำหรับอ่านและ review
talkbut log --no-compact --output review.json

# With diffs - สำหรับ code review
talkbut log --include-diffs --no-compact --output code-review.json
```

### 2. ตั้งชื่อไฟล์ให้มีระบบ

```bash
# ตามวันที่
talkbut log --output daily-$(date +%Y-%m-%d).json

# ตามสัปดาห์
talkbut log --since "1 week ago" --output weekly-$(date +%Y-W%V).json

# ตามเดือน
talkbut log --since "$(date +%Y-%m-01)" --output monthly-$(date +%Y-%m).json

# ตาม author
talkbut log --author "john@example.com" --output john-$(date +%Y-%m-%d).json
```

### 3. ใช้ Automation

```bash
# สร้าง script สำหรับ daily backup
cat > ~/bin/talkbut-daily.sh << 'EOF'
#!/bin/bash
LOG_DIR=~/work-logs
mkdir -p $LOG_DIR
cd /path/to/your/project
talkbut log --output $LOG_DIR/daily-$(date +%Y-%m-%d).json
echo "Daily log saved: $(date)"
EOF

chmod +x ~/bin/talkbut-daily.sh

# เพิ่มใน crontab
crontab -e
# เพิ่มบรรทัดนี้: รันทุกวันเวลา 18:00
0 18 * * * ~/bin/talkbut-daily.sh >> ~/work-logs/cron.log 2>&1
```

### 4. กรองข้อมูลให้เหมาะสม

```bash
# เฉพาะงานของตัวเอง
talkbut log --author "$(git config user.email)" --output my-work.json

# เฉพาะ branch ปัจจุบัน
talkbut log --branch "$(git branch --show-current)" --output current-branch.json

# เฉพาะช่วงเวลาที่กำหนด
talkbut log --since "2025-11-01" --until "2025-11-30" --output november.json
```

### 5. จัดเก็บ Logs อย่างเป็นระบบ

```bash
# สร้างโครงสร้างโฟลเดอร์
mkdir -p ~/work-logs/{daily,weekly,monthly}

# Daily logs
talkbut log --output ~/work-logs/daily/$(date +%Y-%m-%d).json

# Weekly logs (ทุกวันศุกร์)
talkbut log --since "1 week ago" --output ~/work-logs/weekly/$(date +%Y-W%V).json

# Monthly logs (วันสุดท้ายของเดือน)
talkbut log --since "$(date +%Y-%m-01)" --output ~/work-logs/monthly/$(date +%Y-%m).json
```

### 6. ใช้ Git Aliases

```bash
# เพิ่มใน ~/.gitconfig
[alias]
    daily-log = !talkbut log --output ~/work-logs/daily-$(date +%Y-%m-%d).json
    weekly-log = !talkbut log --since "1 week ago" --output ~/work-logs/weekly-$(date +%Y-W%V).json
    my-log = !talkbut log --author "$(git config user.email)" --output my-work.json

# ใช้งาน
git daily-log
git weekly-log
git my-log
```

### 7. Backup และ Archive

```bash
# Backup logs ทุกสัปดาห์
tar -czf ~/backups/work-logs-$(date +%Y-W%V).tar.gz ~/work-logs/daily/*.json

# ลบ logs เก่าที่เกิน 90 วัน
find ~/work-logs/daily -name "*.json" -mtime +90 -delete
```

### 8. Integration กับ Tools อื่น

```bash
# ส่งไปยัง Slack
talkbut log | jq -r '.summary' | slack-cli send "#daily-updates"

# ส่งไปยัง Email
talkbut log --no-compact | mail -s "Daily Work Log" manager@example.com

# Upload ไปยัง Cloud Storage
talkbut log --output /tmp/daily.json && \
  aws s3 cp /tmp/daily.json s3://my-bucket/logs/$(date +%Y-%m-%d).json
```

## 🔧 Troubleshooting

### ปัญหา: AI analysis ล้มเหลว

**อาการ**: Error message เกี่ยวกับ AI API

```bash
# 1. ตรวจสอบ API key
talkbut config check

# 2. ตรวจสอบว่าตั้งค่า API key แล้วหรือยัง
echo $GEMINI_API_KEY

# 3. ตั้งค่า API key
export GEMINI_API_KEY="your-api-key-here"

# 4. หรือเพิ่มใน ~/.zshrc หรือ ~/.bashrc
echo 'export GEMINI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc

# 5. ลองรันอีกครั้ง
talkbut log --output test.json
```

### ปัญหา: ไม่มี commits

**อาการ**: "No commits found in the specified range"

```bash
# 1. ตรวจสอบว่ามี commits ใน range ที่กำหนด
git log --since "1 day ago" --oneline

# 2. ลองเปลี่ยน date range
talkbut log --since "1 week ago"

# 3. ตรวจสอบ author filter
git log --author "your-email" --oneline

# 4. ตรวจสอบ branch
git branch --show-current
git log --oneline

# 5. ลองไม่ใส่ filter
talkbut log --since "1 month ago" --output test.json
```

### ปัญหา: File diffs ใหญ่เกินไป

**อาการ**: ไฟล์ JSON ใหญ่มาก (> 10 MB)

```bash
# 1. ใช้แบบไม่รวม diffs (แนะนำ)
talkbut log --no-diffs --output log.json

# 2. กรองเฉพาะช่วงเวลาสั้นๆ
talkbut log --since "1 day ago" --include-diffs --output log.json

# 3. กรองเฉพาะ author
talkbut log --author "your-email" --include-diffs --output log.json

# 4. ตรวจสอบขนาดไฟล์ก่อน
talkbut log --include-diffs | wc -c
```

### ปัญหา: Repository path ไม่ถูกต้อง

**อาการ**: "Not a git repository"

```bash
# 1. ตรวจสอบว่าอยู่ใน git repository
git status

# 2. ระบุ path ชัดเจน
talkbut log --repo /path/to/your/project --output log.json

# 3. ตรวจสอบ config
talkbut config show

# 4. แก้ไข config
talkbut config init
```

### ปัญหา: Permission denied

**อาการ**: ไม่สามารถเขียนไฟล์ได้

```bash
# 1. ตรวจสอบ permission ของโฟลเดอร์
ls -la ~/work-logs

# 2. สร้างโฟลเดอร์ถ้ายังไม่มี
mkdir -p ~/work-logs

# 3. ตรวจสอบว่าเขียนไฟล์ได้
touch ~/work-logs/test.json && rm ~/work-logs/test.json

# 4. ใช้ path อื่น
talkbut log --output /tmp/log.json
```

### ปัญหา: JSON parsing error

**อาการ**: ไฟล์ JSON ไม่ valid

```bash
# 1. ตรวจสอบ JSON
cat log.json | jq .

# 2. ลองสร้างใหม่
talkbut log --output log-new.json

# 3. ใช้ --no-compact เพื่อดู format
talkbut log --no-compact --output log-readable.json
```

### ปัญหา: Slow performance

**อาการ**: คำสั่งช้ามาก

```bash
# 1. ลดช่วงเวลา
talkbut log --since "1 day ago" --output log.json

# 2. ไม่รวม diffs
talkbut log --no-diffs --output log.json

# 3. กรองเฉพาะ author
talkbut log --author "your-email" --output log.json

# 4. ตรวจสอบจำนวน commits
git log --since "1 day ago" --oneline | wc -l
```

### ปัญหา: Unicode/Thai characters แสดงผิด

**อาการ**: ภาษาไทยแสดงเป็น \uXXXX

```bash
# 1. ใช้ --no-compact
talkbut log --no-compact --output log.json

# 2. ตรวจสอบ encoding
file log.json

# 3. อ่านด้วย jq
cat log.json | jq -r '.summary'

# 4. ตั้งค่า locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### ขอความช่วยเหลือ

หากยังแก้ปัญหาไม่ได้:

1. ตรวจสอบ logs: `~/.talkbut/logs/`
2. รัน debug mode: `talkbut --debug log`
3. ดู version: `talkbut --version`
4. เปิด issue ที่ GitHub repository

## 🔄 เปรียบเทียบกับคำสั่งอื่น

### `talkbut log` vs `talkbut collect` + `talkbut analyze`

| Feature | `talkbut log` | `collect` + `analyze` |
|---------|---------------|----------------------|
| **จำนวนคำสั่ง** | 1 คำสั่ง | 2 คำสั่ง |
| **ความเร็ว** | เร็ว | ช้ากว่า |
| **Output** | JSON file | Cache + Report |
| **AI Analysis** | ✅ รวมอยู่ | ✅ แยกขั้นตอน |
| **File Diffs** | ✅ Optional | ✅ Optional |
| **ประหยัดพื้นที่** | ✅ Compact JSON | ❌ Cache files |
| **Automation** | ✅ เหมาะมาก | ⚠️ ต้องรัน 2 ครั้ง |
| **Use Case** | Daily log, Backup | Development, Testing |

### เมื่อไหร่ควรใช้อะไร?

#### ใช้ `talkbut log` เมื่อ:
- ต้องการ daily log แบบรวดเร็ว
- ต้องการ JSON output ที่กระชับ
- ต้องการ automation (cron job)
- ต้องการประหยัดพื้นที่
- ต้องการส่งข้อมูลไปยังระบบอื่น

#### ใช้ `collect` + `analyze` เมื่อ:
- กำลัง develop/test features
- ต้องการ cache ข้อมูลไว้ใช้ซ้ำ
- ต้องการ report หลายรูปแบบ (Markdown, Text)
- ต้องการควบคุมแต่ละขั้นตอน

### ตัวอย่างการใช้งาน

```bash
# Scenario 1: Daily standup (ใช้ log)
talkbut log --since "yesterday" --output standup.json

# Scenario 2: Development (ใช้ collect + analyze)
talkbut collect --since "1 week ago" --include-diffs
talkbut analyze --date today
talkbut report --format markdown --output report.md

# Scenario 3: Automation (ใช้ log)
# crontab: 0 18 * * * talkbut log --output ~/logs/daily-$(date +\%Y-\%m-\%d).json

# Scenario 4: Code review (ใช้ log)
talkbut log --include-diffs --no-compact --output review.json
```

## 📚 เอกสารเพิ่มเติม

- [README.md](../README.md) - ภาพรวมโปรเจกต์
- [Architecture MVP](architecture_mvp.md) - สถาปัตยกรรมระบบ
- [Project Idea](../idea.txt) - แนวคิดและวิสัยทัศน์

## 🎓 สรุป

คำสั่ง `talkbut log` เป็นคำสั่งหลักที่ออกแบบมาเพื่อความรวดเร็วและความสะดวก:

- **ใช้งานง่าย** - คำสั่งเดียวจบ
- **ยืดหยุ่น** - ปรับแต่งได้หลากหลาย
- **ประหยัด** - JSON format ที่กระชับ
- **ครบถ้วน** - มีทั้งข้อมูลและการวิเคราะห์
- **เหมาะสำหรับ automation** - ใช้กับ cron job ได้ดี

เริ่มต้นใช้งานได้ง่ายๆ:

```bash
# ติดตั้ง
pip install -e .

# ตั้งค่า API key
export GEMINI_API_KEY="your-key"

# สร้าง daily log
talkbut log --output daily.json
```

Happy logging! 🎯
