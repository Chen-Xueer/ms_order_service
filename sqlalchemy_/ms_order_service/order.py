from typing import Optional
from sqlalchemy_.ms_order_service.base import Base
from sqlalchemy import Boolean, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class Order(Base):
    __tablename__ = "order"
    __table_args__ = (UniqueConstraint('transaction_id'),)
    
    transaction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    charge_point_id: Mapped[str] = mapped_column(String(50), nullable=False)
    connector_id: Mapped[int] = mapped_column(Integer, nullable=False)
    ev_driver_id: Mapped[str] = mapped_column(String(50), nullable=False)
    rfid: Mapped[str] = mapped_column(String(50), nullable=False)
    tariff_id: Mapped[int] = mapped_column(Integer, nullable=False)
    is_charging: Mapped[bool] = mapped_column(Boolean, nullable=False)
    is_reservation: Mapped[bool] = mapped_column(Boolean, nullable=False)
    requires_payment: Mapped[bool] = mapped_column(Boolean, nullable=False)
    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_update: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self):
        return "<Order {}>".format(self.transaction_id)
