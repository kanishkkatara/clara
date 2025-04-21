from sqlalchemy import (
    Column, Integer, String, Boolean, TIMESTAMP, func, ForeignKey
)
from sqlalchemy.orm import relationship
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True, index=True)
    google_id     = Column(String, unique=True, index=True, nullable=True)
    email         = Column(String, unique=True, index=True, nullable=False)
    name          = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at    = Column(TIMESTAMP(timezone=True),
                           server_default=func.now(),
                           onupdate=func.now())

    profile       = relationship("UserProfile", back_populates="user", uselist=False)
