import json
import sqlite3

TARGET_KEYWORDS = [
    'devops', 
    'system administrator', 'системный администратор', 'linux',
    'cloud engineer', 'aws', 'yandex cloud', 'облачн',
    'sre', 'site reliability',
    'network engineer', 'сетевой инженер', 'сетевой администратор'
]

def init_db():
    """Инициализация легковесной БД SQLite."""
    conn = sqlite3.connect('vacancies.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vacancies (
            id TEXT PRIMARY KEY,
            name TEXT,
            employer TEXT,
            description TEXT,
            url TEXT
        )
    ''')
    conn.commit()
    return conn

def matches_category(job_name):
    """Проверяет, относится ли вакансия к нашей инфраструктурной категории."""
    if not job_name:
        return False
    name_lower = job_name.lower()
    return any(keyword in name_lower for keyword in TARGET_KEYWORDS)

def parse_and_filter(file_path):
    """Построчное чтение и фильтрация тяжелого JSONL."""
    conn = init_db()
    cursor = conn.cursor()
    
    count = 0
    skipped = 0
    
    print("Начинаю парсинг файла. Это может занять несколько минут...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                vacancy = json.loads(line)
                
                # пропускаем вакансии, которые не удалось скачать
                if vacancy.get('download_status') != 'ok':
                    skipped += 1
                    continue
                
                name = vacancy.get('name', '')
                
                if matches_category(name):
                    v_id = vacancy.get('id')
                    employer = vacancy.get('employer')
                    description = vacancy.get('description', '')
                    url = vacancy.get('url')
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO vacancies (id, name, employer, description, url)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (v_id, name, employer, description, url))
                    
                    count += 1
                    
                    if count % 500 == 0:
                        conn.commit()
                        print(f"Уже сохранено релевантных вакансий: {count}...")
                        
            except json.JSONDecodeError:
                continue

    conn.commit()
    conn.close()
    print(f"\n--- ГОТОВО ---")
    print(f"пропущено closed-вакансий: {skipped}")
    print(f"успешно сохранено вакансий: {count}")

if __name__ == "__main__":
    parse_and_filter('hh_raw_vacancies.jsonl')
