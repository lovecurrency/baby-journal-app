/**
 * Browser notification system for Baby Activity Journal
 * Handles notification permissions, checking reminders, and displaying notifications
 */

class NotificationManager {
    constructor() {
        this.checkInterval = null;
        this.permission = 'default';
        this.init();
    }

    /**
     * Initialize notification manager
     */
    async init() {
        // Check if notifications are supported
        if (!('Notification' in window)) {
            console.warn('This browser does not support desktop notifications');
            return;
        }

        this.permission = Notification.permission;

        // If permission is granted, start checking for reminders
        if (this.permission === 'granted') {
            this.startChecking();
        }
    }

    /**
     * Request notification permission from user
     */
    async requestPermission() {
        if (!('Notification' in window)) {
            alert('Your browser does not support notifications');
            return false;
        }

        if (this.permission === 'granted') {
            return true;
        }

        const permission = await Notification.requestPermission();
        this.permission = permission;

        if (permission === 'granted') {
            this.showWelcomeNotification();
            this.startChecking();
            return true;
        } else {
            alert('Please enable notifications to receive reminders');
            return false;
        }
    }

    /**
     * Show welcome notification after permission is granted
     */
    showWelcomeNotification() {
        this.showNotification({
            title: 'Reminders Enabled!',
            message: 'You will now receive activity reminders',
            icon: '💚'
        });
    }

    /**
     * Start checking for pending reminders
     */
    startChecking() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }

        // Check immediately
        this.checkReminders();

        // Then check every minute
        this.checkInterval = setInterval(() => {
            this.checkReminders();
        }, 60000); // 1 minute

        console.log('Started checking for reminders');
    }

    /**
     * Stop checking for reminders
     */
    stopChecking() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
            console.log('Stopped checking for reminders');
        }
    }

    /**
     * Check for pending reminders from server
     */
    async checkReminders() {
        try {
            const response = await fetch('/api/reminders/check');
            const data = await response.json();

            if (data.reminders && data.reminders.length > 0) {
                data.reminders.forEach(reminder => {
                    this.showReminderNotification(reminder);
                });
            }
        } catch (error) {
            console.error('Error checking reminders:', error);
        }
    }

    /**
     * Show a reminder notification
     */
    showReminderNotification(reminder) {
        const icon = this.getCategoryIcon(reminder.category);

        this.showNotification({
            title: reminder.title,
            message: reminder.message || `Time for ${reminder.category} activity`,
            icon: icon,
            tag: reminder.id,
            data: {
                url: '/quick_add'
            }
        });
    }

    /**
     * Show a generic notification
     */
    showNotification({ title, message, icon, tag, data }) {
        if (this.permission !== 'granted') {
            console.warn('Cannot show notification: permission not granted');
            return;
        }

        const options = {
            body: message,
            icon: this.getIconPath(icon),
            badge: '/static/img/badge-icon.png',
            vibrate: [200, 100, 200],
            tag: tag || `notification-${Date.now()}`,
            data: data || {},
            requireInteraction: true,
            actions: [
                {
                    action: 'add',
                    title: 'Add Activity'
                },
                {
                    action: 'dismiss',
                    title: 'Dismiss'
                }
            ]
        };

        const notification = new Notification(title, options);

        notification.onclick = (event) => {
            event.preventDefault();
            if (data && data.url) {
                window.open(data.url, '_blank');
            }
            notification.close();
        };

        return notification;
    }

    /**
     * Get icon for activity category
     */
    getCategoryIcon(category) {
        const icons = {
            'feeding': '🍼',
            'diaper': '👶',
            'sleep': '😴',
            'health': '🏥',
            'medicine': '💊',
            'vaccine': '💉',
            'other': '⭐'
        };

        return icons[category] || icons['other'];
    }

    /**
     * Get full path to icon (for future use with actual icon files)
     */
    getIconPath(icon) {
        // For now, return emoji as data URL
        // In production, you'd use actual icon files
        return null; // Browser will use page icon or default
    }

    /**
     * Show notification permission button if needed
     */
    showPermissionButton() {
        if (this.permission === 'default') {
            return true;
        }
        return false;
    }

    /**
     * Get permission status
     */
    getPermissionStatus() {
        return this.permission;
    }
}

// Create global instance
const notificationManager = new NotificationManager();

// Auto-request permission when page loads (optional - can be triggered by user action)
document.addEventListener('DOMContentLoaded', () => {
    // Add notification permission button to settings or header if needed
    const notificationStatus = notificationManager.getPermissionStatus();

    if (notificationStatus === 'default') {
        // Show info banner to enable notifications
        console.log('Notifications not enabled. User can enable from Reminders page.');
    } else if (notificationStatus === 'granted') {
        console.log('Notifications enabled');
    } else {
        console.log('Notifications denied');
    }
});

// Expose to global scope for use in templates
window.notificationManager = notificationManager;
