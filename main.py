import time
import requests
import logging
from itertools import cycle

# Пути к файлам
API_KEYS_FILE = "api_keys.txt"
PROXIES_FILE = "proxies.txt"
QUESTIONS_FILE = "questions.txt"

# Конфигурация API Hyperbolic
HYPERBOLIC_API_URL = "https://api.hyperbolic.xyz/v1/chat/completions"
MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
MAX_TOKENS = 2048
TEMPERATURE = 0.7
TOP_P = 0.9
DELAY_BETWEEN_QUESTIONS = 15  # Задержка между вопросами в секундах

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция загрузки списка API-ключей
def load_api_keys(filename: str) -> list:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            keys = [line.strip() for line in f if line.strip()]
        if not keys:
            raise ValueError("Файл API-ключей пуст.")
        return keys
    except Exception as e:
        logger.error(f"Ошибка загрузки API-ключей из {filename}: {e}")
        return []

# Функция загрузки списка прокси
def load_proxies(filename: str) -> list:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            proxies = [line.strip() for line in f if line.strip()]
        if not proxies:
            logger.warning("Файл прокси пуст. Подключение будет выполняться напрямую.")
        return proxies
    except Exception as e:
        logger.error(f"Ошибка загрузки прокси из {filename}: {e}")
        return []

# Загружаем API-ключи и прокси
api_keys = load_api_keys(API_KEYS_FILE)
proxies = load_proxies(PROXIES_FILE)

if not api_keys:
    logger.error("Не загружены API-ключи! Проверьте файл api_keys.txt")
    exit(1)

# Создаем циклы для итерации по API-ключам и прокси (если есть)
api_cycle = cycle(enumerate(api_keys, 1))  # Используем enumerate для получения индекса
proxy_cycle = cycle(enumerate(proxies, 1)) if proxies else None  # Теперь прокси содержит индекс и сам прокси

def send_request(question: str) -> bool:
    """Отправляет запрос и возвращает True, если получен ответ, иначе False."""
    api_index, api_key = next(api_cycle)  # Берем следующий API-ключ с его индексом
    proxy_index, proxy_url = next(proxy_cycle) if proxy_cycle else (None, None)  # Берем следующий прокси с индексом

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "messages": [{"role": "user", "content": question}],
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "top_p": TOP_P
    }

    proxies_dict = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    # В логах отображаем номер API-ключа вместо самого ключа
    logger.info(f"Используется API-ключ #{api_index} | Прокси #{proxy_index if proxy_url else 'Нет'}")

    try:
        response = requests.post(HYPERBOLIC_API_URL, headers=headers, json=data, timeout=30, proxies=proxies_dict)
        response.raise_for_status()  # Проверка на успешный ответ
        logger.info("✅ Ответ получен")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка запроса: {e}")
        return False

def main():
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Ошибка чтения файла {QUESTIONS_FILE}: {e}")
        return

    if not questions:
        logger.error(f"В файле {QUESTIONS_FILE} нет вопросов.")
        return

    index = 0
    while True:
        question = questions[index]
        logger.info(f"📌 Вопрос #{index+1}: {question}")
        send_request(question)
        index = (index + 1) % len(questions)
        time.sleep(DELAY_BETWEEN_QUESTIONS)

if __name__ == "__main__":
    main()
