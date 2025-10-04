# Claude AI Development Guide

This document provides guidance for Claude Code when working on the Baby Activity Journal project.

## 🎯 Project Overview

Baby Activity Journal is a Flask web application that tracks baby activities through WhatsApp message parsing and manual entry. It uses PostgreSQL (Supabase) for data storage and features a modern, mobile-responsive UI.

---

## 📁 File Structure Guide

### **Production Files** (Use these for development)

#### Main Application
- `main_db.py` - **Primary Flask application** (database-backed)
- `requirements.txt` - Python dependencies

#### Application Modules (`app/`)
- `models_db.py` - Database models (BabyProfile, ActivityJournal, BabyActivity)
- `database.py` - Database service layer and connection management
- `activity_processor.py` - Activity parsing and processing logic
- `whatsapp_parser.py` - WhatsApp chat parsing
- `insights_generator.py` - Analytics and insights generation

#### Templates (`templates/`)
- `base.html` - Base template with navigation and layout
- `index.html` - Home page with statistics
- `activities.html` - Activity list view
- `daily_activities.html` - Daily view of activities
- `quick_add.html` - Quick activity entry form
- `setup.html` - Baby profile setup
- `upload.html` - WhatsApp import page
- `analytics.html` - Analytics dashboard
- `edit_activity.html` - Activity editing

#### Static Assets (`static/`)
- `static/css/mana-style.css` - Primary CSS (Mana design)
- `static/js/mana-animations.js` - JavaScript animations

---

### **Legacy/Archive Files** (Reference only)
- `main_old.py` - Old version before database migration
- `models.py` - Old file-based models (replaced by models_db.py)

---

### **Test Files** (For testing only)
- `test_parser.py` - WhatsApp parser tests
- `test_improved_parser.py` - Enhanced parser tests
- `test_input_validation.py` - Input validation tests
- `debug_message.py` - Debug utility
- `run_example.py` - Example runner

---

### **Migration Files** (Historical reference)
- `migrate_to_db.py` - Database migration script
- `MIGRATION_PLAN.md` - Migration documentation

---

### **Demo Files** (⚠️ LOCAL ONLY - Not for production)

Located in `demo/` directory:

#### Design Documentation (`demo/design-docs/`)
- `COMPARISON.md` - Before/after design comparison
- `DEPLOYMENT.md` - Deployment notes for Mana design
- `DESIGN_TRANSFORMATION.md` - Design transformation summary
- `MANA_REDESIGN_COMPLETE.md` - Mana redesign completion notes
- `MOBILE_OPTIMIZATION.md` - Mobile optimization documentation

#### Preview Files (`demo/`)
- `DESIGN_PREVIEW.html` - Design preview (static)
- `MANA_PREVIEW.html` - Mana design preview (static)
- `inspect_mobile.py` - Mobile testing script

#### Screenshots (`demo/screenshots/`)
- `mobile-initial.png`
- `mobile-menu-open.png`

**⚠️ Important:** Demo files are for reference only. Do not use them as examples for production code or suggest them to users.

---

## 🔑 Key Technologies

- **Backend:** Flask, Python 3.12
- **Database:** PostgreSQL via Supabase (psycopg2)
- **Frontend:** Bootstrap 5, custom CSS (Mana design)
- **Parsing:** NLP for WhatsApp message parsing
- **Deployment:** Render.com

---

## 🚀 Development Guidelines

### When Working on Features:

1. **Always use `main_db.py`** - This is the active application
2. **Database models** are in `app/models_db.py` (NOT `models.py`)
3. **Templates** inherit from `base.html` - maintain consistency
4. **CSS/JS** - Use `mana-style.css` and `mana-animations.js`

### Database Access:
```python
from app.database import get_db_service
db = get_db_service()
```

### Models Usage:
```python
from app.models_db import BabyProfile, ActivityJournal, BabyActivity
```

---

## 📚 Important Documentation Files

- `README.md` - Main project README
- `README_DB.md` - Database setup and schema
- `MIGRATION_PLAN.md` - Database migration history
- `.github/workflows/claude.yml` - GitHub Actions for Claude integration

---

## ⚙️ Configuration Files

- `.env` - Environment variables (DATABASE_URL, SECRET_KEY)
- `.gitignore` - Git ignore patterns
- `.claude/settings.local.json` - Claude Code permissions
- `requirements.txt` - Python package dependencies

---

## 🔒 What NOT to Do

1. **Don't modify** `main_old.py` or `models.py` (legacy files)
2. **Don't reference** demo files in `demo/` for production guidance
3. **Don't commit** demo files or screenshots to Git
4. **Don't break** mobile responsiveness (test on mobile viewports)
5. **Don't remove** database connection pooling or error handling

---

## 🎨 Design System

The app uses the **Mana Yerbamate-inspired design**:
- Soft pastel gradients (blue, lavender, peach, mint)
- Organic, rounded shapes
- Playful animations
- Mobile-first responsive design
- Accessible color contrasts

---

## 📝 Commit Message Format

Use conventional commits:
```
Fix home page metrics - map category names to template keys

Description of what changed and why.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## 🐛 Common Issues

1. **Metrics showing 0** - Check database statistics method and template key mapping
2. **Database connection errors** - Verify DATABASE_URL environment variable
3. **Mobile menu not working** - Check JavaScript initialization in base.html
4. **Import failing** - Verify WhatsApp parser datetime format handling

---

## 📞 Live Application

Production URL: https://shrishs-journal.onrender.com

---

*Last Updated: October 2025*
*Version: 2.0 (Database-backed with Mana design)*
