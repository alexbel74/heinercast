# 🎙️ HeinerCast

**Automated Audiobook Production Platform**

HeinerCast is a web application for creating multi-character audiobooks with AI-generated scripts, professional voiceover, sound effects, background music, and cover art.

## ✨ Features

- **AI Script Generation** - Create engaging multi-character scripts using OpenRouter, OpenAI, or Polza.ai
- **Multi-Voice Dialogue** - Professional voiceover with ElevenLabs text-to-dialogue
- **Sound Effects** - AI-generated sound effects automatically placed at key moments
- **Background Music** - Atmospheric instrumental music matching your story's mood
- **Cover Art** - Generate stunning cover images with kie.ai
- **Series Support** - Create multi-episode series with context continuity
- **Dark Studio UI** - Beautiful dark theme optimized for content creation
- **Multi-language** - Interface available in English, Russian, and German

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.12+, FastAPI |
| Database | PostgreSQL |
| Authentication | JWT + API Keys |
| Frontend | HTML/CSS/JS (Jinja2 Templates) |
| Audio Processing | FFmpeg |
| External APIs | ElevenLabs, kie.ai, OpenRouter/OpenAI/Polza |

## 📋 Requirements

- Python 3.12+
- PostgreSQL 14+
- FFmpeg
- Node.js (optional, for frontend development)

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-repo/heinercast.git
cd heinercast
```

### 2. Create virtual environment

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Set up database

```bash
# Create PostgreSQL database
createdb heinercast

# Run migrations
alembic upgrade head
```

### 6. Run the application

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000 to access the application.

## 📁 Project Structure

```
heinercast/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API endpoints
│   ├── services/            # Business logic services
│   ├── core/                # Security, dependencies, exceptions
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JS, images
├── storage/                 # Local file storage
├── migrations/              # Alembic database migrations
├── tests/                   # Test suite
├── .env.example             # Example environment variables
├── requirements.txt         # Python dependencies
├── alembic.ini              # Alembic configuration
└── README.md
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | HeinerCast |
| `APP_ENV` | Environment (development/production) | development |
| `DATABASE_URL` | PostgreSQL connection URL | - |
| `SECRET_KEY` | Application secret key | - |
| `JWT_SECRET_KEY` | JWT signing key | - |
| `STORAGE_TYPE` | Storage type (local/google_drive) | local |

### External API Keys

Configure in Settings page after registration:

- **LLM Provider** - OpenRouter, Polza.ai, or OpenAI API key
- **ElevenLabs** - For voice generation
- **kie.ai** - For cover image generation

## 📚 API Documentation

When running in development mode, access:

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 🎨 UI Theme

HeinerCast uses the "Dark Studio" theme optimized for content creation:

- Primary background: `#0d1117`
- Secondary background: `#161b22`
- Accent gradient: `#7c3aed` → `#2563eb`
- Action color: `#f97316`

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## 🚀 Production Deployment

### Beget VPS Deployment

1. Install system dependencies:
```bash
apt update && apt install -y python3.12 python3.12-venv postgresql ffmpeg nginx
```

2. Clone and setup:
```bash
cd /var/www
git clone https://github.com/your-repo/heinercast.git
cd heinercast
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Configure nginx and systemd (see deployment docs)

4. Setup SSL with Let's Encrypt:
```bash
certbot --nginx -d your-domain.com
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines first.

## 📞 Support

- Documentation: [docs.heinercast.com](https://docs.heinercast.com)
- Issues: [GitHub Issues](https://github.com/your-repo/heinercast/issues)
- Email: support@heinercast.com
