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
        const response = await fetch(url, {
            method: 'GET',
            headers: this.getHeaders(),
            credentials: 'include'
        });
        return this.handleResponse(response);
    },
    
    async post(url, data = {}) {
        const response = await fetch(url, {
            method: 'POST',
            headers: this.getHeaders(),
            credentials: 'include',
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    },
    
    async put(url, data = {}) {
        const response = await fetch(url, {
            method: 'PUT',
            headers: this.getHeaders(),
            credentials: 'include',
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    },
    
    async delete(url) {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: this.getHeaders(),
            credentials: 'include'
        });
        return this.handleResponse(response);
    },
    
    async handleResponse(response) {
        // Store original response for status check
        const result = {
            ok: response.ok,
            status: response.status,
            data: null,
            error: null
        };
        
        try {
            const text = await response.text();
            let data;
            try {
                data = JSON.parse(text);
            } catch {
                data = { message: text || response.statusText };
            }
            
            if (response.ok) {
                result.data = data;
            } else {
                result.error = data;
                
                // Build detailed error message
                let message = data.message || data.detail || data.error;
                
                // Handle various error formats
                if (typeof message === 'object') {
                    message = JSON.stringify(message);
                }
                
                // Add HTTP status context
                const statusMessages = {
                    400: 'Bad request',
                    401: t('error.auth'),
                    403: t('error.forbidden') || 'Access denied',
                    404: t('error.not_found') || 'Not found',
                    422: 'Validation error',
                    429: t('error.rate_limit') || 'Rate limit exceeded',
                    500: t('error.server') || 'Server error',
                    502: 'Service unavailable',
                    503: 'Service temporarily unavailable'
                };
                
                if (!message) {
                    message = statusMessages[response.status] || `Error ${response.status}`;
                }
                
                // Add details if available
                if (data.details) {
                    message += `: ${data.details}`;
                }
                
                showToast(message, 'error');
                
                // Log full error for debugging
                console.error('[API Error]', {
                    status: response.status,
                    url: response.url,
                    error: data
                });
            }
        } catch (e) {
            console.error('[API Parse Error]', e);
            if (!response.ok) {
                result.error = { message: t('error.network') };
                showToast(t('error.network'), 'error');
            }
        }
        
        return result;
    }
};

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        // Create container if doesn't exist
        const newContainer = document.createElement('div');
        newContainer.id = 'toast-container';
        newContainer.className = 'toast-container';
        document.body.appendChild(newContainer);
    }
    
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
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    const targetContainer = document.getElementById('toast-container');
    targetContainer.appendChild(toast);
    
    // Auto remove after timeout (longer for errors)
    const duration = type === 'error' ? 10000 : 5000;
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }
    }, duration);
}

// Modal helpers
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

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
        await fetch('/api/auth/logout', {
            method: 'POST',
            headers: api.getHeaders(),
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

// ==================== Language System ====================

/**
 * Change language and save preference
 */
async function changeLanguage(lang) {
    console.log('[Language] Changing to:', lang);
    
    // Validate language
    if (!['en', 'ru', 'de'].includes(lang)) {
        console.warn('[Language] Invalid language:', lang);
        lang = 'en';
    }
    
    // Save to localStorage immediately
    localStorage.setItem('language', lang);
    
    // Also save to cookie for server-side rendering
    document.cookie = `language=${lang};path=/;max-age=31536000`;
    
    // Update translations immediately (before reload)
    if (typeof setLanguage === 'function') {
        setLanguage(lang);
    }
    
    // If logged in, save to server (async, don't wait)
    if (api.getToken()) {
        fetch('/api/users/settings', {
            method: 'PUT',
            headers: api.getHeaders(),
            credentials: 'include',
            body: JSON.stringify({ language: lang })
        }).catch(error => {
            console.error('[Language] Failed to save to server:', error);
        });
    }
    
    // Small delay to ensure cookie is set, then reload
    setTimeout(() => {
        window.location.reload();
    }, 100);
}

/**
 * Get current language
 */
function getCurrentLanguage() {
    // Priority: localStorage > cookie > default
    const fromStorage = localStorage.getItem('language');
    if (fromStorage && ['en', 'ru', 'de'].includes(fromStorage)) {
        return fromStorage;
    }
    
    const fromCookie = document.cookie.split('; ')
        .find(row => row.startsWith('language='))
        ?.split('=')[1];
    if (fromCookie && ['en', 'ru', 'de'].includes(fromCookie)) {
        return fromCookie;
    }
    
    return 'en';
}

/**
 * Initialize language selector
 */
function initLanguageSelector() {
    const langSelect = document.getElementById('language-select');
    if (langSelect) {
        const currentLang = getCurrentLanguage();
        langSelect.value = currentLang;
        
        // Sync localStorage with current value
        localStorage.setItem('language', currentLang);
        
        // Remove any existing listeners to prevent duplicates
        const newSelect = langSelect.cloneNode(true);
        langSelect.parentNode.replaceChild(newSelect, langSelect);
        
        newSelect.addEventListener('change', (e) => {
            e.preventDefault();
            changeLanguage(e.target.value);
        });
    }
}

// ==================== Generation Progress ====================

/**
 * Generation progress tracker with detailed step info
 */
const generationProgress = {
    modal: null,
    progressBar: null,
    statusText: null,
    detailsText: null,
    subProgressBar: null,
    currentStep: 0,
    totalSteps: 0,
    
    steps: {
        script: { label: 'progress.script', percent: 15, icon: '📝' },
        voiceover: { label: 'progress.voice', percent: 40, icon: '🎙️' },
        sounds: { label: 'progress.sounds', percent: 20, icon: '🔊' },
        music: { label: 'progress.music', percent: 15, icon: '🎵' },
        merge: { label: 'progress.merge', percent: 10, icon: '🔄' },
        cover: { label: 'progress.cover', percent: 0, icon: '🎨' }
    },
    
    show() {
        // Create modal if doesn't exist
        if (!document.getElementById('progress-modal')) {
            this.createModal();
        }
        
        this.modal = document.getElementById('progress-modal');
        this.progressBar = document.getElementById('progress-bar');
        this.statusText = document.getElementById('progress-status');
        this.detailsText = document.getElementById('progress-details');
        this.subProgressBar = document.getElementById('sub-progress-bar');
        this.stepIcon = document.getElementById('progress-step-icon');
        
        // Reset sub-progress
        if (this.subProgressBar) {
            this.subProgressBar.style.display = 'none';
        }
        
        this.modal.classList.add('active');
        this.progressBar?.classList.remove('error');
        this.setProgress(0, t('progress.starting'));
    },
    
    hide() {
        if (this.modal) {
            this.modal.classList.remove('active');
        }
    },
    
    setProgress(percent, status, details = '') {
        if (this.progressBar) {
            this.progressBar.style.width = `${Math.min(100, percent)}%`;
            this.progressBar.setAttribute('data-percent', `${Math.round(percent)}%`);
        }
        if (this.statusText) {
            this.statusText.textContent = status;
        }
        if (this.detailsText) {
            this.detailsText.textContent = details;
        }
    },
    
    setStep(stepName) {
        const step = this.steps[stepName];
        if (step) {
            let accumulatedPercent = 0;
            for (const [key, value] of Object.entries(this.steps)) {
                if (key === stepName) break;
                accumulatedPercent += value.percent;
            }
            
            // Update icon
            if (this.stepIcon) {
                this.stepIcon.textContent = step.icon;
            }
            
            this.setProgress(accumulatedPercent, t(step.label));
            
            // Hide sub-progress for non-voiceover steps
            if (this.subProgressBar && stepName !== 'voiceover') {
                this.subProgressBar.style.display = 'none';
            }
        }
    },
    
    /**
     * Set detailed sub-progress (e.g., "Line 5 of 20")
     */
    setSubProgress(current, total, label = '') {
        if (this.subProgressBar) {
            this.subProgressBar.style.display = 'block';
            const subBar = this.subProgressBar.querySelector('.sub-bar');
            if (subBar) {
                const percent = total > 0 ? (current / total) * 100 : 0;
                subBar.style.width = `${percent}%`;
            }
        }
        
        // Update details text
        const detailText = label || `${current} / ${total}`;
        if (this.detailsText) {
            this.detailsText.textContent = detailText;
        }
    },
    
    /**
     * Set voiceover progress with line info
     */
    setVoiceoverProgress(currentLine, totalLines) {
        const basePercent = 15; // After script
        const voicePercent = 40;
        const linePercent = totalLines > 0 ? (currentLine / totalLines) * voicePercent : 0;
        
        const lang = getCurrentLanguage();
        let detailText;
        if (lang === 'ru') {
            detailText = `Озвучивание реплики ${currentLine} из ${totalLines}`;
        } else if (lang === 'de') {
            detailText = `Vertone Zeile ${currentLine} von ${totalLines}`;
        } else {
            detailText = `Voicing line ${currentLine} of ${totalLines}`;
        }
        
        this.setProgress(basePercent + linePercent, t('progress.voice'), detailText);
        this.setSubProgress(currentLine, totalLines);
    },
    
    complete() {
        this.setProgress(100, t('progress.complete'));
        if (this.subProgressBar) {
            this.subProgressBar.style.display = 'none';
        }
        setTimeout(() => this.hide(), 1500);
    },
    
    error(message, details = '') {
        const currentPercent = this.progressBar ? parseInt(this.progressBar.style.width) || 0 : 0;
        this.setProgress(currentPercent, t('progress.error'), message);
        this.progressBar?.classList.add('error');
        
        // Show error details
        if (details && this.detailsText) {
            this.detailsText.innerHTML = `<span class="error-text">${escapeHtml(message)}</span>`;
            if (details !== message) {
                this.detailsText.innerHTML += `<br><small>${escapeHtml(details)}</small>`;
            }
        }
        
        // Don't auto-hide on error
    },
    
    createModal() {
        const modal = document.createElement('div');
        modal.id = 'progress-modal';
        modal.className = 'modal progress-modal';
        modal.innerHTML = `
            <div class="modal-content progress-modal-content">
                <div class="progress-header">
                    <span id="progress-step-icon" class="progress-icon">🎙️</span>
                    <h3 data-i18n="progress.starting">${t('progress.starting')}</h3>
                </div>
                <div class="progress-container">
                    <div class="progress-bar-wrapper">
                        <div id="progress-bar" class="progress-bar" style="width: 0%" data-percent="0%"></div>
                    </div>
                    <div id="sub-progress-bar" class="sub-progress-wrapper" style="display: none;">
                        <div class="sub-bar"></div>
                    </div>
                    <p id="progress-status" class="progress-status">${t('progress.starting')}</p>
                    <p id="progress-details" class="progress-details"></p>
                </div>
                <button class="btn btn-outline progress-close-btn" onclick="generationProgress.hide()" style="margin-top: 1rem; display: none;">
                    ${t('common.cancel') || 'Close'}
                </button>
            </div>
        `;
        document.body.appendChild(modal);
    }
};

// ==================== Error Display ====================

/**
 * Parse error from API response
 */
function parseApiError(error) {
    let message = '';
    let details = '';
    let code = '';
    
    if (typeof error === 'string') {
        message = error;
    } else if (error) {
        // Try various error formats
        message = error.message || error.error || error.detail || '';
        details = error.details || error.error_details || '';
        code = error.code || error.error_code || '';
        
        // Handle FastAPI validation errors
        if (error.detail && Array.isArray(error.detail)) {
            message = error.detail.map(e => `${e.loc?.join('.')}: ${e.msg}`).join('; ');
        } else if (typeof error.detail === 'object') {
            message = JSON.stringify(error.detail);
        }
        
        // Handle nested error objects
        if (error.error && typeof error.error === 'object') {
            message = error.error.message || JSON.stringify(error.error);
        }
    }
    
    return { message: message || t('error.unknown'), details, code };
}

/**
 * Display error with details
 */
function showError(error, context = '') {
    console.error(`[HeinerCast Error] ${context}:`, error);
    
    const { message: rawMessage, details, code } = parseApiError(error);
    let message = rawMessage;
    
    // Add context if provided
    const contextPrefix = context ? `${context}: ` : '';
    
    // Specific error translations with original message preserved
    let translatedMessage = message;
    
    if (message.includes('401') || message.includes('Unauthorized') || message.includes('unauthenticated')) {
        translatedMessage = t('error.auth');
    } else if (message.includes('API key') || message.includes('api_key') || message.includes('invalid_api_key')) {
        translatedMessage = t('error.api_key') + (details ? `: ${details}` : '');
    } else if (message.toLowerCase().includes('elevenlabs')) {
        translatedMessage = `${t('error.elevenlabs')}: ${message}`;
    } else if (message.toLowerCase().includes('openai')) {
        translatedMessage = `OpenAI: ${message}`;
    } else if (message.includes('network') || message.includes('fetch') || message.includes('ECONNREFUSED')) {
        translatedMessage = t('error.network');
    } else if (message.includes('timeout') || message.includes('ETIMEDOUT')) {
        translatedMessage = t('error.timeout') || 'Request timeout';
    } else if (message.includes('rate limit') || message.includes('429')) {
        translatedMessage = t('error.rate_limit') || 'Rate limit exceeded. Please wait.';
    }
    
    // Build final message
    let finalMessage = contextPrefix + translatedMessage;
    
    // Add error code if present
    if (code) {
        finalMessage += ` (${code})`;
    }
    
    if (message.includes('already in progress')) {
        showToast('⏳ ' + translatedMessage, 'info');
    } else {
        showToast(finalMessage, 'error');
    }
    
    // Log full details to console
    console.error('[HeinerCast] Full error:', { 
        context, 
        message, 
        details, 
        code,
        originalError: error 
    });
    
    if (error?.stack) {
        console.error(error.stack);
    }
    
    return { message: finalMessage, details, code };
}

// ==================== Generation Functions ====================

/**
 * Generate episode content
 */
async function generateEpisode(episodeId, steps = ['script', 'voice', 'sounds', 'music', 'merge']) {
    generationProgress.show();
    
    try {
        for (const step of steps) {
            generationProgress.setStep(step);
            
            const endpoint = `/api/generation/${step}/${episodeId}`;
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: api.getHeaders(),
                credentials: 'include'
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `Failed at step: ${step}`);
            }
            
            // Small delay between steps
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        generationProgress.complete();
        showToast(t('progress.complete'), 'success');
        
        // Reload page to show updated content
        setTimeout(() => window.location.reload(), 1500);
        
    } catch (error) {
        generationProgress.error(error.message);
        showError(error, 'Generation');
    }
}

/**
 * Generate single step
 */
async function generateStep(episodeId, step) {
    generationProgress.show();
    generationProgress.setStep(step);
    
    try {
        const endpoint = `/api/generation/${step}/${episodeId}`;
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: api.getHeaders(),
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `Failed: ${step}`);
        }
        
        generationProgress.complete();
        showToast(t('progress.complete'), 'success');
        
        // Reload page to show updated content
        setTimeout(() => window.location.reload(), 1500);
        
    } catch (error) {
        generationProgress.error(error.message);
        showError(error, step);
    }
}

// ==================== Utility Functions ====================

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
    // Use translated status if translations loaded
    if (typeof t === 'function') {
        return t(`status.${status}`, status);
    }
    
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
        const token = api.getToken();
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        try {
            const response = await fetch('/api/auth/me', {
                method: 'GET',
                headers: api.getHeaders(),
                credentials: 'include'
            });
            
            if (!response.ok) {
                localStorage.removeItem('access_token');
                window.location.href = '/login';
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            window.location.href = '/login';
        }
    }
}

// ==================== Initialize ====================

document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    checkAuth();
    
    // Initialize language selector
    initLanguageSelector();
    
    // Apply translations if available
    if (typeof applyTranslations === 'function') {
        applyTranslations();
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

/* Progress Modal Styles */
.progress-modal-content {
    max-width: 400px;
    text-align: center;
}

.progress-header {
    margin-bottom: 1.5rem;
}

.progress-icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 0.5rem;
}

.progress-container {
    padding: 1rem 0;
}

.progress-bar-wrapper {
    background: var(--bg-tertiary, #2a2a2a);
    border-radius: 8px;
    height: 24px;
    overflow: hidden;
    position: relative;
}

.progress-bar {
    background: linear-gradient(90deg, var(--primary, #6366f1), var(--primary-light, #818cf8));
    height: 100%;
    transition: width 0.3s ease;
    border-radius: 8px;
    position: relative;
}

.progress-bar::after {
    content: attr(data-percent);
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
}

.progress-bar.error {
    background: linear-gradient(90deg, #ef4444, #f87171);
}

.progress-status {
    margin-top: 1rem;
    font-weight: 500;
    color: var(--text-primary, #fff);
}

.progress-details {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-secondary, #aaa);
}

.progress-details .error-text {
    color: #ef4444;
}

.sub-progress-wrapper {
    background: var(--bg-tertiary, #2a2a2a);
    border-radius: 4px;
    height: 8px;
    margin-top: 0.5rem;
    overflow: hidden;
}

.sub-progress-wrapper .sub-bar {
    background: var(--primary-light, #818cf8);
    height: 100%;
    transition: width 0.3s ease;
    border-radius: 4px;
}

.progress-close-btn {
    margin-top: 1rem;
}

/* Toast close button */
.toast-close {
    background: none;
    border: none;
    color: inherit;
    font-size: 1.25rem;
    cursor: pointer;
    padding: 0 0.5rem;
    opacity: 0.7;
}

.toast-close:hover {
    opacity: 1;
}
`;
document.head.appendChild(style);
