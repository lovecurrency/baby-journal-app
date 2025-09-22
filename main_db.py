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
    try:
        logger.info("Analytics route accessed - starting processing")

        # Get basic statistics with error handling
        try:
            logger.info("Getting statistics from journal")
            stats = journal.get_statistics()
            logger.info(f"Statistics retrieved: {stats}")
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            stats = {}

        # Get recent activities for chart calculations with error handling
        try:
            logger.info("Getting recent activities for analytics")

            # Force reload profile from database - don't rely on session
            logger.info("Force reloading profile from database for analytics")
            journal.load_profile()

            if journal.profile:
                logger.info(f"Profile loaded successfully: {journal.profile.name} (ID: {journal.profile.id})")
            else:
                logger.error("No profile could be loaded from database")
                # Try direct database query as fallback
                try:
                    logger.info("Attempting direct database query for profile")
                    db = get_db_service()
                    profile_data = db.get_profile()
                    if profile_data:
                        logger.info(f"Found profile via direct query: {profile_data['name']} (ID: {profile_data['id']})")
                        from app.models_db import BabyProfile
                        journal.profile = BabyProfile.from_db_row(profile_data)
                        logger.info(f"Profile loaded via direct query: {journal.profile.name}")
                    else:
                        logger.error("No profile found even with direct database query")
                except Exception as direct_e:
                    logger.error(f"Direct database query also failed: {direct_e}")

            if journal.profile:
                recent_activities = journal.get_recent_activities(limit=1000)
                logger.info(f"Retrieved {len(recent_activities)} recent activities")
            else:
                logger.error("Cannot get activities - no profile available")
                recent_activities = []

            # Log some details about the activities if any exist
            if recent_activities:
                logger.info(f"Sample activity: {recent_activities[0].description[:50]}...")
                categories = {}
                for activity in recent_activities[:10]:  # Check first 10
                    cat = activity.category.value if activity.category else 'unknown'
                    categories[cat] = categories.get(cat, 0) + 1
                logger.info(f"Activity categories found: {categories}")
            else:
                logger.warning("No activities retrieved - checking database directly")
                # Try to get total activity count from database
                try:
                    if journal.profile:
                        total_stats = journal.get_statistics()
                        logger.info(f"Database statistics: {total_stats}")
                    else:
                        logger.error("Cannot check database statistics - no profile loaded")
                except Exception as db_e:
                    logger.error(f"Error getting database statistics: {db_e}")

        except Exception as e:
            logger.error(f"Error getting recent activities: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            recent_activities = []

        # Initialize default chart data
        chart_data = None

        # Prepare data for charts with comprehensive error handling
        if recent_activities:
            try:
                logger.info("Processing hourly distribution")
                # Activities by hour of day
                hour_distribution = [0] * 24
                for activity in recent_activities:
                    try:
                        if hasattr(activity, 'timestamp') and activity.timestamp:
                            hour = activity.timestamp.hour
                            if 0 <= hour <= 23:
                                hour_distribution[hour] += 1
                    except Exception as e:
                        logger.warning(f"Error processing activity timestamp for hourly distribution: {e}")
                        continue
                logger.info("Hourly distribution completed")

                logger.info("Processing weekday distribution")
                # Activities by day of week
                weekday_distribution = [0] * 7
                for activity in recent_activities:
                    try:
                        if hasattr(activity, 'timestamp') and activity.timestamp:
                            weekday = activity.timestamp.weekday()
                            if 0 <= weekday <= 6:
                                weekday_distribution[weekday] += 1
                    except Exception as e:
                        logger.warning(f"Error processing activity timestamp for weekday distribution: {e}")
                        continue
                logger.info("Weekday distribution completed")

                logger.info("Processing daily trend")
                # Recent 7 days trend
                today = datetime.now().date()
                daily_counts = []
                for i in range(6, -1, -1):
                    try:
                        date = today - timedelta(days=i)
                        count = len([a for a in recent_activities if hasattr(a, 'timestamp') and a.timestamp and a.timestamp.date() == date])
                        daily_counts.append({
                            'date': date.strftime('%m/%d'),
                            'count': count
                        })
                    except Exception as e:
                        logger.warning(f"Error processing daily trend for day {i}: {e}")
                        continue
                logger.info("Daily trend completed")

                logger.info("Processing feeding insights")
                # Calculate feeding insights with safe filtering
                try:
                    feeding_activities = []
                    for a in recent_activities:
                        try:
                            if hasattr(a, 'category') and a.category and hasattr(a.category, 'value') and a.category.value == 'feeding':
                                feeding_activities.append(a)
                        except Exception as e:
                            logger.warning(f"Error filtering feeding activity: {e}")
                            continue

                    feeding_insights = {
                        'avg_amount': 0,
                        'avg_gap_hours': 0,
                        'bottle_percentage': 0,
                        'daily_trend': [],
                        'daily_avg_total': 0,
                        'weekly_avg_total': 0
                    }

                    if feeding_activities:
                        logger.info(f"Processing {len(feeding_activities)} feeding activities")
                        # Average amount with safe extraction
                        amounts = []
                        for a in feeding_activities:
                            try:
                                if hasattr(a, 'amount') and a.amount and isinstance(a.amount, (int, float)) and a.amount > 0:
                                    amounts.append(a.amount)
                            except Exception as e:
                                logger.warning(f"Error extracting amount from feeding activity: {e}")
                                continue

                        if amounts:
                            feeding_insights['avg_amount'] = round(sum(amounts) / len(amounts), 1)
                            logger.info(f"Average feeding amount calculated: {feeding_insights['avg_amount']}")

                        # Calculate daily feeding trend for last 7 days
                        for i in range(6, -1, -1):
                            try:
                                date = today - timedelta(days=i)
                                day_feedings = [a for a in feeding_activities if hasattr(a, 'timestamp') and a.timestamp and a.timestamp.date() == date]
                                daily_amounts = []
                                for a in day_feedings:
                                    try:
                                        if hasattr(a, 'amount') and a.amount and isinstance(a.amount, (int, float)) and a.amount > 0:
                                            daily_amounts.append(a.amount)
                                    except Exception as e:
                                        logger.warning(f"Error extracting daily amount: {e}")
                                        continue

                                total_amount = sum(daily_amounts) if daily_amounts else 0
                                feeding_insights['daily_trend'].append({
                                    'date': date.strftime('%a'),
                                    'amount': round(total_amount, 1) if total_amount else 0,
                                    'count': len(day_feedings)
                                })
                            except Exception as e:
                                logger.warning(f"Error processing feeding daily trend for day {i}: {e}")
                                continue

                        # Bottle percentage with safe type checking
                        try:
                            bottle_feeds = 0
                            for a in feeding_activities:
                                try:
                                    if hasattr(a, 'activity_type') and a.activity_type and hasattr(a.activity_type, 'value') and 'bottle' in str(a.activity_type.value).lower():
                                        bottle_feeds += 1
                                except Exception as e:
                                    logger.warning(f"Error checking bottle feed type: {e}")
                                    continue

                            if len(feeding_activities) > 0:
                                feeding_insights['bottle_percentage'] = round((bottle_feeds / len(feeding_activities)) * 100, 1)
                                logger.info(f"Bottle percentage calculated: {feeding_insights['bottle_percentage']}%")
                        except Exception as e:
                            logger.warning(f"Error calculating bottle percentage: {e}")
                            feeding_insights['bottle_percentage'] = 0

                except Exception as e:
                    logger.error(f"Error in feeding insights calculation: {e}")
                    feeding_insights = {
                        'avg_amount': 0,
                        'avg_gap_hours': 0,
                        'bottle_percentage': 0,
                        'daily_trend': [],
                        'daily_avg_total': 0,
                        'weekly_avg_total': 0
                    }

                logger.info("Processing sleep insights")
                # Calculate sleep insights with safe filtering
                try:
                    sleep_activities = []
                    for a in recent_activities:
                        try:
                            if hasattr(a, 'category') and a.category and hasattr(a.category, 'value') and a.category.value == 'sleep':
                                sleep_activities.append(a)
                        except Exception as e:
                            logger.warning(f"Error filtering sleep activity: {e}")
                            continue

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
                        logger.info(f"Processing {len(sleep_activities)} sleep activities")
                        # Calculate average daily sleep with safe duration extraction
                        durations = []
                        for a in sleep_activities:
                            try:
                                if hasattr(a, 'duration_minutes') and a.duration_minutes and isinstance(a.duration_minutes, (int, float)) and a.duration_minutes > 0:
                                    durations.append(a.duration_minutes)
                            except Exception as e:
                                logger.warning(f"Error extracting duration from sleep activity: {e}")
                                continue

                        if durations:
                            total_minutes = sum(durations)
                            sleep_insights['total_daily_sleep'] = round(total_minutes / 60, 1)
                            logger.info(f"Total daily sleep calculated: {sleep_insights['total_daily_sleep']} hours")

                except Exception as e:
                    logger.error(f"Error in sleep insights calculation: {e}")
                    sleep_insights = {
                        'total_daily_sleep': 0,
                        'night_sleep_avg': 0,
                        'nap_count': 0,
                        'sleep_efficiency': 0,
                        'sleep_pattern': [],
                        'day_sleep_avg': 0,
                        'daily_trend': []
                    }

                logger.info("Processing dynamic insights")
                # Generate dynamic insights with error handling
                feeding_dynamic_insights = []
                sleep_dynamic_insights = []
                try:
                    insights_generator = InsightsGenerator(recent_activities)
                    feeding_dynamic_insights = insights_generator.generate_feeding_insights()
                    sleep_dynamic_insights = insights_generator.generate_sleep_insights()
                    logger.info(f"Dynamic insights generated - feeding: {len(feeding_dynamic_insights)}, sleep: {len(sleep_dynamic_insights)}")
                except Exception as e:
                    logger.warning(f"Could not generate dynamic insights: {e}")
                    feeding_dynamic_insights = []
                    sleep_dynamic_insights = []

                logger.info("Assembling chart data")
                chart_data = {
                    'hourly': hour_distribution,
                    'weekday': weekday_distribution,
                    'daily_trend': daily_counts,
                    'feeding_insights': feeding_insights,
                    'sleep_insights': sleep_insights,
                    'feeding_dynamic_insights': feeding_dynamic_insights,
                    'sleep_dynamic_insights': sleep_dynamic_insights
                }
                logger.info("Chart data assembled successfully")

            except Exception as e:
                logger.error(f"Error processing chart data: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                chart_data = None
        else:
            logger.info("No recent activities found, setting chart_data to None")
            chart_data = None

        logger.info("Rendering analytics template")
        return render_template('analytics_enhanced.html',
                             statistics=stats,
                             chart_data=chart_data)

    except Exception as e:
        logger.error(f"Critical error in analytics route: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")

        # Return a safe error page
        try:
            return render_template('analytics_enhanced.html',
                                 statistics={},
                                 chart_data=None,
                                 error_message="An error occurred while generating analytics. Please try again later.")
        except Exception as template_error:
            logger.error(f"Error rendering error template: {template_error}")
            return f"Analytics temporarily unavailable. Error: {str(e)}", 500


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