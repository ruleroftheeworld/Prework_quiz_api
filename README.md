# AI-Powered Quiz Application — Django REST API

A production-ready, modular Django REST API for an AI-powered quiz platform.

## Features

- JWT Authentication with role-based access (user / admin)
- AI-generated quizzes via Gemini, OpenAI, or Groq
- Dual quiz modes: **Learning** (hints, explanations) and **Test** (strict, timed, one attempt)
- Session persistence — resume after page refresh
- TEST mode security: tab-switch detection, auto-invalidation
- Per-user analytics: weak topics, score history, difficulty breakdown
- Full admin panel: user management, logs, performance monitoring
- Structured activity logging for all user and admin actions

## Quick Start

See [DEPLOYMENT.md](./DEPLOYMENT.md) for full local and Railway setup instructions.

## Project Structure

```
quiz_project/
├── core/           # Settings, URLs, WSGI, utils, health check
├── users/          # Auth, user model, admin user management
├── quizzes/        # Quiz + Question + Option models, AI generation
├── attempts/       # Attempt lifecycle, answer saving, TEST mode enforcement
├── analytics/      # Per-user analytics, topic scoring, weak topic detection
├── ai_service/     # Prompt builder, provider callers, parser, validator
├── logs/           # ActivityLog model, LogService, middleware
└── manage.py
```

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 + DRF |
| Database | PostgreSQL (via dj-database-url) |
| Auth | SimpleJWT |
| AI | Gemini 1.5 Flash / GPT-3.5 / Llama3-70b |
| Deployment | Railway / Gunicorn / WhiteNoise |
