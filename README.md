# Дашборд анализа вакансий: Инфраструктура и DevOps

Веб-приложение для анализа вакансий из базы данных HeadHunter по 5 профессиям из категории «Инфраструктура и DevOps» (вариант 5).

## Профессии

- DevOps-инженер
- System Administrator (Linux)
- Cloud Engineer (AWS / Yandex Cloud)
- SRE (Site Reliability Engineer)
- Network Engineer (сетевой инженер)

## Возможности дашборда

1. **Общие сведения** — количество вакансий по профессиям, топ-10 навыков
2. **Типовая вакансия** — просмотр вакансий по профессии с разделением на требования/обязанности/условия
3. **Классы вакансий** — распределение по грейдам (Junior/Middle/Senior/Lead), обобщённый профиль
4. **Поиск по навыкам** — TF-IDF cosine similarity для поиска 5 наиболее подходящих вакансий

## Быстрый старт

### Вариант 1: Docker (рекомендуется)

#### Установка Docker

**Windows / macOS:**
1. Скачать и установить [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Запустить Docker Desktop (иконка в трее)

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# перелогинься для применения
```

**Linux (Arch/Manjaro):**
```bash
sudo pacman -S docker
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

#### Настройка зеркала (если Docker Hub не доступен)

Если `docker build` зависает или выдаёт ошибку сети — настрой зеркало:

**Linux:**
```bash
sudo mkdir -p /etc/docker
echo '{"registry-mirrors": ["https://mirror.gcr.io"]}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
```

**Windows (Docker Desktop):**
1. Открыть Docker Desktop → Settings → Docker Engine
2. В JSON-конфиг добавить:
```json
{
  "registry-mirrors": ["https://mirror.gcr.io"]
}
```
3. Нажать "Apply & Restart"

#### Сборка и запуск

```bash
git clone https://github.com/rendonett/tssa_project.git
cd tssa_project
docker build -t vacancy-dashboard .
docker run -p 8501:8501 vacancy-dashboard
```

Открыть: http://localhost:8501

---

### Вариант 2: Без Docker (локально)

#### Установка Python

**Windows:**
1. Скачать Python 3.11+ с [python.org](https://www.python.org/downloads/)
2. При установке отметить галочку **"Add Python to PATH"**

**Linux:**
```bash
sudo apt install python3 python3-pip    # Ubuntu/Debian
sudo pacman -S python python-pip         # Arch
```

#### Запуск

```bash
git clone https://github.com/rendonett/tssa_project.git
cd tssa_project
pip install -r requirements.txt
streamlit run app.py
```

Открыть: http://localhost:8501

---

## Структура проекта

| Файл | Описание |
|------|----------|
| `app.py` | Основной код дашборда (Streamlit + Plotly) |
| `parser.py` | Парсер вакансий из JSONL в SQLite |
| `test_app.py` | Тесты (7 тестов, покрытие > 80%) |
| `vacancies.db` | SQLite база данных с вакансиями |
| `hh_raw_vacancies.jsonl` | Исходные данные HeadHunter |
| `requirements.txt` | Зависимости Python |
| `Dockerfile` | Конфигурация Docker |

## Тестирование

```bash
pytest test_app.py --cov=app --cov-report=term-missing
```

## Технологии

- Python 3.11
- Streamlit — веб-интерфейс
- Plotly — визуализация графиков
- SQLite — хранение данных
- scikit-learn — TF-IDF и cosine similarity для поиска
- BeautifulSoup — парсинг HTML-описаний
- Docker — контейнеризация
