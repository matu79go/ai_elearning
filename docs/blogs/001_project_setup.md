# Blog #001: Project Setup - Building an AI e-Learning Platform from Scratch

**Date:** 2026-03-11

## Overview

This is the first entry in our development blog for the AI e-Learning project — a platform that uses LLMs to auto-generate questions from learning materials for children.

## What We Built Today

### 1. Project Architecture

We modeled the project structure after an existing Flask/MySQL/Docker project (`kabu`), adapting it for e-learning:

- **Docker Compose** with 3 services: Flask app, MySQL 8.0, phpMyAdmin (dev only)
- **MySQL** configured with `utf8mb4` from the start to avoid Japanese encoding issues
- **Flask** with SQLAlchemy, Flask-Login for authentication

### 2. Database Schema (9 tables)

Designed a complete schema covering:
- `users` — parent/child accounts with role-based access
- `materials` — learning content (text or URL)
- `questions` — LLM-generated questions with multiple types
- `learning_sessions` / `answer_history` — tracking study progress
- `point_history` — flexible point system (speed bonus, weakness clear bonus, streak bonus)
- `badges` / `user_badges` — achievement/badge system
- `notification_settings` — email notifications for parents

### 3. Security Considerations

Since this repo will be **public on GitHub**:
- All secrets stored in `.env` (excluded via `.gitignore`)
- `config.py` uses `os.getenv()` with empty defaults — no hardcoded passwords
- `docker-compose.yml` uses `${VARIABLE}` references only
- Caught and fixed a default password value in `config.py` before any commit was made

### 4. Internationalization (i18n)

Implemented a custom i18n system:
- **Dictionary files**: `translations/en.json` and `translations/ja.json`
- **URL-based routing**: `/` for English (default), `/ja/` for Japanese
- **Language toggle**: Button in top-right corner on every page
- **Rule**: All display text must come from dictionary files — no hardcoded strings in templates

### 5. Mobile Optimization

All templates use Tailwind CSS responsive utilities:
- `sm:`, `md:`, `lg:` breakpoints for adaptive layouts
- `active:scale-95` for touch feedback on mobile
- Flexible grid layouts (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`)

### 6. Claude Code Skills

Downloaded 5 community skills for development workflow:
- `test-driven-development` — TDD workflow
- `systematic-debugging` — Structured debugging approach
- `owasp-security` — Security best practices
- `webapp-testing` — Playwright web app testing
- `mysql` — Safe MySQL operations

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11 / Flask 3.x |
| Database | MySQL 8.0 (utf8mb4, InnoDB) |
| Frontend | Jinja2 + Tailwind CSS (CDN) |
| Auth | Flask-Login + bcrypt |
| Container | Docker / Docker Compose |
| i18n | Custom JSON dictionary system |
| Production | Sakura VPS (planned) |

## Key Decisions

1. **Custom i18n over Flask-Babel** — Simpler, lighter, URL-based language switching fits our needs better than gettext
2. **Tailwind CDN over npm build** — Keeps the stack simple for now; can switch to build later if needed
3. **phpMyAdmin for dev only** — Added via `docker-compose.override.yml` (gitignored), not deployed to production

## Next Steps

- [ ] Implement login/registration
- [ ] Build the material registration & LLM question generation flow
- [ ] Create the question-answering UI with animations and sound effects
- [ ] Implement the point calculation engine
- [ ] Set up parent notification system
