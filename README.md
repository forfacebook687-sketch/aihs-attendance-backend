# AIHS Attendance Backend

FastAPI + SQLite (local) / PostgreSQL (Railway) backend for AIHS Attendance System.

## Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select `aihs-attendance-backend`
4. Railway auto-detects and deploys
5. Click **Generate Domain** to get your live URL
6. Copy the URL and paste it into the frontend's `API_URL` variable

## Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

API runs at `http://localhost:8000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /students | List all students |
| GET | /subjects | List all subjects |
| GET | /teachers | List all teachers |
| POST | /teachers | Add new teacher |
| PUT | /teachers/{id}/deactivate | Remove teacher (keeps records) |
| PUT | /subjects/{code}/teacher | Reassign subject teacher |
| GET | /timetable/today | Today's subjects |
| PUT | /timetable/switch | Toggle Regular/Ramadan |
| PUT | /timetable/set/{type} | Set specific timetable |
| POST | /attendance | Mark attendance (bulk) |
| GET | /attendance/{subject}/{date} | Get attendance for session |
| GET | /dar/{date} | Daily Activity Report |
| GET | /defaulters | Students below 75% |
| GET | /summary/{roll} | Student attendance summary |
| GET | /class-summary | Full class summary |
| GET | /export/csv | Download CSV |
| POST | /scan | AI scan register image |
| PUT | /settings/{key} | Update settings |
