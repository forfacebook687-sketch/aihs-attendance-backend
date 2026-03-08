import os
import json
import base64
import httpx
from datetime import date, datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Date, Boolean, Text, Float, ForeignKey, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

# ─── Database Setup ───────────────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./aihs.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ─── Models ───────────────────────────────────────────────────────────────────
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    roll_number = Column(String, unique=True, index=True)
    name = Column(String)
    gender = Column(String)
    is_active = Column(Boolean, default=True)

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    is_active = Column(Boolean, default=True)

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    name = Column(String)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    teacher = relationship("Teacher")

class TimetableSlot(Base):
    __tablename__ = "timetable_slots"
    id = Column(Integer, primary_key=True)
    timetable_type = Column(String)  # 'regular' or 'ramadan'
    day_of_week = Column(Integer)    # 0=Mon, 4=Fri
    start_time = Column(String)
    end_time = Column(String)
    subject_code = Column(String, nullable=True)  # null = LIBRARY/BREAK/SPORTS
    label = Column(String)           # display label

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject_code = Column(String)
    date = Column(Date)
    status = Column(String)  # 'P' or 'A'
    student = relationship("Student")

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String)

# ─── Create Tables ────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─── Seed Data ────────────────────────────────────────────────────────────────
STUDENTS = [
    ("PDS23001","ABDUL REHMAN","M"),("PDS23002","ABDUL HADI","M"),("PDS23003","SAKIA KANWAL","F"),
    ("PDS23004","MADIHA BEGUM","F"),("PDS23005","ISMA KHAN","F"),("PDS23006","AIMEN WAJID","F"),
    ("PDS23007","AROOJ IMRAN","F"),("PDS23008","AREEBA SABIR","F"),("PDS23009","SHEHRYAR NAZIR","M"),
    ("PDS23010","SAKHAWAT ALI","M"),("PDS23011","ZARRAR HAIDER","M"),("PDS23012","YASMEEN QAISER","F"),
    ("PDS23013","IQRA KIRAN","F"),("PDS23014","LAIBA AYAZ","F"),("PDS23015","SHANAB AHMED","M"),
    ("PDS23016","UBAID-ULLAH","M"),("PDS23017","MUHAMMAD UMAR","M"),("PDS23018","IQRA IBRAHIM","F"),
    ("PDS24019","AZKA WAHID","F"),("PDS24020","MUHAMMAD HUZAIFA MALIK","M"),("PDS24021","FARRUKH HUSSAIN SHAH","M"),
    ("PDS24022","SAMEER AHMAD KHAN","M"),("PDS24023","NIMRA YASIN","F"),("PDS24024","AREESHA KAINAT","F"),
    ("PDS24025","KAINAT","F"),("PDS24026","GUL-E-SEHAR","F"),("PDS24027","SANA FAREED","F"),
    ("PDS24028","ANSA SAMEER","F"),("PDS24029","EHTISHAM ALI","M"),("PDS24030","IQRA MUBEEN","F"),
    ("PDS24031","NAZIA PARVEEN","F"),("PDS24032","ALISHBA SHAKIR","F"),("PDS24033","MUHAMMAD TARIQ","M"),
    ("PDS24034","SAWAIRA BEGUM","F"),("PDS24035","SEHRISH NADEEM","F"),("PDS24036","AYESHA NAVEED","F"),
    ("PDS24037","SHAHID KHAN","M"),("PDS24038","SAFINA NISAR","F"),("PDS24039","MUHAMMAD UMER MOBEEN","M"),
    ("PDS24040","FATIMA JAVERIA HASHMI","F"),("PDS24041","NIMRA HAIDER","F"),("PDS24042","KHADIJA BIBI","F"),
    ("PDS24043","MUHAMMAD HASSAM HAMEED KHAN","M"),("PDS24044","TEHREEM ASIM","F")
]

TEACHERS = [
    "Miss Ushna Ejaz", "Miss Khadija Ijaz", "Miss Sabina Nazish",
    "Mr. Anwar ul Mehmood", "Mr. Muhammad Farooq"
]

SUBJECTS = [
    ("PHARM2-THR", "Pharmaceutics-II A (Dosage Form Science-1) Theory", "Miss Ushna Ejaz"),
    ("PHARM2-LAB", "Pharmaceutics-II A Lab", "Miss Ushna Ejaz"),
    ("MICRO-THR",  "Microbiology & Immunology Theory", "Miss Khadija Ijaz"),
    ("MICRO-LAB",  "Microbiology & Immunology Lab", "Miss Khadija Ijaz"),
    ("PHARM-THR",  "Pharmacology & Therapeutics-I A Theory", "Miss Khadija Ijaz"),
    ("PHARM-LAB",  "Pharmacology & Therapeutics-I A Lab", "Miss Khadija Ijaz"),
    ("PHCOG-THR",  "Pharmacognosy-I A Theory", "Miss Sabina Nazish"),
    ("PHCOG-LAB",  "Pharmacognosy-I A Lab", "Miss Sabina Nazish"),
    ("PHARMATH",   "Pharmaceutical Mathematics", "Mr. Anwar ul Mehmood"),
    ("ISLM",       "Islamic Studies", "Mr. Muhammad Farooq"),
]

# Regular Timetable: 0=Mon,1=Tue,2=Wed,3=Thu,4=Fri
REGULAR_SLOTS = [
    # Monday
    (0,"08:50","10:15",None,"LIBRARY"),
    (0,"10:15","11:40","PHARM-THR","Pharmacology & Therapeutics-I A Theory"),
    (0,"11:40","12:10",None,"BREAK"),
    (0,"12:10","13:35","MICRO-THR","Microbiology & Immunology Theory"),
    (0,"13:35","15:00","PHARMATH","Pharmaceutical Mathematics"),
    # Tuesday
    (1,"08:50","10:15","PHARM2-THR","Pharmaceutics-II A Theory"),
    (1,"10:15","11:40","PHARM-THR","Pharmacology & Therapeutics-I A Theory"),
    (1,"11:40","12:10",None,"BREAK"),
    (1,"12:10","13:35","PHCOG-THR","Pharmacognosy-I A Theory"),
    (1,"13:35","15:00","PHARMATH","Pharmaceutical Mathematics"),
    # Wednesday
    (2,"08:50","10:15","MICRO-LAB","Microbiology & Immunology Lab"),
    (2,"10:15","11:40","PHCOG-THR","Pharmacognosy-I A Theory"),
    (2,"11:40","12:10",None,"BREAK"),
    (2,"12:10","13:35","PHARM-LAB","Pharmacology & Therapeutics-I A Lab"),
    (2,"13:35","15:00","ISLM","Islamic Studies"),
    # Thursday
    (3,"08:50","10:15","MICRO-THR","Microbiology & Immunology Theory"),
    (3,"10:15","11:40","PHARM2-THR","Pharmaceutics-II A Theory"),
    (3,"11:40","12:10",None,"BREAK"),
    (3,"12:10","13:35",None,"SPORTS"),
    (3,"13:35","15:00","ISLM","Islamic Studies"),
    # Friday
    (4,"08:50","10:15","PHARM2-LAB","Pharmaceutics-II A Lab"),
    (4,"10:15","11:40","PHCOG-LAB","Pharmacognosy-I A Lab"),
    (4,"11:40","12:10",None,"BREAK"),
    (4,"12:10","13:35",None,"LIBRARY"),
    (4,"13:35","15:00",None,"JUMA BREAK"),
]

RAMADAN_SLOTS = [
    # Monday
    (0,"09:00","10:00",None,"LIBRARY"),
    (0,"10:00","11:00","PHARM-THR","Pharmacology & Therapeutics-I A Theory"),
    (0,"11:00","11:30",None,"BREAK"),
    (0,"11:30","12:30","MICRO-THR","Microbiology & Immunology Theory"),
    (0,"12:30","13:30","PHARMATH","Pharmaceutical Mathematics"),
    # Tuesday
    (1,"09:00","10:00","PHARM2-THR","Pharmaceutics-II A Theory"),
    (1,"10:00","11:00","PHARM-THR","Pharmacology & Therapeutics-I A Theory"),
    (1,"11:00","11:30",None,"BREAK"),
    (1,"11:30","12:30","PHCOG-THR","Pharmacognosy-I A Theory"),
    (1,"12:30","13:30","PHARMATH","Pharmaceutical Mathematics"),
    # Wednesday
    (2,"09:00","10:00","MICRO-LAB","Microbiology & Immunology Lab"),
    (2,"10:00","11:00","PHCOG-THR","Pharmacognosy-I A Theory"),
    (2,"11:00","11:30",None,"BREAK"),
    (2,"11:30","12:30","PHARM-LAB","Pharmacology & Therapeutics-I A Lab"),
    (2,"12:30","13:30","ISLM","Islamic Studies"),
    # Thursday
    (3,"09:00","10:00","MICRO-THR","Microbiology & Immunology Theory"),
    (3,"10:00","11:00","PHARM2-THR","Pharmaceutics-II A Theory"),
    (3,"11:00","11:30",None,"BREAK"),
    (3,"11:30","12:30",None,"SPORTS"),
    (3,"12:30","13:30","ISLM","Islamic Studies"),
    # Friday
    (4,"09:00","10:00","PHARM2-LAB","Pharmaceutics-II A Lab"),
    (4,"10:00","11:00","PHCOG-LAB","Pharmacognosy-I A Lab"),
    (4,"11:00","11:30",None,"BREAK"),
    (4,"11:30","12:30",None,"LIBRARY"),
    (4,"12:30","13:30",None,"JUMA BREAK"),
]

def seed_database(db: Session):
    if db.query(Student).count() > 0:
        return
    # Teachers
    teacher_map = {}
    for name in TEACHERS:
        t = Teacher(name=name, is_active=True)
        db.add(t)
        db.flush()
        teacher_map[name] = t.id
    # Subjects
    for code, name, teacher_name in SUBJECTS:
        s = Subject(code=code, name=name, teacher_id=teacher_map[teacher_name])
        db.add(s)
    # Students
    for roll, name, gender in STUDENTS:
        db.add(Student(roll_number=roll, name=name, gender=gender))
    # Timetable
    for day, start, end, code, label in REGULAR_SLOTS:
        db.add(TimetableSlot(timetable_type="regular", day_of_week=day, start_time=start, end_time=end, subject_code=code, label=label))
    for day, start, end, code, label in RAMADAN_SLOTS:
        db.add(TimetableSlot(timetable_type="ramadan", day_of_week=day, start_time=start, end_time=end, subject_code=code, label=label))
    # Default setting
    db.add(Setting(key="active_timetable", value="regular"))
    db.add(Setting(key="openrouter_api_key", value=""))
    db.commit()

# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="AIHS Attendance API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    db = SessionLocal()
    seed_database(db)
    db.close()

# ─── Pydantic Schemas ─────────────────────────────────────────────────────────
class AttendanceSubmit(BaseModel):
    subject_code: str
    date: str
    records: dict  # {roll_number: 'P' or 'A'}

class TeacherCreate(BaseModel):
    name: str

class SubjectUpdate(BaseModel):
    teacher_id: int

class TimetableSlotUpdate(BaseModel):
    label: str
    subject_code: Optional[str] = None
    start_time: str
    end_time: str

class SettingUpdate(BaseModel):
    value: str

class ScanRequest(BaseModel):
    image_base64: str
    subject_code: str
    date: str

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "AIHS Attendance API running"}

# Students
@app.get("/students")
def get_students(db: Session = Depends(get_db)):
    return db.query(Student).filter(Student.is_active == True).all()

# Subjects
@app.get("/subjects")
def get_subjects(db: Session = Depends(get_db)):
    subjects = db.query(Subject).all()
    result = []
    for s in subjects:
        teacher = db.query(Teacher).filter(Teacher.id == s.teacher_id).first()
        result.append({
            "id": s.id, "code": s.code, "name": s.name,
            "teacher_id": s.teacher_id,
            "teacher_name": teacher.name if teacher else "Unassigned"
        })
    return result

# Teachers
@app.get("/teachers")
def get_teachers(db: Session = Depends(get_db)):
    return db.query(Teacher).all()

@app.post("/teachers")
def add_teacher(data: TeacherCreate, db: Session = Depends(get_db)):
    t = Teacher(name=data.name, is_active=True)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t

@app.put("/teachers/{teacher_id}/deactivate")
def deactivate_teacher(teacher_id: int, db: Session = Depends(get_db)):
    t = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not t:
        raise HTTPException(404, "Teacher not found")
    t.is_active = False
    db.commit()
    return {"message": f"{t.name} deactivated. Past records preserved."}

@app.put("/subjects/{subject_code}/teacher")
def reassign_teacher(subject_code: str, data: SubjectUpdate, db: Session = Depends(get_db)):
    s = db.query(Subject).filter(Subject.code == subject_code).first()
    if not s:
        raise HTTPException(404, "Subject not found")
    s.teacher_id = data.teacher_id
    db.commit()
    return {"message": "Teacher reassigned"}

# Timetable
@app.get("/timetable")
def get_timetable(db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.key == "active_timetable").first()
    active = setting.value if setting else "regular"
    slots = db.query(TimetableSlot).filter(TimetableSlot.timetable_type == active).order_by(TimetableSlot.day_of_week, TimetableSlot.start_time).all()
    return {"active_timetable": active, "slots": slots}

@app.get("/timetable/today")
def get_today_subjects(db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.key == "active_timetable").first()
    active = setting.value if setting else "regular"
    day = datetime.now().weekday()  # 0=Mon
    if day >= 5:
        return {"day": "weekend", "subjects": []}
    slots = db.query(TimetableSlot).filter(
        TimetableSlot.timetable_type == active,
        TimetableSlot.day_of_week == day,
        TimetableSlot.subject_code != None
    ).order_by(TimetableSlot.start_time).all()
    result = []
    for slot in slots:
        subj = db.query(Subject).filter(Subject.code == slot.subject_code).first()
        teacher = db.query(Teacher).filter(Teacher.id == subj.teacher_id).first() if subj else None
        result.append({
            "subject_code": slot.subject_code,
            "subject_name": subj.name if subj else slot.label,
            "teacher": teacher.name if teacher else "Unassigned",
            "start_time": slot.start_time,
            "end_time": slot.end_time
        })
    return {"day": day, "active_timetable": active, "subjects": result}

@app.put("/timetable/switch")
def switch_timetable(db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.key == "active_timetable").first()
    setting.value = "ramadan" if setting.value == "regular" else "regular"
    db.commit()
    return {"active_timetable": setting.value}

@app.put("/timetable/set/{timetable_type}")
def set_timetable(timetable_type: str, db: Session = Depends(get_db)):
    if timetable_type not in ["regular", "ramadan"]:
        raise HTTPException(400, "Must be 'regular' or 'ramadan'")
    setting = db.query(Setting).filter(Setting.key == "active_timetable").first()
    setting.value = timetable_type
    db.commit()
    return {"active_timetable": setting.value}

# Attendance
@app.post("/attendance")
def mark_attendance(data: AttendanceSubmit, db: Session = Depends(get_db)):
    att_date = datetime.strptime(data.date, "%Y-%m-%d").date()
    # Delete existing for this subject+date
    db.query(AttendanceRecord).filter(
        AttendanceRecord.subject_code == data.subject_code,
        AttendanceRecord.date == att_date
    ).delete()
    students = db.query(Student).filter(Student.is_active == True).all()
    for student in students:
        status = data.records.get(student.roll_number, "A")
        db.add(AttendanceRecord(
            student_id=student.id,
            subject_code=data.subject_code,
            date=att_date,
            status=status
        ))
    db.commit()
    present = sum(1 for v in data.records.values() if v == "P")
    return {"message": "Saved", "present": present, "total": len(students)}

@app.get("/attendance/{subject_code}/{date}")
def get_attendance(subject_code: str, date: str, db: Session = Depends(get_db)):
    att_date = datetime.strptime(date, "%Y-%m-%d").date()
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.subject_code == subject_code,
        AttendanceRecord.date == att_date
    ).all()
    if not records:
        return {"marked": False, "records": {}}
    return {
        "marked": True,
        "records": {r.student.roll_number: r.status for r in records}
    }

# DAR Report
@app.get("/dar/{date}")
def get_dar(date: str, db: Session = Depends(get_db)):
    att_date = datetime.strptime(date, "%Y-%m-%d").date()
    day = att_date.weekday()
    setting = db.query(Setting).filter(Setting.key == "active_timetable").first()
    active = setting.value if setting else "regular"
    slots = db.query(TimetableSlot).filter(
        TimetableSlot.timetable_type == active,
        TimetableSlot.day_of_week == day,
        TimetableSlot.subject_code != None
    ).order_by(TimetableSlot.start_time).all()
    total_students = db.query(Student).filter(Student.is_active == True).count()
    result = []
    for slot in slots:
        records = db.query(AttendanceRecord).filter(
            AttendanceRecord.subject_code == slot.subject_code,
            AttendanceRecord.date == att_date
        ).all()
        present = sum(1 for r in records if r.status == "P")
        subj = db.query(Subject).filter(Subject.code == slot.subject_code).first()
        teacher = db.query(Teacher).filter(Teacher.id == subj.teacher_id).first() if subj else None
        result.append({
            "subject_code": slot.subject_code,
            "subject_name": subj.name if subj else slot.label,
            "teacher": teacher.name if teacher else "Unassigned",
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "present": present,
            "absent": total_students - present,
            "total": total_students,
            "percentage": round((present / total_students * 100), 1) if total_students > 0 else 0,
            "marked": len(records) > 0
        })
    return {"date": date, "day": day, "slots": result}

# Defaulter List
@app.get("/defaulters")
def get_defaulters(db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.is_active == True).all()
    subjects = db.query(Subject).all()
    defaulters = []
    for student in students:
        student_defaulting = []
        for subject in subjects:
            total = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.subject_code == subject.code
            ).count()
            if total == 0:
                continue
            present = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.subject_code == subject.code,
                AttendanceRecord.status == "P"
            ).count()
            pct = round(present / total * 100, 1)
            if pct < 75:
                student_defaulting.append({
                    "subject_code": subject.code,
                    "subject_name": subject.name,
                    "present": present,
                    "total": total,
                    "percentage": pct
                })
        if student_defaulting:
            defaulters.append({
                "roll_number": student.roll_number,
                "name": student.name,
                "subjects": sorted(student_defaulting, key=lambda x: x["percentage"])
            })
    return sorted(defaulters, key=lambda x: x["subjects"][0]["percentage"])

# Student Summary
@app.get("/summary/{roll_number}")
def get_student_summary(roll_number: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not student:
        raise HTTPException(404, "Student not found")
    subjects = db.query(Subject).all()
    summary = []
    for subject in subjects:
        total = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.subject_code == subject.code
        ).count()
        present = db.query(AttendanceRecord).filter(
            AttendanceRecord.student_id == student.id,
            AttendanceRecord.subject_code == subject.code,
            AttendanceRecord.status == "P"
        ).count()
        summary.append({
            "subject_code": subject.code,
            "subject_name": subject.name,
            "present": present,
            "total": total,
            "percentage": round(present / total * 100, 1) if total > 0 else 0
        })
    return {"student": {"roll_number": student.roll_number, "name": student.name, "gender": student.gender}, "summary": summary}

# Class Summary
@app.get("/class-summary")
def get_class_summary(db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.is_active == True).all()
    subjects = db.query(Subject).all()
    result = []
    for student in students:
        row = {"roll_number": student.roll_number, "name": student.name, "subjects": {}}
        for subject in subjects:
            total = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.subject_code == subject.code
            ).count()
            present = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.subject_code == subject.code,
                AttendanceRecord.status == "P"
            ).count()
            row["subjects"][subject.code] = {
                "present": present, "total": total,
                "percentage": round(present / total * 100, 1) if total > 0 else 0
            }
        result.append(row)
    return result

# Export CSV
@app.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    students = db.query(Student).filter(Student.is_active == True).order_by(Student.roll_number).all()
    subjects = db.query(Subject).all()
    lines = ["Roll Number,Name," + ",".join([s.code for s in subjects])]
    for student in students:
        row = [student.roll_number, student.name]
        for subject in subjects:
            total = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.subject_code == subject.code
            ).count()
            present = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.subject_code == subject.code,
                AttendanceRecord.status == "P"
            ).count()
            pct = round(present / total * 100, 1) if total > 0 else 0
            row.append(f"{present}/{total} ({pct}%)")
        lines.append(",".join(row))
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(lines), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance.csv"})

# Settings
@app.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(Setting).all()
    return {s.key: s.value for s in settings}

@app.put("/settings/{key}")
def update_setting(key: str, data: SettingUpdate, db: Session = Depends(get_db)):
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        setting = Setting(key=key, value=data.value)
        db.add(setting)
    else:
        setting.value = data.value
    db.commit()
    return {"key": key, "value": data.value}

# AI Scanner
@app.post("/scan")
async def scan_attendance(data: ScanRequest, db: Session = Depends(get_db)):
    api_key_setting = db.query(Setting).filter(Setting.key == "openrouter_api_key").first()
    api_key = api_key_setting.value if api_key_setting else ""
    if not api_key:
        raise HTTPException(400, "OpenRouter API key not configured. Go to Admin > Settings to add it.")
    students = db.query(Student).filter(Student.is_active == True).all()
    student_list = "\n".join([f"{s.roll_number} - {s.name}" for s in students])
    subject = db.query(Subject).filter(Subject.code == data.subject_code).first()
    subject_name = subject.name if subject else data.subject_code
    prompt = f"""You are analyzing a paper attendance register for {subject_name}.
Here is the list of all students:\n{student_list}\n
Look at the register image and determine who is Present (P) or Absent (A).
Return ONLY a JSON object in this exact format, no explanation:
{{"PDS23001": "P", "PDS23002": "A", ...}}
Include ALL {len(students)} students. If you cannot determine status, mark as "A"."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "google/gemini-flash-1.5",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{data.image_base64}"}}
                    ]
                }]
            }
        )
    if response.status_code != 200:
        raise HTTPException(500, f"AI scan failed: {response.text}")
    content = response.json()["choices"][0]["message"]["content"]
    # Parse JSON from response
    import re
    match = re.search(r'\{[^{}]+\}', content, re.DOTALL)
    if not match:
        raise HTTPException(500, "Could not parse AI response")
    records = json.loads(match.group())
    return {"records": records, "subject_code": data.subject_code, "date": data.date, "confidence": "review_before_saving"}
