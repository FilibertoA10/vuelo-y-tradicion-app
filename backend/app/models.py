from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("admin", "artesano", name="user_role"), nullable=False, default="artesano")
    created_at = Column(DateTime, server_default=func.now())

    artisan = relationship("Artisan", back_populates="user", uselist=False)


class Artisan(Base):
    __tablename__ = "artisans"

    id = Column(Integer, primary_key=True, index=True)
    # Cuenta de usuario opcional: el administrador puede dar de alta talleres
    # que todavía no tienen cuenta propia.
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)
    full_name = Column(String(150), nullable=False)
    workshop_name = Column(String(150), nullable=False)
    community = Column(String(100), nullable=False)
    bio = Column(Text)
    phone_whatsapp = Column(String(20), nullable=False)
    profile_image_url = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="artisan")
    products = relationship(
        "Product", back_populates="artisan", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    artisan_id = Column(Integer, ForeignKey("artisans.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(60), nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=1)
    image_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())

    artisan = relationship("Artisan", back_populates="products")
