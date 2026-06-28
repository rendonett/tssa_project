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

## Развертывание

### Docker

```bash
docker build -t vacancy-dashboard .
docker run -p 8501:8501 vacancy-dashboard
```

Приложение доступно по адресу: http://localhost:8501

### Локально

```bash
pip install -r requirements.txt
streamlit run app.py
```

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
