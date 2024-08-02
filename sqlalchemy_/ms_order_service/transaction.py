from typing import Optional
from sqlalchemy_.ms_order_service.base import Base
from sqlalchemy import Boolean, DECIMAL, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class Transaction(Base):
    __tablename__ = "transaction"

    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey('order.transaction_id'), primary_key=True)
    amount: Mapped[DECIMAL] = mapped_column(DECIMAL(precision=10, scale=3), nullable=True)
    charged_energy: Mapped[DECIMAL] = mapped_column(DECIMAL(precision=10, scale=4), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    duration: Mapped[int] = mapped_column(Integer, nullable=True)
    meter_start: Mapped[int] = mapped_column(Integer, nullable=True)
    meter_interval: Mapped[int] = mapped_column(Integer, nullable=True)
    meter_stop: Mapped[int] = mapped_column(Integer, nullable=True)
    paid_by: Mapped[str] = mapped_column(String(50), nullable=True)
    transaction_detail: Mapped[str] = mapped_column(String(3000), nullable=True)

    def __repr__(self):
        return "<Transaction {}>".format(self.transaction_id)
