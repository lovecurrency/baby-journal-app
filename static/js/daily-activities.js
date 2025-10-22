/**
 * Daily Activity Tracking with Progress, Motivational Messages, and Celebrations
 */

class DailyActivityTracker {
    constructor() {
        this.activities = [];
        this.initialized = false;
    }

    async initialize() {
        try {
            // Initialize age-appropriate activities
            const initResponse = await fetch('/api/daily-activities/initialize', {
                method: 'POST'
            });
            const initData = await initResponse.json();

            if (initData.success) {
                this.initialized = true;
                await this.loadActivities();
            }
        } catch (error) {
            console.error('Error initializing activities:', error);
        }
    }

    async loadActivities() {
        try {
            const response = await fetch('/api/daily-activities/progress');
            const data = await response.json();

            if (data.activities) {
                this.activities = data.activities;
                this.renderActivities();
            }
        } catch (error) {
            console.error('Error loading activities:', error);
        }
    }

    renderActivities() {
        const container = document.getElementById('todayActivitiesContainer');
        if (!container) return;

        if (this.activities.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <p class="text-muted">Loading activities for your baby's age...</p>
                    <button onclick="dailyActivityTracker.initialize()" class="btn btn-primary">
                        Initialize Activities
                    </button>
                </div>
            `;
            return;
        }

        const html = this.activities.map(activity => this.renderActivityCard(activity)).join('');
        container.innerHTML = html;
    }

    renderActivityCard(activity) {
        const progress = (activity.current_count / activity.target_count) * 100;
        const isCompleted = activity.completed;
        const streakBadge = activity.streak_days > 1 ? `<span class="badge bg-warning ms-2">${activity.streak_days} day streak! 🔥</span>` : '';

        return `
            <div class="activity-card ${isCompleted ? 'completed' : ''}" data-activity-id="${activity.id}">
                <div class="activity-header">
                    <div class="d-flex align-items-center">
                        <span class="activity-icon" style="color: ${activity.color}">
                            <i class="${activity.icon}" style="font-size: 2.5rem;"></i>
                        </span>
                        <div class="ms-3 flex-grow-1">
                            <h5 class="mb-1">${activity.activity_title} ${streakBadge}</h5>
                            <p class="text-muted small mb-0">${activity.activity_description}</p>
                        </div>
                    </div>
                </div>

                <div class="activity-body">
                    <div class="progress-container">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="progress-text">
                                <strong>${activity.current_count}/${activity.target_count}</strong>
                                ${isCompleted ? '✅ Completed!' : ''}
                            </span>
                            ${activity.duration_minutes ? `<span class="text-muted small">${activity.duration_minutes} min each</span>` : ''}
                        </div>
                        <div class="progress" style="height: 12px;">
                            <div class="progress-bar" role="progressbar" style="width: ${progress}%; background-color: ${activity.color};"
                                 aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"></div>
                        </div>
                    </div>

                    <div class="motivational-message mt-3 p-2 rounded" style="background-color: ${activity.color}20;">
                        <p class="mb-0 text-center">💬 ${activity.message}</p>
                    </div>

                    ${!isCompleted ? `
                        <div class="mt-3 text-center">
                            <button class="btn btn-primary btn-mark-done"
                                    onclick="dailyActivityTracker.markDone('${activity.id}')"
                                    style="background-color: ${activity.color}; border-color: ${activity.color};">
                                <i class="bi bi-check-circle"></i> Mark as Done
                            </button>
                        </div>
                    ` : ''}

                    ${activity.benefits ? `
                        <details class="mt-3">
                            <summary class="text-muted small" style="cursor: pointer;">Why this matters</summary>
                            <p class="small mt-2 mb-0">${activity.benefits}</p>
                        </details>
                    ` : ''}
                </div>
            </div>
        `;
    }

    async markDone(goalId) {
        try {
            const response = await fetch(`/api/daily-activities/${goalId}/mark-done`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                // Update activity in list
                const activity = this.activities.find(a => a.id === goalId);
                if (activity) {
                    activity.current_count = data.current_count;
                    activity.completed = data.completed;
                    activity.message = data.message;
                    activity.streak_days = data.streak_days;
                }

                // Show celebration if completed
                if (data.celebration) {
                    this.showCelebration(data.celebration_message);
                }

                // Re-render activities
                this.renderActivities();
            }
        } catch (error) {
            console.error('Error marking activity done:', error);
        }
    }

    showCelebration(message) {
        // Create celebration modal
        const modal = document.createElement('div');
        modal.className = 'celebration-modal';
        modal.innerHTML = `
            <div class="celebration-content">
                <div class="confetti-container"></div>
                <h2>🎉 Congratulations! 🎉</h2>
                <p>${message}</p>
                <button onclick="this.closest('.celebration-modal').remove()" class="btn btn-primary btn-lg">
                    Awesome!
                </button>
            </div>
        `;

        document.body.appendChild(modal);

        // Trigger confetti animation
        this.launchConfetti(modal.querySelector('.confetti-container'));

        // Auto-close after 5 seconds
        setTimeout(() => {
            if (modal.parentNode) {
                modal.remove();
            }
        }, 5000);
    }

    launchConfetti(container) {
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7', '#fd79a8'];
        const confettiCount = 50;

        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.animationDelay = Math.random() * 0.5 + 's';
            confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
            container.appendChild(confetti);
        }
    }
}

// Global instance
const dailyActivityTracker = new DailyActivityTracker();

// Auto-load on page load
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('todayActivitiesContainer')) {
        dailyActivityTracker.loadActivities();
    }
});

// Expose for use in templates
window.dailyActivityTracker = dailyActivityTracker;
