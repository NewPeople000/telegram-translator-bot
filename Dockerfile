# Python rasmiy yengil versiyasi
FROM python:3.11-slim

# Ishchi katalogni belgilash
WORKDIR /app

# Muhit o'zgaruvchilari (Python chiqishini darhol terminalga chiqarish uchun)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Tizim paketlarini yangilash
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Bog'liqliklarni o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha kodini ko'chirish
COPY . .

# Botni ishga tushirish
CMD ["python", "bot.py"]
