import pytest

from app.core.exceptions import (
    InvalidINNChecksumException,
    InvalidSNILSChecksumException,
)
from app.services.validators import (
    is_valid_legal_entity_inn,
    is_valid_snils,
    validate_legal_entity_inn,
    validate_snils,
)


def test_valid_legal_entity_inn():
    valid_inns = [
        "7707083893",  # Сбербанк
        "7736207543",  # Яндекс
        "7702070139",  # Лукойл
        "7708503727",  # РЖД
    ]
    for inn in valid_inns:
        assert validate_legal_entity_inn(inn) == inn
        assert is_valid_legal_entity_inn(inn) is True


def test_invalid_legal_entity_inn():
    invalid_inns = [
        "7707083894",  # Неверная КС
        "1234567890",
        "770708389",   # 9 цифр
        "77070838931", # 11 цифр
        "770708389A",  # Не цифра
    ]
    for inn in invalid_inns:
        assert is_valid_legal_entity_inn(inn) is False
        with pytest.raises(InvalidINNChecksumException):
            validate_legal_entity_inn(inn)


def test_valid_snils():
    valid_snils_list = [
        "112-233-445 95",
        "11223344595",
        "087-452-322 84",
        "08745232284",
        "001-001-998 00",
    ]
    for snils in valid_snils_list:
        assert is_valid_snils(snils) is True
        cleaned = snils.replace("-", "").replace(" ", "")
        assert validate_snils(snils) == cleaned


def test_invalid_snils():
    invalid_snils_list = [
        "112-233-445 00",  # Неверная КС
        "11223344599",
        "112233445",      # Меньше 11 цифр
        "112233445951",   # Больше 11 цифр
        "112233445AA",
    ]
    for snils in invalid_snils_list:
        assert is_valid_snils(snils) is False
        with pytest.raises(InvalidSNILSChecksumException):
            validate_snils(snils)
