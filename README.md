# 🚀 QUIZORA — AI-Powered Quiz & Assessment Platform

A **A **production-ready, AI-powered quiz platform backend**, supported by a frontend prototype that showcases core workflows including authentication, quiz interaction, and performance tracking.** built with Django REST Framework and React.  
Designed to simulate real-world platforms like **HackerEarth / HackerRank**, supporting role-based test management, AI-generated quizzes, and detailed analytics.

---

## 🌐 Live Demo

- 🎯 Frontend: https://quiz-frontend-phi-virid.vercel.app  
- ⚙️ Backend API: https://prework-quiz-api.onrender.com  
- 🔐 Admin Panel: https://prework-quiz-api.onrender.com/admin  

---

## ✨ Features

### 🔐 Authentication & Roles
- JWT-based authentication (SimpleJWT)
- Role-based access:
  - 👨‍🎓 Student
  - 👨‍🏫 Teacher
  - 🛠 Admin
- Secure token handling with refresh rotation

---

### 🧠 AI-Powered Quiz Generation
- Dynamic quiz generation using:
  - Gemini / OpenAI / Groq
- Personalized questions based on:
  - User level (beginner → advanced)
  - Stream (technical / non-technical)
- Supports:
  - Learning mode (hints + explanations)
  - Test mode (strict evaluation)

---

### 📝 Quiz & Test System

> ⚡ **Real-world assessment flow inspired by platforms like HackerEarth**

🚀 **Teacher Capabilities**
- 🧑‍🏫 Create and manage structured tests
- 🎯 Configure difficulty, time limits, and topics

🎓 **Student Experience**
- 🧑‍🎓 Attempt quizzes seamlessly
- 🔄 Resume sessions without losing progress
- ✅ Submit answers with real-time tracking

🔐 **Evaluation Engine**
- ⚡ Secure server-side scoring
- 🛡 Prevents client-side manipulation

---

### ⏱ Test Mode Security

> 🔐 **Strict, exam-grade security inspired by real assessment platforms**

🛑 **Attempt Control**
- 🚫 One-attempt enforcement (no re-attempts)
- ⏳ Timer-based auto submission

👁 **Activity Monitoring**
- 🔄 Tab-switch detection
- ⚠️ 3 violations → automatic test invalidation

🛡 **Anti-Cheating Engine**
- 🔐 Server-side validation of all answers
- 🚫 Prevents manipulation from frontend

---

### 📊 Analytics & Insights
- Per-user performance tracking:
  - Average score
  - Highest / lowest score
- Weak topic detection (<60%)
- Difficulty-wise breakdown:
  - Easy / Medium / Hard
- Topic-based performance history

---

### 🧑‍💼 Admin Dashboard
- Full user management:
  - Create / update / delete users
  - Approve teachers
- View user performance analytics
- Monitor system activity logs

---

### 📋 Activity Logging
- Tracks all system actions:
  - Login
  - Quiz creation
  - Attempts
  - Admin actions
- Immutable audit logs with metadata

---

## ⚡ Tech Stack

| Layer | Technology |
|------|-----------|
| Backend | Django 4.2 + Django REST Framework |
| Database | PostgreSQL |
| Authentication | JWT (SimpleJWT) |
| AI Integration | Gemini / OpenAI / Groq |
| Frontend | React (CRA) |
| Deployment | Render (Backend), Vercel (Frontend) |
| Server | Gunicorn + WhiteNoise |

---

## 🏗 Project Structure
quiz_project/
├── core/ # Settings, URLs, middleware, health check
├── users/ # Authentication, roles, admin management
├── quizzes/ # Quiz, Question, Option models, AI generation
├── attempts/ # Attempt lifecycle, answer handling, security
├── analytics/ # Performance tracking, weak topics
├── ai_service/ # Prompt builder, AI providers, parser
├── logs/ # Activity logging system
└── manage.py


---

## 🔗 API Documentation

👉 Full API documentation available here:

📄 [View API Docs](/api-documentation.md)

Includes:
- 20+ endpoints
- Request & response examples
- Postman usage
- Role-based access details

---

## 🔑 Authentication Flow

1. Register user  
2. Login → receive JWT token  
3. Use token in requests:
Authorization: Bearer <access_token>
---

## 🧪 Core Workflow
Register / Login

Generate AI Quiz

Start Attempt

Submit Answers

Final Submission

View Analytics


---

## 🚀 Deployment

### Backend (Render)
- Auto migrations
- Gunicorn server
- PostgreSQL integration

### Frontend (Vercel)
- React build deployment
- Environment-based API connection

---

## 📌 Key Highlights

- Modular service-layer architecture
- AI-driven adaptive quiz generation
- Secure test environment (anti-cheating)
- Scalable API design
- Real-world assessment platform simulation

---

## 👨‍💻 Author

Developed as  backend-focused system design and a part of full-stack integration project.

---

## 📄 License

This project is for educational and demonstration purposes.