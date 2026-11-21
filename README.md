# B2B Document & Request Validator

Бэкенд-сервис для проверки юридических реквизитов (ИНН юрлиц, СНИЛС) и управления жизненным циклом заявок на изготовление сертификатов.

Стек: Python 3.11+, FastAPI, async SQLAlchemy 2.0, Alembic, Pydantic v2.

---

## Архитектура данных

```mermaid
erDiagram
    ORGANIZATION ||--o{ CERTIFICATE_REQUEST : "has"
    CERTIFICATE_REQUEST ||--o{ REQUEST_STATUS_HISTORY : "has"

    ORGANIZATION {
        int id PK
        string inn "10 цифр"
        string kpp "9 цифр, nullable"
        string name
        datetime created_at
    }

    CERTIFICATE_REQUEST {
        int id PK
        int org_id FK
        string applicant_full_name
        string applicant_snils "11 цифр"
        string status
        string rejection_reason "nullable"
        string idempotency_key "unique, nullable"
        datetime created_at
        datetime updated_at
    }

    REQUEST_STATUS_HISTORY {
        int id PK
        int request_id FK
        string old_status "nullable"
        string new_status
        string changed_by "nullable"
        string comment "nullable"
        datetime created_at
    }
```

---

## Жизненный цикл заявки (State Machine)

Правила переходов:
- Новая заявка создается в статусе `DRAFT`.
- `DRAFT` $\to$ `SUBMITTED`.
- `SUBMITTED` $\to$ `APPROVED` или `REJECTED` (при `REJECTED` обязательно указание `rejection_reason`).
- `REJECTED` $\to$ `DRAFT` (возврат на доработку).
- `APPROVED` — финальный статус, дальнейшие переходы запрещены.
- Любые нерегламентированные переходы возвращают `409 Conflict`.

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Создание заявки
    DRAFT --> SUBMITTED : Отправка
    SUBMITTED --> APPROVED : Одобрение
    SUBMITTED --> REJECTED : Отклонение (с rejection_reason)
    REJECTED --> DRAFT : Возврат на доработку
    APPROVED --> [*] : Финал
```

---

## Коды ошибок API

Ошибки бизнес-логики возвращаются в едином формате:

```json
{
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "Transition from APPROVED to DRAFT is not allowed. Allowed target statuses: []",
    "details": {
      "current_status": "APPROVED",
      "target_status": "DRAFT"
    }
  }
}
```

| Код ошибки | HTTP статус | Причина |
|---|---|---|
| `INVALID_INN_CHECKSUM` | `422` | Ошибка контрольного числа ИНН (по весам ФНС). |
| `INVALID_SNILS_CHECKSUM` | `422` | Ошибка контрольного числа СНИЛС (по алгоритму ПФР). |
| `INVALID_STATUS_TRANSITION` | `409` | Недопустимый переход статуса или отсутствует причина отказа. |
| `ENTITY_NOT_FOUND` | `404` | Запрашиваемая запись не найдена. |
| `DUPLICATE_IDEMPOTENCY_KEY` | `409` | Попытка повторного создания с тем же ключом, но другими данными. |

---

## Запуск

### 1. Окружение
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Конфигурация (.env)
По умолчанию используется SQLite:
```env
DATABASE_URL=sqlite+aiosqlite:///./b2b_validator.db
```
Для PostgreSQL:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/b2b_validator
```

### 3. Миграции
```bash
alembic upgrade head
```

### 4. Запуск сервера
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Swagger UI: `http://localhost:8000/docs`

### 5. Тесты
```bash
pytest -v tests/test_integration.py
```
