# QUIZORA — AI-Powered Quiz & Assessment Platform
## Complete API Documentation

**Base URL (Production):** `https://prework-quiz-api.onrender.com`  
**Base URL (Local):** `http://127.0.0.1:8000`  
**Content-Type:** `application/json` (all requests)  
**Authentication:** JWT Bearer Token

---

## 🔑 How Authentication Works

Every protected endpoint requires a Bearer Token in the request header.

### How to get a token:
1. Call `POST /api/auth/login/` with your credentials
2. Copy the `access` value from the response
3. In Postman: **Authorization tab → Bearer Token → paste the access token**

### Token Details:
| Field | Value |
|---|---|
| Type | JWT (JSON Web Token) |
| Lifetime | 60 minutes (access), 7 days (refresh) |
| Custom Claims | `role`, `username` embedded inside token |
| Header Format | `Authorization: Bearer <access_token>` |

### Roles in the system:
| Role | Description |
|---|---|
| `user` | Student — takes quizzes and attempts tests |
| `teacher` | Educator — creates and manages tests |
| `admin` | Administrator — full system access |

---

## ═══════════════════════════════════════
## 🔐 MODULE 1: AUTHENTICATION
## ═══════════════════════════════════════

---

### API 1 — Register User

**Endpoint:** `POST /api/auth/register/`  
**Authentication:** Not required (public endpoint)  
**Who Uses It:** Any new user (student, teacher)

#### Purpose
Creates a new user account. The role (`user` or `teacher`) is set at registration. Teacher accounts require admin approval before they can create tests.

#### Request Body
```json
{
  "email": "student@example.com",
  "username": "student1",
  "full_name": "John Doe",
  "password": "StrongPass123!",
  "password2": "StrongPass123!",
  "level": "beginner",
  "stream": "computer_science",
  "role": "user"
}
```

| Field | Type | Required | Values |
|---|---|---|---|
| `email` | string | ✅ | Valid email, unique |
| `username` | string | ✅ | Unique |
| `full_name` | string | ❌ | Any string |
| `password` | string | ✅ | Min 8 chars |
| `password2` | string | ✅ | Must match password |
| `level` | string | ✅ | `beginner`, `intermediate`, `advanced` |
| `stream` | string | ✅ | `computer_science`, `non_technical` |
| `role` | string | ❌ | `user` (default), `teacher` |

#### Sample Request (Postman)
```
POST https://prework-quiz-api.onrender.com/api/auth/register/
Content-Type: application/json

{
  "email": "student@example.com",
  "username": "student1",
  "password": "StrongPass123!",
  "password2": "StrongPass123!",
  "level": "beginner",
  "stream": "computer_science"
}
```

#### Success Response (201 Created)
```json
{
  "message": "Registration successful.",
  "user": {
    "id": 5,
    "email": "student@example.com",
    "username": "student1",
    "full_name": "",
    "role": "user",
    "level": "beginner",
    "stream": "computer_science",
    "total_score": 0.0,
    "quizzes_taken": 0,
    "average_score": 0.0,
    "date_joined": "2026-03-20T10:00:00Z",
    "last_seen": null
  }
}
```

#### Error Responses
```json
// 400 — Email already taken
{ "email": ["user with this email already exists."] }

// 400 — Passwords don't match
{ "password": ["Passwords do not match."] }

// 400 — Weak password
{ "password": ["This password is too common."] }
```

#### Impact
Registers the user into the system. Triggers `user_registered` activity log. The `level` and `stream` fields directly influence AI prompt generation — a `beginner` in `computer_science` gets simpler, code-oriented questions while `advanced` in `non_technical` gets conceptual, jargon-free questions.

---

### API 2 — Login

**Endpoint:** `POST /api/auth/login/`  
**Authentication:** Not required (public endpoint)  
**Who Uses It:** Admin, Teacher, Student

#### Purpose
Authenticates user and returns JWT access + refresh tokens. The access token must be used for all subsequent API calls. Custom claims (`role`, `username`) are embedded inside the token so the frontend knows what dashboard to show without an extra API call.

#### Request Body
```json
{
  "email": "admin@test.com",
  "password": "StrongPass123!"
}
```

#### Sample Request (Postman)
```
POST https://prework-quiz-api.onrender.com/api/auth/login/
Content-Type: application/json

{
  "email": "admin@test.com",
  "password": "StrongPass123!"
}
```

#### Success Response (200 OK)
```json
{
  "refresh": "eyJhbGci...long_refresh_token",
  "access": "eyJhbGci...long_access_token",
  "user": {
    "id": 1,
    "email": "admin@test.com",
    "username": "admin",
    "role": "admin",
    "level": "beginner",
    "stream": "computer_science",
    "total_score": 0.0,
    "quizzes_taken": 0,
    "average_score": 0.0,
    "date_joined": "2026-03-20T07:34:29Z",
    "last_seen": "2026-03-20T10:00:00Z"
  }
}
```

#### Error Responses
```json
// 401 — Wrong credentials
{
  "detail": "No active account found with the given credentials"
}
```

#### Impact
Returns a JWT with `role` and `username` baked in. Frontend decodes the token to route `admin → Admin Dashboard`, `teacher → Teacher Dashboard`, `user → Student Dashboard`. Login event is logged to `ActivityLog` with the user's IP address.

---

### API 3 — Refresh Token

**Endpoint:** `POST /api/auth/token/refresh/`  
**Authentication:** Not required  
**Who Uses It:** All roles (called automatically when access token expires)

#### Purpose
Issues a new access token using a valid refresh token. Old refresh token is blacklisted after rotation — prevents token reuse.

#### Request Body
```json
{
  "refresh": "eyJhbGci...your_refresh_token"
}
```

#### Success Response (200 OK)
```json
{
  "access": "eyJhbGci...new_access_token",
  "refresh": "eyJhbGci...new_refresh_token"
}
```

#### Impact
Keeps the user session alive without re-logging in. The old refresh token is immediately invalidated — if someone steals the token and tries to reuse it, the second use will fail.

---

### API 4 — My Profile (View & Update)

**Endpoint:** `GET /api/auth/me/`  
**Method:** GET (view) / PUT (update)  
**Authentication:** ✅ Bearer Token (any logged-in user)  
**Who Uses It:** Admin, Teacher, Student

#### Purpose
View or update the currently logged-in user's profile. Students can update their `level` and `stream` to improve AI question personalization.

#### GET — No request body

#### Success Response (200 OK)
```json
{
  "id": 3,
  "email": "student@test.com",
  "username": "student1",
  "full_name": "",
  "role": "user",
  "level": "beginner",
  "stream": "computer_science",
  "total_score": 166.67,
  "quizzes_taken": 3,
  "average_score": 55.56,
  "date_joined": "2026-03-18T19:35:41Z",
  "last_seen": "2026-03-20T10:00:00Z"
}
```

#### PUT Request Body (update level/stream)
```json
{
  "level": "intermediate",
  "stream": "computer_science"
}
```

#### Impact
`level` and `stream` are passed into the AI prompt builder on every quiz generation. Changing them immediately affects the difficulty and framing of future AI-generated questions.

---

## ═══════════════════════════════════════
## 🧠 MODULE 2: QUIZ GENERATION (AI)
## ═══════════════════════════════════════

---

### API 5 — Generate AI Quiz

**Endpoint:** `POST /api/quizzes/`  
**Authentication:** ✅ Bearer Token (any logged-in user)  
**Who Uses It:** Student (practice), Teacher (self-practice)

#### Purpose
Generates a multiple-choice quiz using AI (Gemini / OpenAI / Groq). The prompt is dynamically built using the user's `level`, `stream`, chosen `topic`, `difficulty`, and `mode`. Questions are stored permanently in the database with options, correct answers, hints, and explanations.

#### Request Body
```json
{
  "topic": "Python basics",
  "difficulty": "easy",
  "mode": "learning",
  "num_questions": 5,
  "time_limit_minutes": null
}
```

| Field | Type | Required | Values |
|---|---|---|---|
| `topic` | string | ✅ | Any topic string |
| `difficulty` | string | ✅ | `easy`, `medium`, `hard` |
| `mode` | string | ✅ | `learning`, `test` |
| `num_questions` | integer | ✅ | 1–50 |
| `time_limit_minutes` | integer | Required for `test` mode | Minutes |

#### Sample Request
```
POST https://prework-quiz-api.onrender.com/api/quizzes/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "topic": "Python basics",
  "difficulty": "easy",
  "mode": "learning",
  "num_questions": 3
}
```

#### Success Response (201 Created)
```json
{
  "id": "2ccc26cb-0fbd-493e-9923-49fbeb9f15db",
  "topic": "Python basics",
  "description": "",
  "difficulty": "easy",
  "mode": "learning",
  "num_questions": 3,
  "time_limit_minutes": null,
  "is_active": true,
  "question_count": 3,
  "created_by_username": "student1",
  "created_at": "2026-03-19T09:12:17Z",
  "questions": [
    {
      "id": "18856219-b229-4603-9276-994b51a5fd2a",
      "text": "What is the syntax for a comment in Python?",
      "order": 1,
      "hint": "Think about how you indicate that a piece of code is for note-taking.",
      "options": [
        { "id": "2fb4baaa-...", "label": "A", "text": "# This is a comment" },
        { "id": "1fd21a03-...", "label": "B", "text": "* This is a comment" },
        { "id": "982be266-...", "label": "C", "text": "// This is a comment" },
        { "id": "33a4b722-...", "label": "D", "text": "/* This is a comment */" }
      ]
    }
  ]
}
```

#### Error Responses
```json
// 400 — Test mode missing time limit
{ "time_limit_minutes": ["TEST mode requires a time limit."] }

// 503 — AI generation failed after all retries
{
  "detail": "Quiz generation failed. Please try again.",
  "error": "Quiz generation failed after 3 attempts."
}
```

#### Impact
Triggers the full AI pipeline: `build_prompt()` → AI API call → `parse_response()` → `validate_questions()`. Retries up to 3 times. Stores Quiz + Questions + Options atomically. Logs `quiz_created` to activity log. The `correct_option` and `explanation` are stored but hidden from the response — they are only revealed during/after attempt based on mode.

---

### API 6 — List Quizzes

**Endpoint:** `GET /api/quizzes/`  
**Authentication:** ✅ Bearer Token (any logged-in user)  
**Who Uses It:** Student, Teacher

#### Purpose
Returns a paginated list of all active quizzes. Supports filtering by mode, difficulty, and topic search.

#### Query Parameters
| Param | Type | Example |
|---|---|---|
| `mode` | string | `?mode=learning` or `?mode=test` |
| `difficulty` | string | `?difficulty=easy` |
| `topic` | string | `?topic=python` (case-insensitive search) |
| `page` | integer | `?page=2` |

#### Sample Request
```
GET https://prework-quiz-api.onrender.com/api/quizzes/?mode=learning&difficulty=easy
Authorization: Bearer <access_token>
```

#### Success Response (200 OK)
```json
{
  "count": 12,
  "next": "http://.../?page=2",
  "previous": null,
  "results": [
    {
      "id": "2ccc26cb-...",
      "topic": "Python basics",
      "difficulty": "easy",
      "mode": "learning",
      "num_questions": 3,
      "question_count": 3,
      "created_by_username": "student1",
      "created_at": "2026-03-19T09:12:17Z"
    }
  ]
}
```

#### Impact
Allows students to browse and retry previous quizzes. Questions are NOT included in list view — only fetched in detail view to keep response size small.

---

### API 7 — Quiz Detail

**Endpoint:** `GET /api/quizzes/{quiz_id}/`  
**Authentication:** ✅ Bearer Token (any logged-in user)  
**Who Uses It:** Student, Teacher

#### Purpose
Returns a single quiz with all questions and options. Used to load quiz questions before starting an attempt. `correct_option` and `explanation` are intentionally excluded — they are only revealed in the attempt result.

#### Sample Request
```
GET https://prework-quiz-api.onrender.com/api/quizzes/2ccc26cb-0fbd-493e-9923-49fbeb9f15db/
Authorization: Bearer <access_token>
```

#### Success Response (200 OK)
Same as the POST quiz response above — full quiz object with questions array.

#### Error Response
```json
// 404
{ "detail": "Quiz not found." }
```

#### Impact
Loads all questions and options for display. `hint` is included so learning mode can show hints. `correct_option` is never exposed here — scoring happens server-side during answer submission.

---

## ═══════════════════════════════════════
## 📝 MODULE 3: QUIZ ATTEMPTS
## ═══════════════════════════════════════

---

### API 8 — Start Quiz Attempt

**Endpoint:** `POST /api/attempts/start/{quiz_id}/`  
**Authentication:** ✅ Bearer Token (Student)  
**Who Uses It:** Student

#### Purpose
Starts a new attempt for a quiz or resumes an existing in-progress one. In **test mode**: enforces one attempt per user — returns existing attempt if in-progress, blocks if already submitted. In **learning mode**: resumes any in-progress attempt automatically. Sets `expires_at` for test mode based on `time_limit_minutes`.

#### Request Body
Empty body `{}`

#### Sample Request
```
POST https://prework-quiz-api.onrender.com/api/attempts/start/2ccc26cb-0fbd-493e-9923-49fbeb9f15db/
Authorization: Bearer <access_token>
Content-Type: application/json

{}
```

#### Success Response (201 Created)
```json
{
  "id": "6ba29b28-f1ae-4b10-a25e-da10e3d73e3b",
  "quiz_id": "2ccc26cb-0fbd-493e-9923-49fbeb9f15db",
  "quiz_topic": "Python basics",
  "quiz_mode": "learning",
  "status": "in_progress",
  "total_questions": 3,
  "current_question_order": 1,
  "started_at": "2026-03-19T09:13:32Z",
  "expires_at": null,
  "time_remaining_seconds": null
}
```

#### Error Responses
```json
// 403 — Test mode: already submitted
{
  "detail": "You have already completed this test. Re-attempts are not allowed."
}

// 403 — Test mode: previous attempt expired
{
  "detail": "Your previous attempt expired."
}
```

#### Impact
Creates an `Attempt` record in the database. For test mode, `expires_at` is set immediately — the server timer starts. Frontend uses `time_remaining_seconds` to show the countdown. Logs `quiz_started` to activity log.

---

### API 9 — Submit Answer

**Endpoint:** `POST /api/attempts/{attempt_id}/answer/`  
**Authentication:** ✅ Bearer Token (Student)  
**Who Uses It:** Student

#### Purpose
Saves the student's answer for a single question. Server-side scoring: compares `selected_option` against the stored `correct_option`. In **learning mode**: returns `is_correct` and `explanation` immediately. In **test mode**: returns `null` for both — correctness hidden until final submission.

#### Request Body
```json
{
  "question_id": "18856219-b229-4603-9276-994b51a5fd2a",
  "selected_option": "A",
  "hint_used": false
}
```

| Field | Type | Required | Values |
|---|---|---|---|
| `question_id` | UUID | ✅ | Must belong to this attempt's quiz |
| `selected_option` | string | ✅ | `A`, `B`, `C`, or `D` |
| `hint_used` | boolean | ❌ | Silently ignored in test mode |

#### Sample Request
```
POST https://prework-quiz-api.onrender.com/api/attempts/6ba29b28-f1ae-4b10-a25e-da10e3d73e3b/answer/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "question_id": "18856219-b229-4603-9276-994b51a5fd2a",
  "selected_option": "A",
  "hint_used": false
}
```

#### Success Response — Learning Mode (200 OK)
```json
{
  "question_id": "18856219-b229-4603-9276-994b51a5fd2a",
  "selected_option": "A",
  "is_correct": true,
  "explanation": "In Python, comments start with the '#' symbol..."
}
```

#### Success Response — Test Mode (200 OK)
```json
{
  "question_id": "18856219-b229-4603-9276-994b51a5fd2a",
  "selected_option": "A",
  "is_correct": null,
  "explanation": null
}
```

#### Error Responses
```json
// 403 — Attempt already submitted
{ "detail": "Attempt is already submitted." }

// 403 — Timer expired
{ "detail": "Time limit exceeded. Attempt auto-submitted." }
```

#### Impact
Uses `update_or_create` — student can change answer before final submission. Updates `current_question_order` for navigation tracking. Server-side scoring ensures answers cannot be faked from frontend. Logs `answer_submitted` to activity log.

---

### API 10 — Submit Attempt (Final)

**Endpoint:** `POST /api/attempts/{attempt_id}/submit/`  
**Authentication:** ✅ Bearer Token (Student)  
**Who Uses It:** Student

#### Purpose
Finalises the quiz attempt. Calculates score as `(correct_answers / total_questions) × 100`. Updates user's aggregate `total_score` and `quizzes_taken`. Updates `UserAnalytics` and `TopicScore`. Checks if timer expired — if yes, auto-submits with partial score.

#### Request Body
Empty body `{}`

#### Sample Request
```
POST https://prework-quiz-api.onrender.com/api/attempts/6ba29b28-f1ae-4b10-a25e-da10e3d73e3b/submit/
Authorization: Bearer <access_token>
Content-Type: application/json

{}
```

#### Success Response (200 OK)
```json
{
  "id": "6ba29b28-f1ae-4b10-a25e-da10e3d73e3b",
  "quiz": { "id": "2ccc26cb-...", "topic": "Python basics", "mode": "learning", ... },
  "status": "submitted",
  "score": 66.67,
  "score_percentage": 66.67,
  "total_questions": 3,
  "correct_answers": 2,
  "started_at": "2026-03-19T09:13:32Z",
  "submitted_at": "2026-03-19T09:36:45Z",
  "tab_switch_count": 0,
  "suspicious_activity": false,
  "answers": [
    {
      "question_id": "18856219-...",
      "question_text": "What is the syntax for a comment in Python?",
      "selected_option": "A",
      "correct_option": "A",
      "is_correct": true,
      "explanation": "In Python, comments start with the '#' symbol.",
      "options": [...]
    }
  ]
}
```

#### Impact
Triggers the full scoring pipeline: score calculation → `UserService.update_score()` → `AnalyticsService.record_attempt()` → `_refresh_weak_topics()`. Any topic where average score drops below 60% is automatically added to `weak_topics`. Logs `quiz_completed` to activity log.

---

### API 11 — Resume Attempt

**Endpoint:** `GET /api/attempts/{attempt_id}/resume/`  
**Authentication:** ✅ Bearer Token (Student)  
**Who Uses It:** Student

#### Purpose
Returns the current state of an in-progress attempt after a page refresh. Includes the list of already-answered question IDs so the frontend can restore navigation state. This is the session persistence mechanism — no progress is lost on refresh.

#### Sample Request
```
GET https://prework-quiz-api.onrender.com/api/attempts/6ba29b28-f1ae-4b10-a25e-da10e3d73e3b/resume/
Authorization: Bearer <access_token>
```

#### Success Response (200 OK)
```json
{
  "id": "6ba29b28-...",
  "quiz_id": "2ccc26cb-...",
  "quiz_mode": "learning",
  "status": "in_progress",
  "total_questions": 3,
  "current_question_order": 2,
  "started_at": "2026-03-19T09:13:32Z",
  "expires_at": null,
  "time_remaining_seconds": null,
  "answered_question_ids": [
    "18856219-b229-4603-9276-994b51a5fd2a"
  ]
}
```

#### Impact
Enables full session persistence. Frontend uses `answered_question_ids` to mark questions as answered in the navigation grid and `current_question_order` to scroll to the last question visited.

---

### API 12 — Attempt History

**Endpoint:** `GET /api/attempts/history/`  
**Authentication:** ✅ Bearer Token (Student)  
**Who Uses It:** Student

#### Purpose
Returns paginated list of all past attempts for the logged-in user, ordered by most recent. Shows score, status, mode, and difficulty for each attempt.

#### Query Parameters
| Param | Type | Example |
|---|---|---|
| `page` | integer | `?page=2` |

#### Sample Request
```
GET https://prework-quiz-api.onrender.com/api/attempts/history/
Authorization: Bearer <access_token>
```

#### Success Response (200 OK)
```json
{
  "count": 4,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "72789bc7-...",
      "quiz_topic": "Python basics",
      "quiz_mode": "test",
      "quiz_difficulty": "medium",
      "status": "submitted",
      "score": 33.33,
      "score_percentage": 33.33,
      "total_questions": 3,
      "correct_answers": 1,
      "started_at": "2026-03-19T09:42:20Z",
      "submitted_at": "2026-03-19T09:44:59Z"
    }
  ]
}
```

#### Impact
Powers the student's personal quiz history view. `in_progress` attempts appear here too — student can click to resume them.

---

### API 13 — Report Security Event

**Endpoint:** `POST /api/attempts/{attempt_id}/event/`  
**Authentication:** ✅ Bearer Token (Student)  
**Who Uses It:** Student (frontend sends automatically)

#### Purpose
Reports a security violation during a test-mode attempt. Accepted event types: `tab_switch`, `blur`, `copy_paste`, `right_click`. Backend increments the `tab_switch_count`. At **3 tab switches**, the attempt is automatically invalidated — student can no longer submit answers.

#### Request Body
```json
{
  "event_type": "tab_switch"
}
```

| `event_type` | Description |
|---|---|
| `tab_switch` | User switched browser tab |
| `blur` | Browser window lost focus |
| `copy_paste` | Copy/paste detected |
| `right_click` | Right-click detected |

#### Success Response (200 OK)
```json
{
  "tab_switch_count": 2,
  "invalidated": false
}
```

#### Response after 3rd tab switch
```json
{
  "tab_switch_count": 3,
  "invalidated": true
}
```

#### Impact
After invalidation, all subsequent answer submissions return `403 "Attempt is already invalidated."` The `suspicious_activity` flag is set to `true` on the attempt and `attempt_invalidated` is logged. Only applies to `test` mode — learning mode events are ignored.

---

## ═══════════════════════════════════════
## 📊 MODULE 4: ANALYTICS
## ═══════════════════════════════════════

---

### API 14 — My Analytics

**Endpoint:** `GET /api/analytics/me/`  
**Authentication:** ✅ Bearer Token (any logged-in user)  
**Who Uses It:** Student, Teacher (self-analytics)

#### Purpose
Returns the logged-in user's complete performance summary. Includes: total quizzes, average score, highest/lowest score, per-difficulty breakdown, weak topics (topics with average below 60%), and per-topic score history.

#### Sample Request
```
GET https://prework-quiz-api.onrender.com/api/analytics/me/
Authorization: Bearer <access_token>
```

#### Success Response (200 OK)
```json
{
  "total_attempts": 2,
  "total_quizzes_completed": 2,
  "average_score": 50.0,
  "highest_score": 66.67,
  "lowest_score": 33.33,
  "weak_topics": [
    { "topic": "Python basics", "avg_score": 50.0 }
  ],
  "easy_attempts": 1,
  "easy_score_sum": 66.67,
  "medium_attempts": 1,
  "medium_score_sum": 33.33,
  "hard_attempts": 0,
  "hard_score_sum": 0.0,
  "last_activity": "2026-03-19T09:44:59Z",
  "topic_breakdown": [
    {
      "topic": "Python basics",
      "attempts": 2,
      "average_score": 50.0,
      "last_attempted": "2026-03-19T09:44:59Z"
    }
  ]
}
```

#### Impact
`weak_topics` is automatically recomputed after every quiz submission. Any topic where `average_score < 60%` is flagged. This data is also visible to admins via the user scores endpoint. Difficulty breakdown (`easy_attempts`, `medium_attempts`, `hard_attempts`) shows where the student struggles most.

---

## ═══════════════════════════════════════
## 🔐 MODULE 5: ADMIN ENDPOINTS
## ═══════════════════════════════════════

---

### API 15 — List / Create Users

**Endpoint:** `GET /api/admin/users/`  
**Method:** GET (list) / POST (create)  
**Authentication:** ✅ Bearer Token — **Admin token only**  
**Who Uses It:** Admin

#### Purpose
**GET:** Returns paginated list of all users with full profile details including scores, role, level, stream, and last seen timestamp.  
**POST:** Creates a new user directly as admin without email verification.

#### GET Query Parameters
| Param | Type | Example |
|---|---|---|
| `role` | string | `?role=teacher` |
| `is_active` | boolean | `?is_active=true` |
| `page` | integer | `?page=2` |

#### GET Sample Request
```
GET https://prework-quiz-api.onrender.com/api/admin/users/
Authorization: Bearer <admin_access_token>
```

#### GET Success Response (200 OK)
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 3,
      "email": "teacher@test.com",
      "username": "teacher1",
      "role": "teacher",
      "level": "intermediate",
      "stream": "computer_science",
      "is_active": true,
      "is_approved": true,
      "total_score": 0.0,
      "quizzes_taken": 0,
      "average_score": 0.0,
      "date_joined": "2026-03-19T16:55:01Z",
      "last_seen": "2026-03-20T09:00:00Z"
    }
  ]
}
```

#### POST Request Body (Create User)
```json
{
  "email": "newteacher@school.com",
  "username": "teacher2",
  "password": "StrongPass123!",
  "role": "teacher",
  "level": "intermediate",
  "stream": "computer_science",
  "is_approved": true
}
```

#### Impact
Admin can see `last_seen` (updated every 60 seconds by middleware) to monitor activity. Admin-created users are logged with `admin_created_user` action. Setting `is_approved: true` immediately allows teachers to create tests.

---

### API 16 — Manage Single User

**Endpoint:** `GET/PATCH/DELETE /api/admin/users/{user_id}/`  
**Authentication:** ✅ Bearer Token — **Admin token only**  
**Who Uses It:** Admin

#### Purpose
**GET:** Retrieve full profile of a specific user.  
**PATCH:** Update any field — most importantly `role` (promote student to teacher) and `is_approved` (approve teacher).  
**DELETE:** Permanently delete user (logged with `admin_deleted_user`).

#### PATCH Request Body (Approve Teacher)
```json
{
  "is_approved": true
}
```

#### PATCH Request Body (Change Role)
```json
{
  "role": "teacher",
  "is_approved": true
}
```

#### Success Response (200 OK)
```json
{
  "id": 3,
  "email": "teacher@test.com",
  "username": "teacher1",
  "role": "teacher",
  "is_approved": true,
  "is_active": true,
  ...
}
```

#### Impact
Setting `is_approved: true` unblocks the teacher to create tests. Deleting a user triggers `admin_deleted_user` log with the deleted email stored in metadata for audit trail. Quiz history is preserved via `SET_NULL` on `created_by`.

---

### API 17 — View User Scores

**Endpoint:** `GET /api/admin/users/{user_id}/scores/`  
**Authentication:** ✅ Bearer Token — **Admin token only**  
**Who Uses It:** Admin

#### Purpose
Returns the full performance summary for any specific user — same data as `GET /api/analytics/me/` but viewable by admin for any user.

#### Sample Request
```
GET https://prework-quiz-api.onrender.com/api/admin/users/3/scores/
Authorization: Bearer <admin_access_token>
```

#### Success Response (200 OK)
```json
{
  "user_id": 3,
  "email": "student@test.com",
  "username": "student1",
  "level": "beginner",
  "stream": "computer_science",
  "total_quizzes": 2,
  "average_score": 50.0,
  "highest_score": 66.67,
  "lowest_score": 33.33,
  "weak_topics": [
    { "topic": "Python basics", "avg_score": 50.0 }
  ],
  "last_activity": "2026-03-19T09:44:59Z"
}
```

#### Impact
Gives admin full visibility into any user's academic performance. Weak topics are automatically computed — admin can identify struggling students and recommend resources.

---

## ═══════════════════════════════════════
## 📋 MODULE 6: ACTIVITY LOGS
## ═══════════════════════════════════════

---

### API 18 — View Activity Logs

**Endpoint:** `GET /api/logs/`  
**Authentication:** ✅ Bearer Token — **Admin token only**  
**Who Uses It:** Admin

#### Purpose
Returns paginated, immutable audit log of all actions taken across the system. Logs include user identity, action type, timestamp, IP address, and JSON metadata with context-specific details.

#### Query Parameters
| Param | Type | Example |
|---|---|---|
| `action` | string | `?action=user_login` |
| `user_id` | integer | `?user_id=3` |
| `page` | integer | `?page=2` |

#### Logged Action Types
| Action | Triggered By |
|---|---|
| `user_registered` | New user registers |
| `user_login` | User logs in |
| `quiz_created` | AI quiz generated |
| `quiz_started` | Attempt started |
| `answer_submitted` | Each answer saved |
| `quiz_completed` | Attempt submitted |
| `attempt_invalidated` | 3 tab switches detected |
| `admin_created_user` | Admin creates user |
| `admin_deleted_user` | Admin deletes user |
| `admin_deleted_quiz` | Admin deletes quiz |

#### Sample Request
```
GET https://prework-quiz-api.onrender.com/api/logs/?action=quiz_completed
Authorization: Bearer <admin_access_token>
```

#### Success Response (200 OK)
```json
{
  "count": 33,
  "next": "http://.../?page=2",
  "previous": null,
  "results": [
    {
      "id": 32,
      "user_email": "student@test.com",
      "action": "quiz_completed",
      "timestamp": "2026-03-19T09:44:59Z",
      "metadata": {
        "attempt_id": "72789bc7-...",
        "quiz_id": "c472b36d-...",
        "score": 33.33,
        "mode": "test"
      },
      "ip_address": null
    }
  ]
}
```

#### Impact
Provides a complete, tamper-proof audit trail. Logs are write-only from the service layer — the admin panel disables add/change permissions. `LogService.log()` wraps all writes in try/except so logging failures never crash the main request flow.

---

## ═══════════════════════════════════════
## ⚙️ MODULE 7: SYSTEM
## ═══════════════════════════════════════

---

### API 19 — Health Check

**Endpoint:** `GET /api/health/`  
**Authentication:** Not required (public)  
**Who Uses It:** DevOps, monitoring systems, Railway/Render deployment checks

#### Purpose
Verifies the server is running and the database connection is active. Used by Render as the `healthcheckPath` in `railway.json`. Returns `503` if the DB is unreachable.

#### Sample Request
```
GET https://prework-quiz-api.onrender.com/api/health/
```

#### Success Response (200 OK)
```json
{
  "status": "ok",
  "db": true
}
```

#### Failure Response (503 Service Unavailable)
```json
{
  "status": "degraded",
  "db": false
}
```

#### Impact
Render's deployment pipeline uses this endpoint to verify each deploy succeeded before marking it live. If this returns non-200, Render rolls back the deployment automatically.

---

## ═══════════════════════════════════════
## 📌 POSTMAN SETUP GUIDE
## ═══════════════════════════════════════

### Step 1 — Set Base URL as Environment Variable
1. Open Postman → Environments → New
2. Add variable: `base_url` = `https://prework-quiz-api.onrender.com`
3. Use `{{base_url}}` in all request URLs

### Step 2 — Get Your Token
```
POST {{base_url}}/api/auth/login/
Body: { "email": "...", "password": "..." }
```
Copy the `access` value.

### Step 3 — Set Authorization
In any request:
- Click **Authorization** tab
- Select **Bearer Token**
- Paste your access token

### Step 4 — Test Order (Recommended)
```
1. POST /api/auth/register/     → create account
2. POST /api/auth/login/        → get token
3. POST /api/quizzes/           → generate quiz (AI)
4. POST /api/attempts/start/    → start attempt
5. POST /api/attempts/answer/   → answer questions
6. POST /api/attempts/submit/   → get score
7. GET  /api/analytics/me/      → view performance
```

---

## ═══════════════════════════════════════
## 📊 COMPLETE ENDPOINT REFERENCE
## ═══════════════════════════════════════

| # | Method | Endpoint | Auth | Role |
|---|---|---|---|---|
| 1 | POST | `/api/auth/register/` | ❌ | Public |
| 2 | POST | `/api/auth/login/` | ❌ | Public |
| 3 | POST | `/api/auth/token/refresh/` | ❌ | Public |
| 4 | GET/PUT | `/api/auth/me/` | ✅ | All |
| 5 | POST | `/api/quizzes/` | ✅ | All |
| 6 | GET | `/api/quizzes/` | ✅ | All |
| 7 | GET | `/api/quizzes/{id}/` | ✅ | All |
| 8 | DELETE | `/api/quizzes/{id}/` | ✅ | Admin |
| 9 | POST | `/api/attempts/start/{quiz_id}/` | ✅ | Student |
| 10 | POST | `/api/attempts/{id}/answer/` | ✅ | Student |
| 11 | POST | `/api/attempts/{id}/submit/` | ✅ | Student |
| 12 | GET | `/api/attempts/{id}/resume/` | ✅ | Student |
| 13 | GET | `/api/attempts/history/` | ✅ | Student |
| 14 | POST | `/api/attempts/{id}/event/` | ✅ | Student |
| 15 | GET | `/api/analytics/me/` | ✅ | All |
| 16 | GET/POST | `/api/admin/users/` | ✅ | Admin |
| 17 | GET/PATCH/DELETE | `/api/admin/users/{id}/` | ✅ | Admin |
| 18 | GET | `/api/admin/users/{id}/scores/` | ✅ | Admin |
| 19 | GET | `/api/logs/` | ✅ | Admin |
| 20 | GET | `/api/health/` | ❌ | Public |

**Total: 20 endpoints across 7 modules**

---

## ═══════════════════════════════════════
## 🏗️ SYSTEM ARCHITECTURE SUMMARY
## ═══════════════════════════════════════

```
CLIENT (Postman / React Frontend)
         │
         ▼
JWT Authentication Layer (SimpleJWT)
         │
         ▼
Django REST Framework Views (thin layer)
         │
         ▼
Service Layer (business logic)
    ├── UserService
    ├── QuizService ──────► AIService
    ├── AttemptService           ├── GeminiCaller
    ├── AnalyticsService         ├── OpenAICaller
    └── LogService               └── GroqCaller
         │
         ▼
PostgreSQL Database (via dj-database-url)
    ├── users
    ├── quizzes / questions / options
    ├── attempts / attempt_answers
    ├── user_analytics / topic_scores
    └── activity_logs
```

---

*Documentation generated from actual implementation — all endpoints verified via Postman during development.*