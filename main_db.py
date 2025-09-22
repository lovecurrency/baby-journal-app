"""
Flask web application for Baby Activity Journal with database support.
This version uses Supabase PostgreSQL instead of JSON files.
"""

import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Database-backed models
from app.models_db import BabyProfile, ActivityJournal, BabyActivity, ActivityCategory, ActivityType
from app.activity_processor import ActivityProcessor
from app.whatsapp_parser import WhatsAppParser
from app.insights_generator import InsightsGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize journal and processor
journal = ActivityJournal()
processor = ActivityProcessor()

# Load existing data on startup
try:
    journal.load_profile()
    journal.load_activities()
    logger.info("Successfully loaded data from database")
except Exception as e:
    logger.error(f"Error loading data from database: {e}")


@app.context_processor
def inject_profile():
    """Make profile available to all templates."""
    return {'profile': journal.profile}


@app.route('/')
def index():
    """Home page showing recent activities and statistics."""
    # Ensure profile is loaded
    if not journal.profile:
        journal.load_profile()

    # Load fresh activities from database
    if journal.profile:
        journal.load_activities()

    recent_activities = journal.get_recent_activities(limit=10)
    stats = journal.get_statistics()

    # Format activities for display
    activities_display = []
    for activity in recent_activities:
        act_dict = activity.to_dict()
        act_dict['timestamp_formatted'] = datetime.fromisoformat(act_dict['timestamp']).strftime('%Y-%m-%d %H:%M')
        activities_display.append(act_dict)

    # Check if profile exists for user guidance
    needs_profile = not journal.profile

    return render_template('index.html',
                         profile=journal.profile,
                         recent_activities=activities_display,
                         statistics=stats,
                         needs_profile=needs_profile)


@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Setup baby profile."""
    if request.method == 'POST':
        name = request.form.get('name')
        birth_date_str = request.form.get('birth_date')
        gender = request.form.get('gender')
        birth_weight_str = request.form.get('birth_weight')
        birth_height_str = request.form.get('birth_height')

        if name and birth_date_str:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d')

            # Parse optional numeric fields
            birth_weight = float(birth_weight_str) if birth_weight_str else None
            birth_height = float(birth_height_str) if birth_height_str else None

            try:
                profile = BabyProfile(name=name, birth_date=birth_date, gender=gender,
                                    birth_weight=birth_weight, birth_height=birth_height)
                journal.set_profile(profile)

                # Verify profile was actually saved to database
                journal.load_profile()

                # Load activities into cache for immediate availability
                if journal.profile:
                    journal.load_activities()

                if journal.profile and journal.profile.id:
                    # Double-check by querying database directly
                    from app.database import get_db_service
                    db = get_db_service()
                    db_profile = db.get_profile(journal.profile.id)

                    if db_profile:
                        flash(f'Baby profile created successfully! Profile ID: {journal.profile.id}', 'success')
                        logger.info(f"Profile verification successful - found in database: {db_profile}")
                    else:
                        flash('Profile appeared to save but not found in database. Please try again.', 'error')
                        logger.error(f"Profile not found in database after save: {journal.profile.id}")
                else:
                    flash('Profile creation failed - not found after save. Please try again.', 'error')
                    logger.error("Profile not loaded after creation")

                return redirect(url_for('index'))
            except Exception as e:
                logger.error(f"Error creating profile: {e}")
                import traceback
                logger.error(f"Profile creation traceback: {traceback.format_exc()}")
                flash(f'Error creating profile: {str(e)}', 'error')

    return render_template('setup.html', profile=journal.profile)


@app.route('/upload', methods=['GET', 'POST'])
def upload_whatsapp():
    """Upload and process WhatsApp chat export."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and file.filename.endswith('.txt'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # Process the WhatsApp file
                activities = processor.process_whatsapp_file(filepath)

                # Add activities to journal
                saved_count = 0
                for activity in activities:
                    try:
                        journal.add_activity(activity)
                        saved_count += 1
                    except Exception as e:
                        logger.error(f"Failed to save activity: {e}")

                # Reload activities from database to update display
                journal.load_activities()

                if saved_count > 0:
                    flash(f'Successfully processed and saved {saved_count} activities!', 'success')
                else:
                    flash('No activities were saved. Please check if you have created a baby profile first.', 'warning')

                return redirect(url_for('index'))

            except Exception as e:
                logger.error(f"Error processing WhatsApp file: {e}")
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(request.url)

    return render_template('upload.html')


@app.route('/quick_add', methods=['GET', 'POST'])
def quick_add():
    """Quick add activity form."""
    if request.method == 'POST':
        message = request.form.get('message')
        activity_type = request.form.get('activity_type', 'other')

        if message:
            try:
                # Process the message
                activity = processor.process_message(message, sender='Manual Entry')

                if activity:
                    journal.add_activity(activity)
                    flash('Activity added successfully!', 'success')
                else:
                    # Create a basic activity if processing fails
                    activity = BabyActivity(
                        timestamp=datetime.now(),
                        category=ActivityCategory.OTHER,
                        activity_type=ActivityType.OTHER,
                        description=message,
                        notes=message,
                        source='manual'
                    )
                    journal.add_activity(activity)
                    flash('Activity added (uncategorized)', 'info')

                # Reload activities to update display
                journal.load_activities()

            except Exception as e:
                logger.error(f"Error adding activity: {e}")
                flash(f'Error adding activity: {str(e)}', 'error')

            return redirect(url_for('index'))

    return render_template('quick_add.html')


@app.route('/activities')
def activities():
    """View all activities with filtering."""
    # Get filter parameters
    date_filter = request.args.get('date')
    category_filter = request.args.get('category')

    # Get activities based on filters
    if date_filter:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d')
        filtered_activities = journal.get_activities_by_date(filter_date)
    elif category_filter:
        filtered_activities = journal.get_activities_by_category(ActivityCategory(category_filter))
    else:
        filtered_activities = journal.get_recent_activities(limit=100)  # Get recent 100 instead of all

    # Sort by timestamp (newest first)
    filtered_activities = sorted(filtered_activities, key=lambda x: x.timestamp, reverse=True)

    # Format for display
    activities_display = []
    for activity in filtered_activities:
        act_dict = activity.to_dict()
        act_dict['timestamp_formatted'] = datetime.fromisoformat(act_dict['timestamp']).strftime('%Y-%m-%d %H:%M')
        activities_display.append(act_dict)

    # Get categories for filter dropdown
    categories = [cat.value for cat in ActivityCategory]

    return render_template('activities.html',
                         activities=activities_display,
                         categories=categories,
                         selected_date=date_filter,
                         selected_category=category_filter)


@app.route('/analytics')
def analytics():
    """Enhanced analytics and visualizations page."""
    # Load profile and activities into cache (like original working version)
    if not journal.profile:
        journal.load_profile()

    if journal.profile:
        journal.load_activities()  # Populate journal.activities cache

    # Get statistics
    stats = journal.get_statistics()

    # Prepare data for charts (restored to original simple approach)
    if journal.activities:
        # Activities by hour of day
        hour_distribution = [0] * 24
        for activity in journal.activities:
            hour = activity.timestamp.hour
            hour_distribution[hour] += 1

        # Activities by day of week
        weekday_distribution = [0] * 7
        for activity in journal.activities:
            weekday = activity.timestamp.weekday()
            weekday_distribution[weekday] += 1

        # Recent 7 days trend
        today = datetime.now().date()
        daily_counts = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            count = len([a for a in journal.activities if a.timestamp.date() == date])
            daily_counts.append({
                'date': date.strftime('%m/%d'),
                'count': count
            })

        # Calculate feeding insights
        feeding_activities = [a for a in journal.activities if a.category.value == 'feeding']
        feeding_insights = {
            'avg_amount': 0,
            'avg_gap_hours': 0,
            'bottle_percentage': 0,
            'daily_trend': [],
            'daily_avg_total': 0,
            'weekly_avg_total': 0
        }

        if feeding_activities:
            # Average amount
            amounts = [a.amount for a in feeding_activities if a.amount]
            if amounts:
                feeding_insights['avg_amount'] = round(sum(amounts) / len(amounts), 1)

            # Calculate daily feeding trend for last 7 days
            for i in range(6, -1, -1):
                date = today - timedelta(days=i)
                day_feedings = [a for a in feeding_activities if a.timestamp.date() == date]
                daily_amounts = [a.amount for a in day_feedings if a.amount]
                total_amount = sum(daily_amounts) if daily_amounts else 0
                feeding_insights['daily_trend'].append({
                    'date': date.strftime('%a'),
                    'amount': round(total_amount, 1),
                    'count': len(day_feedings)
                })

            # Bottle percentage
            bottle_feeds = len([a for a in feeding_activities if 'bottle' in a.activity_type.value])
            feeding_insights['bottle_percentage'] = round((bottle_feeds / len(feeding_activities)) * 100, 1)

            # Daily and weekly average totals
            daily_totals = []
            for i in range(7):  # Last 7 days
                date = today - timedelta(days=i)
                day_feedings = [a for a in feeding_activities if a.timestamp.date() == date]
                daily_amounts = [a.amount for a in day_feedings if a.amount]
                daily_total = sum(daily_amounts) if daily_amounts else 0
                if daily_total > 0:  # Only count days with feeding data
                    daily_totals.append(daily_total)

            if daily_totals:
                feeding_insights['daily_avg_total'] = round(sum(daily_totals) / len(daily_totals), 1)
                feeding_insights['weekly_avg_total'] = round(sum(daily_totals), 1)

        # Calculate sleep insights
        sleep_activities = [a for a in journal.activities if a.category.value == 'sleep']
        sleep_insights = {
            'total_daily_sleep': 0,
            'night_sleep_avg': 0,
            'nap_count': 0,
            'sleep_efficiency': 0,
            'sleep_pattern': [],
            'day_sleep_avg': 0,
            'daily_trend': []
        }

        if sleep_activities:
            # Calculate average daily sleep
            durations = [a.duration_minutes for a in sleep_activities if a.duration_minutes]
            if durations:
                total_minutes = sum(durations)
                sleep_insights['total_daily_sleep'] = round(total_minutes / 60, 1)

                # Sleep pattern by type
                night_sleeps = [a for a in sleep_activities if 'night' in a.activity_type.value.lower()]
                naps = [a for a in sleep_activities if 'nap' in a.activity_type.value.lower()]

                if night_sleeps:
                    night_durations = [a.duration_minutes for a in night_sleeps if a.duration_minutes]
                    if night_durations:
                        sleep_insights['night_sleep_avg'] = round(sum(night_durations) / len(night_durations) / 60, 1)

                sleep_insights['nap_count'] = len(naps)
                sleep_insights['sleep_efficiency'] = min(95, round((total_minutes / (24 * 60)) * 100 * 2, 1))  # Rough calculation

                # Calculate day sleep (6 AM to 9 PM)
                day_sleep_minutes = 0
                for activity in sleep_activities:
                    if activity.duration_minutes and 6 <= activity.timestamp.hour <= 21:
                        day_sleep_minutes += activity.duration_minutes

                sleep_insights['day_sleep_avg'] = round(day_sleep_minutes / 60, 1)

        # Generate dynamic insights if insights generator is available
        try:
            insights_generator = InsightsGenerator(journal.activities)
            feeding_dynamic_insights = insights_generator.generate_feeding_insights()
            sleep_dynamic_insights = insights_generator.generate_sleep_insights()
        except Exception as e:
            logger.warning(f"Could not generate dynamic insights: {e}")
            feeding_dynamic_insights = []
            sleep_dynamic_insights = []

        chart_data = {
            'hourly': hour_distribution,
            'weekday': weekday_distribution,
            'daily_trend': daily_counts,
            'feeding_insights': feeding_insights,
            'sleep_insights': sleep_insights,
            'feeding_dynamic_insights': feeding_dynamic_insights,
            'sleep_dynamic_insights': sleep_dynamic_insights
        }
    else:
        chart_data = None

    return render_template('analytics_enhanced.html',
                         statistics=stats,
                         chart_data=chart_data)


@app.route('/debug')
def debug_dashboard():
    """Debug dashboard to show database connectivity and data status."""
    try:
        debug_info = {
            'database_status': 'Unknown',
            'profile_info': {},
            'activity_summary': {},
            'sample_activities': [],
            'errors': []
        }

        # Test database connectivity
        try:
            db = get_db_service()
            debug_info['database_status'] = 'Connected'
        except Exception as e:
            debug_info['database_status'] = f'Failed: {str(e)}'
            debug_info['errors'].append(f"Database connection error: {e}")

        # Get profile information
        try:
            profile_data = db.get_profile()
            if profile_data:
                debug_info['profile_info'] = {
                    'id': profile_data['id'],
                    'name': profile_data['name'],
                    'birth_date': str(profile_data['birth_date']),
                    'gender': profile_data['gender'],
                    'created_at': str(profile_data['created_at'])
                }
            else:
                debug_info['profile_info'] = {'status': 'No profile found'}
        except Exception as e:
            debug_info['errors'].append(f"Profile query error: {e}")

        # Get activity summary
        try:
            if profile_data:
                activities = db.get_activities(profile_data['id'], limit=100)
                debug_info['activity_summary'] = {
                    'total_count': len(activities),
                    'categories': {},
                    'date_range': {}
                }

                if activities:
                    # Category breakdown
                    for activity in activities:
                        cat = activity.get('category', 'unknown')
                        debug_info['activity_summary']['categories'][cat] = debug_info['activity_summary']['categories'].get(cat, 0) + 1

                    # Date range
                    timestamps = [a['timestamp'] for a in activities if a.get('timestamp')]
                    if timestamps:
                        debug_info['activity_summary']['date_range'] = {
                            'earliest': str(min(timestamps)),
                            'latest': str(max(timestamps))
                        }

                    # Sample activities (first 5)
                    debug_info['sample_activities'] = [
                        {
                            'id': a.get('id', 'N/A'),
                            'timestamp': str(a.get('timestamp', 'N/A')),
                            'category': a.get('category', 'N/A'),
                            'activity_type': a.get('activity_type', 'N/A'),
                            'description': a.get('description', 'N/A')[:100],
                            'amount': a.get('amount'),
                            'unit': a.get('unit')
                        }
                        for a in activities[:5]
                    ]
        except Exception as e:
            debug_info['errors'].append(f"Activity query error: {e}")

        # Test journal loading
        try:
            journal.load_profile()
            if journal.profile:
                debug_info['journal_profile_status'] = f"Loaded: {journal.profile.name}"
                journal_activities = journal.get_recent_activities(limit=10)
                debug_info['journal_activities_count'] = len(journal_activities)
            else:
                debug_info['journal_profile_status'] = "Not loaded"
                debug_info['journal_activities_count'] = 0
        except Exception as e:
            debug_info['errors'].append(f"Journal loading error: {e}")

        return f"""
        <html>
        <head><title>Debug Dashboard</title></head>
        <body style="font-family: monospace; margin: 20px;">
        <h1>Baby Journal Debug Dashboard</h1>

        <h2>Database Status</h2>
        <p><strong>Connection:</strong> {debug_info['database_status']}</p>

        <h2>Profile Information</h2>
        <pre>{debug_info['profile_info']}</pre>

        <h2>Activity Summary</h2>
        <pre>{debug_info['activity_summary']}</pre>

        <h2>Journal Loading Status</h2>
        <p><strong>Profile:</strong> {debug_info.get('journal_profile_status', 'Unknown')}</p>
        <p><strong>Activities Count:</strong> {debug_info.get('journal_activities_count', 'Unknown')}</p>

        <h2>Sample Activities</h2>
        <pre>{debug_info['sample_activities']}</pre>

        <h2>Errors</h2>
        <pre>{debug_info['errors']}</pre>

        <p><a href="/">← Back to Home</a> | <a href="/analytics">Analytics Page</a></p>
        </body>
        </html>
        """

    except Exception as e:
        return f"Debug dashboard error: {str(e)}", 500


@app.route('/api/activity', methods=['POST'])
def api_add_activity():
    """API endpoint to add activity from WhatsApp message."""
    data = request.json

    if not data or 'message' not in data:
        return jsonify({'error': 'Message required'}), 400

    message = data['message']
    sender = data.get('sender', 'API')

    # Process message
    activity = processor.process_message(message, sender)

    if activity:
        journal.add_activity(activity)
        return jsonify({
            'success': True,
            'activity': activity.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Could not extract activity from message'
        }), 400


@app.route('/api/statistics')
def api_statistics():
    """API endpoint to get statistics."""
    stats = journal.get_statistics()
    return jsonify(stats)


@app.route('/api/activity/<activity_id>', methods=['DELETE'])
def api_delete_activity(activity_id):
    """API endpoint to delete an activity by ID."""
    try:
        if journal.delete_activity_by_id(activity_id):
            return jsonify({
                'success': True,
                'message': 'Activity deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Activity not found'
            }), 404
    except Exception as e:
        logger.error(f"Error deleting activity: {e}")
        return jsonify({
            'success': False,
            'message': f'Error deleting activity: {str(e)}'
        }), 500


@app.route('/clear_all_activities', methods=['POST'])
def clear_all_activities():
    """Clear all activities (with confirmation)."""
    confirmation = request.form.get('confirmation')
    if confirmation == 'DELETE_ALL_ACTIVITIES':
        # For database version, we need to delete from database
        if journal.profile:
            try:
                from app.database import get_db_service
                db = get_db_service()
                # Delete all activities for this profile
                db.execute_query(
                    "DELETE FROM baby_activities WHERE profile_id = %s",
                    (journal.profile.id,),
                    fetch=False
                )
                journal.activities = []  # Clear cache
                flash('All activities have been deleted.', 'success')
            except Exception as e:
                logger.error(f"Error clearing activities: {e}")
                flash('Error deleting activities.', 'error')
        else:
            flash('No profile found.', 'error')
    else:
        flash('Incorrect confirmation. Activities not deleted.', 'error')

    return redirect(url_for('activities'))


@app.route('/api/activity/<activity_id>', methods=['PUT'])
def api_update_activity(activity_id):
    """API endpoint to update an activity."""
    try:
        activity = journal.get_activity_by_id(activity_id)
        if activity:
            data = request.json

            # Update fields if provided
            updates = {}
            for field in ['category', 'activity_type', 'timestamp', 'description',
                         'amount', 'unit', 'duration_minutes', 'notes']:
                if field in data:
                    if field == 'category':
                        updates[field] = ActivityCategory(data[field])
                    elif field == 'activity_type':
                        updates[field] = ActivityType(data[field])
                    elif field == 'timestamp':
                        updates[field] = datetime.fromisoformat(data[field])
                    else:
                        updates[field] = data[field]

            # Use the journal's update method
            if journal.update_activity_by_id(activity_id, updates):
                updated_activity = journal.get_activity_by_id(activity_id)
                return jsonify({
                    'success': True,
                    'message': 'Activity updated successfully',
                    'activity': updated_activity.to_dict()
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to update activity'
                }), 500
        else:
            return jsonify({
                'success': False,
                'message': 'Activity not found'
            }), 404
    except Exception as e:
        logger.error(f"Error updating activity: {e}")
        return jsonify({
            'success': False,
            'message': f'Error updating activity: {str(e)}'
        }), 500


@app.route('/edit_activity/<activity_id>')
def edit_activity(activity_id):
    """Edit activity page."""
    activity = journal.get_activity_by_id(activity_id)
    if activity:
        categories = [cat.value for cat in ActivityCategory]
        activity_types = [atype.value for atype in ActivityType]

        return render_template('edit_activity.html',
                             activity=activity.to_dict(),
                             activity_id=activity_id,
                             categories=categories,
                             activity_types=activity_types)
    else:
        flash('Activity not found', 'error')
        return redirect(url_for('activities'))


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test database connection
        from app.database import get_db_service
        db = get_db_service()
        test_result = db.db.execute_query("SELECT 1 as test;")

        # Test table existence
        tables_result = db.db.execute_query("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name IN ('baby_profiles', 'baby_activities');
        """)

        tables = [row['table_name'] for row in tables_result] if tables_result else []

        # Test profile operations
        profile_count = db.db.execute_query("SELECT COUNT(*) as count FROM baby_profiles;")
        activity_count = db.db.execute_query("SELECT COUNT(*) as count FROM baby_activities;")

        # Check table structure
        profile_columns = db.db.execute_query("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'baby_profiles'
            ORDER BY ordinal_position;
        """)

        activity_columns = db.db.execute_query("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'baby_activities'
            ORDER BY ordinal_position;
        """)

        # Test a simple insert to validate the mechanism
        try:
            test_insert_result = db.db.execute_insert_returning(
                "SELECT gen_random_uuid() as id;", ()
            )
            insert_test = f"UUID generation works: {test_insert_result}"
        except Exception as e:
            insert_test = f"UUID generation failed: {str(e)}"

        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'tables': tables,
            'profiles_count': profile_count[0]['count'] if profile_count else 0,
            'activities_count': activity_count[0]['count'] if activity_count else 0,
            'profile_columns': profile_columns,
            'activity_columns': activity_columns,
            'insert_test': insert_test,
            'test_query': test_result[0] if test_result else None,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        import traceback
        logger.error(f"Health check traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)