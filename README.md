# Hiring System Dashboard

Flask-based dashboard for tracking and managing hiring candidates for the Head of Customer Success role.

## Features

- **Candidate Overview**: View all video submissions with filtering and sorting
- **AI Evaluation**: Integrated AI-powered candidate evaluation with scores and recommendations
- **Serial Numbers**: Candidates numbered for easy reference
- **Student Indicator**: Student applicants marked with (S) suffix for quick identification
- **Real-time Updates**: Auto-refresh with countdown timer
- **Status Management**: Update candidate stage status directly from dashboard
- **Reviewer Comments**: Add and save reviewer notes for each candidate

## Deployment

| Environment | URL | Port | Branch |
|-------------|-----|------|--------|
| **Live** | `/hiring/headofcustomersuccess/` | 5010 | main |
| **QA** | `/hiring/headofcustomersuccess-qa/` | 5012 | qa |

**Server**: srv1079050.hstgr.cloud (72.60.219.142)

### VPS Paths
- Live: `/home/Hiring_System/dashboard`
- QA: `/home/Hiring_System/dashboard_QA`

## Quick Start

```bash
# Start service (from dashboard folder)
./venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5010 main:app --daemon

# QA service
cd /home/Hiring_System/dashboard_QA
../dashboard/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5012 main:app --daemon
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main dashboard page |
| GET | `/api/metrics` | Dashboard metrics |
| GET | `/api/video-submitters` | List of candidates with video submissions |
| POST | `/api/update-status` | Update Stage 1 Status |
| POST | `/api/update-comments` | Update Reviewer Comments |
| POST | `/api/trigger-evaluation` | Trigger AI evaluation for a candidate |

## Environment Variables

```
AIRTABLE_PAT=<Airtable Personal Access Token>
AIRTABLE_BASE_ID=<Airtable Base ID>
AIRTABLE_TABLE_ID=<Airtable Table ID>
HIRING_API_URL=https://srv1079050.hstgr.cloud/hiring-api
```

## Development Workflow

1. Make changes on `qa` branch
2. Push to GitHub
3. Deploy to QA: `git pull origin qa` on VPS
4. Test at QA URL
5. Merge to `main` when ready
6. Deploy to Live: `git pull origin main` on VPS

## Data Sources

- **Airtable**: Candidate data, application details, AI evaluations
- **Source Types**:
  - `LinkedIn` - LinkedIn Easy Apply submissions
  - `student_application` - Student portal submissions (shown with (S) suffix)
  - `alumni_referral` - Alumni referral submissions
