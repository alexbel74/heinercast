/**
 * HeinerCast - Translations System
 */

const translations = {
    ru: {
        // Navigation
        'nav.dashboard': 'Панель',
        'nav.projects': 'Проекты',
        'nav.voices': 'Голоса',
        'nav.settings': 'Настройки',
        'nav.logout': 'Выйти',
        
        // Auth
        'auth.login': 'Войти',
        'auth.register': 'Регистрация',
        'auth.email': 'Email',
        'auth.password': 'Пароль',
        'auth.username': 'Имя пользователя',
        'auth.welcome_back': 'С возвращением',
        'auth.sign_in_continue': 'Войдите, чтобы продолжить',
        'auth.create_account': 'Создать аккаунт',
        'auth.already_have_account': 'Уже есть аккаунт?',
        'auth.no_account': 'Нет аккаунта?',
        
        // Dashboard
        'dashboard.title': 'Мои проекты',
        'dashboard.new_project': 'Новый проект',
        'dashboard.no_projects': 'Нет проектов',
        'dashboard.create_first': 'Создайте свой первый проект',
        
        // Projects
        'project.title': 'Название',
        'project.description': 'Описание',
        'project.genre': 'Жанр и тон',
        'project.episodes': 'Эпизоды',
        'project.characters': 'Персонажи',
        'project.create': 'Создать проект',
        'project.edit': 'Редактировать',
        'project.delete': 'Удалить',
        'project.sound_effects': 'Звуковые эффекты',
        'project.background_music': 'Фоновая музыка',
        
        // Episodes
        'episode.new': 'Новый эпизод',
        'episode.generate_script': 'Сгенерировать сценарий',
        'episode.generate_voice': 'Озвучить',
        'episode.generate_sounds': 'Создать звуки',
        'episode.generate_music': 'Создать музыку',
        'episode.merge_audio': 'Собрать аудио',
        'episode.generate_cover': 'Создать обложку',
        'episode.generate_all': 'Сгенерировать всё',
        'episode.download': 'Скачать',
        'episode.play': 'Воспроизвести',
        'episode.duration': 'Длительность',
        'episode.status': 'Статус',
        
        // Status
        'status.draft': '📝 Черновик',
        'status.script_generating': '⏳ Генерация сценария...',
        'status.script_done': '✅ Сценарий готов',
        'status.voiceover_generating': '🎙️ Озвучивание...',
        'status.voiceover_done': '✅ Озвучка готова',
        'status.sounds_generating': '🔊 Создание звуков...',
        'status.sounds_done': '✅ Звуки готовы',
        'status.music_generating': '🎵 Создание музыки...',
        'status.music_done': '✅ Музыка готова',
        'status.merging': '🔄 Сборка аудио...',
        'status.audio_done': '✅ Аудио готово',
        'status.cover_generating': '🎨 Создание обложки...',
        'status.done': '✅ Готово',
        'status.error': '❌ Ошибка',
        
        // Voices
        'voices.title': 'Библиотека голосов',
        'voices.add': 'Добавить голос',
        'voices.import': 'Импорт из ElevenLabs',
        'voices.test': 'Тест',
        'voices.favorite': 'Избранный',
        
        // Settings
        'settings.title': 'Настройки',
        'settings.api_keys': 'API ключи',
        'settings.llm_provider': 'LLM провайдер',
        'settings.language': 'Язык интерфейса',
        'settings.save': 'Сохранить',
        'settings.saved': 'Сохранено!',
        
        // Generation progress
        'progress.starting': 'Начинаем...',
        'progress.script': 'Генерация сценария...',
        'progress.voice': 'Озвучивание текста...',
        'progress.sounds': 'Создание звуковых эффектов...',
        'progress.music': 'Создание фоновой музыки...',
        'progress.merge': 'Сборка финального аудио...',
        'progress.cover': 'Генерация обложки...',
        'progress.complete': 'Завершено!',
        'progress.error': 'Ошибка при генерации',
        
        // Errors
        'error.network': 'Ошибка сети. Проверьте подключение.',
        'error.auth': 'Ошибка авторизации. Войдите снова.',
        'error.api_key': 'Недействительный API ключ',
        'error.elevenlabs': 'Ошибка ElevenLabs',
        'error.llm': 'Ошибка генерации текста',
        'error.unknown': 'Неизвестная ошибка',
        
        // Common
        'common.save': 'Сохранить',
        'common.cancel': 'Отмена',
        'common.delete': 'Удалить',
        'common.edit': 'Редактировать',
        'common.loading': 'Загрузка...',
        'common.confirm_delete': 'Вы уверены, что хотите удалить?'
    },
    
    en: {
        // Navigation
        'nav.dashboard': 'Dashboard',
        'nav.projects': 'Projects',
        'nav.voices': 'Voices',
        'nav.settings': 'Settings',
        'nav.logout': 'Logout',
        
        // Auth
        'auth.login': 'Sign In',
        'auth.register': 'Sign Up',
        'auth.email': 'Email',
        'auth.password': 'Password',
        'auth.username': 'Username',
        'auth.welcome_back': 'Welcome Back',
        'auth.sign_in_continue': 'Sign in to continue',
        'auth.create_account': 'Create Account',
        'auth.already_have_account': 'Already have an account?',
        'auth.no_account': "Don't have an account?",
        
        // Dashboard
        'dashboard.title': 'My Projects',
        'dashboard.new_project': 'New Project',
        'dashboard.no_projects': 'No projects yet',
        'dashboard.create_first': 'Create your first project',
        
        // Projects
        'project.title': 'Title',
        'project.description': 'Description',
        'project.genre': 'Genre & Tone',
        'project.episodes': 'Episodes',
        'project.characters': 'Characters',
        'project.create': 'Create Project',
        'project.edit': 'Edit',
        'project.delete': 'Delete',
        'project.sound_effects': 'Sound Effects',
        'project.background_music': 'Background Music',
        
        // Episodes
        'episode.new': 'New Episode',
        'episode.generate_script': 'Generate Script',
        'episode.generate_voice': 'Generate Voice',
        'episode.generate_sounds': 'Generate Sounds',
        'episode.generate_music': 'Generate Music',
        'episode.merge_audio': 'Merge Audio',
        'episode.generate_cover': 'Generate Cover',
        'episode.generate_all': 'Generate All',
        'episode.download': 'Download',
        'episode.play': 'Play',
        'episode.duration': 'Duration',
        'episode.status': 'Status',
        
        // Status
        'status.draft': '📝 Draft',
        'status.script_generating': '⏳ Generating script...',
        'status.script_done': '✅ Script ready',
        'status.voiceover_generating': '🎙️ Generating voice...',
        'status.voiceover_done': '✅ Voice ready',
        'status.sounds_generating': '🔊 Generating sounds...',
        'status.sounds_done': '✅ Sounds ready',
        'status.music_generating': '🎵 Generating music...',
        'status.music_done': '✅ Music ready',
        'status.merging': '🔄 Merging audio...',
        'status.audio_done': '✅ Audio ready',
        'status.cover_generating': '🎨 Generating cover...',
        'status.done': '✅ Done',
        'status.error': '❌ Error',
        
        // Voices
        'voices.title': 'Voice Library',
        'voices.add': 'Add Voice',
        'voices.import': 'Import from ElevenLabs',
        'voices.test': 'Test',
        'voices.favorite': 'Favorite',
        
        // Settings
        'settings.title': 'Settings',
        'settings.api_keys': 'API Keys',
        'settings.llm_provider': 'LLM Provider',
        'settings.language': 'Interface Language',
        'settings.save': 'Save',
        'settings.saved': 'Saved!',
        
        // Generation progress
        'progress.starting': 'Starting...',
        'progress.script': 'Generating script...',
        'progress.voice': 'Generating voice...',
        'progress.sounds': 'Creating sound effects...',
        'progress.music': 'Creating background music...',
        'progress.merge': 'Merging final audio...',
        'progress.cover': 'Generating cover...',
        'progress.complete': 'Complete!',
        'progress.error': 'Error during generation',
        
        // Errors
        'error.network': 'Network error. Check your connection.',
        'error.auth': 'Authentication error. Please login again.',
        'error.api_key': 'Invalid API key',
        'error.elevenlabs': 'ElevenLabs error',
        'error.llm': 'Text generation error',
        'error.unknown': 'Unknown error',
        
        // Common
        'common.save': 'Save',
        'common.cancel': 'Cancel',
        'common.delete': 'Delete',
        'common.edit': 'Edit',
        'common.loading': 'Loading...',
        'common.confirm_delete': 'Are you sure you want to delete?'
    },
    
    de: {
        // Navigation
        'nav.dashboard': 'Dashboard',
        'nav.projects': 'Projekte',
        'nav.voices': 'Stimmen',
        'nav.settings': 'Einstellungen',
        'nav.logout': 'Abmelden',
        
        // Auth
        'auth.login': 'Anmelden',
        'auth.register': 'Registrieren',
        'auth.email': 'E-Mail',
        'auth.password': 'Passwort',
        'auth.username': 'Benutzername',
        'auth.welcome_back': 'Willkommen zurück',
        'auth.sign_in_continue': 'Melden Sie sich an, um fortzufahren',
        'auth.create_account': 'Konto erstellen',
        'auth.already_have_account': 'Haben Sie bereits ein Konto?',
        'auth.no_account': 'Kein Konto?',
        
        // Dashboard
        'dashboard.title': 'Meine Projekte',
        'dashboard.new_project': 'Neues Projekt',
        'dashboard.no_projects': 'Keine Projekte',
        'dashboard.create_first': 'Erstellen Sie Ihr erstes Projekt',
        
        // Projects
        'project.title': 'Titel',
        'project.description': 'Beschreibung',
        'project.genre': 'Genre & Ton',
        'project.episodes': 'Episoden',
        'project.characters': 'Charaktere',
        'project.create': 'Projekt erstellen',
        'project.edit': 'Bearbeiten',
        'project.delete': 'Löschen',
        'project.sound_effects': 'Soundeffekte',
        'project.background_music': 'Hintergrundmusik',
        
        // Episodes
        'episode.new': 'Neue Episode',
        'episode.generate_script': 'Skript generieren',
        'episode.generate_voice': 'Stimme generieren',
        'episode.generate_sounds': 'Sounds generieren',
        'episode.generate_music': 'Musik generieren',
        'episode.merge_audio': 'Audio zusammenführen',
        'episode.generate_cover': 'Cover generieren',
        'episode.generate_all': 'Alles generieren',
        'episode.download': 'Herunterladen',
        'episode.play': 'Abspielen',
        'episode.duration': 'Dauer',
        'episode.status': 'Status',
        
        // Status
        'status.draft': '📝 Entwurf',
        'status.script_generating': '⏳ Skript wird generiert...',
        'status.script_done': '✅ Skript fertig',
        'status.voiceover_generating': '🎙️ Stimme wird generiert...',
        'status.voiceover_done': '✅ Stimme fertig',
        'status.sounds_generating': '🔊 Sounds werden erstellt...',
        'status.sounds_done': '✅ Sounds fertig',
        'status.music_generating': '🎵 Musik wird erstellt...',
        'status.music_done': '✅ Musik fertig',
        'status.merging': '🔄 Audio wird zusammengeführt...',
        'status.audio_done': '✅ Audio fertig',
        'status.cover_generating': '🎨 Cover wird generiert...',
        'status.done': '✅ Fertig',
        'status.error': '❌ Fehler',
        
        // Voices
        'voices.title': 'Stimmbibliothek',
        'voices.add': 'Stimme hinzufügen',
        'voices.import': 'Von ElevenLabs importieren',
        'voices.test': 'Test',
        'voices.favorite': 'Favorit',
        
        // Settings
        'settings.title': 'Einstellungen',
        'settings.api_keys': 'API-Schlüssel',
        'settings.llm_provider': 'LLM-Anbieter',
        'settings.language': 'Sprache',
        'settings.save': 'Speichern',
        'settings.saved': 'Gespeichert!',
        
        // Generation progress
        'progress.starting': 'Wird gestartet...',
        'progress.script': 'Skript wird generiert...',
        'progress.voice': 'Stimme wird generiert...',
        'progress.sounds': 'Soundeffekte werden erstellt...',
        'progress.music': 'Hintergrundmusik wird erstellt...',
        'progress.merge': 'Audio wird zusammengeführt...',
        'progress.cover': 'Cover wird generiert...',
        'progress.complete': 'Abgeschlossen!',
        'progress.error': 'Fehler bei der Generierung',
        
        // Errors
        'error.network': 'Netzwerkfehler. Überprüfen Sie Ihre Verbindung.',
        'error.auth': 'Authentifizierungsfehler. Bitte erneut anmelden.',
        'error.api_key': 'Ungültiger API-Schlüssel',
        'error.elevenlabs': 'ElevenLabs-Fehler',
        'error.llm': 'Textgenerierungsfehler',
        'error.unknown': 'Unbekannter Fehler',
        
        // Common
        'common.save': 'Speichern',
        'common.cancel': 'Abbrechen',
        'common.delete': 'Löschen',
        'common.edit': 'Bearbeiten',
        'common.loading': 'Laden...',
        'common.confirm_delete': 'Sind Sie sicher, dass Sie löschen möchten?'
    }
};

// Current language
let currentLang = localStorage.getItem('language') || 'en';

/**
 * Get translation by key
 */
function t(key, fallback = null) {
    const lang = translations[currentLang] || translations['en'];
    return lang[key] || fallback || key;
}

/**
 * Set current language
 */
function setLanguage(lang) {
    if (!translations[lang]) {
        console.warn(`Language '${lang}' not supported, using 'en'`);
        lang = 'en';
    }
    currentLang = lang;
    localStorage.setItem('language', lang);
    applyTranslations();
}

/**
 * Get current language
 */
function getLanguage() {
    return currentLang;
}

/**
 * Apply translations to all elements with data-i18n attribute
 */
function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = t(key);
        
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            if (element.hasAttribute('placeholder')) {
                element.placeholder = translation;
            } else {
                element.value = translation;
            }
        } else {
            element.textContent = translation;
        }
    });
    
    // Update data-i18n-placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        element.placeholder = t(key);
    });
    
    // Update data-i18n-title
    document.querySelectorAll('[data-i18n-title]').forEach(element => {
        const key = element.getAttribute('data-i18n-title');
        element.title = t(key);
    });
}

/**
 * Format status with translation
 */
function formatStatusTranslated(status) {
    return t(`status.${status}`, status);
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    // Get language from localStorage or default
    currentLang = localStorage.getItem('language') || 'en';
    
    // Apply translations
    applyTranslations();
    
    // Update language selector if exists
    const langSelect = document.getElementById('language-select');
    if (langSelect) {
        langSelect.value = currentLang;
    }
});
