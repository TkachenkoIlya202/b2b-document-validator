import re

from app.core.exceptions import (
    InvalidINNChecksumException,
    InvalidSNILSChecksumException,
)

INN_WEIGHTS = (2, 4, 10, 3, 5, 9, 4, 6, 8)


def validate_legal_entity_inn(inn: str) -> str:
    cleaned = inn.strip()
    if len(cleaned) != 10 or not cleaned.isdigit():
        raise InvalidINNChecksumException("Legal entity INN must be 10 digits", details={"inn": inn})

    digits = [int(c) for c in cleaned]

    # ФНС: sum(digits[0..8] * weights) % 11 % 10
    checksum = (sum(d * w for d, w in zip(digits[:9], INN_WEIGHTS)) % 11) % 10

    if digits[9] != checksum:
        raise InvalidINNChecksumException(
            f"Invalid INN checksum: expected {checksum}, got {digits[9]}",
            details={"inn": inn, "expected": checksum, "actual": digits[9]},
        )

    return cleaned


def is_valid_legal_entity_inn(inn: str) -> bool:
    try:
        validate_legal_entity_inn(inn)
        return True
    except InvalidINNChecksumException:
        return False


def validate_snils(snils: str) -> str:
    cleaned = re.sub(r"[-\s]", "", snils.strip())

    if len(cleaned) != 11 or not cleaned.isdigit():
        raise InvalidSNILSChecksumException("SNILS must be 11 digits", details={"snils": snils})

    number_part = int(cleaned[:9])
    check_digits = int(cleaned[9:])

    if number_part <= 1001998:
        return cleaned

    # ПФР: sum(d[i] * (9 - i))
    # <100 -> sum; 100/101 -> 0; >101 -> mod 101 (100 -> 0)
    raw_sum = sum(int(cleaned[i]) * (9 - i) for i in range(9))

    if raw_sum < 100:
        expected = raw_sum
    elif raw_sum in (100, 101):
        expected = 0
    else:
        rem = raw_sum % 101
        expected = 0 if rem == 100 else rem

    if check_digits != expected:
        raise InvalidSNILSChecksumException(
            f"Invalid SNILS checksum: expected {expected:02d}, got {check_digits:02d}",
            details={"snils": snils, "expected": expected, "actual": check_digits},
        )

    return cleaned


def is_valid_snils(snils: str) -> bool:
    try:
        validate_snils(snils)
        return True
    except InvalidSNILSChecksumException:
        return False
