/**
 * HeinerCast - Main JavaScript
 */

// API helper with authentication
const api = {
    getToken() {
        return localStorage.getItem('access_token');
    },
    
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        return headers;
    },
    
    async get(url) {
        return fetch(url, {
            method: 'GET',
            headers: this.getHeaders(),
            credentials: 'include'
        });
    },
    
    async post(url, data = {}) {
        return fetch(url, {
            method: 'POST',
            headers: this.getHeaders(),
            credentials: 'include',
            body: JSON.stringify(data)
        });
    },
    
    async put(url, data = {}) {
        return fetch(url, {
            method: 'PUT',
            headers: this.getHeaders(),
            credentials: 'include',
            body: JSON.stringify(data)
        });
    },
    
    async delete(url) {
        return fetch(url, {
            method: 'DELETE',
            headers: this.getHeaders(),
            credentials: 'include'
        });
    }
};

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after 5 seconds (except errors)
    const duration = type === 'error' ? 10000 : 5000;
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Modal helpers
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Close modal on click outside
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
    }
});

// User menu toggle
function toggleUserMenu() {
    const dropdown = document.getElementById('user-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('active');
    }
}

// Close user menu on click outside
document.addEventListener('click', (e) => {
    const userMenu = document.querySelector('.user-menu');
    const dropdown = document.getElementById('user-dropdown');
    if (dropdown && userMenu && !userMenu.contains(e.target)) {
        dropdown.classList.remove('active');
    }
});

// Logout
async function logout() {
    try {
        await api.post('/api/auth/logout');
    } catch (error) {
        console.error('Logout error:', error);
    }
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

// Language change
function changeLanguage(lang) {
    // Save preference
    if (api.getToken()) {
        api.put('/api/users/settings', { language: lang })
            .then(() => window.location.reload())
            .catch(console.error);
    } else {
        localStorage.setItem('language', lang);
        window.location.reload();
    }
}

// Utility functions
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
}

function formatDuration(seconds) {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatStatus(status) {
    const statusMap = {
        'draft': '📝 Draft',
        'script_generating': '⏳ Generating script...',
        'script_done': '✅ Script ready',
        'voiceover_generating': '🎙️ Generating voice...',
        'voiceover_done': '✅ Voice ready',
        'sounds_generating': '🔊 Generating sounds...',
        'sounds_done': '✅ Sounds ready',
        'music_generating': '🎵 Generating music...',
        'music_done': '✅ Music ready',
        'merging': '🔄 Merging audio...',
        'audio_done': '✅ Audio ready',
        'cover_generating': '🎨 Generating cover...',
        'done': '✅ Done',
        'error': '❌ Error'
    };
    return statusMap[status] || status;
}

// Audio playback
function playAudio(episodeId) {
    window.open(`/api/files/stream/${episodeId}`, '_blank');
}

function downloadAudio(episodeId) {
    window.open(`/api/files/audio/${episodeId}`, '_blank');
}

// Check authentication on protected pages
async function checkAuth() {
    const protectedPaths = ['/dashboard', '/projects', '/episodes', '/voices', '/settings'];
    const currentPath = window.location.pathname;
    
    const isProtected = protectedPaths.some(path => currentPath.startsWith(path));
    
    if (isProtected) {
        try {
            const response = await api.get('/api/auth/me');
            if (!response.ok) {
                window.location.href = '/login';
            }
        } catch (error) {
            window.location.href = '/login';
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    
    // Set language selector
    const langSelect = document.getElementById('language-select');
    if (langSelect) {
        const savedLang = localStorage.getItem('language') || 'en';
        langSelect.value = savedLang;
    }
});

// Add CSS animation for toast slide out
const style = document.createElement('style');
style.textContent = `
@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}
`;
document.head.appendChild(style);
