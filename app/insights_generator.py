"""
Dynamic insights generator for baby activity patterns.
Uses rule-based analytics to generate personalized insights.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from statistics import stdev, mean
from app.models import BabyActivity, ActivityCategory, ActivityType


class InsightsGenerator:
    """Generates dynamic insights based on baby activity patterns."""

    def __init__(self, activities: List[BabyActivity]):
        self.activities = activities
        self.today = datetime.now().date()

    def generate_feeding_insights(self) -> List[Dict[str, str]]:
        """Generate dynamic insights for feeding patterns."""
        insights = []
        feeding_activities = [a for a in self.activities if a.category == ActivityCategory.FEEDING]

        if not feeding_activities:
            return [{"text": "Add more feeding activities to see personalized insights.", "type": "info", "icon": "info-circle"}]

        # Get activities from last 7 and 14 days for comparison
        last_7_days = self._get_activities_in_range(feeding_activities, 7)
        last_14_days = self._get_activities_in_range(feeding_activities, 14)
        previous_7_days = self._get_activities_in_range(feeding_activities, 14, 7)

        # Amount trend analysis
        if last_7_days and previous_7_days:
            insights.extend(self._analyze_feeding_amounts(last_7_days, previous_7_days))

        # Consistency analysis
        if last_7_days:
            insights.extend(self._analyze_feeding_consistency(last_7_days))

        # Type preference analysis
        if len(feeding_activities) >= 5:
            insights.extend(self._analyze_feeding_types(feeding_activities))

        # Gap pattern analysis
        if len(feeding_activities) >= 3:
            insights.extend(self._analyze_feeding_gaps(feeding_activities))

        return insights if insights else [{"text": "Keep tracking to unlock personalized feeding insights!", "type": "info", "icon": "clock"}]

    def generate_sleep_insights(self) -> List[Dict[str, str]]:
        """Generate dynamic insights for sleep patterns."""
        insights = []
        sleep_activities = [a for a in self.activities if a.category == ActivityCategory.SLEEP and a.duration_minutes]

        if not sleep_activities:
            return [{"text": "Add sleep activities with duration to see sleep insights.", "type": "info", "icon": "info-circle"}]

        # Get activities from last 7 and 14 days for comparison
        last_7_days = self._get_activities_in_range(sleep_activities, 7)
        previous_7_days = self._get_activities_in_range(sleep_activities, 14, 7)

        # Duration trend analysis
        if last_7_days and previous_7_days:
            insights.extend(self._analyze_sleep_duration(last_7_days, previous_7_days))

        # Day vs night analysis
        if last_7_days:
            insights.extend(self._analyze_sleep_timing(last_7_days))

        # Sleep quality patterns
        if len(sleep_activities) >= 5:
            insights.extend(self._analyze_sleep_quality(sleep_activities))

        return insights if insights else [{"text": "Track more sleep data to unlock sleep pattern insights!", "type": "info", "icon": "clock"}]

    def _get_activities_in_range(self, activities: List[BabyActivity], days_back: int, offset: int = 0) -> List[BabyActivity]:
        """Get activities within a specific date range."""
        start_date = self.today - timedelta(days=days_back + offset)
        end_date = self.today - timedelta(days=offset)

        return [a for a in activities if start_date <= a.timestamp.date() <= end_date]

    def _analyze_feeding_amounts(self, current_week: List[BabyActivity], previous_week: List[BabyActivity]) -> List[Dict[str, str]]:
        """Analyze feeding amount trends."""
        insights = []

        current_amounts = [a.amount for a in current_week if a.amount]
        previous_amounts = [a.amount for a in previous_week if a.amount]

        if current_amounts and previous_amounts:
            current_avg = mean(current_amounts)
            previous_avg = mean(previous_amounts)
            difference = current_avg - previous_avg
            percentage_change = (difference / previous_avg) * 100

            if abs(difference) >= 5:  # Significant change threshold
                if difference > 0:
                    insights.append({
                        "text": f"Feeding amounts increased by {difference:.1f}ml this week ({percentage_change:+.1f}%) - great growth!",
                        "type": "success",
                        "icon": "trending-up"
                    })
                else:
                    insights.append({
                        "text": f"Feeding amounts decreased by {abs(difference):.1f}ml this week. Monitor if this continues.",
                        "type": "warning",
                        "icon": "trending-down"
                    })
            else:
                insights.append({
                    "text": f"Steady feeding amounts around {current_avg:.1f}ml - consistent nutrition intake.",
                    "type": "info",
                    "icon": "arrow-right"
                })

        return insights

    def _analyze_feeding_consistency(self, activities: List[BabyActivity]) -> List[Dict[str, str]]:
        """Analyze feeding schedule consistency."""
        insights = []

        if len(activities) < 3:
            return insights

        # Calculate time gaps between feeds
        sorted_activities = sorted(activities, key=lambda x: x.timestamp)
        gaps = []

        for i in range(1, len(sorted_activities)):
            gap = (sorted_activities[i].timestamp - sorted_activities[i-1].timestamp).total_seconds() / 3600
            gaps.append(gap)

        if gaps:
            avg_gap = mean(gaps)
            gap_variance = stdev(gaps) if len(gaps) > 1 else 0

            if gap_variance < 1.0:  # Very consistent
                insights.append({
                    "text": f"Very consistent feeding schedule with {avg_gap:.1f}hr average gaps - excellent routine!",
                    "type": "success",
                    "icon": "check-circle"
                })
            elif gap_variance < 2.0:  # Moderately consistent
                insights.append({
                    "text": f"Good feeding rhythm with {avg_gap:.1f}hr gaps. Minor variations are normal.",
                    "type": "info",
                    "icon": "clock"
                })
            else:  # Variable schedule
                insights.append({
                    "text": f"Feeding times vary significantly. Consider establishing a more regular routine.",
                    "type": "warning",
                    "icon": "exclamation-triangle"
                })

        return insights

    def _analyze_feeding_types(self, activities: List[BabyActivity]) -> List[Dict[str, str]]:
        """Analyze breast vs bottle feeding preferences."""
        insights = []

        breast_feeds = [a for a in activities if a.activity_type == ActivityType.BREAST_FEED]
        bottle_feeds = [a for a in activities if a.activity_type == ActivityType.BOTTLE_FEED]

        total_feeds = len(breast_feeds) + len(bottle_feeds)

        if total_feeds >= 5:
            breast_percentage = (len(breast_feeds) / total_feeds) * 100

            # Analyze by time of day
            morning_breast = len([a for a in breast_feeds if 6 <= a.timestamp.hour < 12])
            morning_total = len([a for a in activities if 6 <= a.timestamp.hour < 12])

            if morning_total > 0:
                morning_breast_pct = (morning_breast / morning_total) * 100

                if morning_breast_pct >= 70:
                    insights.append({
                        "text": f"Baby prefers breast feeding in morning hours ({morning_breast_pct:.0f}% of AM feeds).",
                        "type": "info",
                        "icon": "sunrise"
                    })

            if breast_percentage >= 70:
                insights.append({
                    "text": f"Primarily breast feeding ({breast_percentage:.0f}%) - great for bonding and nutrition!",
                    "type": "success",
                    "icon": "heart"
                })
            elif breast_percentage <= 30:
                insights.append({
                    "text": f"Mostly bottle feeding ({100-breast_percentage:.0f}%) - allows flexible feeding schedule.",
                    "type": "info",
                    "icon": "cup"
                })
            else:
                insights.append({
                    "text": f"Balanced mix of breast ({breast_percentage:.0f}%) and bottle feeding - flexibility with bonding.",
                    "type": "info",
                    "icon": "balance-scale"
                })

        return insights

    def _analyze_feeding_gaps(self, activities: List[BabyActivity]) -> List[Dict[str, str]]:
        """Analyze feeding gap patterns."""
        insights = []

        sorted_activities = sorted(activities, key=lambda x: x.timestamp)

        # Analyze night vs day gaps
        night_gaps = []
        day_gaps = []

        for i in range(1, len(sorted_activities)):
            prev_activity = sorted_activities[i-1]
            curr_activity = sorted_activities[i]
            gap_hours = (curr_activity.timestamp - prev_activity.timestamp).total_seconds() / 3600

            if 21 <= prev_activity.timestamp.hour or prev_activity.timestamp.hour <= 6:  # Night time
                night_gaps.append(gap_hours)
            else:  # Day time
                day_gaps.append(gap_hours)

        if night_gaps and day_gaps and len(night_gaps) >= 2 and len(day_gaps) >= 2:
            avg_night_gap = mean(night_gaps)
            avg_day_gap = mean(day_gaps)

            if avg_night_gap > avg_day_gap * 1.5:
                insights.append({
                    "text": f"Longer night feeding gaps ({avg_night_gap:.1f}h vs {avg_day_gap:.1f}h) - great sleep consolidation!",
                    "type": "success",
                    "icon": "moon"
                })

        return insights

    def _analyze_sleep_duration(self, current_week: List[BabyActivity], previous_week: List[BabyActivity]) -> List[Dict[str, str]]:
        """Analyze sleep duration trends."""
        insights = []

        current_durations = [a.duration_minutes for a in current_week if a.duration_minutes]
        previous_durations = [a.duration_minutes for a in previous_week if a.duration_minutes]

        if current_durations and previous_durations:
            current_avg = mean(current_durations)
            previous_avg = mean(previous_durations)
            difference = current_avg - previous_avg

            if abs(difference) >= 30:  # 30+ minute change
                if difference > 0:
                    insights.append({
                        "text": f"Sleep duration improved by {difference:.0f} minutes this week - better rest quality!",
                        "type": "success",
                        "icon": "trending-up"
                    })
                else:
                    insights.append({
                        "text": f"Sleep duration decreased by {abs(difference):.0f} minutes. Consider reviewing bedtime routine.",
                        "type": "warning",
                        "icon": "trending-down"
                    })
            else:
                insights.append({
                    "text": f"Consistent sleep patterns with {current_avg/60:.1f}hr average duration.",
                    "type": "info",
                    "icon": "arrow-right"
                })

        return insights

    def _analyze_sleep_timing(self, activities: List[BabyActivity]) -> List[Dict[str, str]]:
        """Analyze day vs night sleep balance."""
        insights = []

        day_sleep = []
        night_sleep = []

        for activity in activities:
            hour = activity.timestamp.hour
            if 6 <= hour < 21:  # Day time (6 AM to 9 PM)
                day_sleep.append(activity.duration_minutes)
            else:  # Night time
                night_sleep.append(activity.duration_minutes)

        if day_sleep and night_sleep:
            total_day = sum(day_sleep)
            total_night = sum(night_sleep)
            total_sleep = total_day + total_night

            day_percentage = (total_day / total_sleep) * 100

            if 30 <= day_percentage <= 50:
                insights.append({
                    "text": f"Great sleep balance: {100-day_percentage:.0f}% night, {day_percentage:.0f}% day sleep - healthy pattern!",
                    "type": "success",
                    "icon": "sun"
                })
            elif day_percentage > 60:
                insights.append({
                    "text": f"High day sleep ({day_percentage:.0f}%). Consider longer night sleep periods.",
                    "type": "warning",
                    "icon": "sun-fill"
                })
            else:
                insights.append({
                    "text": f"Strong night sleep preference ({100-day_percentage:.0f}%) - good sleep consolidation.",
                    "type": "info",
                    "icon": "moon-fill"
                })

        return insights

    def _analyze_sleep_quality(self, activities: List[BabyActivity]) -> List[Dict[str, str]]:
        """Analyze sleep quality indicators."""
        insights = []

        # Analyze sleep session lengths
        durations = [a.duration_minutes for a in activities if a.duration_minutes]

        if len(durations) >= 5:
            avg_duration = mean(durations)
            long_sleeps = [d for d in durations if d >= 180]  # 3+ hours

            if len(long_sleeps) >= len(durations) * 0.6:  # 60% of sleeps are long
                insights.append({
                    "text": f"Excellent sleep consolidation - {len(long_sleeps)} of {len(durations)} sessions are 3+ hours!",
                    "type": "success",
                    "icon": "shield-check"
                })
            elif avg_duration >= 120:  # 2+ hours average
                insights.append({
                    "text": f"Good sleep quality with {avg_duration/60:.1f}hr average sessions.",
                    "type": "info",
                    "icon": "clock"
                })

        return insights