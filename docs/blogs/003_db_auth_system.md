# Blog #003: Database Redesign & Authentication System

**Date:** 2026-03-11

## Overview

Separated the user model into parents and children, implemented a family code system for child login, and built the complete authentication flow with Flask Blueprints.

## Database Changes

### Parents & Children Separation

The original single `users` table was split into dedicated tables:

- **`parents`** — Email + password authentication, auto-generated `family_code`
- **`children`** — Display name + 4-digit PIN authentication, linked to parents
- **`parent_children`** — Many-to-many junction table (both parents can manage multiple kids)

### Family Code System

Each parent gets a unique 6-character alphanumeric code (e.g. `ABC123`) on registration. Children use this code to find their family, then select their name and enter a PIN. This avoids children needing email addresses or complex passwords.

Design choices:
- Excluded confusing characters (0/O, 1/I/L) from the alphabet
- Collision check on generation
- Displayed prominently in the admin panel with copy button

### Bilingual Master Data Convention

New rule: all master tables must have `_en` / `_ja` suffix columns for bilingual support.

```sql
-- Example: badges table
name_en VARCHAR(100), name_ja VARCHAR(100),
description_en TEXT, description_ja TEXT
```

### SQL File Reorganization

- `sql/001_init.sql` → `sql/01_schema.sql` + `sql/02_master_data.sql`
- Files are prefixed with numbers for Docker entrypoint execution order

## Flask Architecture Refactoring

### Blueprint Structure

Refactored from a monolithic `app.py` into feature-based modules:

```
app.py              → App init + i18n only (thin)
models/
├── __init__.py      → db = SQLAlchemy()
├── parent.py        → Parent, ParentChild
└── child.py         → Child
routes/
├── __init__.py      → dual_route() helper
├── top.py           → Landing page
├── auth.py          → Parent login/register, Child login (family code + PIN)
├── child_dashboard.py
├── child_study.py
├── admin_dashboard.py
└── admin_children.py → Child account CRUD for parents
```

### `dual_route()` Helper

A decorator that registers both `/path` and `/ja/path` routes, eliminating duplicated route definitions:

```python
@dual_route(bp, '/parent/login', methods=['GET', 'POST'])
def parent_login():
    ...
```

## Authentication Flows

### Parent Flow
1. Register with email + password → family code auto-generated
2. Login with email + password → admin dashboard
3. Session persists — visiting `/parent/login` while logged in redirects to dashboard

### Child Flow
1. Enter family code → shows children for that family only
2. Select name → enter 4-digit PIN → child dashboard
3. Logout available via profile tab in bottom navigation

### Admin: Child Management (`/admin/children`)
- Family code displayed with copy button
- Add child form (name, grade, PIN)
- Child list with stats (points, level, streak)
- Delete with confirmation

## UI Updates

### Admin Header
- User name + avatar displayed in header (right side, kabu-style)
- Logout button (icon-only on mobile, text on desktop)
- Removed date/time display from header

### Child Dashboard
- Hero shows logged-in child's name: "Hello Taro! 👋"
- Stats (points, level, streak) pulled from DB
- Profile tab in bottom nav → popup menu with logout

## Rules Added

- **CLAUDE.md Rule 9**: DB design rules reference `docs/database.md`
- **docs/database.md**: Bilingual master data convention documented
