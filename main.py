"""
Flask web application for Baby Activity Journal.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import json

from app.models import BabyProfile, ActivityJournal, BabyActivity, ActivityCategory, ActivityType
from app.activity_processor import ActivityProcessor
from app.whatsapp_parser import WhatsAppParser
from app.insights_generator import InsightsGenerator

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

# Initialize journal and processor
journal = ActivityJournal()
processor = ActivityProcessor()

# Load existing data
journal.load_profile()
journal.load_activities()


@app.context_processor
def inject_profile():
    """Make profile available to all templates."""
    return {'profile': journal.profile}


@app.route('/')
def index():
    """Home page showing recent activities and statistics."""
    recent_activities = journal.get_recent_activities(limit=10)
    stats = journal.get_statistics()

    # Format activities for display
    activities_display = []
    for activity in recent_activities:
        act_dict = activity.to_dict()
        act_dict['timestamp_formatted'] = datetime.fromisoformat(act_dict['timestamp']).strftime('%Y-%m-%d %H:%M')
        activities_display.append(act_dict)

    return render_template('index.html',
                         profile=journal.profile,
                         recent_activities=activities_display,
                         statistics=stats)


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

            profile = BabyProfile(name=name, birth_date=birth_date, gender=gender,
                                birth_weight=birth_weight, birth_height=birth_height)
            journal.set_profile(profile)
            flash('Baby profile created successfully!', 'success')
            return redirect(url_for('index'))

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
                for activity in activities:
                    journal.add_activity(activity)

                flash(f'Successfully processed {len(activities)} activities!', 'success')
                return redirect(url_for('index'))

            except Exception as e:
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
        filtered_activities = journal.activities

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
    stats = journal.get_statistics()

    # Prepare data for charts
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
                    if activity.duration_minutes:
                        hour = activity.timestamp.hour
                        if 6 <= hour < 21:  # 6 AM to 9 PM
                            day_sleep_minutes += activity.duration_minutes

                sleep_insights['day_sleep_avg'] = round(day_sleep_minutes / 60, 1) if day_sleep_minutes > 0 else 0

            # Calculate daily sleep trend for last 7 days
            for i in range(6, -1, -1):
                date = today - timedelta(days=i)
                day_sleeps = [a for a in sleep_activities if a.timestamp.date() == date]
                daily_durations = [a.duration_minutes for a in day_sleeps if a.duration_minutes]
                total_hours = round(sum(daily_durations) / 60, 1) if daily_durations else 0
                sleep_insights['daily_trend'].append({
                    'date': date.strftime('%a'),
                    'hours': total_hours,
                    'count': len(day_sleeps)
                })

        # Calculate extraction insights
        extraction_activities = [a for a in journal.activities if a.activity_type.value == 'breast_milk_extraction']
        extraction_insights = {
            'daily_avg': 0,
            'weekly_avg': 0,
            'daily_trend': []
        }

        if extraction_activities:
            # Calculate daily extraction trend for last 7 days
            for i in range(6, -1, -1):
                date = today - timedelta(days=i)
                day_extractions = [a for a in extraction_activities if a.timestamp.date() == date]
                daily_amounts = [a.amount for a in day_extractions if a.amount]
                total_amount = sum(daily_amounts) if daily_amounts else 0
                extraction_insights['daily_trend'].append({
                    'date': date.strftime('%a'),
                    'amount': round(total_amount, 1)
                })

            # Daily and weekly averages
            daily_totals = []
            for i in range(7):  # Last 7 days
                date = today - timedelta(days=i)
                day_extractions = [a for a in extraction_activities if a.timestamp.date() == date]
                daily_amounts = [a.amount for a in day_extractions if a.amount]
                daily_total = sum(daily_amounts) if daily_amounts else 0
                if daily_total > 0:  # Only count days with extraction data
                    daily_totals.append(daily_total)

            if daily_totals:
                extraction_insights['daily_avg'] = round(sum(daily_totals) / len(daily_totals), 1)
                extraction_insights['weekly_avg'] = round(sum(daily_totals), 1)

        # Generate dynamic insights
        insights_generator = InsightsGenerator(journal.activities)
        feeding_dynamic_insights = insights_generator.generate_feeding_insights()
        sleep_dynamic_insights = insights_generator.generate_sleep_insights()

        chart_data = {
            'hourly': hour_distribution,
            'weekday': weekday_distribution,
            'daily_trend': daily_counts,
            'feeding_insights': feeding_insights,
            'sleep_insights': sleep_insights,
            'extraction_insights': extraction_insights,
            'feeding_dynamic_insights': feeding_dynamic_insights,
            'sleep_dynamic_insights': sleep_dynamic_insights
        }
    else:
        chart_data = None

    return render_template('analytics_enhanced.html',
                         statistics=stats,
                         chart_data=chart_data)


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
        return jsonify({
            'success': False,
            'message': f'Error deleting activity: {str(e)}'
        }), 500


@app.route('/clear_all_activities', methods=['POST'])
def clear_all_activities():
    """Clear all activities (with confirmation)."""
    confirmation = request.form.get('confirmation')
    if confirmation == 'DELETE_ALL_ACTIVITIES':
        journal.activities = []
        journal._save_activities()
        flash('All activities have been deleted.', 'success')
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
            if 'category' in data:
                activity.category = ActivityCategory(data['category'])

            if 'activity_type' in data:
                activity.activity_type = ActivityType(data['activity_type'])

            if 'timestamp' in data:
                activity.timestamp = datetime.fromisoformat(data['timestamp'])

            if 'description' in data:
                activity.description = data['description']

            if 'amount' in data:
                activity.amount = float(data['amount']) if data['amount'] else None

            if 'unit' in data:
                activity.unit = data['unit'] if data['unit'] else None

            if 'duration_minutes' in data:
                activity.duration_minutes = int(data['duration_minutes']) if data['duration_minutes'] else None

            if 'notes' in data:
                activity.notes = data['notes']

            journal._save_activities()

            return jsonify({
                'success': True,
                'message': 'Activity updated successfully',
                'activity': activity.to_dict()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Activity not found'
            }), 404
    except Exception as e:
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


if __name__ == '__main__':
    app.run(debug=True, port=5001)