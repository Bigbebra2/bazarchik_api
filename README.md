Всі дії будуть відбуватися в каталогу Olx-analog/Backend!


# Створюємо нове середовище
python3 -m venv venv

# Активовуємо його
source venv/bin/activate

# Встановлюємо всі необхідні бібліотеки для середовища
pip install -r requirements.txt

# Створюємо .env файл (для конфігурації):
touch .env
# Та прописуємо там наступне:
DATABASE_URL=mysql://<користувач>:<пароль>@<хост>:<порт>/<назва_бази>
JWT_SECRET_KEY=<секретний ключ>
SECRET_KEY=<секретний ключ2>


# Створюємо .flaskenv файл:
touch .flaskenv
# Та прописуємо там наступне:
FLASK_APP=run.py
FLASK_ENV=development


# Готово, тепер в консолі (маючи приписку '(venv)') прописуємо:
flask run
