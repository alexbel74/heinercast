#!/bin/bash
# HeinerCast - Quick Run Script

cd "$(dirname "$0")"

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Виртуальное окружение не найдено!"
    echo "   Сначала запустите: ./setup.sh"
    exit 1
fi

echo "🎙️ Запускаю HeinerCast..."
echo "🌐 Откройте: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo ""
echo "Нажмите Ctrl+C для остановки"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
