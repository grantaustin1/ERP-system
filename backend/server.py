from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import qrcode
from io import BytesIO
import base64
import jwt
from passlib.context import CryptContext
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from services.respondio_service import RespondIOService

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize respond.io service
respondio_service = RespondIOService()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Utility Functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None

def generate_qr_code(data: str) -> str:
    """Generate QR code and return as base64 string"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def geocode_address(address: str) -> tuple:
    """Geocode an address and return (latitude, longitude)"""
    if not address or len(address.strip()) < 5:
        return None, None
    
    try:
        geolocator = Nominatim(user_agent="gym_access_hub")
        location = geolocator.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        return None, None
    except (GeocoderTimedOut, GeocoderServiceError):
        return None, None

# Models
class MembershipType(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    billing_frequency: str  # monthly, 6months, yearly, one-time
    duration_months: int
    duration_days: int = 0  # For sub-month durations (1 day, 3 day, 1 week, etc)
    payment_type: str = "debit_order"  # paid_upfront, debit_order
    rollover_enabled: bool = False  # If true, converts to monthly after term
    # Base membership and variations
    is_base_membership: bool = True
    base_membership_id: Optional[str] = None  # If this is a variation, links to base
    variation_type: Optional[str] = None  # student, corporate, promo, senior, etc
    discount_percentage: float = 0.0  # Discount applied from base price
    # Multiple members support
    max_members: int = 1  # Maximum members allowed per membership (1 = individual, 2+ = group/family)
    # Levy configuration
    levy_enabled: bool = False
    levy_frequency: str = "annual"  # annual, biannual
    levy_timing: str = "anniversary"  # anniversary, fixed_dates (1 June, 1 Dec)
    levy_amount_type: str = "fixed"  # fixed, same_as_membership
    levy_amount: float = 0.0  # Only used if levy_amount_type is "fixed"
    levy_payment_method: str = "debit_order"  # debit_order, upfront (for paid_upfront memberships)
    features: List[str] = []
    peak_hours_only: bool = False
    multi_site_access: bool = False
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MembershipTypeCreate(BaseModel):
    name: str
    description: str
    price: float
    billing_frequency: str
    duration_months: int
    duration_days: int = 0
    payment_type: str = "debit_order"
    rollover_enabled: bool = False
    is_base_membership: bool = True
    base_membership_id: Optional[str] = None
    variation_type: Optional[str] = None
    discount_percentage: float = 0.0
    max_members: int = 1
    levy_enabled: bool = False
    levy_frequency: str = "annual"
    levy_timing: str = "anniversary"
    levy_amount_type: str = "fixed"
    levy_amount: float = 0.0
    levy_payment_method: str = "debit_order"
    features: List[str] = []
    peak_hours_only: bool = False
    multi_site_access: bool = False

class Member(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    last_name: str
    email: EmailStr
    phone: str  # Mobile number
    home_phone: Optional[str] = None
    work_phone: Optional[str] = None
    membership_type_id: str
    membership_status: str = "active"  # active, suspended, cancelled
    join_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expiry_date: Optional[datetime] = None
    qr_code: str = ""
    photo_url: Optional[str] = None
    is_debtor: bool = False
    debt_amount: float = 0.0  # Calculated debt amount
    # Sales consultant
    sales_consultant_id: Optional[str] = None
    sales_consultant_name: Optional[str] = None
    # Source and referral tracking
    source: Optional[str] = None  # Walk-in, Online, Social Media, Phone-in, Referral, Canvassing, Flyers
    referred_by: Optional[str] = None  # Name or ID of referrer
    # Membership group (for family/corporate packages)
    membership_group_id: Optional[str] = None
    is_primary_member: bool = True  # True if primary payer
    # Payment option selected
    selected_payment_option_id: Optional[str] = None
    # Address and geo-location
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Banking details
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch_code: Optional[str] = None
    account_holder_name: Optional[str] = None
    # Identification
    id_number: Optional[str] = None  # Identity or Passport number
    id_type: Optional[str] = None  # "id", "passport"
    # Contract dates
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[datetime] = None
    # Other
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None

class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    home_phone: Optional[str] = None
    work_phone: Optional[str] = None
    membership_type_id: str
    sales_consultant_id: Optional[str] = None
    source: Optional[str] = None  # Walk-in, Online, Social Media, Phone-in, Referral, Canvassing, Flyers
    referred_by: Optional[str] = None
    address: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_branch_code: Optional[str] = None
    account_holder_name: Optional[str] = None
    id_number: Optional[str] = None
    id_type: Optional[str] = None
    contract_start_date: Optional[datetime] = None
    contract_end_date: Optional[str] = None
    emergency_contact: Optional[str] = None
    notes: Optional[str] = None

class AccessLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_id: str
    member_name: str
    access_method: str  # qr_code, fingerprint, facial_recognition, manual_override
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str  # granted, denied
    reason: Optional[str] = None
    override_by: Optional[str] = None

class AccessLogCreate(BaseModel):
    member_id: str
    access_method: str
    reason: Optional[str] = None
    override_by: Optional[str] = None

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_id: str
    invoice_number: str
    amount: float
    description: str
    due_date: datetime
    paid_date: Optional[datetime] = None
    status: str = "pending"  # pending, paid, overdue, cancelled, failed
    payment_method: Optional[str] = None
    payment_gateway: Optional[str] = None  # Stripe, PayPal, Manual, etc.
    status_message: Optional[str] = None  # Additional status information
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # For tracking debit order batches
    batch_id: Optional[str] = None
    batch_date: Optional[datetime] = None

class InvoiceCreate(BaseModel):
    member_id: str
    amount: float
    description: str
    due_date: datetime

class Payment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str
    member_id: str
    amount: float
    payment_method: str  # cash, card, debit_order, eft
    payment_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "completed"
    reference: Optional[str] = None

class PaymentCreate(BaseModel):
    invoice_id: str
    member_id: str
    amount: float
    payment_method: str
    reference: Optional[str] = None

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password: str
    full_name: str
    role: str = "admin"  # admin, staff, member
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class CancellationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_id: str
    member_name: str
    membership_type: str
    reason: str
    requested_by: str  # member, staff
    request_source: str = "staff"  # staff, mobile_app, email
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # pending, staff_approved, manager_approved, admin_approved, rejected, completed
    staff_approval: Optional[dict] = None  # {approved_by, approved_at, comments}
    manager_approval: Optional[dict] = None
    admin_approval: Optional[dict] = None
    rejection_reason: Optional[str] = None
    completed_at: Optional[datetime] = None

class CancellationRequestCreate(BaseModel):
    member_id: str
    reason: str
    request_source: str = "staff"

class ApprovalAction(BaseModel):
    request_id: str
    action: str  # approve, reject
    comments: Optional[str] = None
    rejection_reason: Optional[str] = None

class MembershipVariationCreate(BaseModel):
    variation_type: str  # student, corporate, promo, senior, family
    discount_percentage: float
    description: Optional[str] = None


# ============= PAYMENT OPTIONS MODELS =============

class PaymentOption(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    membership_type_id: str  # Links to membership variation or base
    payment_name: str  # e.g., "Upfront Saver", "Monthly Budget Plan"
    payment_type: str  # "single", "recurring"
    payment_frequency: str  # "one-time", "monthly", "quarterly", "bi-annual", "annual"
    installment_amount: float  # Amount per installment
    number_of_installments: int  # Total number of payments
    total_amount: float  # Total cost (calculated or set)
    # Auto-renewal settings
    auto_renewal_enabled: bool = False
    auto_renewal_frequency: str = "monthly"  # "monthly", "same_frequency", "none"
    auto_renewal_price: Optional[float] = None  # Price after auto-renewal (if different)
    # Description and display
    description: Optional[str] = None
    display_order: int = 0  # For sorting payment options
    is_default: bool = False  # Default selected option
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PaymentOptionCreate(BaseModel):
    membership_type_id: str
    payment_name: str
    payment_type: str
    payment_frequency: str
    installment_amount: float
    number_of_installments: int
    auto_renewal_enabled: bool = False
    auto_renewal_frequency: str = "monthly"
    auto_renewal_price: Optional[float] = None
    description: Optional[str] = None
    display_order: int = 0
    is_default: bool = False

class PaymentOptionUpdate(BaseModel):
    payment_name: Optional[str] = None
    installment_amount: Optional[float] = None
    number_of_installments: Optional[int] = None
    auto_renewal_enabled: Optional[bool] = None
    auto_renewal_frequency: Optional[str] = None
    auto_renewal_price: Optional[float] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

# ============= MULTIPLE MEMBERS MODELS =============

class MembershipGroup(BaseModel):
    """Represents a group of members sharing one membership (e.g., family package)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    membership_type_id: str
    primary_member_id: str  # The member who owns the membership
    group_name: Optional[str] = None  # e.g., "Smith Family"
    max_members: int = 1  # Maximum members allowed in this group
    current_member_count: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MembershipGroupCreate(BaseModel):
    membership_type_id: str
    primary_member_id: str
    group_name: Optional[str] = None
    max_members: int = 1


class PaymentSource(BaseModel):
    """Represents configurable payment sources for member acquisition tracking"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Walk-in, Online, Social Media, Phone-in, Referral, Canvassing, Flyers
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class PaymentSourceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


class PaymentSourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class Consultant(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    employee_id: Optional[str] = None
    status: str = "active"  # active, inactive
    hire_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_monthly_sales: float = 0.0  # Monthly sales target
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConsultantCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    employee_id: Optional[str] = None
    target_monthly_sales: float = 0.0

class CommissionStructure(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    commission_type: str  # fixed, percentage, tiered
    # For fixed commission
    fixed_amount: float = 0.0
    # For percentage commission
    percentage: float = 0.0
    # For tiered commission (JSON string of tiers)
    tiers: List[dict] = []  # [{"min_sales": 0, "max_sales": 5000, "rate": 5}, ...]
    # Commission frequency
    frequency: str = "one_time"  # one_time, recurring_monthly
    applies_to: str = "all"  # all, membership_type_id
    membership_type_id: Optional[str] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CommissionStructureCreate(BaseModel):
    name: str
    description: str
    commission_type: str
    fixed_amount: float = 0.0
    percentage: float = 0.0
    tiers: List[dict] = []
    frequency: str = "one_time"
    applies_to: str = "all"
    membership_type_id: Optional[str] = None

class Commission(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    consultant_id: str
    consultant_name: str
    member_id: str
    member_name: str
    membership_type: str
    sale_amount: float
    commission_amount: float
    commission_structure_id: str
    commission_structure_name: str
    commission_type: str
    sale_date: datetime
    payment_status: str = "pending"  # pending, paid
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Levy(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_id: str
    member_name: str
    levy_type: str  # annual, biannual
    amount: float
    due_date: datetime
    status: str = "pending"  # pending, paid, overdue
    invoice_id: Optional[str] = None
    paid_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Automation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    trigger_type: str  # payment_failed, member_joined, member_inactive, membership_expiring, invoice_overdue
    conditions: dict = {}  # Additional filters like membership_type, amount_threshold, days_inactive
    actions: List[dict] = []  # List of actions: [{type: "send_whatsapp", delay_minutes: 1, message: "..."}]
    enabled: bool = True
    test_mode: bool = False  # If true, automation runs in test/non-live mode
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered: Optional[datetime] = None
    execution_count: int = 0

class AutomationCreate(BaseModel):
    name: str
    description: str
    trigger_type: str
    conditions: dict = {}
    actions: List[dict] = []
    test_mode: bool = False

class AutomationExecution(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    automation_id: str
    automation_name: str
    trigger_data: dict  # Info about what triggered it
    scheduled_for: datetime  # When the action should execute
    executed_at: Optional[datetime] = None
    status: str = "pending"  # pending, completed, failed
    result: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Lead(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str  # facebook, instagram, whatsapp, walk_in, referral
    full_name: str
    email: Optional[str] = None
    phone: str
    message: Optional[str] = None
    interest: Optional[str] = None
    assigned_to_consultant_id: Optional[str] = None
    assigned_to_consultant_name: Optional[str] = None
    status: str = "new"  # new, contacted, qualified, converted, lost
    follow_up_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LeadCreate(BaseModel):
    source: str
    full_name: str
    email: Optional[str] = None
    phone: str
    message: Optional[str] = None
    interest: Optional[str] = None
    assigned_to_consultant_id: Optional[str] = None

# Auth dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"email": payload.get("sub")}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

# Auth Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = user_data.model_dump()
    user_dict["password"] = hash_password(user_dict["password"])
    user = User(**user_dict)
    
    doc = user.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.users.insert_one(doc)
    
    token = create_access_token({"sub": user.email, "role": user.role})
    return Token(access_token=token)

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["email"], "role": user["role"]})
    return Token(access_token=token)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    for u in users:
        if isinstance(u.get("created_at"), str):
            u["created_at"] = datetime.fromisoformat(u["created_at"])
    return users

# Duration Templates (predefined common durations)
DURATION_TEMPLATES = [
    {"name": "Single Visit", "days": 1, "months": 0},
    {"name": "2 Day Pass", "days": 2, "months": 0},
    {"name": "3 Day Pass", "days": 3, "months": 0},
    {"name": "1 Week", "days": 7, "months": 0},
    {"name": "2 Week", "days": 14, "months": 0},
    {"name": "1 Month", "days": 0, "months": 1},
    {"name": "3 Month", "days": 0, "months": 3},
    {"name": "6 Month", "days": 0, "months": 6},
    {"name": "12 Month", "days": 0, "months": 12},
    {"name": "24 Month", "days": 0, "months": 24},
    {"name": "36 Month", "days": 0, "months": 36},
]

VARIATION_TYPES = [
    {"value": "student", "label": "Student Discount", "typical_discount": 15},
    {"value": "corporate", "label": "Corporate Rate", "typical_discount": 10},
    {"value": "senior", "label": "Senior Citizen", "typical_discount": 20},
    {"value": "family", "label": "Family Package", "typical_discount": 25},
    {"value": "promo", "label": "Promotional Offer", "typical_discount": 30},
    {"value": "early_bird", "label": "Early Bird Special", "typical_discount": 15},
    {"value": "referral", "label": "Referral Discount", "typical_discount": 10},
]

@api_router.get("/membership-types/templates/durations")
async def get_duration_templates():
    """Get predefined duration templates"""
    return DURATION_TEMPLATES

@api_router.get("/membership-types/templates/variations")
async def get_variation_types():
    """Get predefined variation types"""
    return VARIATION_TYPES

# Membership Types Routes
@api_router.post("/membership-types", response_model=MembershipType)
async def create_membership_type(data: MembershipTypeCreate, current_user: User = Depends(get_current_user)):
    membership = MembershipType(**data.model_dump())
    doc = membership.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.membership_types.insert_one(doc)
    return membership

@api_router.get("/membership-types", response_model=List[MembershipType])
async def get_membership_types():
    types = await db.membership_types.find({"status": "active"}, {"_id": 0}).to_list(1000)
    for t in types:
        if isinstance(t.get("created_at"), str):
            t["created_at"] = datetime.fromisoformat(t["created_at"])
    return types

@api_router.get("/membership-types/{type_id}", response_model=MembershipType)
async def get_membership_type(type_id: str):
    membership_type = await db.membership_types.find_one({"id": type_id}, {"_id": 0})
    if not membership_type:
        raise HTTPException(status_code=404, detail="Membership type not found")
    if isinstance(membership_type.get("created_at"), str):
        membership_type["created_at"] = datetime.fromisoformat(membership_type["created_at"])
    return MembershipType(**membership_type)

@api_router.get("/membership-types/base/list")
async def get_base_memberships():
    """Get only base memberships (no variations)"""
    base_memberships = await db.membership_types.find(
        {"is_base_membership": True, "status": "active"}, 
        {"_id": 0}
    ).to_list(1000)
    for bm in base_memberships:
        if isinstance(bm.get("created_at"), str):
            bm["created_at"] = datetime.fromisoformat(bm["created_at"])
    return base_memberships

@api_router.get("/membership-types/{type_id}/variations")
async def get_membership_variations(type_id: str):
    """Get all variations of a base membership"""
    variations = await db.membership_types.find(
        {"base_membership_id": type_id, "status": "active"},
        {"_id": 0}
    ).to_list(1000)
    for var in variations:
        if isinstance(var.get("created_at"), str):
            var["created_at"] = datetime.fromisoformat(var["created_at"])
    return variations

@api_router.post("/membership-types/{base_id}/create-variation", response_model=MembershipType)
async def create_membership_variation(base_id: str, data: MembershipVariationCreate, current_user: User = Depends(get_current_user)):
    """Create a variation of a base membership with discount"""
    # Get base membership
    base = await db.membership_types.find_one({"id": base_id})
    if not base:
        raise HTTPException(status_code=404, detail="Base membership not found")
    
    # Calculate discounted price
    base_price = base["price"]
    discounted_price = base_price * (1 - data.discount_percentage / 100)
    
    # Get variation label
    variation_label = next((v["label"] for v in VARIATION_TYPES if v["value"] == data.variation_type), data.variation_type.title())
    
    # Create variation with inherited properties
    variation = MembershipType(
        name=f"{base['name']} - {variation_label}",
        description=data.description or f"{variation_label} - {data.discount_percentage}% off",
        price=discounted_price,
        billing_frequency=base["billing_frequency"],
        duration_months=base["duration_months"],
        duration_days=base.get("duration_days", 0),
        payment_type=base["payment_type"],
        rollover_enabled=base.get("rollover_enabled", False),
        is_base_membership=False,
        base_membership_id=base_id,
        variation_type=data.variation_type,
        discount_percentage=data.discount_percentage,
        levy_enabled=base.get("levy_enabled", False),
        levy_frequency=base.get("levy_frequency", "annual"),
        levy_timing=base.get("levy_timing", "anniversary"),
        levy_amount_type=base.get("levy_amount_type", "fixed"),
        levy_amount=base.get("levy_amount", 0.0),
        levy_payment_method=base.get("levy_payment_method", "debit_order"),
        features=base.get("features", []),
        peak_hours_only=base.get("peak_hours_only", False),
        multi_site_access=base.get("multi_site_access", False),
    )
    
    doc = variation.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.membership_types.insert_one(doc)
    
    return variation


# ============= PAYMENT OPTIONS ENDPOINTS =============

@api_router.get("/payment-options/{membership_type_id}")
async def get_payment_options(membership_type_id: str):
    """Get all payment options for a membership type"""
    options = await db.payment_options.find(
        {"membership_type_id": membership_type_id, "is_active": True},
        {"_id": 0}
    ).sort("display_order", 1).to_list(100)
    
    for opt in options:
        if isinstance(opt.get("created_at"), str):
            opt["created_at"] = datetime.fromisoformat(opt["created_at"])
    
    return options

@api_router.post("/payment-options", response_model=PaymentOption)
async def create_payment_option(data: PaymentOptionCreate, current_user: User = Depends(get_current_user)):
    """Create a new payment option for a membership type"""
    # Verify membership type exists
    membership = await db.membership_types.find_one({"id": data.membership_type_id})
    if not membership:
        raise HTTPException(status_code=404, detail="Membership type not found")
    
    # Calculate total amount
    total_amount = data.installment_amount * data.number_of_installments
    
    # Create payment option
    payment_option = PaymentOption(
        **data.dict(),
        total_amount=total_amount
    )
    
    # Prepare for MongoDB
    option_dict = payment_option.dict()
    option_dict["created_at"] = option_dict["created_at"].isoformat()
    
    await db.payment_options.insert_one(option_dict)
    
    return payment_option

@api_router.put("/payment-options/{option_id}")
async def update_payment_option(
    option_id: str,
    data: PaymentOptionUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a payment option"""
    existing = await db.payment_options.find_one({"id": option_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Payment option not found")
    
    # Update fields
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    
    # Recalculate total if installment fields changed
    if "installment_amount" in update_data or "number_of_installments" in update_data:
        installment_amount = update_data.get("installment_amount", existing["installment_amount"])
        number_of_installments = update_data.get("number_of_installments", existing["number_of_installments"])
        update_data["total_amount"] = installment_amount * number_of_installments
    
    await db.payment_options.update_one(
        {"id": option_id},
        {"$set": update_data}
    )
    
    updated = await db.payment_options.find_one({"id": option_id}, {"_id": 0})
    return updated

@api_router.delete("/payment-options/{option_id}")
async def delete_payment_option(option_id: str, current_user: User = Depends(get_current_user)):
    """Delete a payment option (soft delete by setting is_active to False)"""
    result = await db.payment_options.update_one(
        {"id": option_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment option not found")
    
    return {"message": "Payment option deleted successfully"}

# ============= MEMBERSHIP GROUPS ENDPOINTS =============

@api_router.get("/membership-groups/{group_id}")
async def get_membership_group(group_id: str, current_user: User = Depends(get_current_user)):
    """Get membership group details"""
    group = await db.membership_groups.find_one({"id": group_id}, {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Membership group not found")
    
    if isinstance(group.get("created_at"), str):
        group["created_at"] = datetime.fromisoformat(group["created_at"])
    
    return group

@api_router.get("/membership-groups/{group_id}/members")
async def get_group_members(group_id: str, current_user: User = Depends(get_current_user)):
    """Get all members in a membership group"""
    members = await db.members.find(
        {"membership_group_id": group_id},
        {"_id": 0}
    ).to_list(100)
    
    return members

@api_router.post("/membership-groups", response_model=MembershipGroup)
async def create_membership_group(data: MembershipGroupCreate, current_user: User = Depends(get_current_user)):
    """Create a new membership group"""
    # Verify membership type exists
    membership = await db.membership_types.find_one({"id": data.membership_type_id})
    if not membership:
        raise HTTPException(status_code=404, detail="Membership type not found")
    
    # Verify primary member exists
    member = await db.members.find_one({"id": data.primary_member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Primary member not found")
    
    # Create group
    group = MembershipGroup(
        **data.dict(),
        current_member_count=1
    )
    
    group_dict = group.dict()
    group_dict["created_at"] = group_dict["created_at"].isoformat()
    
    await db.membership_groups.insert_one(group_dict)
    
    # Update primary member with group ID
    await db.members.update_one(
        {"id": data.primary_member_id},
        {"$set": {
            "membership_group_id": group.id,
            "is_primary_member": True
        }}
    )
    
    return group

@api_router.post("/membership-groups/{group_id}/add-member")
async def add_member_to_group(
    group_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user)
):
    """Add a member to an existing group"""
    # Get group
    group = await db.membership_groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if group is full
    if group["current_member_count"] >= group["max_members"]:
        raise HTTPException(status_code=400, detail="Group is full")
    
    # Verify member exists
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Update member with group ID
    await db.members.update_one(
        {"id": member_id},
        {"$set": {
            "membership_group_id": group_id,
            "is_primary_member": False
        }}
    )
    
    # Update group member count
    await db.membership_groups.update_one(
        {"id": group_id},
        {"$inc": {"current_member_count": 1}}
    )
    
    return {"message": "Member added to group successfully"}

@api_router.delete("/membership-groups/{group_id}/remove-member/{member_id}")
async def remove_member_from_group(
    group_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a group"""
    # Verify member is in group
    member = await db.members.find_one({"id": member_id, "membership_group_id": group_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not in this group")
    
    # Check if primary member
    if member.get("is_primary_member"):
        raise HTTPException(status_code=400, detail="Cannot remove primary member. Transfer ownership first.")
    
    # Remove member from group
    await db.members.update_one(
        {"id": member_id},
        {"$set": {
            "membership_group_id": None,
            "is_primary_member": True
        }}
    )
    
    # Update group member count
    await db.membership_groups.update_one(
        {"id": group_id},
        {"$inc": {"current_member_count": -1}}
    )
    
    return {"message": "Member removed from group successfully"}


# ============= PAYMENT SOURCES ENDPOINTS =============

@api_router.get("/payment-sources")
async def get_payment_sources(current_user: User = Depends(get_current_user)):
    """Get all payment sources sorted by display order"""
    sources = await db.payment_sources.find(
        {"is_active": True},
        {"_id": 0}
    ).sort("display_order", 1).to_list(100)
    
    # Parse datetime fields
    for source in sources:
        if isinstance(source.get("created_at"), str):
            source["created_at"] = datetime.fromisoformat(source["created_at"])
        if isinstance(source.get("updated_at"), str):
            source["updated_at"] = datetime.fromisoformat(source["updated_at"])
    
    return sources

@api_router.post("/payment-sources", response_model=PaymentSource)
async def create_payment_source(data: PaymentSourceCreate, current_user: User = Depends(get_current_user)):
    """Create a new payment source"""
    # Check if payment source with this name already exists
    existing = await db.payment_sources.find_one({"name": data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Payment source with this name already exists")
    
    source = PaymentSource(**data.dict())
    
    source_dict = source.dict()
    source_dict["created_at"] = source_dict["created_at"].isoformat()
    if source_dict.get("updated_at"):
        source_dict["updated_at"] = source_dict["updated_at"].isoformat()
    
    await db.payment_sources.insert_one(source_dict)
    
    return source

@api_router.put("/payment-sources/{source_id}", response_model=PaymentSource)
async def update_payment_source(
    source_id: str,
    data: PaymentSourceUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a payment source"""
    # Get existing source
    existing = await db.payment_sources.find_one({"id": source_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Payment source not found")
    
    # Update fields
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.payment_sources.update_one(
        {"id": source_id},
        {"$set": update_data}
    )
    
    # Get updated source
    updated = await db.payment_sources.find_one({"id": source_id}, {"_id": 0})
    
    # Parse datetime fields
    if isinstance(updated.get("created_at"), str):
        updated["created_at"] = datetime.fromisoformat(updated["created_at"])
    if isinstance(updated.get("updated_at"), str):
        updated["updated_at"] = datetime.fromisoformat(updated["updated_at"])
    
    return PaymentSource(**updated)

@api_router.delete("/payment-sources/{source_id}")
async def delete_payment_source(source_id: str, current_user: User = Depends(get_current_user)):
    """Delete a payment source (soft delete by setting is_active to False)"""
    result = await db.payment_sources.update_one(
        {"id": source_id},
        {"$set": {
            "is_active": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Payment source not found")
    
    return {"message": "Payment source deleted successfully"}


async def calculate_member_debt(member_id: str):
    """Calculate total debt for a member based on overdue/failed invoices"""
    # Get all overdue or failed invoices for the member
    invoices = await db.invoices.find({
        "member_id": member_id,
        "status": {"$in": ["overdue", "failed"]},
        "paid_date": None
    }, {"_id": 0}).to_list(100)
    
    # Calculate total debt
    total_debt = sum(invoice.get("amount", 0) for invoice in invoices)
    
    # Update member's debt amount and debtor status
    await db.members.update_one(
        {"id": member_id},
        {"$set": {
            "debt_amount": total_debt,
            "is_debtor": total_debt > 0
        }}
    )
    
    return total_debt



async def calculate_commission(member_id: str, consultant_id: str, membership_price: float, membership_type_name: str):
    """Calculate and create commission for a sale"""
    # Get consultant
    consultant = await db.consultants.find_one({"id": consultant_id}, {"_id": 0})
    if not consultant:
        return
    
    # Get applicable commission structures
    structures = await db.commission_structures.find({
        "status": "active",
        "$or": [
            {"applies_to": "all"},
            {"membership_type_id": membership_type_name}
        ]
    }, {"_id": 0}).to_list(100)
    
    if not structures:
        return
    
    # Use first applicable structure (can be enhanced for multiple)
    structure = structures[0]
    
    # Calculate commission amount
    commission_amount = 0.0
    if structure["commission_type"] == "fixed":
        commission_amount = structure["fixed_amount"]
    elif structure["commission_type"] == "percentage":
        commission_amount = membership_price * (structure["percentage"] / 100)
    elif structure["commission_type"] == "tiered":
        # Get consultant's month sales to determine tier
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_sales = await db.members.count_documents({
            "sales_consultant_id": consultant_id,
            "join_date": {"$gte": month_start.isoformat()}
        })
        
        # Find applicable tier
        for tier in structure["tiers"]:
            if tier["min_sales"] <= month_sales < tier.get("max_sales", float('inf')):
                commission_amount = membership_price * (tier["rate"] / 100)
                break
    
    # Get member info
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    
    # Create commission record
    commission = Commission(
        consultant_id=consultant_id,
        consultant_name=f"{consultant['first_name']} {consultant['last_name']}",
        member_id=member_id,
        member_name=f"{member['first_name']} {member['last_name']}",
        membership_type=membership_type_name,
        sale_amount=membership_price,
        commission_amount=commission_amount,
        commission_structure_id=structure["id"],
        commission_structure_name=structure["name"],
        commission_type=structure["commission_type"],
        sale_date=datetime.now(timezone.utc)
    )
    
    comm_doc = commission.model_dump()
    comm_doc["sale_date"] = comm_doc["sale_date"].isoformat()
    comm_doc["created_at"] = comm_doc["created_at"].isoformat()
    await db.commissions.insert_one(comm_doc)

# Consultant Routes
@api_router.post("/consultants", response_model=Consultant)
async def create_consultant(data: ConsultantCreate, current_user: User = Depends(get_current_user)):
    consultant = Consultant(**data.model_dump())
    doc = consultant.model_dump()
    doc["hire_date"] = doc["hire_date"].isoformat()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.consultants.insert_one(doc)
    return consultant

@api_router.get("/consultants", response_model=List[Consultant])
async def get_consultants(status: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"status": status} if status else {}
    consultants = await db.consultants.find(query, {"_id": 0}).to_list(1000)
    for c in consultants:
        if isinstance(c.get("hire_date"), str):
            c["hire_date"] = datetime.fromisoformat(c["hire_date"])
        if isinstance(c.get("created_at"), str):
            c["created_at"] = datetime.fromisoformat(c["created_at"])
    return consultants

# Commission Structure Routes
@api_router.post("/commission-structures", response_model=CommissionStructure)
async def create_commission_structure(data: CommissionStructureCreate, current_user: User = Depends(get_current_user)):
    structure = CommissionStructure(**data.model_dump())
    doc = structure.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.commission_structures.insert_one(doc)
    return structure

@api_router.get("/commission-structures", response_model=List[CommissionStructure])
async def get_commission_structures(current_user: User = Depends(get_current_user)):
    structures = await db.commission_structures.find({"status": "active"}, {"_id": 0}).to_list(1000)
    for s in structures:
        if isinstance(s.get("created_at"), str):
            s["created_at"] = datetime.fromisoformat(s["created_at"])
    return structures

# Commission Routes
@api_router.get("/commissions")
async def get_commissions(consultant_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"consultant_id": consultant_id} if consultant_id else {}
    commissions = await db.commissions.find(query, {"_id": 0}).sort("sale_date", -1).to_list(1000)
    for c in commissions:
        if isinstance(c.get("sale_date"), str):
            c["sale_date"] = datetime.fromisoformat(c["sale_date"])
        if isinstance(c.get("created_at"), str):
            c["created_at"] = datetime.fromisoformat(c["created_at"])
        if c.get("payment_date") and isinstance(c["payment_date"], str):
            c["payment_date"] = datetime.fromisoformat(c["payment_date"])
    return commissions

@api_router.get("/commissions/dashboard")
async def get_commission_dashboard(current_user: User = Depends(get_current_user)):
    """Get commission dashboard with performance metrics"""
    # Current month dates
    now = datetime.now(timezone.utc)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Previous month dates
    if now.month == 1:
        prev_month_start = current_month_start.replace(year=now.year - 1, month=12)
        prev_month_end = current_month_start
    else:
        prev_month_start = current_month_start.replace(month=now.month - 1)
        prev_month_end = current_month_start
    
    # Get all consultants
    consultants = await db.consultants.find({"status": "active"}, {"_id": 0}).to_list(1000)
    
    dashboard_data = []
    
    for consultant in consultants:
        consultant_id = consultant["id"]
        
        # Current month sales
        current_month_members = await db.members.find({
            "sales_consultant_id": consultant_id,
            "join_date": {"$gte": current_month_start.isoformat()}
        }, {"_id": 0}).to_list(1000)
        
        # Previous month sales
        prev_month_members = await db.members.find({
            "sales_consultant_id": consultant_id,
            "join_date": {
                "$gte": prev_month_start.isoformat(),
                "$lt": prev_month_end.isoformat()
            }
        }, {"_id": 0}).to_list(1000)
        
        # Calculate totals
        current_month_sales = len(current_month_members)
        prev_month_sales = len(prev_month_members)
        
        # Get membership prices for revenue calculation
        current_month_revenue = 0.0
        for member in current_month_members:
            membership = await db.membership_types.find_one({"id": member["membership_type_id"]}, {"_id": 0})
            if membership:
                current_month_revenue += membership["price"]
        
        prev_month_revenue = 0.0
        for member in prev_month_members:
            membership = await db.membership_types.find_one({"id": member["membership_type_id"]}, {"_id": 0})
            if membership:
                prev_month_revenue += membership["price"]
        
        # Get commissions
        current_month_commissions = await db.commissions.find({
            "consultant_id": consultant_id,
            "sale_date": {"$gte": current_month_start.isoformat()}
        }, {"_id": 0}).to_list(1000)
        
        current_month_commission_total = sum([c["commission_amount"] for c in current_month_commissions])
        
        # Calculate changes
        sales_change = current_month_sales - prev_month_sales
        sales_change_pct = (sales_change / prev_month_sales * 100) if prev_month_sales > 0 else 0
        
        revenue_change = current_month_revenue - prev_month_revenue
        revenue_change_pct = (revenue_change / prev_month_revenue * 100) if prev_month_revenue > 0 else 0
        
        dashboard_data.append({
            "consultant_id": consultant_id,
            "consultant_name": f"{consultant['first_name']} {consultant['last_name']}",
            "target_monthly_sales": consultant.get("target_monthly_sales", 0),
            "current_month": {
                "sales_count": current_month_sales,
                "revenue": current_month_revenue,
                "commission_total": current_month_commission_total,
                "avg_deal_size": current_month_revenue / current_month_sales if current_month_sales > 0 else 0
            },
            "previous_month": {
                "sales_count": prev_month_sales,
                "revenue": prev_month_revenue
            },
            "change": {
                "sales_count": sales_change,
                "sales_pct": sales_change_pct,
                "revenue": revenue_change,
                "revenue_pct": revenue_change_pct
            },
            "target_progress": (current_month_sales / consultant.get("target_monthly_sales", 1) * 100) if consultant.get("target_monthly_sales", 0) > 0 else 0
        })
    
    # Sort by current month sales
    dashboard_data.sort(key=lambda x: x["current_month"]["sales_count"], reverse=True)
    
    return {
        "consultants": dashboard_data,
        "period": {
            "current_month": current_month_start.strftime("%B %Y"),
            "previous_month": prev_month_start.strftime("%B %Y")
        }
    }

# Members Routes
@api_router.post("/members", response_model=Member)
async def create_member(data: MemberCreate, current_user: User = Depends(get_current_user)):
    # Check if membership type exists
    membership_type = await db.membership_types.find_one({"id": data.membership_type_id})
    if not membership_type:
        raise HTTPException(status_code=404, detail="Membership type not found")
    
    member_dict = data.model_dump()
    member = Member(**member_dict)
    
    # Calculate expiry date
    duration_months = membership_type["duration_months"]
    member.expiry_date = datetime.now(timezone.utc) + timedelta(days=30 * duration_months)
    
    # Generate QR code
    qr_data = f"MEMBER:{member.id}:{member.email}"
    member.qr_code = generate_qr_code(qr_data)
    
    # Geocode address if provided
    if member.address:
        lat, lon = geocode_address(member.address)
        member.latitude = lat
        member.longitude = lon
    
    # Set consultant name if consultant_id provided
    if member.sales_consultant_id:
        consultant = await db.consultants.find_one({"id": member.sales_consultant_id}, {"_id": 0})
        if consultant:
            member.sales_consultant_name = f"{consultant['first_name']} {consultant['last_name']}"
    
    doc = member.model_dump()
    doc["join_date"] = doc["join_date"].isoformat()
    if doc.get("expiry_date"):
        doc["expiry_date"] = doc["expiry_date"].isoformat()
    await db.members.insert_one(doc)
    
    # Create first invoice
    invoice = Invoice(
        member_id=member.id,
        invoice_number=f"INV-{member.id[:8]}-001",
        amount=membership_type["price"],
        description=f"Membership: {membership_type['name']}",
        due_date=datetime.now(timezone.utc) + timedelta(days=7)
    )
    invoice_doc = invoice.model_dump()
    invoice_doc["due_date"] = invoice_doc["due_date"].isoformat()
    invoice_doc["created_at"] = invoice_doc["created_at"].isoformat()
    await db.invoices.insert_one(invoice_doc)
    
    # Schedule levies if enabled
    if membership_type.get("levy_enabled", False):
        await schedule_member_levies(member, membership_type)
    
    # Calculate commission if consultant assigned
    if member.sales_consultant_id:
        await calculate_commission(
            member.id,
            member.sales_consultant_id,
            membership_type["price"],
            membership_type["name"]
        )
    
    # Trigger automation: member_joined
    await trigger_automation("member_joined", {
        "member_id": member.id,
        "member_name": f"{member.first_name} {member.last_name}",
        "email": member.email,
        "phone": member.phone,
        "membership_type": membership_type["name"],
        "join_date": member.join_date.isoformat()
    })
    
    return member

async def schedule_member_levies(member: Member, membership_type: dict):
    """Schedule levy payments for a member based on membership type configuration"""
    levy_frequency = membership_type.get("levy_frequency", "annual")
    levy_timing = membership_type.get("levy_timing", "anniversary")
    levy_amount_type = membership_type.get("levy_amount_type", "fixed")
    levy_amount = membership_type.get("levy_amount", 0.0)
    
    # Calculate levy amount
    if levy_amount_type == "same_as_membership":
        levy_amount = membership_type["price"]
    
    join_date = member.join_date
    current_year = datetime.now(timezone.utc).year
    
    if levy_timing == "anniversary":
        # Schedule on membership anniversary
        if levy_frequency == "annual":
            # Annual levy on anniversary
            levy_due = join_date.replace(year=current_year + 1)
        else:  # biannual
            # First levy after 6 months, then annually
            levy_due = join_date + timedelta(days=183)  # ~6 months
    else:  # fixed_dates (1 June and 1 December)
        # Determine next levy date
        now = datetime.now(timezone.utc)
        june_1 = datetime(now.year, 6, 1, tzinfo=timezone.utc)
        dec_1 = datetime(now.year, 12, 1, tzinfo=timezone.utc)
        
        if levy_frequency == "biannual":
            # Next due date is whichever comes next
            if now < june_1:
                levy_due = june_1
            elif now < dec_1:
                levy_due = dec_1
            else:
                levy_due = datetime(now.year + 1, 6, 1, tzinfo=timezone.utc)
        else:  # annual - use June 1
            if now < june_1:
                levy_due = june_1
            else:
                levy_due = datetime(now.year + 1, 6, 1, tzinfo=timezone.utc)
    
    # Create levy record
    levy = Levy(
        member_id=member.id,
        member_name=f"{member.first_name} {member.last_name}",
        levy_type=levy_frequency,
        amount=levy_amount,
        due_date=levy_due
    )
    
    levy_doc = levy.model_dump()
    levy_doc["due_date"] = levy_doc["due_date"].isoformat()
    levy_doc["created_at"] = levy_doc["created_at"].isoformat()
    await db.levies.insert_one(levy_doc)

@api_router.get("/members", response_model=List[Member])
async def get_members(current_user: User = Depends(get_current_user)):
    members = await db.members.find({}, {"_id": 0}).to_list(1000)
    for m in members:
        if isinstance(m.get("join_date"), str):
            m["join_date"] = datetime.fromisoformat(m["join_date"])
        if m.get("expiry_date") and isinstance(m["expiry_date"], str):
            m["expiry_date"] = datetime.fromisoformat(m["expiry_date"])
    return members

@api_router.get("/members/{member_id}", response_model=Member)
async def get_member(member_id: str):
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if isinstance(member.get("join_date"), str):
        member["join_date"] = datetime.fromisoformat(member["join_date"])
    if member.get("expiry_date") and isinstance(member["expiry_date"], str):
        member["expiry_date"] = datetime.fromisoformat(member["expiry_date"])
    return Member(**member)

@api_router.put("/members/{member_id}/block")
async def block_member(member_id: str, current_user: User = Depends(get_current_user)):
    result = await db.members.update_one(
        {"id": member_id},
        {"$set": {"is_debtor": True, "membership_status": "suspended"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Member blocked successfully"}

@api_router.put("/members/{member_id}/unblock")
async def unblock_member(member_id: str, current_user: User = Depends(get_current_user)):
    result = await db.members.update_one(
        {"id": member_id},
        {"$set": {"is_debtor": False, "membership_status": "active"}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Member unblocked successfully"}

# Access Control Routes
@api_router.post("/access/validate")
async def validate_access(data: AccessLogCreate):
    member = await db.members.find_one({"id": data.member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member_obj = Member(**member)
    
    # Check if member is blocked
    if member_obj.is_debtor or member_obj.membership_status != "active":
        if not data.override_by:
            access_log = AccessLog(
                member_id=member_obj.id,
                member_name=f"{member_obj.first_name} {member_obj.last_name}",
                access_method=data.access_method,
                status="denied",
                reason="Member is blocked or suspended"
            )
            log_doc = access_log.model_dump()
            log_doc["timestamp"] = log_doc["timestamp"].isoformat()
            await db.access_logs.insert_one(log_doc)
            return {"access": "denied", "reason": "Member is blocked or suspended", "member": member_obj}
    
    # Check expiry
    if member_obj.expiry_date and member_obj.expiry_date < datetime.now(timezone.utc):
        if not data.override_by:
            access_log = AccessLog(
                member_id=member_obj.id,
                member_name=f"{member_obj.first_name} {member_obj.last_name}",
                access_method=data.access_method,
                status="denied",
                reason="Membership expired"
            )
            log_doc = access_log.model_dump()
            log_doc["timestamp"] = log_doc["timestamp"].isoformat()
            await db.access_logs.insert_one(log_doc)
            return {"access": "denied", "reason": "Membership expired", "member": member_obj}
    
    # Grant access
    access_log = AccessLog(
        member_id=member_obj.id,
        member_name=f"{member_obj.first_name} {member_obj.last_name}",
        access_method=data.access_method,
        status="granted",
        reason=data.reason,
        override_by=data.override_by
    )
    log_doc = access_log.model_dump()
    log_doc["timestamp"] = log_doc["timestamp"].isoformat()
    await db.access_logs.insert_one(log_doc)
    
    return {"access": "granted", "member": member_obj}

@api_router.get("/access/logs", response_model=List[AccessLog])
async def get_access_logs(limit: int = 100, current_user: User = Depends(get_current_user)):
    logs = await db.access_logs.find({}, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    for log in logs:
        if isinstance(log.get("timestamp"), str):
            log["timestamp"] = datetime.fromisoformat(log["timestamp"])
    return logs

# Invoice Routes
@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(data: InvoiceCreate, current_user: User = Depends(get_current_user)):
    # Get invoice count for member
    count = await db.invoices.count_documents({"member_id": data.member_id})
    invoice_number = f"INV-{data.member_id[:8]}-{str(count + 1).zfill(3)}"
    
    invoice = Invoice(
        invoice_number=invoice_number,
        **data.model_dump()
    )
    doc = invoice.model_dump()
    doc["due_date"] = doc["due_date"].isoformat()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.invoices.insert_one(doc)
    return invoice

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(member_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"member_id": member_id} if member_id else {}
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    for inv in invoices:
        if isinstance(inv.get("due_date"), str):
            inv["due_date"] = datetime.fromisoformat(inv["due_date"])
        if isinstance(inv.get("created_at"), str):
            inv["created_at"] = datetime.fromisoformat(inv["created_at"])
        if inv.get("paid_date") and isinstance(inv["paid_date"], str):
            inv["paid_date"] = datetime.fromisoformat(inv["paid_date"])
    return invoices

# Payment Routes
@api_router.post("/payments", response_model=Payment)
async def create_payment(data: PaymentCreate, current_user: User = Depends(get_current_user)):
    # Check if invoice exists
    invoice = await db.invoices.find_one({"id": data.invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    payment = Payment(**data.model_dump())
    doc = payment.model_dump()
    doc["payment_date"] = doc["payment_date"].isoformat()
    await db.payments.insert_one(doc)
    
    # Update invoice status
    await db.invoices.update_one(
        {"id": data.invoice_id},
        {"$set": {
            "status": "paid",
            "paid_date": datetime.now(timezone.utc).isoformat(),
            "payment_method": data.payment_method
        }}
    )
    
    # Check if member should be unblocked and recalculate debt
    await calculate_member_debt(data.member_id)
    
    return payment

@api_router.get("/payments", response_model=List[Payment])
async def get_payments(member_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"member_id": member_id} if member_id else {}
    payments = await db.payments.find(query, {"_id": 0}).sort("payment_date", -1).to_list(1000)
    for pay in payments:
        if isinstance(pay.get("payment_date"), str):
            pay["payment_date"] = datetime.fromisoformat(pay["payment_date"])
    return payments

@api_router.post("/invoices/{invoice_id}/mark-failed")
async def mark_invoice_failed(
    invoice_id: str,
    failure_reason: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Mark an invoice payment as failed (e.g., debit order failed)"""
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update invoice status
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "status": "failed",
            "failure_reason": failure_reason,
            "failure_date": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Get member details for trigger
    member = await db.members.find_one({"id": invoice["member_id"]}, {"_id": 0})
    if member:
        # Calculate and update member debt
        await calculate_member_debt(member["id"])
        
        # Trigger automation: payment_failed
        await trigger_automation("payment_failed", {
            "member_id": member["id"],
            "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
            "email": member.get("email", ""),
            "phone": member.get("phone", ""),
            "invoice_id": invoice_id,
            "invoice_number": invoice["invoice_number"],
            "amount": invoice["amount"],
            "failure_reason": failure_reason or "Payment failed"
        })
    
    return {"message": "Invoice marked as failed, debt calculated, and automations triggered"}

@api_router.post("/invoices/{invoice_id}/mark-overdue")
async def mark_invoice_overdue(invoice_id: str, current_user: User = Depends(get_current_user)):
    """Mark an invoice as overdue"""
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update invoice status
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {"status": "overdue"}}
    )
    
    # Get member details for trigger
    member = await db.members.find_one({"id": invoice["member_id"]}, {"_id": 0})
    if member:
        # Calculate and update member debt
        await calculate_member_debt(member["id"])
        
        # Trigger automation: invoice_overdue
        await trigger_automation("invoice_overdue", {
            "member_id": member["id"],
            "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
            "email": member.get("email", ""),
            "phone": member.get("phone", ""),
            "invoice_id": invoice_id,
            "invoice_number": invoice["invoice_number"],
            "amount": invoice["amount"],
            "due_date": invoice.get("due_date", "")
        })
    
    return {"message": "Invoice marked as overdue, debt calculated, and automations triggered"}


# Member Analytics and Geo-location
@api_router.get("/analytics/member-distribution")
async def get_member_distribution(current_user: User = Depends(get_current_user)):
    """Get member distribution with geo-location for marketing analytics"""
    members = await db.members.find({}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, 
                                          "address": 1, "latitude": 1, "longitude": 1, 
                                          "membership_status": 1}).to_list(10000)
    
    # Filter members with valid geo-location
    geo_members = [m for m in members if m.get("latitude") and m.get("longitude")]
    
    return {
        "total_members": len(members),
        "geo_located_members": len(geo_members),
        "members": geo_members
    }


@api_router.get("/payment-report")
async def get_payment_report(
    member_id: Optional[str] = None,
    status: Optional[str] = None,
    payment_gateway: Optional[str] = None,
    source: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive payment report with member details, invoices, and analytics
    Supports filtering by member, status, payment gateway, source, and date range
    """
    # Build query for invoices
    invoice_query = {}
    if member_id:
        invoice_query["member_id"] = member_id
    if status:
        invoice_query["status"] = status
    if payment_gateway:
        invoice_query["payment_gateway"] = payment_gateway
    if start_date:
        invoice_query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in invoice_query:
            invoice_query["created_at"]["$lte"] = end_date
        else:
            invoice_query["created_at"] = {"$lte": end_date}
    
    # Get invoices
    invoices = await db.invoices.find(invoice_query, {"_id": 0}).sort("created_at", -1).to_list(10000)
    
    # Get all unique member IDs
    member_ids = list(set(inv["member_id"] for inv in invoices))
    
    # Get member details
    members_query = {"id": {"$in": member_ids}}
    if source:
        members_query["source"] = source
    
    members = await db.members.find(members_query, {"_id": 0}).to_list(10000)
    members_dict = {m["id"]: m for m in members}
    
    # Get membership types
    membership_types = await db.membership_types.find({}, {"_id": 0}).to_list(1000)
    membership_dict = {mt["id"]: mt for mt in membership_types}
    
    # Build comprehensive report
    report_data = []
    for invoice in invoices:
        member = members_dict.get(invoice["member_id"])
        if not member:
            continue
        
        membership_type = membership_dict.get(member.get("membership_type_id"))
        
        # Parse dates
        due_date = invoice.get("due_date")
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)
        
        paid_date = invoice.get("paid_date")
        if paid_date and isinstance(paid_date, str):
            paid_date = datetime.fromisoformat(paid_date)
        
        join_date = member.get("join_date")
        if isinstance(join_date, str):
            join_date = datetime.fromisoformat(join_date)
        
        expiry_date = member.get("expiry_date")
        if expiry_date and isinstance(expiry_date, str):
            expiry_date = datetime.fromisoformat(expiry_date)
        
        contract_start = member.get("contract_start_date")
        if contract_start and isinstance(contract_start, str):
            contract_start = datetime.fromisoformat(contract_start)
        
        contract_end = member.get("contract_end_date")
        if contract_end and isinstance(contract_end, str):
            contract_end = datetime.fromisoformat(contract_end)
        
        report_item = {
            # Member info
            "member_id": member["id"],
            "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
            "membership_number": member["id"][:8].upper(),  # First 8 chars as membership number
            "email": member.get("email"),
            "phone": member.get("phone"),
            "membership_status": member.get("membership_status"),
            
            # Membership details
            "membership_type": membership_type.get("name") if membership_type else "Unknown",
            "membership_type_id": member.get("membership_type_id"),
            
            # Financial info
            "invoice_id": invoice["id"],
            "invoice_number": invoice.get("invoice_number"),
            "amount": invoice.get("amount"),
            "status": invoice.get("status"),
            "payment_method": invoice.get("payment_method"),
            "payment_gateway": invoice.get("payment_gateway"),
            "status_message": invoice.get("status_message"),
            "debt": member.get("debt_amount", 0),
            "is_debtor": member.get("is_debtor", False),
            
            # Dates
            "due_date": due_date.isoformat() if due_date else None,
            "paid_date": paid_date.isoformat() if paid_date else None,
            "start_date": join_date.isoformat() if join_date else None,
            "end_renewal_date": expiry_date.isoformat() if expiry_date else None,
            "contract_start_date": contract_start.isoformat() if contract_start else None,
            "contract_end_date": contract_end.isoformat() if contract_end else None,
            
            # Source and referral
            "source": member.get("source"),
            "referred_by": member.get("referred_by"),
            
            # Sales consultant
            "sales_consultant_id": member.get("sales_consultant_id"),
            "sales_consultant_name": member.get("sales_consultant_name"),
        }
        
        report_data.append(report_item)
    
    return {
        "total_records": len(report_data),
        "data": report_data
    }


@api_router.get("/analytics/payment-duration")
async def get_payment_duration_analytics(current_user: User = Depends(get_current_user)):
    """
    Get payment duration analytics showing average membership payment duration
    by global, club, region, and membership type
    """
    # Get all paid payments with member details
    payments = await db.payments.find({"payment_method": {"$exists": True}}, {"_id": 0}).to_list(10000)
    
    # Get all members
    members = await db.members.find({}, {"_id": 0}).to_list(10000)
    members_dict = {m["id"]: m for m in members}
    
    # Get all membership types
    membership_types = await db.membership_types.find({}, {"_id": 0}).to_list(1000)
    membership_dict = {mt["id"]: mt for mt in membership_types}
    
    # Calculate payment duration for each member
    member_payment_data = {}
    
    for payment in payments:
        member_id = payment.get("member_id")
        if not member_id or member_id not in members_dict:
            continue
        
        member = members_dict[member_id]
        
        # Calculate duration in months from join date to latest payment
        join_date = member.get("join_date")
        payment_date = payment.get("payment_date")
        
        if join_date and payment_date:
            if isinstance(join_date, str):
                join_date = datetime.fromisoformat(join_date)
            if isinstance(payment_date, str):
                payment_date = datetime.fromisoformat(payment_date)
            
            # Calculate months difference
            months_diff = (payment_date.year - join_date.year) * 12 + (payment_date.month - join_date.month)
            
            if member_id not in member_payment_data:
                member_payment_data[member_id] = {
                    "member": member,
                    "total_months": months_diff,
                    "payment_count": 1,
                    "total_amount": payment.get("amount", 0)
                }
            else:
                # Update with longest duration
                if months_diff > member_payment_data[member_id]["total_months"]:
                    member_payment_data[member_id]["total_months"] = months_diff
                member_payment_data[member_id]["payment_count"] += 1
                member_payment_data[member_id]["total_amount"] += payment.get("amount", 0)
    
    # Calculate global average
    if member_payment_data:
        total_months = sum(data["total_months"] for data in member_payment_data.values())
        global_avg = total_months / len(member_payment_data)
    else:
        global_avg = 0
    
    # Calculate by membership type
    type_stats = {}
    for member_id, data in member_payment_data.items():
        member = data["member"]
        type_id = member.get("membership_type_id")
        
        if type_id:
            if type_id not in type_stats:
                type_name = membership_dict.get(type_id, {}).get("name", "Unknown")
                type_stats[type_id] = {
                    "type_name": type_name,
                    "total_months": 0,
                    "member_count": 0,
                    "total_revenue": 0
                }
            
            type_stats[type_id]["total_months"] += data["total_months"]
            type_stats[type_id]["member_count"] += 1
            type_stats[type_id]["total_revenue"] += data["total_amount"]
    
    # Calculate averages for each type
    for type_id, stats in type_stats.items():
        if stats["member_count"] > 0:
            stats["avg_months"] = round(stats["total_months"] / stats["member_count"], 2)
            stats["avg_revenue_per_member"] = round(stats["total_revenue"] / stats["member_count"], 2)
    
    # Calculate by source
    source_stats = {}
    for member_id, data in member_payment_data.items():
        member = data["member"]
        source = member.get("source") or "Unknown"
        
        if source not in source_stats:
            source_stats[source] = {
                "source_name": source,
                "total_months": 0,
                "member_count": 0,
                "total_revenue": 0
            }
        
        source_stats[source]["total_months"] += data["total_months"]
        source_stats[source]["member_count"] += 1
        source_stats[source]["total_revenue"] += data["total_amount"]
    
    # Calculate averages for each source
    for source, stats in source_stats.items():
        if stats["member_count"] > 0:
            stats["avg_months"] = round(stats["total_months"] / stats["member_count"], 2)
            stats["avg_revenue_per_member"] = round(stats["total_revenue"] / stats["member_count"], 2)
    
    # Get top performing metrics
    top_members = sorted(
        [{"member_name": f"{data['member'].get('first_name', '')} {data['member'].get('last_name', '')}".strip(),
          "months": data["total_months"],
          "total_paid": data["total_amount"]}
         for data in member_payment_data.values()],
        key=lambda x: x["months"],
        reverse=True
    )[:10]
    
    # Calculate retention rate (members paying for 6+ months)
    long_term_members = sum(1 for data in member_payment_data.values() if data["total_months"] >= 6)
    retention_rate = round((long_term_members / len(member_payment_data) * 100), 2) if member_payment_data else 0
    
    return {
        "global_stats": {
            "average_payment_months": round(global_avg, 2),
            "total_paying_members": len(member_payment_data),
            "total_revenue": sum(data["total_amount"] for data in member_payment_data.values()),
            "retention_rate_6months": retention_rate
        },
        "by_membership_type": list(type_stats.values()),
        "by_source": list(source_stats.values()),
        "top_members": top_members,
        "summary": {
            "longest_paying_member_months": max((data["total_months"] for data in member_payment_data.values()), default=0),
            "shortest_paying_member_months": min((data["total_months"] for data in member_payment_data.values()), default=0),
            "median_payment_months": round(sorted([data["total_months"] for data in member_payment_data.values()])[len(member_payment_data)//2], 2) if member_payment_data else 0
        }
    }



@api_router.post("/members/{member_id}/geocode")
async def geocode_member_address(member_id: str, current_user: User = Depends(get_current_user)):
    """Manually trigger geocoding for a member's address"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if not member.get("address"):
        raise HTTPException(status_code=400, detail="Member has no address")
    
    lat, lon = geocode_address(member["address"])
    if lat and lon:
        await db.members.update_one(
            {"id": member_id},
            {"$set": {"latitude": lat, "longitude": lon}}
        )
        return {"message": "Geocoding successful", "latitude": lat, "longitude": lon}
    else:
        raise HTTPException(status_code=400, detail="Could not geocode address")

# Dashboard Stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    total_members = await db.members.count_documents({})
    active_members = await db.members.count_documents({"membership_status": "active"})
    blocked_members = await db.members.count_documents({"is_debtor": True})
    
    pending_invoices = await db.invoices.count_documents({"status": "pending"})
    overdue_invoices = await db.invoices.count_documents({"status": "overdue"})
    
    # Total revenue (paid invoices)
    paid_invoices = await db.invoices.find({"status": "paid"}, {"_id": 0, "amount": 1}).to_list(10000)
    total_revenue = sum([inv.get("amount", 0) for inv in paid_invoices])
    
    # Today's access count
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_access = await db.access_logs.count_documents({
        "timestamp": {"$gte": today_start.isoformat()}
    })
    
    return {
        "total_members": total_members,
        "active_members": active_members,
        "blocked_members": blocked_members,
        "pending_invoices": pending_invoices,
        "overdue_invoices": overdue_invoices,
        "total_revenue": total_revenue,
        "today_access_count": today_access
    }

# Levy Routes
@api_router.get("/levies", response_model=List[Levy])
async def get_levies(status: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"status": status} if status else {}
    levies = await db.levies.find(query, {"_id": 0}).sort("due_date", 1).to_list(1000)
    
    for levy in levies:
        if isinstance(levy.get("due_date"), str):
            levy["due_date"] = datetime.fromisoformat(levy["due_date"])
        if isinstance(levy.get("created_at"), str):
            levy["created_at"] = datetime.fromisoformat(levy["created_at"])
        if levy.get("paid_date") and isinstance(levy["paid_date"], str):
            levy["paid_date"] = datetime.fromisoformat(levy["paid_date"])
    
    return levies

@api_router.post("/levies/{levy_id}/generate-invoice")
async def generate_levy_invoice(levy_id: str, current_user: User = Depends(get_current_user)):
    """Generate a separate invoice for a levy payment"""
    levy = await db.levies.find_one({"id": levy_id})
    if not levy:
        raise HTTPException(status_code=404, detail="Levy not found")
    
    if levy["status"] == "paid":
        raise HTTPException(status_code=400, detail="Levy already paid")
    
    # Get invoice count for member
    count = await db.invoices.count_documents({"member_id": levy["member_id"]})
    invoice_number = f"LEV-{levy['member_id'][:8]}-{str(count + 1).zfill(3)}"
    
    invoice = Invoice(
        member_id=levy["member_id"],
        invoice_number=invoice_number,
        amount=levy["amount"],
        description=f"{levy['levy_type'].capitalize()} Levy - Separate Billing",
        due_date=datetime.fromisoformat(levy["due_date"]) if isinstance(levy["due_date"], str) else levy["due_date"]
    )
    
    invoice_doc = invoice.model_dump()
    invoice_doc["due_date"] = invoice_doc["due_date"].isoformat()
    invoice_doc["created_at"] = invoice_doc["created_at"].isoformat()
    await db.invoices.insert_one(invoice_doc)
    
    # Update levy with invoice ID
    await db.levies.update_one(
        {"id": levy_id},
        {"$set": {"invoice_id": invoice.id}}
    )
    
    return {"message": "Levy invoice generated", "invoice_id": invoice.id}

@api_router.post("/levies/{levy_id}/mark-paid")
async def mark_levy_paid(levy_id: str, current_user: User = Depends(get_current_user)):
    """Mark a levy as paid (called after payment is processed)"""
    result = await db.levies.update_one(
        {"id": levy_id},
        {"$set": {
            "status": "paid",
            "paid_date": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Levy not found")
    
    return {"message": "Levy marked as paid"}

@api_router.get("/levies/member/{member_id}", response_model=List[Levy])
async def get_member_levies(member_id: str, current_user: User = Depends(get_current_user)):
    """Get all levies for a specific member"""
    levies = await db.levies.find({"member_id": member_id}, {"_id": 0}).sort("due_date", 1).to_list(100)
    
    for levy in levies:
        if isinstance(levy.get("due_date"), str):
            levy["due_date"] = datetime.fromisoformat(levy["due_date"])
        if isinstance(levy.get("created_at"), str):
            levy["created_at"] = datetime.fromisoformat(levy["created_at"])
        if levy.get("paid_date") and isinstance(levy["paid_date"], str):
            levy["paid_date"] = datetime.fromisoformat(levy["paid_date"])
    
    return levies

# Cancellation Request Routes
@api_router.post("/cancellations", response_model=CancellationRequest)
async def create_cancellation_request(data: CancellationRequestCreate, current_user: User = Depends(get_current_user)):
    # Get member details
    member = await db.members.find_one({"id": data.member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get membership type
    membership_type = await db.membership_types.find_one({"id": member["membership_type_id"]}, {"_id": 0})
    
    cancellation = CancellationRequest(
        member_id=data.member_id,
        member_name=f"{member['first_name']} {member['last_name']}",
        membership_type=membership_type["name"] if membership_type else "Unknown",
        reason=data.reason,
        requested_by=current_user.email,
        request_source=data.request_source
    )
    
    doc = cancellation.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.cancellation_requests.insert_one(doc)
    
    return cancellation

@api_router.get("/cancellations", response_model=List[CancellationRequest])
async def get_cancellation_requests(status: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"status": status} if status else {}
    requests = await db.cancellation_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    for req in requests:
        if isinstance(req.get("created_at"), str):
            req["created_at"] = datetime.fromisoformat(req["created_at"])
        if req.get("completed_at") and isinstance(req["completed_at"], str):
            req["completed_at"] = datetime.fromisoformat(req["completed_at"])
    
    return requests

@api_router.post("/cancellations/approve-staff")
async def approve_cancellation_staff(data: ApprovalAction, current_user: User = Depends(get_current_user)):
    """Staff level approval - first level"""
    request = await db.cancellation_requests.find_one({"id": data.request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Cancellation request not found")
    
    if data.action == "reject":
        await db.cancellation_requests.update_one(
            {"id": data.request_id},
            {"$set": {
                "status": "rejected",
                "rejection_reason": data.rejection_reason,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {"message": "Request rejected"}
    
    # Approve at staff level
    approval_data = {
        "approved_by": current_user.email,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "comments": data.comments
    }
    
    await db.cancellation_requests.update_one(
        {"id": data.request_id},
        {"$set": {
            "status": "staff_approved",
            "staff_approval": approval_data
        }}
    )
    
    return {"message": "Staff approval completed. Awaiting manager approval."}

@api_router.post("/cancellations/approve-manager")
async def approve_cancellation_manager(data: ApprovalAction, current_user: User = Depends(get_current_user)):
    """Manager level approval - second level"""
    request = await db.cancellation_requests.find_one({"id": data.request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Cancellation request not found")
    
    if request["status"] != "staff_approved":
        raise HTTPException(status_code=400, detail="Request must be staff approved first")
    
    if data.action == "reject":
        await db.cancellation_requests.update_one(
            {"id": data.request_id},
            {"$set": {
                "status": "rejected",
                "rejection_reason": data.rejection_reason,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {"message": "Request rejected by manager"}
    
    approval_data = {
        "approved_by": current_user.email,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "comments": data.comments
    }
    
    await db.cancellation_requests.update_one(
        {"id": data.request_id},
        {"$set": {
            "status": "manager_approved",
            "manager_approval": approval_data
        }}
    )
    
    return {"message": "Manager approval completed. Awaiting admin approval."}

@api_router.post("/cancellations/approve-admin")
async def approve_cancellation_admin(data: ApprovalAction, current_user: User = Depends(get_current_user)):
    """Admin level approval - final level"""
    request = await db.cancellation_requests.find_one({"id": data.request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Cancellation request not found")
    
    if request["status"] != "manager_approved":
        raise HTTPException(status_code=400, detail="Request must be manager approved first")
    
    if data.action == "reject":
        await db.cancellation_requests.update_one(
            {"id": data.request_id},
            {"$set": {
                "status": "rejected",
                "rejection_reason": data.rejection_reason,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {"message": "Request rejected by admin"}
    
    approval_data = {
        "approved_by": current_user.email,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "comments": data.comments
    }
    
    # Final approval - cancel the membership
    await db.cancellation_requests.update_one(
        {"id": data.request_id},
        {"$set": {
            "status": "completed",
            "admin_approval": approval_data,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Update member status
    await db.members.update_one(
        {"id": request["member_id"]},
        {"$set": {"membership_status": "cancelled"}}
    )
    
    return {"message": "Cancellation approved and completed. Member status updated."}

# ============= AUTOMATION & TRIGGERS ENDPOINTS =============

@api_router.get("/automations")
async def get_automations(current_user: User = Depends(get_current_user)):
    """Get all automation rules"""
    automations = await db.automations.find({}, {"_id": 0}).to_list(length=None)
    return automations

@api_router.get("/automations/{automation_id}")
async def get_automation(automation_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific automation rule"""
    automation = await db.automations.find_one({"id": automation_id}, {"_id": 0})
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    return automation

@api_router.post("/automations")
async def create_automation(automation: AutomationCreate, current_user: User = Depends(get_current_user)):
    """Create a new automation rule"""
    new_automation = Automation(
        **automation.dict(),
        created_by=current_user.email
    )
    
    automation_dict = new_automation.dict()
    automation_dict["created_at"] = automation_dict["created_at"].isoformat()
    if automation_dict.get("last_triggered"):
        automation_dict["last_triggered"] = automation_dict["last_triggered"].isoformat()
    
    await db.automations.insert_one(automation_dict)
    return new_automation

@api_router.put("/automations/{automation_id}")
async def update_automation(
    automation_id: str,
    automation_data: AutomationCreate,
    current_user: User = Depends(get_current_user)
):
    """Update an automation rule"""
    existing = await db.automations.find_one({"id": automation_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    update_data = automation_data.dict()
    await db.automations.update_one(
        {"id": automation_id},
        {"$set": update_data}
    )
    
    updated = await db.automations.find_one({"id": automation_id}, {"_id": 0})
    return updated

@api_router.delete("/automations/{automation_id}")
async def delete_automation(automation_id: str, current_user: User = Depends(get_current_user)):
    """Delete an automation rule"""
    result = await db.automations.delete_one({"id": automation_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Automation not found")
    return {"message": "Automation deleted successfully"}

@api_router.post("/automations/{automation_id}/toggle")
async def toggle_automation(automation_id: str, current_user: User = Depends(get_current_user)):
    """Enable/disable an automation rule"""
    automation = await db.automations.find_one({"id": automation_id})
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    new_status = not automation.get("enabled", True)
    await db.automations.update_one(
        {"id": automation_id},
        {"$set": {"enabled": new_status}}
    )
    
    return {"message": f"Automation {'enabled' if new_status else 'disabled'}", "enabled": new_status}

@api_router.get("/automation-executions")
async def get_automation_executions(
    limit: int = 50,
    automation_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get automation execution history"""
    query = {}
    if automation_id:
        query["automation_id"] = automation_id
    
    executions = await db.automation_executions.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(length=None)
    return executions

@api_router.post("/automations/test/{automation_id}")
async def test_automation(
    automation_id: str,
    test_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Test an automation rule with sample data"""
    automation = await db.automations.find_one({"id": automation_id})
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    
    # Execute the automation with test data
    try:
        result = await execute_automation(automation, test_data, is_test=True)
        return {
            "success": True,
            "message": "Test execution completed",
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Test execution failed: {str(e)}",
            "error": str(e)
        }

# ============= AUTOMATION TRIGGER EXECUTION LOGIC =============

async def execute_automation(automation: dict, trigger_data: dict, is_test: bool = False):
    """Execute an automation rule"""
    try:
        # Check conditions
        if automation.get("conditions"):
            conditions_met = check_automation_conditions(automation["conditions"], trigger_data)
            if not conditions_met:
                return {"skipped": True, "reason": "Conditions not met"}
        
        results = []
        
        # Execute each action
        for action in automation.get("actions", []):
            action_type = action.get("type")
            delay_minutes = action.get("delay_minutes", 0)
            
            # Calculate scheduled time
            scheduled_for = datetime.now(timezone.utc)
            if delay_minutes > 0:
                from datetime import timedelta
                scheduled_for = scheduled_for + timedelta(minutes=delay_minutes)
            
            # Create execution record
            execution = AutomationExecution(
                automation_id=automation["id"],
                automation_name=automation["name"],
                trigger_data=trigger_data,
                scheduled_for=scheduled_for,
                status="pending" if delay_minutes > 0 else "completed",
                executed_at=datetime.now(timezone.utc) if delay_minutes == 0 else None
            )
            
            execution_dict = execution.dict()
            execution_dict["created_at"] = execution_dict["created_at"].isoformat()
            execution_dict["scheduled_for"] = execution_dict["scheduled_for"].isoformat()
            if execution_dict.get("executed_at"):
                execution_dict["executed_at"] = execution_dict["executed_at"].isoformat()
            
            # If no delay and not test, execute immediately
            if delay_minutes == 0 and not is_test:
                action_result = await execute_action(action, trigger_data)
                execution_dict["result"] = action_result
                execution_dict["status"] = "completed"
            
            if not is_test:
                await db.automation_executions.insert_one(execution_dict)
            
            results.append({
                "action_type": action_type,
                "scheduled_for": execution_dict["scheduled_for"],
                "status": execution_dict["status"]
            })
        
        # Update automation stats
        if not is_test:
            await db.automations.update_one(
                {"id": automation["id"]},
                {
                    "$set": {"last_triggered": datetime.now(timezone.utc).isoformat()},
                    "$inc": {"execution_count": 1}
                }
            )
        
        return {
            "executed": True,
            "actions_executed": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error executing automation {automation.get('id')}: {str(e)}")
        return {
            "executed": False,
            "error": str(e)
        }

def check_automation_conditions(conditions: dict, trigger_data: dict) -> bool:
    """Check if automation conditions are met"""
    # Simple condition checking - can be extended
    for key, expected_value in conditions.items():
        actual_value = trigger_data.get(key)
        
        # Handle different condition types
        if isinstance(expected_value, dict):
            # Complex conditions like {"operator": ">=", "value": 100}
            operator = expected_value.get("operator", "==")
            value = expected_value.get("value")
            
            if operator == "==":
                if actual_value != value:
                    return False
            elif operator == ">":
                if not (actual_value and actual_value > value):
                    return False
            elif operator == ">=":
                if not (actual_value and actual_value >= value):
                    return False
            elif operator == "<":
                if not (actual_value and actual_value < value):
                    return False
            elif operator == "<=":
                if not (actual_value and actual_value <= value):
                    return False
            elif operator == "contains":
                if not (actual_value and value in str(actual_value)):
                    return False
        else:
            # Simple equality check
            if actual_value != expected_value:
                return False
    
    return True

async def execute_action(action: dict, trigger_data: dict):
    """Execute a specific automation action"""
    action_type = action.get("type")
    
    if action_type == "send_sms":
        # SMS action - placeholder for now
        phone = trigger_data.get("phone") or action.get("phone")
        message = action.get("message", "").format(**trigger_data)
        # TODO: Integrate SMS service (Twilio, etc.)
        logger.info(f"SMS Action (Mock): Sending to {phone}: {message}")
        return {"type": "sms", "status": "sent_mock", "phone": phone, "message": message}
    
    elif action_type == "send_whatsapp":
        # WhatsApp action via respond.io
        phone = trigger_data.get("phone") or action.get("phone")
        message = action.get("message", "").format(**trigger_data)
        
        # Get member details for contact creation
        first_name = trigger_data.get("member_name", "Member")
        if " " in first_name:
            parts = first_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1]
        else:
            last_name = None
        
        email = trigger_data.get("email")
        
        try:
            # Determine template name based on trigger type
            template_name = action.get("template_name")
            if not template_name:
                # Auto-select template based on trigger type
                trigger_type = trigger_data.get("trigger_type", "")
                template_map = {
                    "payment_failed": "payment_failed_alert",
                    "member_joined": "member_welcome",
                    "invoice_overdue": "invoice_overdue_reminder",
                    "membership_expiring": "membership_renewal_reminder"
                }
                template_name = template_map.get(trigger_type, "general_notification")
            
            # Extract template parameters from trigger_data
            # The message will be formatted by the template itself
            template_params = []
            if "{member_name}" in message or "member_name" in trigger_data:
                template_params.append(trigger_data.get("member_name", ""))
            if "{amount}" in message or "amount" in trigger_data:
                template_params.append(str(trigger_data.get("amount", "")))
            if "{invoice_number}" in message or "invoice_number" in trigger_data:
                template_params.append(trigger_data.get("invoice_number", ""))
            if "{due_date}" in message or "due_date" in trigger_data:
                template_params.append(trigger_data.get("due_date", ""))
            
            # Send via respond.io
            result = await respondio_service.send_whatsapp_message(
                contact_phone=phone,
                template_name=template_name,
                template_params=template_params,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            
            return {
                "type": "whatsapp",
                "status": "sent" if not respondio_service.is_mocked else "sent_mock",
                "phone": phone,
                "message": message,
                "message_id": result.get("messageId"),
                "template_name": template_name
            }
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {str(e)}")
            return {
                "type": "whatsapp",
                "status": "failed",
                "phone": phone,
                "error": str(e)
            }
    
    elif action_type == "send_email":
        # Email action - placeholder for now
        email = trigger_data.get("email") or action.get("email")
        subject = action.get("subject", "").format(**trigger_data)
        body = action.get("body", "").format(**trigger_data)
        # TODO: Integrate email service (SendGrid, AWS SES, etc.)
        logger.info(f"Email Action (Mock): Sending to {email}: {subject}")
        return {"type": "email", "status": "sent_mock", "email": email, "subject": subject}
    
    elif action_type == "update_member_status":
        # Update member status
        member_id = trigger_data.get("member_id")
        new_status = action.get("status")
        if member_id and new_status:
            await db.members.update_one(
                {"id": member_id},
                {"$set": {"membership_status": new_status}}
            )
            return {"type": "update_status", "status": "completed", "member_id": member_id}
    
    elif action_type == "create_task":
        # Create a follow-up task
        task_data = {
            "id": str(uuid.uuid4()),
            "title": action.get("task_title", "Follow-up required"),
            "description": action.get("task_description", "").format(**trigger_data),
            "assigned_to": action.get("assigned_to"),
            "due_date": action.get("due_date"),
            "related_member_id": trigger_data.get("member_id"),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.tasks.insert_one(task_data)
        return {"type": "create_task", "status": "completed", "task_id": task_data["id"]}
    
    else:
        logger.warning(f"Unknown action type: {action_type}")
        return {"type": action_type, "status": "unknown_action"}

# ============= TRIGGER HELPERS =============

async def trigger_automation(trigger_type: str, trigger_data: dict):
    """Trigger all enabled automations for a specific event type (excludes test_mode automations)"""
    automations = await db.automations.find({
        "trigger_type": trigger_type,
        "enabled": True,
        "test_mode": {"$ne": True}  # Exclude automations in test mode
    }).to_list(length=None)
    
    results = []
    for automation in automations:
        result = await execute_automation(automation, trigger_data)
        results.append({
            "automation_id": automation["id"],
            "automation_name": automation["name"],
            "result": result
        })
    
    return results




# ============= RESPOND.IO WHATSAPP INTEGRATION ENDPOINTS =============

@api_router.get("/whatsapp/status")
async def get_whatsapp_status(current_user: User = Depends(get_current_user)):
    """Get WhatsApp integration status"""
    return {
        "integrated": not respondio_service.is_mocked,
        "is_mocked": respondio_service.is_mocked,
        "api_key_configured": bool(respondio_service.api_key),
        "channel_id_configured": bool(respondio_service.channel_id),
        "base_url": respondio_service.base_url,
        "message": "WhatsApp integration is active via respond.io" if not respondio_service.is_mocked 
                   else "WhatsApp integration is in MOCK mode (set RESPOND_IO_API_KEY in .env to activate)"
    }

@api_router.get("/whatsapp/templates")
async def list_whatsapp_templates(current_user: User = Depends(get_current_user)):
    """List available WhatsApp message templates"""
    try:
        templates = await respondio_service.list_message_templates()
        return {
            "templates": templates,
            "count": len(templates),
            "is_mocked": respondio_service.is_mocked
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {str(e)}")

@api_router.post("/whatsapp/test-message")
async def send_test_whatsapp_message(
    phone: str,
    template_name: str = "payment_failed_alert",
    member_name: str = "Test Member",
    current_user: User = Depends(get_current_user)
):
    """Send a test WhatsApp message"""
    try:
        # Format the test parameters
        template_params = [member_name, "500.00", "INV-TEST-001", "2024-12-31"]
        
        result = await respondio_service.send_whatsapp_message(
            contact_phone=phone,
            template_name=template_name,
            template_params=template_params,
            first_name=member_name.split()[0] if " " in member_name else member_name,
            last_name=member_name.split()[1] if " " in member_name and len(member_name.split()) > 1 else None,
            email="test@example.com"
        )
        
        return {
            "success": True,
            "message": "Test message sent successfully" if not respondio_service.is_mocked 
                      else "Test message logged (MOCK mode)",
            "result": result,
            "formatted_phone": respondio_service.format_phone_number(phone)
        }
    except Exception as e:
        logger.error(f"Test message failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send test message: {str(e)}")

@api_router.post("/whatsapp/format-phone")
async def format_phone_number_endpoint(phone: str):
    """Test phone number formatting (no auth required for testing)"""
    try:
        formatted = respondio_service.format_phone_number(phone)
        return {
            "original": phone,
            "formatted": formatted,
            "valid": len(formatted.replace("+", "")) == 11
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid phone number: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()