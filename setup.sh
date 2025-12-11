#!/bin/bash
# HeinerCast - Local Setup Script
# Запуск: chmod +x setup.sh && ./setup.sh

set -e

echo "🎙️ HeinerCast - Локальная установка"
echo "===================================="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "📌 Python версия: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    echo "❌ Требуется Python 3.10 или выше!"
    exit 1
fi

# Create virtual environment
echo ""
echo "📦 Создаю виртуальное окружение..."
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
echo "📥 Устанавливаю зависимости..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env if not exists
if [ ! -f .env ]; then
    echo ""
    echo "⚙️ Создаю .env файл..."
    cp .env.example .env
    
    # Generate random keys
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    ENCRYPT_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(24)[:32])")
    
    # Update .env with generated keys
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
        sed -i '' "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" .env
        sed -i '' "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENCRYPT_KEY|" .env
    else
        # Linux
        sed -i "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
        sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=$JWT_SECRET|" .env
        sed -i "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENCRYPT_KEY|" .env
    fi
    
    echo "✅ .env создан с уникальными ключами"
fi

# Create directories
echo ""
echo "📁 Создаю директории..."
mkdir -p storage/audio storage/covers storage/temp storage/references logs

echo ""
echo "===================================="
echo "✅ Установка завершена!"
echo ""
echo "🚀 Для запуска выполните:"
echo ""
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🌐 Затем откройте: http://localhost:8000"
echo ""
echo "📝 Тестовый пользователь будет создан при первой регистрации"
echo "===================================="
