"""initial_b2b_entities

Revision ID: 0001_initial_entities
Revises: 
Create Date: 2026-11-21 00:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_entities"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

request_status_enum = sa.Enum("DRAFT", "SUBMITTED", "REJECTED", "APPROVED", name="request_status_enum")


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("inn", sa.String(length=12), nullable=False),
        sa.Column("kpp", sa.String(length=9), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organizations_inn"), "organizations", ["inn"], unique=False)
    op.create_index("ix_organizations_inn_kpp", "organizations", ["inn", "kpp"], unique=False)

    op.create_table(
        "certificate_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("applicant_full_name", sa.String(length=255), nullable=False),
        sa.Column("applicant_snils", sa.String(length=14), nullable=False),
        sa.Column("status", request_status_enum, nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_certificate_requests_org_id"), "certificate_requests", ["org_id"], unique=False)
    op.create_index(op.f("ix_certificate_requests_applicant_snils"), "certificate_requests", ["applicant_snils"], unique=False)
    op.create_index(op.f("ix_certificate_requests_status"), "certificate_requests", ["status"], unique=False)
    op.create_index(op.f("ix_certificate_requests_idempotency_key"), "certificate_requests", ["idempotency_key"], unique=True)

    op.create_table(
        "request_status_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("old_status", request_status_enum, nullable=True),
        sa.Column("new_status", request_status_enum, nullable=False),
        sa.Column("changed_by", sa.String(length=100), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["certificate_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_request_status_history_request_id"), "request_status_history", ["request_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_request_status_history_request_id"), table_name="request_status_history")
    op.drop_table("request_status_history")

    op.drop_index(op.f("ix_certificate_requests_idempotency_key"), table_name="certificate_requests")
    op.drop_index(op.f("ix_certificate_requests_status"), table_name="certificate_requests")
    op.drop_index(op.f("ix_certificate_requests_applicant_snils"), table_name="certificate_requests")
    op.drop_index(op.f("ix_certificate_requests_org_id"), table_name="certificate_requests")
    op.drop_table("certificate_requests")

    op.drop_index("ix_organizations_inn_kpp", table_name="organizations")
    op.drop_index(op.f("ix_organizations_inn"), table_name="organizations")
    op.drop_table("organizations")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        request_status_enum.drop(bind, checkfirst=True)
