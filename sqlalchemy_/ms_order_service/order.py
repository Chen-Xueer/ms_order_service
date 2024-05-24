from typing import Optional
from sqlalchemy_.ms_order_service.base import Base
from sqlalchemy import Boolean, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class Order(Base):
    __tablename__ = "order"
    __table_args__ = (UniqueConstraint('transaction_id'),)
    
    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    charge_point_id: Mapped[str] = mapped_column(String(50), nullable=True)
    connector_id: Mapped[int] = mapped_column(Integer, nullable=True)
    ev_driver_id: Mapped[str] = mapped_column(String(50), nullable=True)
    tariff_id: Mapped[int] = mapped_column(Integer, nullable=True)
    is_charging: Mapped[bool] = mapped_column(Boolean, nullable=True)
    is_reservation: Mapped[bool] = mapped_column(Boolean, nullable=True)
    requires_payment: Mapped[bool] = mapped_column(Boolean, nullable=True)
    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_update: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    request_id: Mapped[str] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return "<Order {}>".format(self.transaction_id)
