# Database Migration Guide

Your Baby Journal app now supports Supabase PostgreSQL database for persistent data storage! 🎉

## Quick Setup Instructions

### 1. Set up Supabase Database

1. **Create Supabase Account**: Go to [supabase.com](https://supabase.com) and sign up
2. **Create New Project**: Choose a project name and password
3. **Get Connection Details**: Go to Settings > Database and copy the connection string

### 2. Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Copy from .env.example
cp .env.example .env
```

Update the `.env` file with your Supabase connection string:

```bash
DATABASE_URL=postgresql://postgres.user:password@host:5432/postgres
SECRET_KEY=your-secret-key-here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Migration (If You Have Existing Data)

If you have existing JSON data files, migrate them to the database:

```bash
python migrate_to_db.py
```

This will:
- Back up your JSON files
- Create database tables
- Transfer all your existing data
- Optionally remove the JSON files

### 5. Run the Database Version

Use the database-enabled version of the app:

```bash
python main_db.py
```

## Files Overview

- **`main_db.py`** - Database-enabled Flask application
- **`app/database.py`** - Database connection and service layer
- **`app/models_db.py`** - Database-backed models
- **`migrate_to_db.py`** - Migration script for existing JSON data

## Key Benefits

✅ **Persistent Storage** - Data survives deployments and restarts
✅ **No Data Loss** - Reliable PostgreSQL database
✅ **Scalable** - Handles thousands of activities efficiently
✅ **Free Tier** - Supabase offers generous free usage
✅ **Backup & Recovery** - Built-in database features

## Deploy to Render with Database

When deploying to Render, add this environment variable:

- **DATABASE_URL**: Your Supabase connection string

The app will automatically create tables on first run.

## Switching Between Versions

- **JSON Version**: `python main.py` (original)
- **Database Version**: `python main_db.py` (new)

Both versions have the same features, but the database version offers persistent storage.

## Troubleshooting

**Connection Issues?**
- Check your DATABASE_URL format
- Ensure Supabase project is active
- Verify network connectivity

**Migration Problems?**
- Run `python migrate_to_db.py` to diagnose
- Check backup files in `data_backup/`
- Original JSON files are preserved until you choose to remove them

**Need Help?**
- Check Supabase logs in your dashboard
- Verify environment variables are set correctly
- Test connection with the health check endpoint: `/health`