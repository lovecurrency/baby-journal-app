"""
Flask web application for Baby Activity Journal with database support.
This version uses Supabase PostgreSQL instead of JSON files.
"""

import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_cors import CORS
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

# Configure CORS for Next.js frontend
CORS(app, origins=[
    'http://localhost:3000',  # Next.js development server
    'https://baby-journal.vercel.app',  # Production domain (update when you have it)
    'https://*.vercel.app'  # Allow all Vercel preview deployments
])
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
                duplicate_count = 0
                error_count = 0

                for activity in activities:
                    try:
                        # Try to save the activity
                        if journal.add_activity(activity):
                            saved_count += 1
                        else:
                            # Check if it was a duplicate by trying to find it in database
                            db = get_db_service()
                            existing = db.get_activities(
                                journal.profile.id,
                                limit=1
                            )
                            # Simple heuristic: if we have activities in DB, likely a duplicate
                            if existing:
                                duplicate_count += 1
                            else:
                                error_count += 1
                    except Exception as e:
                        logger.error(f"Failed to save activity: {e}")
                        error_count += 1

                # Reload activities from database to update display
                journal.load_activities()

                # Provide detailed feedback
                total_processed = len(activities)
                if saved_count > 0:
                    message = f'Successfully processed {total_processed} activities: {saved_count} new'
                    if duplicate_count > 0:
                        message += f', {duplicate_count} duplicates skipped'
                    if error_count > 0:
                        message += f', {error_count} errors'
                    flash(message, 'success')
                elif duplicate_count > 0:
                    flash(f'Processed {total_processed} activities: {duplicate_count} were duplicates (skipped)', 'info')
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
    """Simple feeding analytics page."""
    try:
        logger.info("Simple analytics route accessed")

        # Load profile if not already loaded
        if not journal.profile:
            journal.load_profile()

        if not journal.profile:
            logger.error("No profile found for analytics")
            return render_template('analytics_simple.html', error="Please create a baby profile first.")

        logger.info(f"Profile loaded: {journal.profile.name}")

        # Get feeding activities directly from database
        from app.database import get_db_service
        db = get_db_service()

        # Query feeding activities directly
        feeding_rows = db.get_activities(journal.profile.id, category='feeding')
        logger.info(f"Found {len(feeding_rows)} feeding activities in database")

        if not feeding_rows:
            return render_template('analytics_simple.html', error="No feeding activities found. Add some feeding activities first.")

        # Process feeding data for chart and calculate metrics
        feeding_data = []
        breast_feeds = 0
        total_amount = 0
        valid_amounts = []
        dates_set = set()

        # Import feeding type classifier
        from app.whatsapp_parser import WhatsAppParser
        parser = WhatsAppParser()

        for row in feeding_rows:
            try:
                # Convert amount to float, ensure it's a number
                amount = 0
                if row['amount'] is not None:
                    amount = float(row['amount']) if row['amount'] != '' else 0

                # Classify feeding type
                feeding_type = parser._determine_feeding_type(row['description'] or '')
                if feeding_type == 'breast':
                    breast_feeds += 1

                feeding_record = {
                    'id': str(row['id']),  # Add activity ID for editing
                    'date': row['timestamp'].strftime('%Y-%m-%d'),
                    'time': row['timestamp'].strftime('%H:%M'),
                    'amount': amount,
                    'description': row['description'],
                    'feeding_type': feeding_type
                }
                feeding_data.append(feeding_record)

                # Collect data for metrics
                if amount > 0:
                    total_amount += amount
                    valid_amounts.append(amount)
                dates_set.add(feeding_record['date'])

            except Exception as e:
                logger.warning(f"Error processing feeding row: {e}")
                continue

        # Sort by timestamp
        feeding_data.sort(key=lambda x: x['date'] + ' ' + x['time'])

        # Calculate metrics
        total_feeds = len(feeding_data)
        days_tracked = len(dates_set)
        avg_amount = sum(valid_amounts) / len(valid_amounts) if valid_amounts else 0
        daily_avg_amount = total_amount / days_tracked if days_tracked > 0 else 0  # ml per day
        frequency = total_feeds / days_tracked if days_tracked > 0 else 0  # feeds per day
        weekly_avg_amount = total_amount / (days_tracked / 7) if days_tracked > 0 else 0  # ml per week
        breast_feed_percentage = (breast_feeds / total_feeds * 100) if total_feeds > 0 else 0

        metrics = {
            'daily_avg_feed': round(daily_avg_amount, 1),  # ml per day
            'frequency': round(frequency, 1),  # feeds per day
            'days_tracked': days_tracked,
            'avg_amount': round(avg_amount, 1),
            'weekly_avg_feed': round(weekly_avg_amount, 1),  # ml per week
            'breast_feed_percentage': round(breast_feed_percentage, 1),
            'total_feeds': total_feeds,
            'total_amount': round(total_amount, 1)
        }

        logger.info(f"Processed {len(feeding_data)} feeding records")
        logger.info(f"Calculated metrics: {metrics}")

        return render_template('analytics_simple.html', feeding_data=feeding_data, metrics=metrics)

    except Exception as e:
        logger.error(f"Error in simple analytics: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return render_template('analytics_simple.html', error=f"Error loading analytics: {str(e)}")


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


# Additional API endpoints for Next.js frontend
@app.route('/api/profile', methods=['GET'])
def api_get_profile():
    """Get baby profile via API."""
    if not journal.profile:
        journal.load_profile()

    if journal.profile:
        return jsonify({
            'success': True,
            'profile': journal.profile.to_dict()
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No profile found'
        }), 404


@app.route('/api/profile', methods=['POST'])
def api_create_profile():
    """Create or update baby profile via API."""
    data = request.json

    if not data.get('name') or not data.get('birth_date'):
        return jsonify({
            'success': False,
            'message': 'Name and birth_date are required'
        }), 400

    try:
        birth_date = datetime.fromisoformat(data['birth_date'])

        profile = BabyProfile(
            name=data['name'],
            birth_date=birth_date,
            gender=data.get('gender'),
            birth_weight=data.get('birth_weight'),
            birth_height=data.get('birth_height')
        )

        journal.profile = profile
        journal.save_profile()

        return jsonify({
            'success': True,
            'profile': profile.to_dict()
        })
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/activities', methods=['GET'])
def api_get_activities():
    """Get all activities via API."""
    try:
        # Load fresh activities from database
        if journal.profile:
            journal.load_activities()

        # Get query parameters for filtering
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', 0, type=int)

        activities = journal.get_recent_activities(limit=limit) if limit else journal.activities

        # Convert to dict format
        activities_data = [activity.to_dict() for activity in activities[offset:]]

        return jsonify({
            'success': True,
            'activities': activities_data,
            'total': len(journal.activities)
        })
    except Exception as e:
        logger.error(f"Error fetching activities: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/analytics-data', methods=['GET'])
def api_get_analytics_data():
    """Get analytics data for charts via API."""
    try:
        if not journal.profile:
            return jsonify({
                'success': False,
                'message': 'No profile found'
            }), 404

        # Load fresh data
        journal.load_activities()

        # Generate analytics data
        insights_gen = InsightsGenerator()
        insights = insights_gen.generate_insights(journal)

        # Get activity distribution
        activity_dist = {}
        for activity in journal.activities:
            act_type = activity.activity_type
            if act_type not in activity_dist:
                activity_dist[act_type] = 0
            activity_dist[act_type] += 1

        # Get daily patterns
        daily_patterns = {}
        for activity in journal.activities:
            hour = activity.timestamp.hour
            if hour not in daily_patterns:
                daily_patterns[hour] = 0
            daily_patterns[hour] += 1

        return jsonify({
            'success': True,
            'statistics': journal.get_statistics(),
            'insights': insights,
            'activity_distribution': activity_dist,
            'daily_patterns': daily_patterns,
            'recent_activities': [a.to_dict() for a in journal.get_recent_activities(limit=20)]
        })
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/upload', methods=['POST'])
def api_upload_whatsapp():
    """Handle WhatsApp chat upload via API."""
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No file provided'
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No file selected'
        }), 400

    if not journal.profile:
        return jsonify({
            'success': False,
            'message': 'Please set up baby profile first'
        }), 400

    try:
        if file and file.filename.endswith('.txt'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Parse WhatsApp chat
            parser = WhatsAppParser()
            messages = parser.parse_file(filepath)

            # Process messages
            processor = ActivityProcessor()
            new_activities = []

            for msg in messages:
                activities = processor.process_message(msg['message'], msg['timestamp'])
                for activity in activities:
                    # Check for duplicates
                    is_duplicate = False
                    for existing in journal.activities:
                        if (existing.timestamp == activity.timestamp and
                            existing.type == activity.type and
                            existing.details == activity.details):
                            is_duplicate = True
                            break

                    if not is_duplicate:
                        new_activities.append(activity)

            # Add new activities
            for activity in new_activities:
                journal.add_activity(activity)

            # Clean up uploaded file
            os.remove(filepath)

            return jsonify({
                'success': True,
                'message': f'Successfully processed {len(messages)} messages',
                'activities_added': len(new_activities),
                'total_activities': len(journal.activities)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid file format. Please upload a .txt file'
            }), 400
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)