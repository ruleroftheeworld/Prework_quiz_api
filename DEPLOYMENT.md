# Deployment Guide

## Local Setup

```bash
# 1. Clone / unzip the project
cd quiz_project

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment file
cp .env.example .env
# Edit .env with your values (DATABASE_URL, AI keys, SECRET_KEY)

# 5. Create the PostgreSQL database
createdb quiz_db

# 6. Run migrations
python manage.py migrate

# 7. Create a superuser (admin)
python manage.py createsuperuser

# 8. Run the dev server
python manage.py runserver
```

## Deployment — Render

### Live URL
https://prework-quiz-api.onrender.com

### Platform
Render (render.com) — Free tier

### Database
Render PostgreSQL — Free tier (90 days)

### Environment Variables
Set in Render dashboard → Service → Environment:
- SECRET_KEY
- DEBUG=False
- ALLOWED_HOSTS=prework-quiz-api.onrender.com
- DATABASE_URL (Render PostgreSQL internal URL)
- AI_PROVIDER=groq
- GROQ_API_KEY
- CORS_ALLOWED_ORIGINS

### Build Command
pip install -r requirements.txt && python manage.py collectstatic --noinput

### Start Command
gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 2

### Post-deploy
python manage.py migrate
python manage.py createsuperuser

## Environment Variables Reference

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | Django secret key | ✅ |
| `DEBUG` | True/False | ✅ |
| `ALLOWED_HOSTS` | Comma-separated hostnames | ✅ |
| `DATABASE_URL` | PostgreSQL connection URL | ✅ |
| `AI_PROVIDER` | gemini / openai / groq | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | If using Gemini |
| `OPENAI_API_KEY` | OpenAI API key | If using OpenAI |
| `GROQ_API_KEY` | Groq API key | If using Groq |
| `CORS_ALLOWED_ORIGINS` | Frontend URL(s) | ✅ |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | JWT access token lifetime | Optional (default 60) |
| `REFRESH_TOKEN_LIFETIME_DAYS` | JWT refresh token lifetime | Optional (default 7) |

## API Quick Reference

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register user |
| POST | `/api/auth/login/` | Login (returns JWT) |
| POST | `/api/auth/token/refresh/` | Refresh JWT |
| GET/PUT | `/api/auth/me/` | View/update own profile |
| POST | `/api/quizzes/` | Generate AI quiz |
| GET | `/api/quizzes/` | List quizzes |
| GET | `/api/quizzes/{id}/` | Quiz detail |
| POST | `/api/attempts/start/{quiz_id}/` | Start attempt |
| POST | `/api/attempts/{id}/answer/` | Submit answer |
| POST | `/api/attempts/{id}/submit/` | Submit attempt |
| GET | `/api/attempts/{id}/resume/` | Resume attempt |
| GET | `/api/attempts/history/` | Attempt history |
| POST | `/api/attempts/{id}/event/` | Report tab switch |
| GET | `/api/analytics/me/` | My analytics |
| GET | `/api/admin/users/` | List all users (admin) |
| POST | `/api/admin/users/` | Create user (admin) |
| DELETE | `/api/admin/users/{id}/` | Delete user (admin) |
| GET | `/api/admin/users/{id}/scores/` | User scores (admin) |
| GET | `/api/logs/` | Activity logs (admin) |
| GET | `/api/health/` | Health check |
