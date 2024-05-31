from typing import Optional
from sqlalchemy_.ms_order_service.base import Base
from sqlalchemy import Boolean, DECIMAL, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime


class Tenant(Base):
    __tablename__ = "tenant"

    tenant_id: Mapped[int] = mapped_column(Integer, autoincrement=True, primary_key=True)
    tenant: Mapped[str] = mapped_column(String(100), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(3000), nullable=True)

    def __repr__(self):
        return "<Tenant {}>".format(self.tenant_id)