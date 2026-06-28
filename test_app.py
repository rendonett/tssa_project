import pytest
from app import (
    clean_html, extract_skills, determine_class,
    extract_salary_range, classify_vacancy, split_description
)
from streamlit.testing.v1 import AppTest


def test_clean_html():
    """Тестируем очистку HTML-тегов из описания."""
    raw = "<p><strong>Обязанности:</strong> Настройка серверов</p>"
    cleaned = clean_html(raw)
    assert cleaned == "Обязанности: Настройка серверов"
    assert clean_html(None) == ""
    assert clean_html("") == ""


def test_extract_skills():
    """Тестируем извлечение навыков из описания."""
    text1 = "Опыт работы с linux, Docker и KUBERNETES. Знание bash."
    skills1 = extract_skills(text1)
    assert "linux" in skills1
    assert "docker" in skills1
    assert "kubernetes" in skills1
    assert "bash" in skills1
    assert "python" not in skills1

    text2 = "Умение работать с go и aws"
    skills2 = extract_skills(text2)
    assert "go" in skills2
    assert "aws" in skills2


def test_determine_class():
    """Тестируем определение грейда вакансии."""
    assert determine_class("Ищем толкового junior специалиста без опыта") == "Junior"
    assert determine_class("Требуется Senior DevOps Engineer") == "Senior"
    assert determine_class("Открыта вакансия Lead SRE") == "Lead"
    assert determine_class("Просто системный администратор на поддержку") == "Middle"


def test_classify_vacancy():
    """Тестируем классификацию вакансий по профессиям."""
    assert classify_vacancy("DevOps-инженер Middle") == "DevOps-инженер"
    assert classify_vacancy("Senior DevOps Engineer") == "DevOps-инженер"
    assert classify_vacancy("Системный администратор Linux") == "System Administrator (Linux)"
    assert classify_vacancy("System Administrator") == "System Administrator (Linux)"
    assert classify_vacancy("Cloud Engineer (AWS)") == "Cloud Engineer (AWS / Yandex Cloud)"
    assert classify_vacancy("SRE-инженер") == "SRE (Site Reliability Engineer)"
    assert classify_vacancy("Сетевой инженер") == "Network Engineer (сетевой инженер)"
    assert classify_vacancy("Network Engineer") == "Network Engineer (сетевой инженер)"
    assert classify_vacancy("Бухгалтер") is None
    assert classify_vacancy(None) is None
    assert classify_vacancy("") is None


def test_split_description():
    """Тестируем разделение описания на секции."""
    html = "<p>Требования:</p><ul><li>Знание Linux</li><li>Опыт с Docker</li></ul><p>Условия работы:</p><ul><li>Офис в Москве</li></ul>"
    sections = split_description(html)
    assert 'Требования' in sections
    assert len(sections['Требования']) >= 1
    assert 'Условия работы' in sections

    html2 = "<p><strong>Обязанности:</strong></p><ul><li>Настройка серверов</li></ul><p><strong>Требования:</strong></p><ul><li>Python</li></ul>"
    sections2 = split_description(html2)
    assert 'Обязанности' in sections2
    assert 'Требования' in sections2

    html_br = '<p>Ты нам подходишь, если:</p><p>имеешь опыт с Linux</p><p>Опыт с Docker</p><p>Что мы предлагаем:</p><p>Удалёнка</p>'
    sections3 = split_description(html_br)
    assert 'Требования' in sections3
    assert len(sections3['Требования']) >= 2
    assert 'Условия работы' in sections3


def test_extract_salary_range():
    """Тестируем извлечение зарплатного диапазона."""
    assert extract_salary_range("Зарплата от 150 000 до 200 000 руб. на руки") == "150 000 - 200 000 ₽"
    assert extract_salary_range("Доход 120000 ₽") == "120 000 ₽"
    assert extract_salary_range("Оплата по договоренности") == "Не указана"
    assert extract_salary_range("Премия за проект 5 000 руб.") == "Не указана"
    assert extract_salary_range("") == "Не указана"
    assert extract_salary_range(None) == "Не указана"
    assert extract_salary_range("Зарплата 100 тыс руб") == "100 000 ₽"
    assert extract_salary_range("от 850 до 900 тыс руб") == "850 000 - 900 000 ₽"
    assert extract_salary_range("Ожидаем от 100 000 до 150 000 руб.") == "100 000 - 150 000 ₽"
    assert extract_salary_range("опыт работы с 50 ПК и серверами") == "Не указана"


def test_streamlit_app_runs():
    """Симулируем запуск Streamlit-приложения и нажатие кнопки поиска."""
    at = AppTest.from_file("app.py")
    at.run(timeout=30)
    assert not at.exception

    if at.button:
        at.button[0].click().run(timeout=30)
        assert not at.exception
