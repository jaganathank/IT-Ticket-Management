document.addEventListener('DOMContentLoaded', function () {
    // Notification menu toggle
    const notificationToggles = document.querySelectorAll('.notification-toggle');
    const notificationDropdowns = document.querySelectorAll('.notification-dropdown');
    
    notificationToggles.forEach(toggle => {
        toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            const dropdown = this.closest('.notification-menu-wrapper').querySelector('.notification-dropdown');
            const isActive = dropdown.classList.contains('active');
            
            // Close all other dropdowns
            notificationDropdowns.forEach(d => d.classList.remove('active'));
            profileDropdowns.forEach(d => d.classList.remove('active'));
            
            // Toggle current dropdown
            if (!isActive) {
                dropdown.classList.add('active');
                loadNotifications();
            }
        });
    });
    
    // Load notifications (placeholder)
    function loadNotifications() {
        const notificationList = document.getElementById('notification-list');
        if (!notificationList) return;
        
        // Fetch notifications from server
        fetch('/api/notifications')
            .then(res => res.json())
            .then(data => {
                if (data.notifications && data.notifications.length > 0) {
                    notificationList.innerHTML = data.notifications.map(notif => `
                        <div class="notification-item ${notif.is_read ? '' : 'unread'}">
                            <p class="notification-item-text">${notif.message}</p>
                            <p class="notification-item-time">${new Date(notif.created_at).toLocaleString()}</p>
                        </div>
                    `).join('');
                } else {
                    notificationList.innerHTML = '<div class="notification-empty">No notifications</div>';
                }
            })
            .catch(err => {
                console.error('Error loading notifications:', err);
                notificationList.innerHTML = '<div class="notification-empty">No notifications</div>';
            });
    }
    
    // Close notification dropdown when clicking elsewhere
    document.addEventListener('click', function (e) {
        if (!e.target.closest('.notification-menu-wrapper')) {
            notificationDropdowns.forEach(d => d.classList.remove('active'));
        }
    });

    // Profile menu toggle
    const profileToggles = document.querySelectorAll('.profile-toggle');
    const profileDropdowns = document.querySelectorAll('.profile-dropdown');
    
    profileToggles.forEach(toggle => {
        toggle.addEventListener('click', function (e) {
            e.stopPropagation();
            const dropdown = this.closest('.profile-menu-wrapper').querySelector('.profile-dropdown');
            const isActive = dropdown.classList.contains('active');
            
            // Close all other dropdowns
            profileDropdowns.forEach(d => d.classList.remove('active'));
            notificationDropdowns.forEach(d => d.classList.remove('active'));
            
            // Toggle current dropdown
            if (!isActive) {
                dropdown.classList.add('active');
            }
        });
    });
    
    // Close profile dropdown when clicking elsewhere
    document.addEventListener('click', function (e) {
        if (!e.target.closest('.profile-menu-wrapper')) {
            profileDropdowns.forEach(d => d.classList.remove('active'));
        }
    });

    // Theme toggle functionality
    const themeToggle = document.getElementById('theme-toggle');
    const html = document.documentElement;
    
    // Load theme preference from localStorage
    const savedTheme = localStorage.getItem('theme') || 'light';
    html.setAttribute('data-theme', savedTheme);
    if (savedTheme === 'dark' && themeToggle) {
        themeToggle.textContent = '☀️';
    }
    
    // Toggle theme on button click
    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            themeToggle.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        });
    }

    const selects = document.querySelectorAll('select');
    selects.forEach(select => {
        select.addEventListener('change', function () {
            this.classList.add('active-select');
        });
    });

    const toggleButtons = document.querySelectorAll('.toggle-password');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (!input) return;
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            this.textContent = isPassword ? '🙈' : '👁';
        });
    });
    
    // Notification polling - check for updates every 30 seconds
    setInterval(checkForNotifications, 30000);
    
    function checkForNotifications() {
        // This would fetch notifications from the server
        // For now, it's a placeholder for future implementation
    }
});
