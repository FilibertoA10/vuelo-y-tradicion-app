from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .whatsapp import normalize_phone


class ArtisanBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    workshop_name: str = Field(min_length=2, max_length=150)
    community: str = Field(min_length=2, max_length=100)
    bio: Optional[str] = Field(default=None, max_length=2000)
    phone_whatsapp: str
    profile_image_url: Optional[str] = Field(default=None, max_length=255)

    @field_validator("phone_whatsapp")
    @classmethod
    def _phone(cls, value: str) -> str:
        return normalize_phone(value)


class ArtisanCreate(ArtisanBase):
    pass


class ArtisanUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    workshop_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    community: Optional[str] = Field(default=None, min_length=2, max_length=100)
    bio: Optional[str] = Field(default=None, max_length=2000)
    phone_whatsapp: Optional[str] = None
    profile_image_url: Optional[str] = Field(default=None, max_length=255)

    @field_validator("phone_whatsapp")
    @classmethod
    def _phone(cls, value: Optional[str]) -> Optional[str]:
        return normalize_phone(value) if value is not None else value


class ArtisanOut(ArtisanBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ArtisanListOut(ArtisanOut):
    product_count: int = 0


class ProductBase(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=2, max_length=4000)
    category: str = Field(min_length=2, max_length=60)
    price: float = Field(gt=0, le=1_000_000)
    stock: int = Field(default=1, ge=0, le=100_000)
    image_url: str = Field(min_length=1, max_length=255)
    is_active: bool = True


class ProductCreate(ProductBase):
    artisan_id: int


class ProductUpdate(BaseModel):
    artisan_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, min_length=2, max_length=4000)
    category: Optional[str] = Field(default=None, min_length=2, max_length=60)
    price: Optional[float] = Field(default=None, gt=0, le=1_000_000)
    stock: Optional[int] = Field(default=None, ge=0, le=100_000)
    image_url: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class ProductBrief(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    artisan_id: int


class ProductOut(ProductBrief):
    artisan: ArtisanOut


class ArtisanDetail(ArtisanOut):
    products: List[ProductBrief] = []


# --- Autenticación ---
class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=1, max_length=128)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str


# --- Pedido por WhatsApp ---
class OrderItem(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=99)


class CheckoutRequest(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    items: List[OrderItem] = Field(min_length=1, max_length=50)
    notes: Optional[str] = Field(default=None, max_length=500)


class OrderLineOut(BaseModel):
    product_id: int
    title: str
    quantity: int
    subtotal: float


class WhatsAppOrderOut(BaseModel):
    artisan_id: int
    artisan: str
    workshop: str
    items: List[OrderLineOut]
    total: float
    whatsapp_url: str


class CheckoutOut(BaseModel):
    orders: List[WhatsAppOrderOut]
    grand_total: float
