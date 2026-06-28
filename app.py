import sqlite3
import pandas as pd
import streamlit as st
import re
import plotly.express as px
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PROFESSION_SHORT = {
    'DevOps-инженер': 'DevOps',
    'System Administrator (Linux)': 'SysAdmin',
    'Cloud Engineer (AWS / Yandex Cloud)': 'Cloud Eng.',
    'SRE (Site Reliability Engineer)': 'SRE',
    'Network Engineer (сетевой инженер)': 'Network Eng.',
}

PROFESSION_CATEGORIES = {
    'DevOps-инженер': [
        'devops', 'devsecops', 'devops-инженер', 'devops engineer',
        'devops/devsecops', 'mlops/devops', 'platform engineer',
        'head of devops', 'devops teamlead', 'devops-специалист'
    ],
    'System Administrator (Linux)': [
        'системный администратор', 'system administrator',
        'linux-администратор', 'linux administrator',
        'linux engineer', 'linux инженер',
        'системный администратор linux'
    ],
    'Cloud Engineer (AWS / Yandex Cloud)': [
        'cloud engineer', 'cloud', 'облачн',
        'aws', 'yandex cloud', 'openstack',
        'облачная инфраструктура', 'яндекс облако'
    ],
    'SRE (Site Reliability Engineer)': [
        'sre', 'site reliability', 'надежност',
        'инженер по надежности', 'инженер по обеспечению надежности'
    ],
    'Network Engineer (сетевой инженер)': [
        'сетевой инженер', 'network engineer', 'сетевой администратор',
        'netops', 'сетевик', 'network'
    ]
}

PROFESSIONS = list(PROFESSION_CATEGORIES.keys())


def classify_vacancy(name):
    """Классифицирует вакансию по одной из 5 профессий варианта 5."""
    if not name:
        return None
    name_lower = name.lower()
    for profession, keywords in PROFESSION_CATEGORIES.items():
        for kw in keywords:
            if kw in name_lower:
                return profession
    return None


@st.cache_data
def load_data():
    """Загружает вакансии из БД и классифицирует по профессиям."""
    conn = sqlite3.connect('vacancies.db')
    df = pd.read_sql_query("SELECT * FROM vacancies", conn)
    conn.close()
    df['profession'] = df['name'].apply(classify_vacancy)
    df = df[df['profession'].notna()].copy()
    return df


def clean_html(raw_html):
    """Очищает HTML-теги из описания вакансии."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ")
    return " ".join(text.split())


def extract_skills(text):
    """Извлекает ключевые навыки из описания вакансии."""
    tech_stack = [
        'linux', 'windows', 'bash', 'python', 'go', 'docker', 'kubernetes', 'k8s',
        'ansible', 'terraform', 'ci/cd', 'jenkins', 'gitlab', 'aws', 'yandex cloud',
        'zabbix', 'prometheus', 'grafana', 'sql', 'postgresql', 'tcp/ip', 'bgp', 'ospf'
    ]
    text_lower = text.lower()
    return [skill for skill in tech_stack if re.search(r'\b' + re.escape(skill) + r'\b', text_lower)]


def extract_salary_range(text):
    """Вытаскивает зарплатную вилку из текста описания."""
    if not text:
        return "Не указана"

    text_lower = text.lower()

    salary_context_re = re.compile(
        r'(?:зарплат[ауеы]|з/п|оклад[ауеы]?|доход[ауеы]?|'
        r'от\s+\d.*?(?:руб|₽|р\.|тыс)|'
        r'(?:руб|₽|р\.)\s*(?:на руки|net|gross|до вычета|после вычета))',
        re.IGNORECASE
    )

    salary_windows = []
    for m in salary_context_re.finditer(text_lower):
        start = max(0, m.start() - 80)
        end = min(len(text_lower), m.end() + 80)
        salary_windows.append(text_lower[start:end])

    if not salary_windows:
        return "Не указана"

    combined = ' '.join(salary_windows)

    clean_nums = []

    pattern_full = r'(\d{2,3}[\s\xa0_.]?\d{3})'
    for m in re.findall(pattern_full, combined):
        num = int(re.sub(r'[\s\xa0_.]', '', m))
        if 30000 <= num <= 1500000:
            clean_nums.append(num)

    if re.search(r'тыс|тысяч|т\.?\s*р', combined):
        for m in re.findall(r'(\d{2,4})', combined):
            num = int(m) * 1000
            if 30000 <= num <= 1500000:
                clean_nums.append(num)

    clean_nums = list(dict.fromkeys(clean_nums))

    if not clean_nums:
        return "Не указана"

    min_sal = min(clean_nums)
    max_sal = max(clean_nums)

    if min_sal == max_sal:
        return f"{min_sal:,} ₽".replace(',', ' ')
    return f"{min_sal:,} - {max_sal:,} ₽".replace(',', ' ')


def extract_salary_value(text):
    """Возвращает числовое значение зарплаты (нижнюю границу) для фильтрации."""
    if not text or text == "Не указана":
        return None
    nums = re.findall(r'(\d[\d\s]*\d)', text.replace('\xa0', ' '))
    if not nums:
        return None
    clean = [int(re.sub(r'\s', '', n)) for n in nums]
    return min(clean) if clean else None


def determine_class(text):
    """Определяет грейд (класс) вакансии по ключевым словам."""
    text_lower = text.lower()
    if 'junior' in text_lower or 'младш' in text_lower or 'без опыта' in text_lower:
        return 'Junior'
    elif 'senior' in text_lower or 'старш' in text_lower or 'ведущ' in text_lower:
        return 'Senior'
    elif 'lead' in text_lower or 'руководител' in text_lower:
        return 'Lead'
    return 'Middle'


def split_description(raw_html):
    """Разделяет HTML-описание вакансии на требования и обязанности."""
    if not raw_html:
        return {}

    soup = BeautifulSoup(raw_html, "html.parser")

    section_patterns = {
        'требования': 'Требования', 'требования к кандидатам': 'Требования',
        'мы ищем': 'Требования', 'кто вы': 'Требования',
        'ты нам подходишь': 'Требования', 'мы рассчитываем': 'Требования',
        'ожид': 'Требования', 'нужн': 'Требования',
        'пожелания': 'Требования', 'навыки': 'Требования',
        'будет плюсом': 'Требования', 'приветствуется': 'Требования',

        'условия': 'Условия работы', 'что мы предлагаем': 'Условия работы',
        'мы предлагаем': 'Условия работы', 'преимущества': 'Условия работы',
        'что интересного': 'Условия работы', 'бенефит': 'Условия работы',
        'стань частью': 'Условия работы', 'льготы': 'Условия работы',

        'обязанности': 'Обязанности', 'ключевые обязанности': 'Обязанности',
        'вам предстоит': 'Обязанности', 'чем предстоит': 'Обязанности',
        'чем вам предстоит': 'Обязанности', 'в задачи': 'Обязанности',
        'будет входить': 'Обязанности',
    }

    skip_item_re = re.compile(
        r'^(привет|здравствуйте|добрый|день|hi|hello|ок|хорошо|понял|'
        r'спасибо|пожалуйста|отлично|супер|класс|круто|'
        r'рассмотрим|свяжемся|ждем|ждём|откликнитесь|'
        r'нажмите|отправьте|отправить|заполните|оставьте|'
        r'мы – компания|уже более|создаём|сотрудничали|'
        r'сотрудничество по аутстаф|интересно сотрудничество|'
        r'❗|обратите внимание|формат не рассматриваем|'
        r'аккредитованн|реестр| минцифры|рф)$',
        re.IGNORECASE
    )

    section_header_re = re.compile(
        r'^(требован\w{0,5}|услови\w{0,3}|обязан\w{0,5}|'
        r'будет плюсом|приветствуется|наш стек|'
        r'чем .* предстоит|мы (ищем|рассчитываем)|'
        r'ты нам подходишь|что (мы предлагаем|интересного)|'
        r'ключев\w+ обязан\w+|пожелани\w+|навык\w+)$',
        re.IGNORECASE
    )

    def extract_lines(tag):
        """Извлекает строки, разбивая по <br>, • и номерам."""
        for br in tag.find_all('br'):
            br.replace_with('\n')
        text = tag.get_text(separator="\n")
        lines = []
        for part in text.split('\n'):
            part = part.strip()
            part = re.sub(r'^[•●◦▪]\s*', '', part)
            part = re.sub(r'^\d+[\.\)]\s*', '', part)
            if part:
                lines.append(part)
        return lines

    sections = {}
    current_section = None

    for tag in soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'strong', 'b']):
        lines = extract_lines(tag)

        for text in lines:
            if not text or len(text) < 5:
                continue

            text_lower = text.lower().strip()

            matched_section = None
            for pattern, section in section_patterns.items():
                if pattern in text_lower:
                    matched_section = section
                    break

            if matched_section:
                current_section = matched_section
                if current_section not in sections:
                    sections[current_section] = []
                if tag.name in ['h1', 'h2', 'h3', 'h4']:
                    continue
                if not section_header_re.match(text_lower):
                    sections[current_section].append(text)
            elif skip_item_re.match(text_lower):
                continue
            elif current_section:
                sections[current_section].append(text)

    result = {}
    for sec_name, items in sections.items():
        seen = set()
        deduped = []
        for item in items:
            normalized = re.sub(r'\s+', ' ', item.lower().strip())
            if len(normalized) < 5:
                continue
            if normalized not in seen:
                seen.add(normalized)
                deduped.append(item)

        merged = []
        for item in deduped:
            if merged and not re.search(r'[.!?;:]\s*$', merged[-1]) and len(item) < 50:
                merged[-1] = merged[-1].rstrip('.;:') + ' ' + item.lstrip()
            else:
                merged.append(item)

        if merged:
            result[sec_name] = merged

    return result


def main():
    """Главная функция приложения — дашборд анализа вакансий."""
    st.set_page_config(page_title="Анализ вакансий: Инфраструктура и DevOps", layout="wide")

    st.title("Дашборд анализа вакансий")

    df = load_data()
    df['clean_description'] = df['description'].apply(clean_html)
    df['skills'] = df['clean_description'].apply(extract_skills)
    df['job_class'] = df['clean_description'].apply(determine_class)
    df['salary_range'] = df['clean_description'].apply(extract_salary_range)
    df['salary_numeric'] = df['salary_range'].apply(extract_salary_value)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Общие сведения",
        "Типовая вакансия",
        "Классы вакансий",
        "Поиск по навыкам"
    ])

    # БЛОК 1: Общие сведения о выборке
    with tab1:
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.metric("Всего вакансий", len(df))
        with col2:
            salaries_found = len(df[df['salary_range'] != 'Не указана'])
            st.metric("Указана ЗП", f"{salaries_found} вак.")
        with col3:
            pass

        st.subheader("Количество вакансий по профессиям")
        prof_counts = df['profession'].value_counts().reset_index()
        prof_counts.columns = ['profession', 'count']
        prof_counts['short'] = prof_counts['profession'].map(PROFESSION_SHORT)
        fig_prof = px.bar(
            prof_counts, x='count', y='short', orientation='h',
            text='count', height=300
        )
        fig_prof.update_layout(yaxis_title='', xaxis_title='Количество', margin=dict(l=0, r=0, t=10, b=10))
        fig_prof.update_traces(textposition='outside')
        st.plotly_chart(fig_prof, width='stretch')

        st.subheader("Топ-10 самых востребованных навыков")
        all_skills = df.explode('skills')['skills'].dropna()
        skill_counts = all_skills.value_counts().head(10).reset_index()
        skill_counts.columns = ['skill', 'count']
        fig_skills = px.bar(
            skill_counts, x='count', y='skill', orientation='h',
            text='count', height=400
        )
        fig_skills.update_layout(yaxis_title='', xaxis_title='Количество', margin=dict(l=0, r=0, t=10, b=10))
        fig_skills.update_traces(textposition='outside')
        st.plotly_chart(fig_skills, width='stretch')

    # БЛОК 2: Типовая вакансия по каждой профессии
    with tab2:
        st.header("Типовая вакансия по профессии")
        selected_prof = st.selectbox("Выберите профессию:", PROFESSIONS, key="prof1")
        prof_df = df[df['profession'] == selected_prof].reset_index(drop=True)

        if not prof_df.empty:
            st.info(f"Найдено вакансий: {len(prof_df)}")

            vacancy_idx = st.number_input(
                "Номер вакансии (листайте для просмотра всех):",
                min_value=0,
                max_value=len(prof_df) - 1,
                value=0,
                key="vac_idx"
            )

            sample = prof_df.iloc[vacancy_idx]

            st.subheader(sample['name'])
            st.write(f"**Работодатель:** {sample['employer']}")
            st.write(f"**Профессия:** {sample['profession']}")
            st.write(f"**Грейд:** {sample['job_class']}")

            if sample['salary_range'] != 'Не указана':
                st.success(f"**Зарплата:** {sample['salary_range']}")
            else:
                st.warning("**Зарплата:** Не указана в описании")

            skills_str = ", ".join(sample['skills']) if sample['skills'] else "Специфичные навыки не найдены"
            st.write(f"**Выявленные навыки:** {skills_str}")

            st.write(f"[Открыть вакансию на HH]({sample['url']})")

            sections = split_description(sample['description'])
            if sections:
                for section_name, items in sections.items():
                    with st.expander(section_name, expanded=(section_name == 'Требования')):
                        for item in items:
                            st.write(f"• {item}")
            else:
                with st.expander("Полное описание"):
                    st.write(sample['clean_description'])

            st.divider()
            with st.expander("Полное описание (вся вакансия)"):
                st.write(sample['clean_description'])

    # БЛОК 3: Классы вакансий (обобщенная вакансия)
    with tab3:
        st.header("Распределение по классам")
        selected_prof_class = st.selectbox("Выберите профессию:", PROFESSIONS, key="prof2")
        class_df = df[df['profession'] == selected_prof_class]

        if not class_df.empty:
            class_counts = class_df['job_class'].value_counts().reset_index()
            class_counts.columns = ['class', 'count']
            fig_class = px.bar(
                class_counts, x='count', y='class', orientation='h',
                text='count', height=300
            )
            fig_class.update_layout(yaxis_title='', xaxis_title='Количество', margin=dict(l=0, r=0, t=10, b=10))
            fig_class.update_traces(textposition='outside')
            st.plotly_chart(fig_class, width='stretch')

            st.write("**Обобщённый профиль вакансии:**")
            all_skills_prof = class_df.explode('skills')['skills'].dropna()
            if not all_skills_prof.empty:
                top_skills = all_skills_prof.value_counts().head(10)
                st.write(f"Топ-навыки: {', '.join(top_skills.index.tolist())}")

            st.write(f"Всего вакансий: {len(class_df)}")
            salary_stats = class_df[class_df['salary_range'] != 'Не указана']
            if not salary_stats.empty:
                st.write(f"С указанием ЗП: {len(salary_stats)} вакансий")
            else:
                st.write("Зарплата не указана ни в одной вакансии этой категории")

    # БЛОК 4: Поиск подходящих вакансий по навыкам
    with tab4:
        st.header("Поиск подходящих вакансий")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            search_prof = st.selectbox("Фильтр по профессии:", ["Все"] + PROFESSIONS, key="prof_search")
        with col_f2:
            user_input = st.text_input("Введите ваши навыки через запятую:", "linux, docker, python, bash")

        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            sal_min = st.number_input("Мин. зарплата (₽):", min_value=0, value=0, step=10000, key="sal_min")
        with col_s2:
            sal_max = st.number_input("Макс. зарплата (₽):", min_value=0, value=0, step=10000, key="sal_max")
        with col_s3:
            sort_by = st.selectbox("Сортировка:", [
                "По релевантности",
                "ЗП ↓ (убывание)",
                "ЗП ↑ (возрастание)",
            ], key="sort_by")

        if st.button("Рассчитать похожесть и найти"):
            if user_input:
                search_df = df.copy()
                if search_prof != "Все":
                    search_df = search_df[search_df['profession'] == search_prof]

                if sal_min > 0:
                    search_df = search_df[
                        (search_df['salary_numeric'].notna()) &
                        (search_df['salary_numeric'] >= sal_min)
                    ]
                if sal_max > 0:
                    search_df = search_df[
                        (search_df['salary_numeric'].notna()) &
                        (search_df['salary_numeric'] <= sal_max)
                    ]

                if search_df.empty:
                    st.warning("Нет вакансий, соответствующих фильтрам")
                else:
                    corpus = search_df['clean_description'].tolist()
                    corpus.append(user_input)

                    vectorizer = TfidfVectorizer(stop_words='english')
                    tfidf_matrix = vectorizer.fit_transform(corpus)

                    cosine_sim = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()

                    search_df = search_df.copy()
                    search_df['similarity'] = cosine_sim

                    if sort_by == "ЗП ↓ (убывание)":
                        top_matches = search_df.dropna(subset=['salary_numeric']).sort_values(
                            by='salary_numeric', ascending=False
                        ).head(5)
                    elif sort_by == "ЗП ↑ (возрастание)":
                        top_matches = search_df.dropna(subset=['salary_numeric']).sort_values(
                            by='salary_numeric', ascending=True
                        ).head(5)
                    else:
                        top_matches = search_df.sort_values(by='similarity', ascending=False).head(5)

                    st.subheader("Топ-5 подходящих вакансий:")
                    for _, row in top_matches.iterrows():
                        match_percent = round(row['similarity'] * 100, 1)
                        if match_percent > 0:
                            st.markdown(f"#### {row['name']} — **{match_percent}% совпадения**")
                            st.write(f"**Профессия:** {row['profession']} | **Работодатель:** {row['employer']} | **Доход:** `{row['salary_range']}`")
                            st.write(f"[Открыть вакансию на HH]({row['url']})")
                            st.divider()


if __name__ == "__main__":
    main()
