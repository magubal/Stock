from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from ..database import Base


class MoatStockSnapshot(Base):
    __tablename__ = "moat_stock_snapshot"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(12), nullable=False, unique=True, index=True)
    name = Column(String(120), nullable=False)
    eval_date = Column(String(40))
    moat_score = Column(Integer)
    investment_value = Column(Integer)
    bm = Column(String(200))
    bigo_raw = Column(Text, nullable=False, default="")
    details_json = Column(Text, nullable=False, default="{}")
    source_file = Column(String(260), nullable=False)
    source_row_hash = Column(String(64), nullable=False, index=True)
    source_updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MoatStockSyncRun(Base):
    __tablename__ = "moat_stock_sync_runs"

    id = Column(Integer, primary_key=True, index=True)
    source_file = Column(String(260), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    finished_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    total_rows = Column(Integer, nullable=False, default=0)
    inserted_count = Column(Integer, nullable=False, default=0)
    updated_count = Column(Integer, nullable=False, default=0)
    unchanged_count = Column(Integer, nullable=False, default=0)
    reactivated_count = Column(Integer, nullable=False, default=0)
    deactivated_count = Column(Integer, nullable=False, default=0)
    duplicate_ticker_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    note = Column(Text)


class MoatStockHistory(Base):
    __tablename__ = "moat_stock_history"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("moat_stock_sync_runs.id", ondelete="SET NULL"), index=True)
    ticker = Column(String(12), nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # insert/update/deactivate/reactivate
    change_json = Column(Text, nullable=False, default="{}")
    source_file = Column(String(260), nullable=False)
    source_row_hash = Column(String(64), nullable=False, index=True)
    happened_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
