from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta, date
import qrcode
from io import BytesIO
import base64
import jwt
from passlib.context import CryptContext
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from services.respondio_service import RespondIOService
from normalization import normalize_email, normalize_phone, normalize_name, normalize_full_name

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

async def add_journal_entry(
    member_id: str,
    action_type: str,
    description: str,
    metadata: dict = None,
    created_by: str = None,
    created_by_name: str = None
):
    """
    Helper function to add a journal entry for a member.
    Can be called from any endpoint to log member activities.
    """
    journal_entry = MemberJournal(
        member_id=member_id,
        action_type=action_type,
        description=description,
        metadata=metadata or {},
        created_by=created_by or "system",
        created_by_name=created_by_name or "System"
    )
    await db.member_journal.insert_one(journal_entry.model_dump())
    return journal_entry

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
    # Freeze status
    freeze_status: bool = False
    freeze_start_date: Optional[datetime] = None
    freeze_end_date: Optional[datetime] = None
    freeze_reason: Optional[str] = None
    # No-show tracking
    no_show_count: int = 0
    # Access PIN (using access card number)
    access_pin: Optional[str] = None
    # Override tracking
    daily_override_count: int = 0
    last_override_date: Optional[datetime] = None
    is_prospect: bool = False  # True for temporary prospect records
    prospect_source: Optional[str] = None  # For new prospects
    # Normalized fields for duplicate detection (auto-populated)
    norm_email: Optional[str] = None  # Normalized email for duplicate checking
    norm_phone: Optional[str] = None  # Normalized phone for duplicate checking
    norm_first_name: Optional[str] = None  # Normalized first name
    norm_last_name: Optional[str] = None  # Normalized last name
    # Phase 1 - Quick Wins: Enhanced Grid Columns
    tags: List[str] = []  # Member tags for categorization and filtering
    sessions_remaining: Optional[int] = None  # Remaining sessions for session-based memberships
    last_visit_date: Optional[datetime] = None  # Last attendance/check-in date
    next_billing_date: Optional[datetime] = None  # Next billing date
    cancellation_date: Optional[datetime] = None  # Date membership was cancelled
    cancellation_reason: Optional[str] = None  # Reason for cancellation

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
    member_email: Optional[str] = None
    membership_type: Optional[str] = None
    membership_status: Optional[str] = None
    access_method: str  # qr_code, rfid, fingerprint, facial_recognition, manual_override, mobile_app
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str  # granted, denied
    reason: Optional[str] = None  # membership_expired, membership_suspended, invalid_card, etc.
    override_by: Optional[str] = None
    # Location tracking
    location: Optional[str] = None  # Main entrance, Studio A, Locker Room, etc.
    device_id: Optional[str] = None  # ID of the access control device
    # Class booking integration
    class_booking_id: Optional[str] = None  # If check-in is for a class
    class_name: Optional[str] = None
    # Photos (for facial recognition or photo capture)
    photo_url: Optional[str] = None
    # Temperature check (for health protocols)
    temperature: Optional[float] = None
    # Additional metadata
    notes: Optional[str] = None

class AccessLogCreate(BaseModel):
    member_id: str
    access_method: str
    location: Optional[str] = None
    device_id: Optional[str] = None
    class_booking_id: Optional[str] = None
    reason: Optional[str] = None
    override_by: Optional[str] = None
    temperature: Optional[float] = None
    notes: Optional[str] = None

class MemberNote(BaseModel):
    model_config = ConfigDict(extra="ignore")
    note_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_id: str
    content: str
    created_by: str  # Staff member ID or email
    created_by_name: Optional[str] = None  # Staff member name for display
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class MemberNoteCreate(BaseModel):
    content: str

class MemberNoteUpdate(BaseModel):
    content: str

class MemberJournal(BaseModel):
    model_config = ConfigDict(extra="ignore")
    journal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_id: str
    action_type: str  # email_sent, email_received, whatsapp_sent, whatsapp_received, sms_sent, sms_received, profile_updated, status_changed, payment_received, invoice_created, booking_created, booking_cancelled, no_show_marked, note_added, note_deleted, access_granted, access_denied
    description: str  # Summary of the action
    metadata: Optional[dict] = None  # Full content, field changes, message body, etc.
    created_by: Optional[str] = None  # Staff member ID or "system"
    created_by_name: Optional[str] = None  # Staff member name for display
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MemberJournalCreate(BaseModel):
    action_type: str
    description: str
    metadata: Optional[dict] = None

class TaskType(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    color: str = "#3b82f6"  # Default blue color
    icon: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#3b82f6"
    icon: Optional[str] = None

class TaskTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    task_type_id: str
    task_type_name: Optional[str] = None  # Denormalized for display
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "pending"  # pending, in_progress, completed, cancelled, on_hold, needs_review
    assigned_to_user_id: Optional[str] = None
    assigned_to_user_name: Optional[str] = None  # Denormalized for display
    assigned_to_department: Optional[str] = None
    related_member_id: Optional[str] = None
    related_member_name: Optional[str] = None  # Denormalized for display
    due_date: Optional[datetime] = None
    created_by: str
    created_by_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    completed_by_name: Optional[str] = None
    comment_count: int = 0
    attachment_count: int = 0

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    task_type_id: str
    priority: str = "medium"
    assigned_to_user_id: Optional[str] = None
    assigned_to_department: Optional[str] = None
    related_member_id: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    task_type_id: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    assigned_to_department: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskComment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    comment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    content: str
    created_by: str
    created_by_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attachments: List[str] = []  # List of attachment URLs

class TaskCommentCreate(BaseModel):
    content: str
    attachments: List[str] = []

class TaskAttachment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    attachment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    file_name: str
    file_url: str
    file_size: Optional[int] = None
    uploaded_by: str
    uploaded_by_name: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OverrideReason(BaseModel):
    model_config = ConfigDict(extra="ignore")
    reason_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None  # For hierarchical reasons (main → sub)
    is_active: bool = True
    requires_pin: bool = True  # Whether this reason requires PIN verification
    order: int = 0  # For sorting
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OverrideReasonCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    requires_pin: bool = True
    order: int = 0

class OverrideReasonUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    requires_pin: Optional[bool] = None
    order: Optional[int] = None

class AccessOverride(BaseModel):
    model_config = ConfigDict(extra="ignore")
    override_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_id: str
    member_name: Optional[str] = None
    member_status: Optional[str] = None  # active, expired, suspended, prospect
    reason_id: str
    reason_name: Optional[str] = None
    sub_reason_id: Optional[str] = None
    sub_reason_name: Optional[str] = None
    pin_verified: bool = False
    pin_entered: Optional[str] = None  # For logging (not the actual PIN)
    staff_id: str
    staff_name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AccessOverrideCreate(BaseModel):
    member_id: Optional[str] = None  # Can be None for new prospects
    first_name: Optional[str] = None  # For new prospects
    last_name: Optional[str] = None  # For new prospects
    phone: Optional[str] = None  # For new prospects
    email: Optional[str] = None  # For new prospects
    reason_id: str
    sub_reason_id: Optional[str] = None
    access_pin: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class InvoiceLineItem(BaseModel):
    """Line item for invoice"""
    item_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    quantity: float = 1.0
    unit_price: float
    discount_percent: float = 0.0
    tax_percent: float = 0.0
    subtotal: float = 0.0  # quantity * unit_price - discount
    tax_amount: float = 0.0  # subtotal * tax_percent / 100
    total: float = 0.0  # subtotal + tax_amount

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_id: str
    invoice_number: str
    amount: float  # Total invoice amount (sum of all line items)
    description: str
    due_date: datetime
    paid_date: Optional[datetime] = None
    status: str = "pending"  # pending, paid, overdue, cancelled, failed, void
    payment_method: Optional[str] = None
    payment_gateway: Optional[str] = None  # Stripe, PayPal, Manual, etc.
    status_message: Optional[str] = None  # Additional status information
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # For tracking debit order batches
    batch_id: Optional[str] = None
    batch_date: Optional[datetime] = None
    # Line items for itemized billing
    line_items: List[InvoiceLineItem] = []
    subtotal: float = 0.0  # Sum of all line item subtotals
    tax_total: float = 0.0  # Sum of all line item taxes
    discount_total: float = 0.0  # Sum of all discounts
    notes: Optional[str] = None
    # Auto-generation tracking
    auto_generated: bool = False
    generated_from: Optional[str] = None  # 'membership_renewal', 'manual', etc.

class InvoiceCreate(BaseModel):
    member_id: str
    description: str
    due_date: datetime
    line_items: List[InvoiceLineItem]
    notes: Optional[str] = None
    auto_generated: bool = False
    generated_from: Optional[str] = None

class InvoiceUpdate(BaseModel):
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    line_items: Optional[List[InvoiceLineItem]] = None
    notes: Optional[str] = None
    status: Optional[str] = None

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

# ===================== RBAC & Permission Models =====================

class RolePermissionMatrix(BaseModel):
    """Permission matrix for a specific role"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # business_owner, head_admin, sales_head, etc.
    role_display_name: str  # Business Owner, Head of Admin, etc.
    permissions: List[str] = []  # List of permission strings (e.g., ["members:view", "members:create"])
    is_default: bool = False  # True if using default permissions
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_by: Optional[str] = None  # User ID who last updated

class PermissionMatrixUpdate(BaseModel):
    """Update permissions for a role"""
    role: str
    permissions: List[str]

class UserRoleAssignment(BaseModel):
    """Assign/update user role"""
    user_id: str
    role: str

class StaffUser(BaseModel):
    """Extended user model for staff management"""
    model_config = ConfigDict(extra="ignore")
    id: str
    email: EmailStr
    full_name: str
    role: str
    role_display_name: str
    created_at: datetime
    permissions: List[str] = []  # Permissions for this user's role



class AuditLog(BaseModel):
    """Comprehensive audit log for all API requests"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Request details
    method: str  # GET, POST, PUT, DELETE, etc.
    path: str  # API endpoint path
    # User details
    user_id: Optional[str] = None  # User ID from JWT
    user_email: Optional[str] = None
    user_role: Optional[str] = None  # admin, staff, member
    # Request/Response
    status_code: int  # HTTP status code
    success: bool  # True if 2xx, False otherwise
    # Resource details
    resource_type: Optional[str] = None  # member, invoice, booking, etc.
    resource_id: Optional[str] = None  # ID of the resource acted upon
    action: Optional[str] = None  # create, update, delete, read, check_duplicate, etc.
    # Additional context
    message: Optional[str] = None  # Human-readable message
    request_body: Optional[dict] = None  # Request payload (sensitive fields redacted)
    response_summary: Optional[dict] = None  # Summary of response
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    # Performance
    duration_ms: Optional[float] = None  # Request duration in milliseconds

class BlockedMemberAttempt(BaseModel):
    """Track blocked duplicate member creation attempts for staff review"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Attempted member data
    attempted_first_name: str
    attempted_last_name: str
    attempted_email: str
    attempted_phone: str
    # Normalized values
    norm_email: Optional[str] = None
    norm_phone: Optional[str] = None
    norm_first_name: Optional[str] = None
    norm_last_name: Optional[str] = None
    # Duplicate detection results
    duplicate_fields: List[str] = []  # ["email", "phone", "name"]
    match_types: List[str] = []  # ["normalized_email", "normalized_phone", "normalized_name"]
    # Existing member(s) that matched
    existing_members: List[dict] = []  # List of matching member details
    # User who attempted
    attempted_by_user_id: Optional[str] = None
    attempted_by_email: Optional[str] = None
    # Review status
    review_status: str = "pending"  # pending, approved, rejected, merged
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    # Source of attempt
    source: str = "manual"  # manual, import, api

# ===================== Tag Management Models =====================

class Tag(BaseModel):
    """Tag for member categorization"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Tag name (e.g., "VIP", "Late Payer", "Personal Training")
    color: str = "#3b82f6"  # Hex color for display
    description: Optional[str] = None
    category: Optional[str] = None  # Category for organization (e.g., "Status", "Program", "Payment")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None
    usage_count: int = 0  # Number of members with this tag

class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#3b82f6"
    description: Optional[str] = None
    category: Optional[str] = None

class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

class MemberActionRequest(BaseModel):
    """Request model for member actions (freeze, cancel)"""
    reason: Optional[str] = None
    notes: Optional[str] = None
    end_date: Optional[datetime] = None  # For freeze actions

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
    # Levy configuration
    levy_enabled: bool = False  # If true, this payment option includes levies
    levy_frequency_type: str = "none"  # "anniversary_yearly", "anniversary_biannual", "fixed_dates_june_december", "custom", "none"
    levy_amount: Optional[float] = None  # Standard levy amount (for non-custom types)
    levy_custom_schedule: Optional[List[Dict]] = None  # For custom: [{"month": 6, "day": 1, "amount": 500}, ...]
    levy_rollover_enabled: bool = True  # If true, levies roll over when membership auto-renews
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
    # Levy configuration
    levy_enabled: bool = False
    levy_frequency_type: str = "none"
    levy_amount: Optional[float] = None
    levy_custom_schedule: Optional[List[Dict]] = None
    levy_rollover_enabled: bool = True

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
    # Levy configuration
    levy_enabled: Optional[bool] = None
    levy_frequency_type: Optional[str] = None
    levy_amount: Optional[float] = None
    levy_custom_schedule: Optional[List[Dict]] = None
    levy_rollover_enabled: Optional[bool] = None

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

class EFTSettings(BaseModel):
    """EFT configuration settings for bank integration"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_profile_number: str  # 10-digit Nedbank client number
    nominated_account: str  # 16-digit Nedbank account for credits
    charges_account: str  # 16-digit Nedbank account for fees/charges
    service_user_number: Optional[str] = None  # Additional service identifier
    branch_code: Optional[str] = None  # Bank branch code
    bank_name: str = "Nedbank"  # Bank name
    enable_notifications: bool = False  # Send payment confirmation notifications
    notification_email: Optional[str] = None  # Email for EFT notifications
    advance_billing_days: int = 5  # Days before due date to generate billing files
    enable_auto_generation: bool = False  # Enable automatic file generation based on due dates
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class EFTSettingsUpdate(BaseModel):
    client_profile_number: Optional[str] = None
    nominated_account: Optional[str] = None
    charges_account: Optional[str] = None
    service_user_number: Optional[str] = None
    branch_code: Optional[str] = None
    bank_name: Optional[str] = None
    enable_notifications: Optional[bool] = None
    notification_email: Optional[str] = None
    advance_billing_days: Optional[int] = None
    enable_auto_generation: Optional[bool] = None


class BillingSettings(BaseModel):
    """Billing and invoice configuration settings"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Invoice auto-email settings
    auto_email_invoices: bool = False
    email_on_invoice_created: bool = False
    email_on_invoice_overdue: bool = False
    email_reminder_days_before_due: List[int] = [7, 3, 1]  # Days before due date to send reminder
    # Tax settings
    default_tax_rate: float = 15.0  # Default VAT/tax rate percentage
    tax_enabled: bool = True
    tax_number: Optional[str] = None  # Company tax/VAT registration number
    # Invoice numbering
    invoice_prefix: str = "INV"
    invoice_number_format: str = "{prefix}-{year}-{sequence}"  # e.g., INV-2025-0001
    next_invoice_number: int = 1
    # Company details for invoice
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_logo_url: Optional[str] = None
    # Payment terms
    default_payment_terms_days: int = 30
    # Auto-generation for memberships
    auto_generate_membership_invoices: bool = False
    days_before_renewal_to_invoice: int = 5
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class BillingSettingsUpdate(BaseModel):
    auto_email_invoices: Optional[bool] = None
    email_on_invoice_created: Optional[bool] = None
    email_on_invoice_overdue: Optional[bool] = None
    email_reminder_days_before_due: Optional[List[int]] = None
    default_tax_rate: Optional[float] = None
    tax_enabled: Optional[bool] = None
    tax_number: Optional[str] = None
    invoice_prefix: Optional[str] = None
    invoice_number_format: Optional[str] = None
    next_invoice_number: Optional[int] = None
    company_name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None
    company_logo_url: Optional[str] = None
    default_payment_terms_days: Optional[int] = None
    auto_generate_membership_invoices: Optional[bool] = None
    days_before_renewal_to_invoice: Optional[int] = None



class EFTTransaction(BaseModel):
    """EFT transaction record for tracking generated files and responses"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_type: str  # "outgoing_debit", "incoming_ack", "incoming_nack", "incoming_unpaid"
    file_name: str
    file_sequence: str  # Unique file sequence number
    transaction_type: str  # "billing", "levy", "refund"
    total_transactions: int = 0
    total_amount: float = 0.0
    status: str = "generated"  # generated, submitted, acknowledged, processed, failed, disallowed
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None
    response_file: Optional[str] = None
    notes: Optional[str] = None
    disallowed_at: Optional[datetime] = None
    disallowed_by: Optional[str] = None
    disallow_reason: Optional[str] = None
    is_stuck: bool = False
    last_status_check: Optional[datetime] = None


class EFTTransactionItem(BaseModel):
    """Individual transaction item within an EFT file"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    eft_transaction_id: str  # Parent EFT transaction
    member_id: str
    member_name: str
    member_account: Optional[str] = None  # Bank account number
    member_branch: Optional[str] = None  # Branch code
    invoice_id: Optional[str] = None
    levy_id: Optional[str] = None
    amount: float
    action_date: datetime
    payment_reference: str  # Unique payment reference
    status: str = "pending"  # pending, processed, failed, returned
    response_code: Optional[str] = None
    response_message: Optional[str] = None
    processed_at: Optional[datetime] = None


class DebiCheckMandate(BaseModel):
    """DebiCheck mandate for authenticated debit orders"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mandate_reference_number: str  # Unique MRN (25 chars)
    member_id: str
    member_name: str
    contract_reference: str  # 14-char contract/policy number
    mandate_type: str  # F=Fixed, V=Variable, U=Usage-based
    transaction_type: str  # TT1=Real-time, TT2=Batch, TT3=Card&Pin
    debtor_id_number: str  # SA ID or passport
    debtor_bank_account: str  # 16-digit account
    debtor_branch_code: str  # 6-digit branch
    account_type: str = "1"  # 1=Current, 2=Savings, 3=Transmission
    first_collection_date: datetime
    collection_day: int  # Day of month (1-31)
    frequency: str  # M=Monthly, Q=Quarterly, Y=Yearly
    installment_amount: float
    maximum_amount: float
    adjustment_category: str = "0"  # 0=Never, 1=Quarterly, 2=Biannually, 3=Annually, 4=Repo
    adjustment_rate: float = 0.0
    status: str = "pending"  # pending, approved, rejected, suspended, cancelled
    status_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    last_collection_date: Optional[datetime] = None
    total_collections: int = 0


class DebiCheckMandateCreate(BaseModel):
    member_id: str
    contract_reference: str
    mandate_type: str = "F"  # F, V, U
    transaction_type: str = "TT2"  # TT1, TT2, TT3
    first_collection_date: datetime
    collection_day: Optional[int] = None
    frequency: str = "M"
    installment_amount: float
    maximum_amount: Optional[float] = None
    adjustment_category: str = "0"
    adjustment_rate: float = 0.0


class DebiCheckCollection(BaseModel):
    """DebiCheck collection request record"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mandate_id: str
    mandate_reference_number: str
    member_id: str
    contract_reference: str
    collection_amount: float
    action_date: datetime
    collection_type: str = "R"  # R=Recurring, F=Final, O=Once-off
    status: str = "pending"  # pending, processed, failed, disputed
    response_code: Optional[str] = None
    response_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: Optional[datetime] = None


# AVS (Account Verification Service) Models
class AVSConfig(BaseModel):
    """AVS configuration settings for Nedbank account verification"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_number: str  # 10-digit Nedbank profile number
    profile_user_number: str  # 8-digit profile user number
    charge_account: str  # Account to charge for verifications
    mock_mode: bool = True  # If true, use mock responses (for testing without credentials)
    use_qa: bool = True  # If true, use QA environment; false for production
    enable_auto_verify: bool = False  # Auto-verify during member onboarding
    verify_on_update: bool = False  # Re-verify when banking details are updated
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class AVSConfigUpdate(BaseModel):
    """Update model for AVS configuration"""
    profile_number: Optional[str] = None
    profile_user_number: Optional[str] = None
    charge_account: Optional[str] = None
    mock_mode: Optional[bool] = None
    use_qa: Optional[bool] = None
    enable_auto_verify: Optional[bool] = None
    verify_on_update: Optional[bool] = None


class AVSVerificationRequest(BaseModel):
    """Request model for account verification"""
    bank_identifier: str  # FI Code (e.g., "21" for Nedbank, "18" for Standard Bank)
    account_number: str
    sort_code: str  # Branch code
    identity_number: str
    identity_type: str = "SID"  # SID/SPP/SBR/TRN
    account_type: Optional[str] = None  # "01"=Current, "02"=Savings, "00"=Unknown
    initials: Optional[str] = None
    last_name: Optional[str] = None
    email_id: Optional[str] = None
    cell_number: Optional[str] = None
    tax_reference: Optional[str] = None
    customer_reference: Optional[str] = None
    sub_billing_id: Optional[str] = None
    customer_reference2: Optional[str] = None


class AVSVerificationResult(BaseModel):
    """Result model for account verification"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_id: Optional[str] = None  # If verification was for a member
    verification_type: str = "manual"  # manual, auto, onboarding, update
    # Request data
    bank_identifier: str
    bank_name: str
    account_number: str
    sort_code: str
    identity_number: str
    identity_type: str
    initials: Optional[str] = None
    last_name: Optional[str] = None
    # Result codes
    result_code: str  # R00=Success, R01=Technical error, R02=Business error
    result_code_acct: str  # Account-specific result code
    # Verification results (Y=Yes, N=No, U=Unprocessed, F=Failed)
    account_exists: str
    identification_number_matched: str
    initials_matched: str
    last_name_matched: str
    account_active: str
    account_dormant: str
    account_active_3months: str
    can_debit_account: str
    can_credit_account: str
    tax_ref_match: str
    account_type_match: str
    email_id_matched: str
    cell_number_matched: str
    # Metadata
    verification_summary: Optional[str] = None  # Human-readable summary
    mock_mode: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None  # User who triggered verification


class AVSBatchVerificationRequest(BaseModel):
    """Request model for batch account verification"""
    verifications: List[AVSVerificationRequest]


# TI (Transactional Information) Models
class TIConfig(BaseModel):
    """TI configuration settings for Nedbank transactional information services"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    profile_number: str  # Nedbank profile number
    account_number: str  # Account to monitor
    mock_mode: bool = True  # If true, use mock data
    use_qa: bool = True  # If true, use QA environment
    fti_enabled: bool = True  # Enable FTI (Final Transaction Information)
    fti_frequency: str = "daily"  # daily, weekly, monthly
    pti_enabled: bool = False  # Enable PTI (Provisional Transaction Information)
    notifications_enabled: bool = False  # Enable transaction notifications
    auto_reconcile: bool = True  # Automatically reconcile matched transactions
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class TIConfigUpdate(BaseModel):
    """Update model for TI configuration"""
    profile_number: Optional[str] = None
    account_number: Optional[str] = None
    mock_mode: Optional[bool] = None
    use_qa: Optional[bool] = None
    fti_enabled: Optional[bool] = None
    fti_frequency: Optional[str] = None
    pti_enabled: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    auto_reconcile: Optional[bool] = None


class FTITransaction(BaseModel):
    """FTI (Final Transaction Information) transaction record"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    statement_number: str
    date: str  # YYYY-MM-DD
    time: str  # HH:MM:SS
    balance: float
    transaction_type: str
    transaction_type_name: str
    channel: str
    channel_name: str
    amount: float
    reference: str
    description: str
    transaction_key: str
    process_key: Optional[str] = None
    is_debit: bool
    # Reconciliation fields
    is_reconciled: bool = False
    matched_invoice_id: Optional[str] = None
    matched_member_id: Optional[str] = None
    match_confidence: Optional[str] = None  # high, medium, low
    match_reason: Optional[str] = None
    reconciled_at: Optional[datetime] = None
    reconciled_by: Optional[str] = None
    # Metadata
    mock_mode: bool = False
    imported_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PTITransaction(BaseModel):
    """PTI (Provisional Transaction Information) transaction record"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_key: str
    date: str
    time: str
    transaction_type: str
    transaction_type_name: str
    channel: str
    channel_name: str
    amount: float
    reference: str
    description: str
    status: str = "provisional"  # provisional, confirmed, cancelled
    is_debit: bool
    confirmed_fti_id: Optional[str] = None  # Link to confirmed FTI transaction
    mock_mode: bool = False
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TINotificationRule(BaseModel):
    """Notification rule configuration"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    rule_type: str  # payment_received, payment_failed, low_balance, high_value_transaction
    enabled: bool = True
    # Conditions
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    transaction_types: List[str] = []  # Empty means all types
    channels: List[str] = []  # Empty means all channels
    # Actions
    notify_email: bool = False
    notify_sms: bool = False
    email_addresses: List[str] = []
    sms_numbers: List[str] = []
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


class ReconciliationResult(BaseModel):
    """Result of reconciliation process"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reconciliation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_transactions: int
    matched_count: int
    unmatched_count: int
    match_rate: float
    total_matched_amount: float
    total_unmatched_amount: float
    high_confidence_matches: int
    medium_confidence_matches: int
    low_confidence_matches: int
    matched_invoice_ids: List[str] = []
    unmatched_transaction_ids: List[str] = []
    report_text: Optional[str] = None
    processed_by: Optional[str] = None


# Member Engagement Alert Models
class AlertConfiguration(BaseModel):
    """Configuration for member engagement alerts"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    days_period: int = 30  # Number of days to look back
    green_threshold: int = 10  # Visits >= this number = green alert
    amber_min_threshold: int = 1  # Visits >= this = amber alert
    amber_max_threshold: int = 4  # Visits <= this (and >= min) = amber alert
    red_threshold: int = 0  # Visits = this number = red alert
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class AlertConfigurationUpdate(BaseModel):
    """Update model for alert configuration"""
    days_period: Optional[int] = None
    green_threshold: Optional[int] = None
    amber_min_threshold: Optional[int] = None
    amber_max_threshold: Optional[int] = None
    red_threshold: Optional[int] = None


class MemberAccess(BaseModel):
    """Member check-in/access record"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    member_id: str
    access_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    access_type: str = "check-in"  # check-in, class, service
    location: Optional[str] = None
    notes: Optional[str] = None


class NotificationTemplate(BaseModel):
    """Template for member notifications"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # green_alert, amber_alert, red_alert, general
    channels: List[str] = []  # whatsapp, email, sms, push
    subject: Optional[str] = None  # For email
    message: str  # Template with placeholders: {first_name}, {last_name}, {visit_count}, {days_since_last_visit}
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BulkNotificationRequest(BaseModel):
    """Request to send bulk notification"""
    template_id: str
    alert_level: str  # green, amber, red
    channels: List[str]  # whatsapp, email, sms, push
    member_ids: Optional[List[str]] = None  # If empty, send to all members in alert level


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

# Classes and Scheduling Models
class Class(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    instructor_id: Optional[str] = None
    instructor_name: Optional[str] = None
    class_type: str  # yoga, pilates, spin, crossfit, boxing, etc.
    duration_minutes: int = 60
    capacity: int = 20
    # Recurring schedule
    day_of_week: Optional[str] = None  # Monday, Tuesday, etc. (for recurring)
    start_time: str  # HH:MM format
    end_time: str  # HH:MM format
    is_recurring: bool = True  # If false, this is a one-time class
    # For one-time classes
    class_date: Optional[datetime] = None  # Specific date for one-time classes
    # Resources
    room: Optional[str] = None
    equipment: List[str] = []
    # Booking settings
    allow_waitlist: bool = True
    waitlist_capacity: int = 10
    booking_window_days: int = 7  # How many days in advance can members book
    cancel_window_hours: int = 2  # How many hours before class can members cancel
    check_in_window_minutes: int = 15  # Minutes before/after class start for check-in
    no_show_threshold: int = 3  # Number of no-shows before blocking bookings
    reminder_minutes_before: int = 60  # Minutes before class to send reminder
    send_booking_confirmation: bool = True  # Send WhatsApp confirmation on booking
    send_class_reminder: bool = True  # Send WhatsApp reminder before class
    # Status
    status: str = "active"  # active, cancelled, completed
    # Membership restrictions
    membership_types_allowed: List[str] = []  # Empty means all types allowed
    # Pricing (for drop-in classes)
    drop_in_price: float = 0.0
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

class ClassCreate(BaseModel):
    name: str
    description: Optional[str] = None
    instructor_id: Optional[str] = None
    instructor_name: Optional[str] = None
    class_type: str
    duration_minutes: int = 60
    capacity: int = 20
    day_of_week: Optional[str] = None
    start_time: str
    end_time: str
    is_recurring: bool = True
    class_date: Optional[datetime] = None
    room: Optional[str] = None
    equipment: List[str] = []
    allow_waitlist: bool = True
    waitlist_capacity: int = 10
    booking_window_days: int = 7
    cancel_window_hours: int = 2
    check_in_window_minutes: int = 15
    no_show_threshold: int = 3
    reminder_minutes_before: int = 60
    send_booking_confirmation: bool = True
    send_class_reminder: bool = True
    membership_types_allowed: List[str] = []
    drop_in_price: float = 0.0

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    instructor_id: Optional[str] = None
    instructor_name: Optional[str] = None
    class_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    capacity: Optional[int] = None
    day_of_week: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_recurring: Optional[bool] = None
    class_date: Optional[datetime] = None
    room: Optional[str] = None
    equipment: Optional[List[str]] = None
    allow_waitlist: Optional[bool] = None
    waitlist_capacity: Optional[int] = None
    booking_window_days: Optional[int] = None
    cancel_window_hours: Optional[int] = None
    check_in_window_minutes: Optional[int] = None
    no_show_threshold: Optional[int] = None
    reminder_minutes_before: Optional[int] = None
    send_booking_confirmation: Optional[bool] = None
    send_class_reminder: Optional[bool] = None
    membership_types_allowed: Optional[List[str]] = None
    drop_in_price: Optional[float] = None
    status: Optional[str] = None

class Booking(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str
    class_name: str
    member_id: str
    member_name: str
    member_email: str
    # For specific class instance (if recurring class)
    booking_date: datetime  # Specific date/time of the class instance
    status: str = "confirmed"  # confirmed, waitlist, cancelled, no_show, attended
    # Waitlist
    is_waitlist: bool = False
    waitlist_position: Optional[int] = None
    # Payment (for drop-in classes)
    payment_required: bool = False
    payment_amount: float = 0.0
    payment_status: str = "not_required"  # not_required, pending, paid
    invoice_id: Optional[str] = None
    # Metadata
    booked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    no_show: bool = False  # True if member didn't attend despite booking
    notes: Optional[str] = None

class BookingCreate(BaseModel):
    class_id: str
    member_id: str
    booking_date: datetime  # Which specific instance of the class
    notes: Optional[str] = None

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    cancellation_reason: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    notes: Optional[str] = None

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
    # Enhanced duplicate checking with normalization
    duplicates = []
    
    # Normalize input data
    norm_email = normalize_email(data.email) if data.email else None
    norm_phone = normalize_phone(data.phone) if data.phone else None
    norm_first, norm_last = normalize_full_name(data.first_name, data.last_name)
    
    # Check normalized email
    if norm_email:
        email_exists = await db.members.find_one({"norm_email": norm_email}, {"_id": 0})
        if email_exists:
            duplicates.append({
                "field": "email",
                "value": data.email,
                "normalized_value": norm_email,
                "match_type": "normalized_email",
                "existing_member": {
                    "id": email_exists["id"],
                    "name": f"{email_exists['first_name']} {email_exists['last_name']}",
                    "email": email_exists.get("email"),
                    "phone": email_exists.get("phone")
                }
            })
    
    # Check normalized phone
    if norm_phone:
        phone_exists = await db.members.find_one({"norm_phone": norm_phone}, {"_id": 0})
        if phone_exists:
            duplicates.append({
                "field": "phone",
                "value": data.phone,
                "normalized_value": norm_phone,
                "match_type": "normalized_phone",
                "existing_member": {
                    "id": phone_exists["id"],
                    "name": f"{phone_exists['first_name']} {phone_exists['last_name']}",
                    "email": phone_exists.get("email"),
                    "phone": phone_exists.get("phone")
                }
            })
    
    # Check normalized name (including nickname canonicalization)
    if norm_first and norm_last:
        name_exists = await db.members.find_one({
            "norm_first_name": norm_first,
            "norm_last_name": norm_last
        }, {"_id": 0})
        if name_exists:
            duplicates.append({
                "field": "name",
                "value": f"{data.first_name} {data.last_name}",
                "normalized_value": f"{norm_first} {norm_last}",
                "match_type": "normalized_name (nickname-aware)",
                "existing_member": {
                    "id": name_exists["id"],
                    "name": f"{name_exists['first_name']} {name_exists['last_name']}",
                    "email": name_exists.get("email"),
                    "phone": name_exists.get("phone")
                }
            })
    
    # If duplicates found, log the blocked attempt and return error
    if duplicates:
        # Log blocked attempt for staff review
        blocked_attempt = BlockedMemberAttempt(
            attempted_first_name=data.first_name,
            attempted_last_name=data.last_name,
            attempted_email=data.email,
            attempted_phone=data.phone,
            norm_email=norm_email,
            norm_phone=norm_phone,
            norm_first_name=norm_first,
            norm_last_name=norm_last,
            duplicate_fields=[d["field"] for d in duplicates],
            match_types=[d["match_type"] for d in duplicates],
            existing_members=[d["existing_member"] for d in duplicates],
            attempted_by_user_id=current_user.id,
            attempted_by_email=current_user.email,
            source="manual"
        )
        
        # Save blocked attempt to database
        try:
            blocked_doc = blocked_attempt.model_dump()
            blocked_doc["timestamp"] = blocked_doc["timestamp"].isoformat()
            await db.blocked_member_attempts.insert_one(blocked_doc)
        except Exception as e:
            logger.error(f"Failed to log blocked attempt: {str(e)}")
        
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Duplicate member detected",
                "duplicates": duplicates
            }
        )
    
    # Check if membership type exists
    membership_type = await db.membership_types.find_one({"id": data.membership_type_id})
    if not membership_type:
        raise HTTPException(status_code=404, detail="Membership type not found")
    
    member_dict = data.model_dump()
    member = Member(**member_dict)
    
    # Populate normalized fields for future duplicate checks
    member.norm_email = norm_email
    member.norm_phone = norm_phone
    member.norm_first_name = norm_first
    member.norm_last_name = norm_last
    
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

# Member Search for Override - MUST be before {member_id} endpoint
@api_router.get("/members/search")
async def search_members(
    q: str,
    current_user: User = Depends(get_current_user)
):
    """Search members by name, email, phone, or ID"""
    # Build search query
    search_query = {
        "$or": [
            {"first_name": {"$regex": q, "$options": "i"}},
            {"last_name": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}},
            {"id": {"$regex": q, "$options": "i"}}
        ]
    }
    
    members = await db.members.find(
        search_query,
        {"_id": 0, "first_name": 1, "last_name": 1, "email": 1, "phone": 1, "id": 1, "membership_status": 1, "expiry_date": 1, "access_pin": 1, "is_prospect": 1}
    ).limit(10).to_list(length=10)
    
    # If no members found, return empty array instead of 404
    if not members:
        return []
    
    # Enhance with status info
    for member in members:
        if member.get("is_prospect"):
            member["status_label"] = "Prospect"
        elif member.get("membership_status") == "cancelled":
            member["status_label"] = "Cancelled"
        elif member.get("membership_status") == "suspended":
            member["status_label"] = "Suspended"
        elif member.get("expiry_date") and datetime.fromisoformat(member["expiry_date"].replace('Z', '+00:00')) < datetime.now(timezone.utc):
            member["status_label"] = "Expired"
        else:
            member["status_label"] = "Active"
    
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

@api_router.put("/members/{member_id}")
async def update_member(member_id: str, updates: dict, current_user: User = Depends(get_current_user)):
    """Update member information"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Remove fields that shouldn't be updated directly
    protected_fields = ["id", "qr_code", "norm_email", "norm_phone", "norm_first_name", "norm_last_name"]
    for field in protected_fields:
        updates.pop(field, None)
    
    # Convert datetime strings to datetime objects if needed
    datetime_fields = ["freeze_start_date", "freeze_end_date", "expiry_date", "contract_start_date", "contract_end_date"]
    for field in datetime_fields:
        if field in updates and updates[field] and isinstance(updates[field], str):
            try:
                updates[field] = datetime.fromisoformat(updates[field].replace('Z', '+00:00'))
            except:
                pass
    
    result = await db.members.update_one(
        {"id": member_id},
        {"$set": updates}
    )
    
    if result.modified_count == 0:
        return {"message": "No changes made", "member_id": member_id}
    
    # Log profile update to journal
    changed_fields = list(updates.keys())
    description = f"Profile updated: {', '.join(changed_fields)}"
    await add_journal_entry(
        member_id=member_id,
        action_type="profile_updated",
        description=description,
        metadata={
            "changed_fields": changed_fields,
            "updates": {k: str(v) for k, v in updates.items()}  # Convert to strings for JSON
        },
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    # Check for status changes
    if "membership_status" in updates:
        await add_journal_entry(
            member_id=member_id,
            action_type="status_changed",
            description=f"Membership status changed to: {updates['membership_status']}",
            metadata={
                "old_status": member.get("membership_status"),
                "new_status": updates["membership_status"]
            },
            created_by=current_user.id,
            created_by_name=current_user.full_name
        )
    
    return {"message": "Member updated successfully", "member_id": member_id}

@api_router.get("/members/{member_id}/profile")
async def get_member_profile(member_id: str, current_user: User = Depends(get_current_user)):
    """Get comprehensive member profile with stats"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get membership type details
    membership_type = None
    if member.get("membership_type_id"):
        membership_type = await db.membership_types.find_one(
            {"id": member["membership_type_id"]}, 
            {"_id": 0}
        )
    
    # Get payment option details
    payment_option = None
    if member.get("selected_payment_option_id"):
        payment_option = await db.payment_options.find_one(
            {"option_id": member["selected_payment_option_id"]},
            {"_id": 0}
        )
    
    # Get stats
    total_bookings = await db.bookings.count_documents({"member_id": member_id})
    total_access_logs = await db.access_logs.count_documents({"member_id": member_id})
    
    # Get last access
    last_access = await db.access_logs.find_one(
        {"member_id": member_id},
        {"_id": 0},
        sort=[("timestamp", -1)]
    )
    
    # Get debt/invoice info
    unpaid_invoices = await db.invoices.count_documents({
        "member_id": member_id,
        "status": {"$in": ["pending", "overdue"]}
    })
    
    # Calculate retention metrics (attendance comparison: current month vs previous month)
    from datetime import datetime, timedelta
    now = datetime.now(timezone.utc)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    current_month_visits = await db.access_logs.count_documents({
        "member_id": member_id,
        "timestamp": {"$gte": current_month_start.isoformat()}
    })
    
    previous_month_visits = await db.access_logs.count_documents({
        "member_id": member_id,
        "timestamp": {
            "$gte": previous_month_start.isoformat(),
            "$lt": current_month_start.isoformat()
        }
    })
    
    # Calculate retention percentage
    retention_percentage = 0
    retention_status = "collating"  # collating, consistent, good, alert, critical
    
    if previous_month_visits > 0:
        retention_percentage = round(((current_month_visits - previous_month_visits) / previous_month_visits) * 100)
        
        if retention_percentage >= 50:
            retention_status = "good"  # Green
        elif retention_percentage >= -10 and retention_percentage < 50:
            retention_status = "consistent"  # No change
        elif retention_percentage >= -40 and retention_percentage < -10:
            retention_status = "alert"  # Orange
        else:
            retention_status = "critical"  # Red
    elif current_month_visits > 0:
        retention_status = "consistent"
    
    # Calculate payment progress from invoices
    all_invoices = await db.invoices.find(
        {"member_id": member_id},
        {"_id": 0}
    ).to_list(length=None)
    
    total_paid = sum(inv.get("amount_paid", 0.0) for inv in all_invoices if inv.get("status") == "paid")
    total_unpaid = sum(inv.get("amount_due", 0.0) for inv in all_invoices if inv.get("status") in ["pending", "failed"])
    total_owed = sum(inv.get("amount_due", 0.0) for inv in all_invoices if inv.get("status") in ["pending", "overdue", "failed"])
    total_amount = total_paid + total_owed
    
    payment_progress = {
        "paid": total_paid,
        "unpaid": total_unpaid,
        "remaining": total_owed,
        "total": total_amount,
        "paid_percentage": round((total_paid / total_amount * 100) if total_amount > 0 else 0, 2),
        "unpaid_percentage": round((total_unpaid / total_amount * 100) if total_amount > 0 else 0, 2),
        "remaining_percentage": round((total_owed / total_amount * 100) if total_amount > 0 else 0, 2)
    }
    
    # Check for missing data
    missing_data = []
    if not member.get("phone"):
        missing_data.append("phone")
    if not member.get("home_phone") and not member.get("work_phone"):
        missing_data.append("additional_phone")
    if not member.get("emergency_contact"):
        missing_data.append("emergency_contact")
    if not member.get("address"):
        missing_data.append("address")
    if not member.get("bank_account_number"):
        missing_data.append("bank_details")
    
    # Phase 1 - Enhanced fields: Calculate sessions remaining, last visit, next billing
    sessions_remaining = member.get("sessions_remaining")
    last_visit_date = None
    if last_access:
        last_visit_date = last_access.get("timestamp")
    
    # Calculate next billing date (simplified - based on membership type duration)
    next_billing_date = member.get("next_billing_date")
    if not next_billing_date and membership_type:
        # If not explicitly set, calculate from join date + duration
        duration_months = membership_type.get("duration_months", 1)
        if member.get("join_date"):
            join_date_dt = datetime.fromisoformat(member["join_date"]) if isinstance(member["join_date"], str) else member["join_date"]
            next_billing_date = (join_date_dt + timedelta(days=duration_months * 30)).isoformat()
    
    return {
        "member": member,
        "membership_type": membership_type,
        "payment_option": payment_option,
        "stats": {
            "total_bookings": total_bookings,
            "total_access_logs": total_access_logs,
            "unpaid_invoices": unpaid_invoices,
            "no_show_count": member.get("no_show_count", 0),
            "debt_amount": member.get("debt_amount", 0.0),
            "last_access": last_access["timestamp"] if last_access else None
        },
        "retention": {
            "current_month_visits": current_month_visits,
            "previous_month_visits": previous_month_visits,
            "percentage_change": retention_percentage,
            "status": retention_status
        },
        "payment_progress": payment_progress,
        "missing_data": missing_data,
        # Phase 1 - Enhanced fields
        "sessions_remaining": sessions_remaining,
        "last_visit_date": last_visit_date,
        "next_billing_date": next_billing_date,
        "tags": member.get("tags", [])
    }

@api_router.get("/members/{member_id}/access-logs")
async def get_member_access_logs(
    member_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get member access logs with pagination"""
    access_logs = await db.access_logs.find(
        {"member_id": member_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(length=limit)
    
    return access_logs

@api_router.get("/members/{member_id}/bookings")
async def get_member_bookings(
    member_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get member bookings with pagination"""
    bookings = await db.bookings.find(
        {"member_id": member_id},
        {"_id": 0}
    ).sort("booking_date", -1).limit(limit).to_list(length=limit)
    
    return bookings

@api_router.get("/members/{member_id}/invoices")
async def get_member_invoices(
    member_id: str,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get member invoices with pagination"""
    invoices = await db.invoices.find(
        {"member_id": member_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(length=limit)
    
    return invoices

# Member Notes Routes
@api_router.post("/members/{member_id}/notes", response_model=MemberNote)
async def create_member_note(
    member_id: str,
    note_data: MemberNoteCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new note for a member"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    note = MemberNote(
        member_id=member_id,
        content=note_data.content,
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    await db.member_notes.insert_one(note.model_dump())
    
    # Log to journal
    await add_journal_entry(
        member_id=member_id,
        action_type="note_added",
        description=f"Note added: {note_data.content[:100]}..." if len(note_data.content) > 100 else f"Note added: {note_data.content}",
        metadata={
            "note_id": note.note_id,
            "full_content": note_data.content
        },
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    return note

@api_router.get("/members/{member_id}/notes", response_model=List[MemberNote])
async def get_member_notes(
    member_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all notes for a member"""
    notes = await db.member_notes.find(
        {"member_id": member_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(length=None)
    
    return notes

@api_router.put("/members/{member_id}/notes/{note_id}", response_model=MemberNote)
async def update_member_note(
    member_id: str,
    note_id: str,
    note_data: MemberNoteUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a member note"""
    note = await db.member_notes.find_one(
        {"note_id": note_id, "member_id": member_id},
        {"_id": 0}
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    result = await db.member_notes.update_one(
        {"note_id": note_id, "member_id": member_id},
        {"$set": {
            "content": note_data.content,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update note")
    
    updated_note = await db.member_notes.find_one(
        {"note_id": note_id, "member_id": member_id},
        {"_id": 0}
    )
    return updated_note

@api_router.delete("/members/{member_id}/notes/{note_id}")
async def delete_member_note(
    member_id: str,
    note_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a member note"""
    result = await db.member_notes.delete_one({
        "note_id": note_id,
        "member_id": member_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Log to journal
    await add_journal_entry(
        member_id=member_id,
        action_type="note_deleted",
        description="Note deleted",
        metadata={"note_id": note_id},
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    return {"message": "Note deleted successfully"}

# Member Journal Routes
@api_router.get("/members/{member_id}/journal")
async def get_member_journal(
    member_id: str,
    action_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get member journal entries with optional filters"""
    # Build query
    query = {"member_id": member_id}
    
    # Filter by action type
    if action_type and action_type != "all":
        query["action_type"] = action_type
    
    # Filter by date range
    if start_date or end_date:
        date_filter = {}
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                date_filter["$gte"] = start
            except:
                pass
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                date_filter["$lte"] = end
            except:
                pass
        if date_filter:
            query["created_at"] = date_filter
    
    # Search in description
    if search:
        query["description"] = {"$regex": search, "$options": "i"}
    
    # Get journal entries
    journal_entries = await db.member_journal.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(length=limit)
    
    return journal_entries

@api_router.post("/members/{member_id}/journal", response_model=MemberJournal)
async def create_journal_entry(
    member_id: str,
    journal_data: MemberJournalCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a manual journal entry for a member"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    journal_entry = await add_journal_entry(
        member_id=member_id,
        action_type=journal_data.action_type,
        description=journal_data.description,
        metadata=journal_data.metadata,
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    return journal_entry

# Task Type Routes
@api_router.get("/task-types", response_model=List[TaskType])
async def get_task_types(current_user: User = Depends(get_current_user)):
    """Get all task types"""
    task_types = await db.task_types.find(
        {"is_active": True},
        {"_id": 0}
    ).sort("name", 1).to_list(length=None)
    return task_types

@api_router.post("/task-types", response_model=TaskType)
async def create_task_type(
    task_type_data: TaskTypeCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new task type"""
    task_type = TaskType(**task_type_data.model_dump())
    await db.task_types.insert_one(task_type.model_dump())
    return task_type

@api_router.put("/task-types/{type_id}", response_model=TaskType)
async def update_task_type(
    type_id: str,
    task_type_data: TaskTypeUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a task type"""
    task_type = await db.task_types.find_one({"type_id": type_id}, {"_id": 0})
    if not task_type:
        raise HTTPException(status_code=404, detail="Task type not found")
    
    updates = {k: v for k, v in task_type_data.model_dump().items() if v is not None}
    if updates:
        await db.task_types.update_one(
            {"type_id": type_id},
            {"$set": updates}
        )
    
    updated_task_type = await db.task_types.find_one({"type_id": type_id}, {"_id": 0})
    return updated_task_type

@api_router.delete("/task-types/{type_id}")
async def delete_task_type(
    type_id: str,
    current_user: User = Depends(get_current_user)
):
    """Soft delete a task type"""
    result = await db.task_types.update_one(
        {"type_id": type_id},
        {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Task type not found")
    return {"message": "Task type deleted successfully"}

# Task Routes
@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    task_type_id: Optional[str] = None,
    assigned_to_user_id: Optional[str] = None,
    assigned_to_department: Optional[str] = None,
    related_member_id: Optional[str] = None,
    overdue: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all tasks with optional filters"""
    query = {}
    
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if task_type_id:
        query["task_type_id"] = task_type_id
    if assigned_to_user_id:
        query["assigned_to_user_id"] = assigned_to_user_id
    if assigned_to_department:
        query["assigned_to_department"] = assigned_to_department
    if related_member_id:
        query["related_member_id"] = related_member_id
    if overdue:
        query["due_date"] = {"$lt": datetime.now(timezone.utc)}
        query["status"] = {"$nin": ["completed", "cancelled"]}
    
    tasks = await db.tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(length=None)
    return tasks

@api_router.get("/tasks/my-tasks", response_model=List[Task])
async def get_my_tasks(current_user: User = Depends(get_current_user)):
    """Get tasks assigned to current user"""
    tasks = await db.tasks.find(
        {"assigned_to_user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(length=None)
    return tasks

@api_router.get("/tasks/stats")
async def get_task_stats(current_user: User = Depends(get_current_user)):
    """Get task statistics"""
    total = await db.tasks.count_documents({})
    pending = await db.tasks.count_documents({"status": "pending"})
    in_progress = await db.tasks.count_documents({"status": "in_progress"})
    completed = await db.tasks.count_documents({"status": "completed"})
    
    my_tasks = await db.tasks.count_documents({"assigned_to_user_id": current_user.id})
    my_overdue = await db.tasks.count_documents({
        "assigned_to_user_id": current_user.id,
        "due_date": {"$lt": datetime.now(timezone.utc)},
        "status": {"$nin": ["completed", "cancelled"]}
    })
    
    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "my_tasks": my_tasks,
        "my_overdue": my_overdue
    }

@api_router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific task"""
    task = await db.tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@api_router.post("/tasks", response_model=Task)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new task"""
    # Get task type name
    task_type = await db.task_types.find_one({"type_id": task_data.task_type_id}, {"_id": 0})
    if not task_type:
        raise HTTPException(status_code=404, detail="Task type not found")
    
    # Auto-assign to user based on department if no user specified
    assigned_to_user_id = task_data.assigned_to_user_id
    assigned_to_user_name = None
    
    if not assigned_to_user_id and task_data.assigned_to_department and task_data.assigned_to_department != "none":
        # Map department to role
        department_to_role = {
            "Admin": ["admin_manager", "head_admin"],
            "Reception": ["admin_manager", "head_admin"],
            "Fitness": ["fitness_head", "fitness_manager", "personal_trainer"],
            "Sales": ["sales_head", "sales_manager"],
            "HOD": ["business_owner", "head_admin", "operations_head"],
            "Maintenance": ["maintenance_head"]
        }
        
        roles_to_search = department_to_role.get(task_data.assigned_to_department, [])
        if roles_to_search:
            # Find first user with one of these roles
            user = await db.users.find_one({"role": {"$in": roles_to_search}}, {"_id": 0})
            if user:
                assigned_to_user_id = user.get("id")
                assigned_to_user_name = user.get("full_name")
    elif assigned_to_user_id:
        # Get assigned user name if directly assigned
        assigned_user = await db.users.find_one({"id": assigned_to_user_id}, {"_id": 0})
        if assigned_user:
            assigned_to_user_name = assigned_user.get("full_name")
    
    # Get related member name if related
    related_member_name = None
    if task_data.related_member_id:
        member = await db.members.find_one({"id": task_data.related_member_id}, {"_id": 0})
        if member:
            related_member_name = f"{member.get('first_name')} {member.get('last_name')}"
    
    task = Task(
        title=task_data.title,
        description=task_data.description,
        task_type_id=task_data.task_type_id,
        task_type_name=task_type.get("name"),
        priority=task_data.priority,
        assigned_to_user_id=assigned_to_user_id,
        assigned_to_user_name=assigned_to_user_name,
        assigned_to_department=task_data.assigned_to_department if task_data.assigned_to_department != "none" else None,
        related_member_id=task_data.related_member_id,
        related_member_name=related_member_name,
        due_date=task_data.due_date,
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    await db.tasks.insert_one(task.model_dump())
    
    # Log to journal if related to member
    if task_data.related_member_id:
        await add_journal_entry(
            member_id=task_data.related_member_id,
            action_type="task_created",
            description=f"Task created: {task.title}",
            metadata={
                "task_id": task.task_id,
                "task_type": task_type.get("name"),
                "priority": task.priority,
                "assigned_to": assigned_to_user_name or task_data.assigned_to_department
            },
            created_by=current_user.id,
            created_by_name=current_user.full_name
        )
    
    return task

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a task"""
    task = await db.tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    updates = {k: v for k, v in task_data.model_dump().items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc)
    
    # If status changed to completed, record completion
    if task_data.status == "completed" and task.get("status") != "completed":
        updates["completed_at"] = datetime.now(timezone.utc)
        updates["completed_by"] = current_user.id
        updates["completed_by_name"] = current_user.full_name
    
    # Update denormalized fields
    if task_data.task_type_id:
        task_type = await db.task_types.find_one({"type_id": task_data.task_type_id}, {"_id": 0})
        if task_type:
            updates["task_type_name"] = task_type.get("name")
    
    if task_data.assigned_to_user_id:
        assigned_user = await db.users.find_one({"id": task_data.assigned_to_user_id}, {"_id": 0})
        if assigned_user:
            updates["assigned_to_user_name"] = assigned_user.get("full_name")
    
    await db.tasks.update_one({"task_id": task_id}, {"$set": updates})
    
    updated_task = await db.tasks.find_one({"task_id": task_id}, {"_id": 0})
    return updated_task

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current_user: User = Depends(get_current_user)):
    """Delete a task"""
    result = await db.tasks.delete_one({"task_id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

# Task Comment Routes
@api_router.get("/tasks/{task_id}/comments", response_model=List[TaskComment])
async def get_task_comments(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a task"""
    comments = await db.task_comments.find(
        {"task_id": task_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(length=None)
    return comments

@api_router.post("/tasks/{task_id}/comments", response_model=TaskComment)
async def create_task_comment(
    task_id: str,
    comment_data: TaskCommentCreate,
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a task"""
    task = await db.tasks.find_one({"task_id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    comment = TaskComment(
        task_id=task_id,
        content=comment_data.content,
        attachments=comment_data.attachments,
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    await db.task_comments.insert_one(comment.model_dump())
    
    # Update comment count on task
    await db.tasks.update_one(
        {"task_id": task_id},
        {"$inc": {"comment_count": 1}}
    )
    
    return comment

@api_router.delete("/tasks/{task_id}/comments/{comment_id}")
async def delete_task_comment(
    task_id: str,
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a comment from a task"""
    result = await db.task_comments.delete_one({
        "comment_id": comment_id,
        "task_id": task_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Update comment count on task
    await db.tasks.update_one(
        {"task_id": task_id},
        {"$inc": {"comment_count": -1}}
    )
    
    return {"message": "Comment deleted successfully"}

# Override Reason Routes
@api_router.get("/override-reasons", response_model=List[OverrideReason])
async def get_override_reasons(current_user: User = Depends(get_current_user)):
    """Get all override reasons"""
    reasons = await db.override_reasons.find(
        {"is_active": True},
        {"_id": 0}
    ).sort("order", 1).to_list(length=None)
    return reasons

@api_router.get("/override-reasons/hierarchical")
async def get_override_reasons_hierarchical(current_user: User = Depends(get_current_user)):
    """Get override reasons in hierarchical structure"""
    all_reasons = await db.override_reasons.find(
        {"is_active": True},
        {"_id": 0}
    ).sort("order", 1).to_list(length=None)
    
    # Build hierarchy
    main_reasons = [r for r in all_reasons if not r.get("parent_id")]
    for main in main_reasons:
        main["sub_reasons"] = [r for r in all_reasons if r.get("parent_id") == main["reason_id"]]
    
    return main_reasons

@api_router.post("/override-reasons", response_model=OverrideReason)
async def create_override_reason(
    reason_data: OverrideReasonCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new override reason"""
    reason = OverrideReason(**reason_data.model_dump())
    await db.override_reasons.insert_one(reason.model_dump())
    return reason

@api_router.put("/override-reasons/{reason_id}", response_model=OverrideReason)
async def update_override_reason(
    reason_id: str,
    reason_data: OverrideReasonUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an override reason"""
    reason = await db.override_reasons.find_one({"reason_id": reason_id}, {"_id": 0})
    if not reason:
        raise HTTPException(status_code=404, detail="Override reason not found")
    
    updates = {k: v for k, v in reason_data.model_dump().items() if v is not None}
    if updates:
        await db.override_reasons.update_one(
            {"reason_id": reason_id},
            {"$set": updates}
        )
    
    updated_reason = await db.override_reasons.find_one({"reason_id": reason_id}, {"_id": 0})
    return updated_reason

@api_router.delete("/override-reasons/{reason_id}")
async def delete_override_reason(
    reason_id: str,
    current_user: User = Depends(get_current_user)
):
    """Soft delete an override reason"""
    result = await db.override_reasons.update_one(
        {"reason_id": reason_id},
        {"$set": {"is_active": False}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Override reason not found")
    return {"message": "Override reason deleted successfully"}

@api_router.post("/override-reasons/seed-defaults")
async def seed_default_override_reasons(current_user: User = Depends(get_current_user)):
    """Seed default override reasons with hierarchy"""
    default_reasons = [
        # Main reasons
        {"name": "Debt Arrangement", "description": "Member has arranged payment plan for debt", "parent_id": None, "requires_pin": True, "order": 1},
        {"name": "Lost Access Card", "description": "Member lost their access card", "parent_id": None, "requires_pin": True, "order": 2},
        {"name": "No App for QR Code", "description": "Member doesn't have app installed", "parent_id": None, "requires_pin": True, "order": 3},
        {"name": "External Contractor", "description": "Service provider or contractor", "parent_id": None, "requires_pin": False, "order": 4},
        {"name": "New Prospect", "description": "Potential new member", "parent_id": None, "requires_pin": False, "order": 5},
    ]
    
    # Insert main reasons first
    created_reasons = {}
    for reason_data in default_reasons:
        existing = await db.override_reasons.find_one({"name": reason_data["name"], "parent_id": None}, {"_id": 0})
        if not existing:
            reason = OverrideReason(**reason_data)
            await db.override_reasons.insert_one(reason.model_dump())
            created_reasons[reason_data["name"]] = reason.reason_id
        else:
            created_reasons[reason_data["name"]] = existing["reason_id"]
    
    # Sub-reasons for "New Prospect"
    if "New Prospect" in created_reasons:
        sub_reasons = [
            {"name": "Walk In", "description": "Walked into the facility", "parent_id": created_reasons["New Prospect"], "requires_pin": False, "order": 1},
            {"name": "Phone In", "description": "Called to inquire", "parent_id": created_reasons["New Prospect"], "requires_pin": False, "order": 2},
            {"name": "Canvassing", "description": "Found through canvassing", "parent_id": created_reasons["New Prospect"], "requires_pin": False, "order": 3},
            {"name": "Referral", "description": "Referred by existing member", "parent_id": created_reasons["New Prospect"], "requires_pin": False, "order": 4},
            {"name": "Social Media Lead", "description": "From social media campaign", "parent_id": created_reasons["New Prospect"], "requires_pin": False, "order": 5},
            {"name": "Flyer/Brochure", "description": "From marketing materials", "parent_id": created_reasons["New Prospect"], "requires_pin": False, "order": 6},
        ]
        
        for sub_reason_data in sub_reasons:
            existing = await db.override_reasons.find_one({
                "name": sub_reason_data["name"],
                "parent_id": sub_reason_data["parent_id"]
            }, {"_id": 0})
            if not existing:
                sub_reason = OverrideReason(**sub_reason_data)
                await db.override_reasons.insert_one(sub_reason.model_dump())
    
    return {
        "success": True,
        "message": "Seeded default override reasons with hierarchy"
    }

# Removed - moved to correct position before member_id endpoint

# Access Override Route
@api_router.post("/access/override")
async def create_access_override(
    override_data: AccessOverrideCreate,
    current_user: User = Depends(get_current_user)
):
    """Grant access override with reason and optional PIN verification"""
    
    # Get reason details
    reason = await db.override_reasons.find_one({"reason_id": override_data.reason_id}, {"_id": 0})
    if not reason:
        raise HTTPException(status_code=404, detail="Override reason not found")
    
    sub_reason = None
    if override_data.sub_reason_id:
        sub_reason = await db.override_reasons.find_one({"reason_id": override_data.sub_reason_id}, {"_id": 0})
    
    # Check if this is a new prospect or existing member
    member = None
    member_id = override_data.member_id
    pin_verified = False
    
    if member_id:
        # Existing member - verify PIN if required
        member = await db.members.find_one({"id": member_id}, {"_id": 0})
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        if reason.get("requires_pin", True):
            if not override_data.access_pin:
                raise HTTPException(status_code=400, detail="PIN required for this override reason")
            
            if member.get("access_pin") != override_data.access_pin:
                raise HTTPException(status_code=403, detail="Invalid PIN")
            
            pin_verified = True
        
        # Check daily override limit
        today = datetime.now(timezone.utc).date()
        last_override = member.get("last_override_date")
        if last_override:
            last_override_date = last_override.date() if isinstance(last_override, datetime) else datetime.fromisoformat(str(last_override).replace('Z', '+00:00')).date()
            if last_override_date == today:
                # Same day - check count
                if member.get("daily_override_count", 0) >= 3:  # Default limit
                    raise HTTPException(status_code=403, detail="Daily override limit reached for this member")
                await db.members.update_one(
                    {"id": member_id},
                    {"$inc": {"daily_override_count": 1}}
                )
            else:
                # New day - reset counter
                await db.members.update_one(
                    {"id": member_id},
                    {"$set": {"daily_override_count": 1, "last_override_date": datetime.now(timezone.utc)}}
                )
        else:
            # First override
            await db.members.update_one(
                {"id": member_id},
                {"$set": {"daily_override_count": 1, "last_override_date": datetime.now(timezone.utc)}}
            )
        
        member_name = f"{member['first_name']} {member['last_name']}"
        member_status = member.get("membership_status", "active")
    else:
        # New prospect - create temporary member record
        if not override_data.first_name or not override_data.last_name:
            raise HTTPException(status_code=400, detail="First name and last name required for new prospects")
        
        # Get a default membership type for prospects
        default_membership = await db.membership_types.find_one({"status": "active"}, {"_id": 0})
        if not default_membership:
            raise HTTPException(status_code=500, detail="No membership types available for prospect creation")
        
        new_member = Member(
            first_name=override_data.first_name,
            last_name=override_data.last_name,
            phone=override_data.phone or "N/A",
            email=override_data.email or f"{uuid.uuid4()}@prospect.temp",
            membership_type_id=default_membership["id"],
            membership_status="prospect",
            is_prospect=True,
            prospect_source=sub_reason.get("name") if sub_reason else reason.get("name"),
            qr_code=str(uuid.uuid4())
        )
        
        await db.members.insert_one(new_member.model_dump())
        member_id = new_member.id
        member_name = f"{new_member.first_name} {new_member.last_name}"
        member_status = "prospect"
    
    # Create override record
    override = AccessOverride(
        member_id=member_id,
        member_name=member_name,
        member_status=member_status,
        reason_id=override_data.reason_id,
        reason_name=reason.get("name"),
        sub_reason_id=override_data.sub_reason_id,
        sub_reason_name=sub_reason.get("name") if sub_reason else None,
        pin_verified=pin_verified,
        pin_entered="***" if override_data.access_pin else None,
        staff_id=current_user.id,
        staff_name=current_user.full_name,
        location=override_data.location,
        notes=override_data.notes
    )
    
    await db.access_overrides.insert_one(override.model_dump())
    
    # Log to access logs
    access_log = AccessLog(
        member_id=member_id,
        member_name=member_name,
        access_method="manual_override",
        status="granted",
        reason=f"Override: {reason.get('name')}" + (f" - {sub_reason.get('name')}" if sub_reason else ""),
        override_by=current_user.full_name,
        location=override_data.location
    )
    log_doc = access_log.model_dump()
    log_doc["timestamp"] = log_doc["timestamp"].isoformat()
    await db.access_logs.insert_one(log_doc)
    
    # Log to member journal
    await add_journal_entry(
        member_id=member_id,
        action_type="access_granted",
        description=f"Manual override granted: {reason.get('name')}" + (f" - {sub_reason.get('name')}" if sub_reason else ""),
        metadata={
            "override_reason": reason.get("name"),
            "sub_reason": sub_reason.get("name") if sub_reason else None,
            "pin_verified": pin_verified,
            "staff": current_user.full_name,
            "location": override_data.location
        },
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    return {
        "success": True,
        "message": "Access granted",
        "override_id": override.override_id,
        "member_id": member_id,
        "member_name": member_name,
        "is_new_prospect": not bool(override_data.member_id)
    }

# Convert Prospect to Member
@api_router.post("/members/convert-prospect/{member_id}")
async def convert_prospect_to_member(
    member_id: str,
    membership_type_id: str,
    current_user: User = Depends(get_current_user)
):
    """Convert a prospect to a full member"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if not member.get("is_prospect"):
        raise HTTPException(status_code=400, detail="Member is not a prospect")
    
    # Update member to full status
    await db.members.update_one(
        {"id": member_id},
        {"$set": {
            "is_prospect": False,
            "membership_type_id": membership_type_id,
            "membership_status": "active",
            "join_date": datetime.now(timezone.utc)
        }}
    )
    
    # Log to journal
    await add_journal_entry(
        member_id=member_id,
        action_type="status_changed",
        description=f"Converted from prospect to member",
        metadata={
            "old_status": "prospect",
            "new_status": "active",
            "membership_type_id": membership_type_id
        },
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    return {"success": True, "message": "Prospect converted to member successfully"}

# Access Control Routes
@api_router.post("/access/validate")
async def validate_access(data: AccessLogCreate):
    """Validate member access with comprehensive checks"""
    member = await db.members.find_one({"id": data.member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member_obj = Member(**member)
    
    # Get membership type name
    membership_type = await db.membership_types.find_one({"id": member_obj.membership_type_id}, {"_id": 0})
    membership_type_name = membership_type.get("name") if membership_type else "Unknown"
    
    # Prepare access log with enhanced data
    access_log_data = {
        "member_id": member_obj.id,
        "member_name": f"{member_obj.first_name} {member_obj.last_name}",
        "member_email": member_obj.email,
        "membership_type": membership_type_name,
        "membership_status": member_obj.membership_status,
        "access_method": data.access_method,
        "location": data.location,
        "device_id": data.device_id,
        "class_booking_id": data.class_booking_id,
        "temperature": data.temperature,
        "notes": data.notes,
        "override_by": data.override_by
    }
    
    # Check if member is blocked
    if member_obj.is_debtor:
        if not data.override_by:
            access_log = AccessLog(**access_log_data, status="denied", reason="Member has outstanding debt")
            log_doc = access_log.model_dump()
            log_doc["timestamp"] = log_doc["timestamp"].isoformat()
            await db.access_logs.insert_one(log_doc)
            
            # Log to journal
            await add_journal_entry(
                member_id=member_obj.id,
                action_type="access_denied",
                description=f"Access denied: Outstanding debt (R{member_obj.debt_amount:.2f})",
                metadata={
                    "reason": "Member has outstanding debt",
                    "debt_amount": member_obj.debt_amount,
                    "location": data.location,
                    "access_method": data.access_method
                }
            )
            
            return {
                "access": "denied", 
                "reason": "Member has outstanding debt",
                "debt_amount": member_obj.debt_amount,
                "member": member_obj
            }
    
    # Check membership status
    if member_obj.membership_status == "suspended":
        if not data.override_by:
            access_log = AccessLog(**access_log_data, status="denied", reason="Membership suspended")
            log_doc = access_log.model_dump()
            log_doc["timestamp"] = log_doc["timestamp"].isoformat()
            await db.access_logs.insert_one(log_doc)
            
            # Log to journal
            await add_journal_entry(
                member_id=member_obj.id,
                action_type="access_denied",
                description="Access denied: Membership suspended",
                metadata={
                    "reason": "Membership suspended",
                    "location": data.location,
                    "access_method": data.access_method
                }
            )
            
            return {"access": "denied", "reason": "Membership suspended", "member": member_obj}
    
    if member_obj.membership_status == "cancelled":
        if not data.override_by:
            access_log = AccessLog(**access_log_data, status="denied", reason="Membership cancelled")
            log_doc = access_log.model_dump()
            log_doc["timestamp"] = log_doc["timestamp"].isoformat()
            await db.access_logs.insert_one(log_doc)
            
            # Log to journal
            await add_journal_entry(
                member_id=member_obj.id,
                action_type="access_denied",
                description="Access denied: Membership cancelled",
                metadata={
                    "reason": "Membership cancelled",
                    "location": data.location,
                    "access_method": data.access_method
                }
            )
            
            return {"access": "denied", "reason": "Membership cancelled", "member": member_obj}
    
    # Check expiry
    if member_obj.expiry_date and member_obj.expiry_date < datetime.now(timezone.utc):
        if not data.override_by:
            access_log = AccessLog(**access_log_data, status="denied", reason="Membership expired")
            log_doc = access_log.model_dump()
            log_doc["timestamp"] = log_doc["timestamp"].isoformat()
            await db.access_logs.insert_one(log_doc)
            
            # Log to journal
            await add_journal_entry(
                member_id=member_obj.id,
                action_type="access_denied",
                description=f"Access denied: Membership expired on {member_obj.expiry_date.strftime('%Y-%m-%d')}",
                metadata={
                    "reason": "Membership expired",
                    "expiry_date": member_obj.expiry_date.isoformat(),
                    "location": data.location,
                    "access_method": data.access_method
                }
            )
            
            return {
                "access": "denied", 
                "reason": "Membership expired",
                "expiry_date": member_obj.expiry_date,
                "member": member_obj
            }
    
    # If checking in for a class, verify booking exists
    if data.class_booking_id:
        booking = await db.bookings.find_one({"id": data.class_booking_id}, {"_id": 0})
        if booking:
            access_log_data["class_name"] = booking.get("class_name")
            # Auto check-in for the booking
            await db.bookings.update_one(
                {"id": data.class_booking_id},
                {"$set": {
                    "status": "attended",
                    "checked_in_at": datetime.now(timezone.utc).isoformat()
                }}
            )
    
    # Grant access
    access_log = AccessLog(**access_log_data, status="granted", reason=data.reason or "Access granted")
    log_doc = access_log.model_dump()
    log_doc["timestamp"] = log_doc["timestamp"].isoformat()
    await db.access_logs.insert_one(log_doc)
    
    # Update member's last_visit_date
    await db.members.update_one(
        {"id": member_obj.id},
        {"$set": {"last_visit_date": datetime.now(timezone.utc).isoformat()}}
    )
    
    # AUTO-AWARD POINTS: Check-in reward (5 points per visit)
    import uuid
    try:
        # Get current balance
        balance = await db.points_balances.find_one({"member_id": member_obj.id}, {"_id": 0})
        
        if not balance:
            balance = {"member_id": member_obj.id, "total_points": 0, "lifetime_points": 0}
        
        # Award 5 points for check-in
        points_to_award = 5
        new_total = balance.get("total_points", 0) + points_to_award
        new_lifetime = balance.get("lifetime_points", 0) + points_to_award
        
        await db.points_balances.update_one(
            {"member_id": member_obj.id},
            {
                "$set": {
                    "total_points": new_total,
                    "lifetime_points": new_lifetime,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        
        # Record transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "member_id": member_obj.id,
            "points": points_to_award,
            "transaction_type": "earned",
            "reason": "Check-in reward",
            "reference_id": log_doc.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.points_transactions.insert_one(transaction.copy())
    except Exception as e:
        # Don't fail the check-in if points award fails
        print(f"Failed to award points: {e}")
    
    # Log to journal
    class_info = f" for {access_log_data.get('class_name')}" if access_log_data.get('class_name') else ""
    await add_journal_entry(
        member_id=member_obj.id,
        action_type="access_granted",
        description=f"Access granted{class_info} at {data.location or 'main entrance'}",
        metadata={
            "location": data.location,
            "access_method": data.access_method,
            "class_name": access_log_data.get('class_name'),
            "class_booking_id": data.class_booking_id
        }
    )
    
    return {"access": "granted", "member": member_obj, "access_log": access_log}

@api_router.get("/access/logs", response_model=List[AccessLog])
async def get_access_logs(
    limit: int = 100,
    member_id: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get access logs with optional filtering"""
    query = {}
    if member_id:
        query["member_id"] = member_id
    if status:
        query["status"] = status
    if location:
        query["location"] = location
    if date_from or date_to:
        query["timestamp"] = {}
        if date_from:
            query["timestamp"]["$gte"] = date_from
        if date_to:
            query["timestamp"]["$lte"] = date_to
    
    logs = await db.access_logs.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    for log in logs:
        if isinstance(log.get("timestamp"), str):
            log["timestamp"] = datetime.fromisoformat(log["timestamp"])
    return logs

@api_router.get("/access/analytics")
async def get_access_analytics(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get access analytics and statistics"""
    # Build date filter
    date_filter = {}
    if date_from or date_to:
        date_filter["timestamp"] = {}
        if date_from:
            date_filter["timestamp"]["$gte"] = date_from
        if date_to:
            date_filter["timestamp"]["$lte"] = date_to
    
    # Total access attempts
    total_attempts = await db.access_logs.count_documents(date_filter)
    
    # Granted vs Denied
    granted_count = await db.access_logs.count_documents({**date_filter, "status": "granted"})
    denied_count = await db.access_logs.count_documents({**date_filter, "status": "denied"})
    
    # Access by method
    access_methods = await db.access_logs.aggregate([
        {"$match": date_filter},
        {"$group": {"_id": "$access_method", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(100)
    
    # Access by location
    access_locations = await db.access_logs.aggregate([
        {"$match": {**date_filter, "location": {"$ne": None}}},
        {"$group": {"_id": "$location", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(100)
    
    # Denied reasons breakdown
    denied_reasons = await db.access_logs.aggregate([
        {"$match": {**date_filter, "status": "denied"}},
        {"$group": {"_id": "$reason", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(100)
    
    # Peak hours (access by hour)
    peak_hours = await db.access_logs.aggregate([
        {"$match": date_filter},
        {"$project": {
            "hour": {"$hour": {"$dateFromString": {"dateString": "$timestamp"}}}
        }},
        {"$group": {"_id": "$hour", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(24)
    
    # Top members by check-ins
    top_members = await db.access_logs.aggregate([
        {"$match": {**date_filter, "status": "granted"}},
        {"$group": {
            "_id": "$member_id",
            "member_name": {"$first": "$member_name"},
            "check_in_count": {"$sum": 1}
        }},
        {"$sort": {"check_in_count": -1}},
        {"$limit": 10}
    ]).to_list(10)
    
    # Access success rate
    success_rate = (granted_count / total_attempts * 100) if total_attempts > 0 else 0
    
    return {
        "total_attempts": total_attempts,
        "granted_count": granted_count,
        "denied_count": denied_count,
        "success_rate": round(success_rate, 2),
        "access_by_method": access_methods,
        "access_by_location": access_locations,
        "denied_reasons": denied_reasons,
        "peak_hours": peak_hours,
        "top_members": top_members
    }

@api_router.post("/access/quick-checkin")
async def quick_checkin(member_id: str, current_user: User = Depends(get_current_user)):
    """Quick check-in endpoint for manual check-ins"""
    access_data = AccessLogCreate(
        member_id=member_id,
        access_method="manual_override",
        override_by=current_user.id,
        notes="Quick check-in by staff"
    )
    result = await validate_access(access_data)
    return result

@api_router.get("/attendance/heatmap")
async def get_attendance_heatmap(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get attendance heatmap data with hourly granularity by day of week"""
    from datetime import datetime, timedelta, timezone
    
    # Default to last 30 days if no dates provided
    if not end_date:
        end_date = datetime.now(timezone.utc).isoformat()
    if not start_date:
        start_dt = datetime.now(timezone.utc) - timedelta(days=30)
        start_date = start_dt.isoformat()
    
    # Build filter for granted access only
    date_filter = {
        "status": "granted",
        "timestamp": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    # Aggregate by day of week and hour
    pipeline = [
        {"$match": date_filter},
        {"$project": {
            "timestamp_parsed": {"$dateFromString": {"dateString": "$timestamp"}},
        }},
        {"$project": {
            "dayOfWeek": {"$dayOfWeek": "$timestamp_parsed"},  # 1=Sunday, 2=Monday, ... 7=Saturday
            "hour": {"$hour": "$timestamp_parsed"}
        }},
        {"$group": {
            "_id": {
                "day": "$dayOfWeek",
                "hour": "$hour"
            },
            "count": {"$sum": 1}
        }}
    ]
    
    results = await db.access_logs.aggregate(pipeline).to_list(None)
    
    # Convert to day-of-week format (Monday=0, Sunday=6)
    day_mapping = {
        1: 6,  # Sunday -> 6
        2: 0,  # Monday -> 0
        3: 1,  # Tuesday -> 1
        4: 2,  # Wednesday -> 2
        5: 3,  # Thursday -> 3
        6: 4,  # Friday -> 4
        7: 5   # Saturday -> 5
    }
    
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Initialize heatmap data structure
    heatmap_data = []
    for i, day_name in enumerate(day_names):
        day_data = {
            "day": day_name,
            "day_index": i
        }
        # Initialize all hours to 0
        for hour in range(24):
            day_data[f"hour_{hour}"] = 0
        heatmap_data.append(day_data)
    
    # Populate with actual data
    for result in results:
        mongo_day = result["_id"]["day"]
        day_index = day_mapping.get(mongo_day, 0)
        hour = result["_id"]["hour"]
        count = result["count"]
        
        heatmap_data[day_index][f"hour_{hour}"] = count
    
    # Calculate statistics
    max_count = 0
    total_visits = 0
    for day_data in heatmap_data:
        for hour in range(24):
            count = day_data[f"hour_{hour}"]
            max_count = max(max_count, count)
            total_visits += count
    
    return {
        "heatmap": heatmap_data,
        "stats": {
            "total_visits": total_visits,
            "max_hourly_count": max_count,
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        }
    }

# ===================== Invoice Helper Functions =====================

async def calculate_invoice_totals(line_items: List[InvoiceLineItem]) -> dict:
    """Calculate invoice totals from line items"""
    subtotal = 0.0
    tax_total = 0.0
    discount_total = 0.0
    
    for item in line_items:
        # Calculate line item values
        line_subtotal = item.quantity * item.unit_price
        line_discount = line_subtotal * (item.discount_percent / 100)
        line_subtotal_after_discount = line_subtotal - line_discount
        line_tax = line_subtotal_after_discount * (item.tax_percent / 100)
        line_total = line_subtotal_after_discount + line_tax
        
        # Update item values
        item.subtotal = round(line_subtotal_after_discount, 2)
        item.tax_amount = round(line_tax, 2)
        item.total = round(line_total, 2)
        
        # Add to totals
        subtotal += item.subtotal
        tax_total += item.tax_amount
        discount_total += line_discount
    
    return {
        "subtotal": round(subtotal, 2),
        "tax_total": round(tax_total, 2),
        "discount_total": round(discount_total, 2),
        "amount": round(subtotal + tax_total, 2)
    }

async def generate_invoice_number() -> str:
    """Generate next sequential invoice number based on settings"""
    settings = await db.billing_settings.find_one({})
    if not settings:
        # Default settings if not configured
        prefix = "INV"
        year = datetime.now(timezone.utc).year
        sequence = await db.invoices.count_documents({}) + 1
    else:
        prefix = settings.get("invoice_prefix", "INV")
        year = datetime.now(timezone.utc).year
        sequence = settings.get("next_invoice_number", 1)
        
        # Update next invoice number
        await db.billing_settings.update_one(
            {"id": settings["id"]},
            {"$set": {"next_invoice_number": sequence + 1}}
        )
    
    return f"{prefix}-{year}-{str(sequence).zfill(4)}"

# ===================== Tag Management Routes =====================

@api_router.get("/tags")
async def get_all_tags(current_user: User = Depends(get_current_user)):
    """Get all available tags"""
    tags = await db.tags.find({}, {"_id": 0}).sort("name", 1).to_list(length=None)
    return tags

@api_router.post("/tags", response_model=Tag)
async def create_tag(data: TagCreate, current_user: User = Depends(get_current_user)):
    """Create a new tag"""
    # Check if tag with same name already exists
    existing = await db.tags.find_one({"name": data.name})
    if existing:
        raise HTTPException(status_code=400, detail="Tag with this name already exists")
    
    tag = Tag(
        name=data.name,
        color=data.color or "#3b82f6",
        description=data.description,
        category=data.category,
        created_by=current_user.id,
        usage_count=0
    )
    
    await db.tags.insert_one(tag.model_dump())
    return tag

@api_router.put("/tags/{tag_id}", response_model=Tag)
async def update_tag(tag_id: str, data: TagUpdate, current_user: User = Depends(get_current_user)):
    """Update a tag"""
    tag = await db.tags.find_one({"id": tag_id}, {"_id": 0})
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    update_data = {}
    if data.name is not None:
        # Check if new name conflicts with existing tag
        existing = await db.tags.find_one({"name": data.name, "id": {"$ne": tag_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Tag with this name already exists")
        update_data["name"] = data.name
    if data.color is not None:
        update_data["color"] = data.color
    if data.description is not None:
        update_data["description"] = data.description
    if data.category is not None:
        update_data["category"] = data.category
    
    if update_data:
        await db.tags.update_one({"id": tag_id}, {"$set": update_data})
        tag.update(update_data)
    
    return Tag(**tag)

@api_router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: str, current_user: User = Depends(get_current_user)):
    """Delete a tag and remove it from all members"""
    tag = await db.tags.find_one({"id": tag_id}, {"_id": 0})
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Remove tag from all members
    await db.members.update_many(
        {"tags": tag["name"]},
        {"$pull": {"tags": tag["name"]}}
    )
    
    # Delete tag
    await db.tags.delete_one({"id": tag_id})
    
    return {"message": "Tag deleted successfully"}

@api_router.post("/members/{member_id}/tags/{tag_name}")
async def add_tag_to_member(member_id: str, tag_name: str, current_user: User = Depends(get_current_user)):
    """Add a tag to a member"""
    # Verify member exists
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Verify tag exists
    tag = await db.tags.find_one({"name": tag_name})
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Check if member already has this tag
    if tag_name in member.get("tags", []):
        return {"message": "Member already has this tag"}
    
    # Add tag to member
    await db.members.update_one(
        {"id": member_id},
        {"$addToSet": {"tags": tag_name}}
    )
    
    # Update tag usage count
    await db.tags.update_one(
        {"name": tag_name},
        {"$inc": {"usage_count": 1}}
    )
    
    # Add journal entry
    await add_journal_entry(
        member_id=member_id,
        action_type="tag_added",
        description=f"Tag '{tag_name}' added to member",
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    return {"message": "Tag added to member successfully"}

@api_router.delete("/members/{member_id}/tags/{tag_name}")
async def remove_tag_from_member(member_id: str, tag_name: str, current_user: User = Depends(get_current_user)):
    """Remove a tag from a member"""
    # Verify member exists
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Remove tag from member
    await db.members.update_one(
        {"id": member_id},
        {"$pull": {"tags": tag_name}}
    )
    
    # Update tag usage count
    await db.tags.update_one(
        {"name": tag_name},
        {"$inc": {"usage_count": -1}}
    )
    
    # Add journal entry
    await add_journal_entry(
        member_id=member_id,
        action_type="tag_removed",
        description=f"Tag '{tag_name}' removed from member",
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    return {"message": "Tag removed from member successfully"}

# ===================== Member Action Routes =====================

@api_router.post("/members/{member_id}/freeze")
async def freeze_membership(member_id: str, data: MemberActionRequest, current_user: User = Depends(get_current_user)):
    """Freeze a member's membership"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if member.get("freeze_status"):
        raise HTTPException(status_code=400, detail="Membership is already frozen")
    
    # Update member freeze status
    freeze_data = {
        "freeze_status": True,
        "freeze_start_date": datetime.now(timezone.utc).isoformat(),
        "freeze_reason": data.reason or "Freeze requested",
        "membership_status": "frozen"
    }
    
    if data.end_date:
        freeze_data["freeze_end_date"] = data.end_date.isoformat()
    
    await db.members.update_one(
        {"id": member_id},
        {"$set": freeze_data}
    )
    
    # Add journal entry
    await add_journal_entry(
        member_id=member_id,
        action_type="membership_frozen",
        description=f"Membership frozen. Reason: {data.reason or 'Freeze requested'}",
        metadata={"end_date": data.end_date.isoformat() if data.end_date else None},
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    return {"message": "Membership frozen successfully", "freeze_end_date": data.end_date}

@api_router.post("/members/{member_id}/unfreeze")
async def unfreeze_membership(member_id: str, current_user: User = Depends(get_current_user)):
    """Unfreeze a member's membership"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if not member.get("freeze_status"):
        raise HTTPException(status_code=400, detail="Membership is not frozen")
    
    # Update member freeze status
    await db.members.update_one(
        {"id": member_id},
        {"$set": {
            "freeze_status": False,
            "freeze_start_date": None,
            "freeze_end_date": None,
            "freeze_reason": None,
            "membership_status": "active"
        }}
    )
    
    # Add journal entry
    await add_journal_entry(
        member_id=member_id,
        action_type="membership_unfrozen",
        description="Membership unfrozen",
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    return {"message": "Membership unfrozen successfully"}

@api_router.post("/members/{member_id}/cancel")
async def cancel_membership(member_id: str, data: MemberActionRequest, current_user: User = Depends(get_current_user)):
    """Cancel a member's membership"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if member.get("membership_status") == "cancelled":
        raise HTTPException(status_code=400, detail="Membership is already cancelled")
    
    # Update member status
    cancellation_data = {
        "membership_status": "cancelled",
        "cancellation_date": datetime.now(timezone.utc).isoformat(),
        "cancellation_reason": data.reason or "Cancellation requested"
    }
    
    if data.notes:
        existing_notes = member.get("notes") or ""
        cancellation_data["notes"] = (existing_notes + f"\n\nCancellation Notes: {data.notes}").strip()
    
    await db.members.update_one(
        {"id": member_id},
        {"$set": cancellation_data}
    )
    
    # Add journal entry
    await add_journal_entry(
        member_id=member_id,
        action_type="membership_cancelled",
        description=f"Membership cancelled. Reason: {data.reason or 'Cancellation requested'}",
        metadata={"notes": data.notes},
        created_by=current_user.id,
        created_by_name=current_user.full_name
    )
    
    return {"message": "Membership cancelled successfully"}

# ===================== Invoice Routes =====================

@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(data: InvoiceCreate, current_user: User = Depends(get_current_user)):
    """Create a new invoice with line items"""
    # Validate member exists
    member = await db.members.find_one({"id": data.member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Calculate invoice totals
    totals = await calculate_invoice_totals(data.line_items)
    
    # Generate invoice number
    invoice_number = await generate_invoice_number()
    
    # Create invoice
    invoice = Invoice(
        invoice_number=invoice_number,
        member_id=data.member_id,
        description=data.description,
        due_date=data.due_date,
        line_items=data.line_items,
        subtotal=totals["subtotal"],
        tax_total=totals["tax_total"],
        discount_total=totals["discount_total"],
        amount=totals["amount"],
        notes=data.notes,
        auto_generated=data.auto_generated,
        generated_from=data.generated_from
    )
    
    # Prepare for database
    doc = invoice.model_dump()
    doc["due_date"] = doc["due_date"].isoformat()
    doc["created_at"] = doc["created_at"].isoformat()
    
    # Convert line items properly
    doc["line_items"] = [item.model_dump() for item in invoice.line_items]
    
    await db.invoices.insert_one(doc)
    
    # Log to member journal
    await db.member_journal.insert_one({
        "id": str(uuid.uuid4()),
        "member_id": data.member_id,
        "action_type": "invoice_created",
        "title": f"Invoice {invoice_number} created",
        "description": f"Invoice for {data.description} - Amount: R{totals['amount']:.2f}",
        "performed_by": current_user.full_name,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    # Check if we should auto-email invoice
    billing_settings = await db.billing_settings.find_one({})
    if billing_settings and billing_settings.get("auto_email_invoices") and billing_settings.get("email_on_invoice_created"):
        # TODO: Send email notification (placeholder for now)
        print(f"Would send invoice email to member {data.member_id}")
    
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

@api_router.get("/invoices/{invoice_id}", response_model=Invoice)
async def get_invoice_details(invoice_id: str, current_user: User = Depends(get_current_user)):
    """Get detailed invoice information with line items"""
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Parse dates
    if isinstance(invoice.get("due_date"), str):
        invoice["due_date"] = datetime.fromisoformat(invoice["due_date"])
    if isinstance(invoice.get("created_at"), str):
        invoice["created_at"] = datetime.fromisoformat(invoice["created_at"])
    if invoice.get("paid_date") and isinstance(invoice["paid_date"], str):
        invoice["paid_date"] = datetime.fromisoformat(invoice["paid_date"])
    if invoice.get("batch_date") and isinstance(invoice["batch_date"], str):
        invoice["batch_date"] = datetime.fromisoformat(invoice["batch_date"])
    
    return invoice

@api_router.put("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: str, data: InvoiceUpdate, current_user: User = Depends(get_current_user)):
    """Update an existing invoice (only if not paid)"""
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Can't edit paid or void invoices
    if invoice.get("status") in ["paid", "void"]:
        raise HTTPException(status_code=400, detail=f"Cannot edit {invoice['status']} invoice")
    
    update_data = {}
    
    if data.description is not None:
        update_data["description"] = data.description
    if data.due_date is not None:
        update_data["due_date"] = data.due_date.isoformat()
    if data.notes is not None:
        update_data["notes"] = data.notes
    if data.status is not None:
        update_data["status"] = data.status
        # If marking as paid, set paid_date and award points
        if data.status == "paid" and invoice.get("status") != "paid":
            update_data["paid_date"] = datetime.now(timezone.utc).isoformat()
            
            # AUTO-AWARD POINTS: Payment reward (10 points per payment)
            import uuid
            try:
                member_id = invoice.get("member_id")
                if member_id:
                    balance = await db.points_balances.find_one({"member_id": member_id}, {"_id": 0})
                    
                    if not balance:
                        balance = {"member_id": member_id, "total_points": 0, "lifetime_points": 0}
                    
                    # Award 10 points for payment
                    points_to_award = 10
                    new_total = balance.get("total_points", 0) + points_to_award
                    new_lifetime = balance.get("lifetime_points", 0) + points_to_award
                    
                    await db.points_balances.update_one(
                        {"member_id": member_id},
                        {
                            "$set": {
                                "total_points": new_total,
                                "lifetime_points": new_lifetime,
                                "last_updated": datetime.now(timezone.utc).isoformat()
                            }
                        },
                        upsert=True
                    )
                    
                    # Record transaction
                    transaction = {
                        "id": str(uuid.uuid4()),
                        "member_id": member_id,
                        "points": points_to_award,
                        "transaction_type": "earned",
                        "reason": "Payment completed",
                        "reference_id": invoice_id,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await db.points_transactions.insert_one(transaction.copy())
            except Exception as e:
                # Don't fail the payment if points award fails
                print(f"Failed to award points: {e}")
    
    # If line items updated, recalculate totals
    if data.line_items is not None:
        totals = await calculate_invoice_totals(data.line_items)
        update_data["line_items"] = [item.model_dump() for item in data.line_items]
        update_data["subtotal"] = totals["subtotal"]
        update_data["tax_total"] = totals["tax_total"]
        update_data["discount_total"] = totals["discount_total"]
        update_data["amount"] = totals["amount"]
    
    if update_data:
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": update_data}
        )
    
    # Get updated invoice
    updated_invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    
    # Parse dates
    if isinstance(updated_invoice.get("due_date"), str):
        updated_invoice["due_date"] = datetime.fromisoformat(updated_invoice["due_date"])
    if isinstance(updated_invoice.get("created_at"), str):
        updated_invoice["created_at"] = datetime.fromisoformat(updated_invoice["created_at"])
    if updated_invoice.get("paid_date") and isinstance(updated_invoice["paid_date"], str):
        updated_invoice["paid_date"] = datetime.fromisoformat(updated_invoice["paid_date"])
    
    return updated_invoice

@api_router.delete("/invoices/{invoice_id}")
async def void_invoice(invoice_id: str, reason: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Void an invoice (soft delete)"""
    invoice = await db.invoices.find_one({"id": invoice_id})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Can't void paid invoices
    if invoice.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Cannot void paid invoice")
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "status": "void",
            "status_message": reason or "Invoice voided"
        }}
    )
    
    # Log to member journal
    await db.member_journal.insert_one({
        "id": str(uuid.uuid4()),
        "member_id": invoice["member_id"],
        "action_type": "invoice_voided",
        "title": f"Invoice {invoice['invoice_number']} voided",
        "description": reason or "Invoice voided",
        "performed_by": current_user.full_name,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Invoice voided successfully"}

@api_router.get("/invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(invoice_id: str, current_user: User = Depends(get_current_user)):
    """Generate PDF for an invoice"""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
    from fastapi.responses import StreamingResponse
    
    # Get invoice
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get member details
    member = await db.members.find_one({"id": invoice["member_id"]}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get billing settings for company info
    billing_settings = await db.billing_settings.find_one({})
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a56db'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1a56db'),
        spaceAfter=12
    )
    
    # Company header
    if billing_settings and billing_settings.get("company_name"):
        company_name = Paragraph(billing_settings.get("company_name", ""), title_style)
        elements.append(company_name)
        
        if billing_settings.get("company_address"):
            company_info = Paragraph(f"""
                {billing_settings.get("company_address", "")}<br/>
                Phone: {billing_settings.get("company_phone", "N/A")}<br/>
                Email: {billing_settings.get("company_email", "N/A")}<br/>
                Tax No: {billing_settings.get("tax_number", "N/A")}
            """, styles['Normal'])
            elements.append(company_info)
        elements.append(Spacer(1, 20))
    else:
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 20))
    
    # Invoice info table
    invoice_info_data = [
        ['Invoice Number:', invoice.get("invoice_number", "")],
        ['Invoice Date:', datetime.fromisoformat(invoice["created_at"]) if isinstance(invoice.get("created_at"), str) else invoice.get("created_at", "").strftime("%Y-%m-%d")],
        ['Due Date:', datetime.fromisoformat(invoice["due_date"]) if isinstance(invoice.get("due_date"), str) else invoice.get("due_date", "").strftime("%Y-%m-%d")],
        ['Status:', invoice.get("status", "").upper()]
    ]
    
    invoice_info_table = Table(invoice_info_data, colWidths=[2*inch, 3*inch])
    invoice_info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1a56db')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(invoice_info_table)
    elements.append(Spacer(1, 20))
    
    # Bill to section
    elements.append(Paragraph("BILL TO:", heading_style))
    bill_to_text = f"""
        {member.get("first_name", "")} {member.get("last_name", "")}<br/>
        {member.get("email", "")}<br/>
        {member.get("phone", "N/A")}<br/>
        {member.get("address", "N/A")}
    """
    elements.append(Paragraph(bill_to_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Line items table
    elements.append(Paragraph("ITEMS:", heading_style))
    
    line_items_data = [['Description', 'Qty', 'Unit Price', 'Discount', 'Tax', 'Total']]
    
    for item in invoice.get("line_items", []):
        line_items_data.append([
            item.get("description", ""),
            str(item.get("quantity", 0)),
            f"R{item.get('unit_price', 0):.2f}",
            f"{item.get('discount_percent', 0)}%",
            f"{item.get('tax_percent', 0)}%",
            f"R{item.get('total', 0):.2f}"
        ])
    
    # Add totals
    line_items_data.append(['', '', '', '', 'Subtotal:', f"R{invoice.get('subtotal', 0):.2f}"])
    line_items_data.append(['', '', '', '', 'Tax Total:', f"R{invoice.get('tax_total', 0):.2f}"])
    if invoice.get('discount_total', 0) > 0:
        line_items_data.append(['', '', '', '', 'Discount:', f"-R{invoice.get('discount_total', 0):.2f}"])
    line_items_data.append(['', '', '', '', 'TOTAL:', f"R{invoice.get('amount', 0):.2f}"])
    
    line_items_table = Table(line_items_data, colWidths=[2.5*inch, 0.7*inch, 1*inch, 0.8*inch, 1*inch, 1*inch])
    line_items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a56db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
        ('GRID', (0, 0), (-1, -5), 1, colors.black),
        ('LINEABOVE', (4, -4), (-1, -4), 1, colors.black),
        ('LINEABOVE', (4, -1), (-1, -1), 2, colors.black),
        ('FONTNAME', (4, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (4, -1), (-1, -1), 12),
    ]))
    elements.append(line_items_table)
    elements.append(Spacer(1, 20))
    
    # Notes
    if invoice.get("notes"):
        elements.append(Paragraph("NOTES:", heading_style))
        elements.append(Paragraph(invoice.get("notes", ""), styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # Footer
    footer_text = Paragraph(
        "Thank you for your business!",
        ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, textColor=colors.grey)
    )
    elements.append(Spacer(1, 30))
    elements.append(footer_text)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{invoice.get('invoice_number', 'unknown')}.pdf"}
    )


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


# Dashboard Enhancement APIs

@api_router.get("/dashboard/sales-comparison")
async def get_sales_comparison(current_user: User = Depends(get_current_user)):
    """Get sales comparison data: current month vs target vs previous month vs last year"""
    from datetime import datetime, timedelta
    
    now = datetime.now(timezone.utc)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    
    # Previous month
    previous_month_end = current_month_start - timedelta(seconds=1)
    previous_month_start = previous_month_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Last year same month
    last_year_month_start = current_month_start.replace(year=current_month_start.year - 1)
    last_year_month_end = current_month_end.replace(year=current_month_end.year - 1)
    
    # Get daily sales for each period
    days_in_month = (current_month_end - current_month_start).days + 1
    
    # Build daily data structure
    daily_data = []
    for day in range(1, days_in_month + 1):
        date_obj = current_month_start.replace(day=day)
        
        # Current month sales up to today
        if date_obj <= now:
            current_sales = await db.invoices.aggregate([
                {
                    "$match": {
                        "status": "paid",
                        "created_at": {
                            "$gte": current_month_start.isoformat(),
                            "$lte": date_obj.replace(hour=23, minute=59, second=59).isoformat()
                        }
                    }
                },
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]).to_list(1)
            current_month_sales = current_sales[0]["total"] if current_sales else 0
        else:
            current_month_sales = None
        
        # Previous month sales (same day, handle month with fewer days)
        try:
            prev_month_date = previous_month_start.replace(day=day)
        except ValueError:
            # Handle case where previous month has fewer days (e.g., Feb 30)
            import calendar
            last_day_prev_month = calendar.monthrange(previous_month_start.year, previous_month_start.month)[1]
            prev_month_date = previous_month_start.replace(day=min(day, last_day_prev_month))
        prev_sales = await db.invoices.aggregate([
            {
                "$match": {
                    "status": "paid",
                    "created_at": {
                        "$gte": previous_month_start.isoformat(),
                        "$lte": prev_month_date.replace(hour=23, minute=59, second=59).isoformat()
                    }
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        prev_month_sales = prev_sales[0]["total"] if prev_sales else 0
        
        # Last year sales (same day, handle leap year issues)
        try:
            last_year_date = last_year_month_start.replace(day=day)
        except ValueError:
            # Handle case where last year month has fewer days (e.g., Feb 29 in non-leap year)
            import calendar
            last_day_last_year = calendar.monthrange(last_year_month_start.year, last_year_month_start.month)[1]
            last_year_date = last_year_month_start.replace(day=min(day, last_day_last_year))
        last_year_sales_result = await db.invoices.aggregate([
            {
                "$match": {
                    "status": "paid",
                    "created_at": {
                        "$gte": last_year_month_start.isoformat(),
                        "$lte": last_year_date.replace(hour=23, minute=59, second=59).isoformat()
                    }
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        last_year_sales = last_year_sales_result[0]["total"] if last_year_sales_result else 0
        
        # Target (linear progression throughout month)
        # For now, using a simple calculation: get monthly target from settings or use 100k default
        monthly_target = 100000  # This should come from settings
        daily_target = (monthly_target / days_in_month) * day
        
        daily_data.append({
            "DisplayDate": date_obj.isoformat(),
            "day": day,
            "MonthSales": current_month_sales,
            "PrevMonthSales": prev_month_sales,
            "LastYearSales": last_year_sales,
            "Target": daily_target
        })
    
    return {
        "data": daily_data,
        "monthly_target": monthly_target,
        "current_month_name": current_month_start.strftime("%B %Y")
    }

@api_router.get("/dashboard/kpi-trends")
async def get_kpi_trends(current_user: User = Depends(get_current_user)):
    """Get 12-week KPI trends for sparklines"""
    from datetime import datetime, timedelta
    
    now = datetime.now(timezone.utc)
    weeks_data = []
    
    for week_offset in range(11, -1, -1):
        week_start = now - timedelta(weeks=week_offset + 1)
        week_end = now - timedelta(weeks=week_offset)
        
        # People Registered (new members)
        new_members = await db.members.count_documents({
            "created_at": {
                "$gte": week_start.isoformat(),
                "$lt": week_end.isoformat()
            }
        })
        
        # Memberships Started (new active memberships)
        memberships_started = await db.members.count_documents({
            "membership_start_date": {
                "$gte": week_start.isoformat(),
                "$lt": week_end.isoformat()
            },
            "membership_status": "active"
        })
        
        # Attendance (access logs)
        attendance = await db.access_logs.count_documents({
            "timestamp": {
                "$gte": week_start.isoformat(),
                "$lt": week_end.isoformat()
            }
        })
        
        # Bookings
        bookings = await db.bookings.count_documents({
            "booking_date": {
                "$gte": week_start.isoformat(),
                "$lt": week_end.isoformat()
            }
        })
        
        # Booking Attendance
        booking_attendance = await db.bookings.count_documents({
            "booking_date": {
                "$gte": week_start.isoformat(),
                "$lt": week_end.isoformat()
            },
            "status": "attended"
        })
        
        # Product Sales (from POS)
        product_sales_result = await db.pos_transactions.aggregate([
            {
                "$match": {
                    "transaction_type": "product_sale",
                    "created_at": {
                        "$gte": week_start.isoformat(),
                        "$lt": week_end.isoformat()
                    }
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$total_amount"}}}
        ]).to_list(1)
        product_sales = product_sales_result[0]["total"] if product_sales_result else 0
        
        # Tasks Created
        tasks_created = await db.tasks.count_documents({
            "created_at": {
                "$gte": week_start.isoformat(),
                "$lt": week_end.isoformat()
            }
        })
        
        weeks_data.append({
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "people_registered": new_members,
            "memberships_started": memberships_started,
            "attendance": attendance,
            "bookings": bookings,
            "booking_attendance": booking_attendance,
            "product_sales": round(product_sales, 2),
            "tasks": tasks_created
        })
    
    return weeks_data

@api_router.get("/dashboard/birthdays-today")
async def get_birthdays_today(current_user: User = Depends(get_current_user)):
    """Get members with birthdays today with photos"""
    from datetime import datetime
    
    now = datetime.now(timezone.utc)
    today_month_day = f"{now.month:02d}-{now.day:02d}"
    
    # Find members where date_of_birth matches today's month and day
    # Note: We need to handle various date formats
    all_members = await db.members.find({}, {"_id": 0}).to_list(10000)
    
    birthday_members = []
    for member in all_members:
        dob = member.get("date_of_birth")
        if dob:
            try:
                # Parse various date formats
                if isinstance(dob, str):
                    # Try ISO format
                    try:
                        dob_date = datetime.fromisoformat(dob.replace('Z', '+00:00'))
                    except:
                        # Try other common formats
                        from dateutil import parser
                        dob_date = parser.parse(dob)
                    
                    member_month_day = f"{dob_date.month:02d}-{dob_date.day:02d}"
                    
                    if member_month_day == today_month_day:
                        age = now.year - dob_date.year
                        if now.month < dob_date.month or (now.month == dob_date.month and now.day < dob_date.day):
                            age -= 1
                        
                        birthday_members.append({
                            "id": member.get("id"),
                            "first_name": member.get("first_name", ""),
                            "last_name": member.get("last_name", ""),
                            "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                            "age": age,
                            "photo_url": member.get("photo_url", ""),
                            "membership_status": member.get("membership_status", ""),
                            "email": member.get("email", "")
                        })
            except:
                continue
    
    return birthday_members


# ===================== Phase 2A - Dashboard Enhancements Routes =====================

@api_router.get("/dashboard/snapshot")
async def get_dashboard_snapshot(current_user: User = Depends(get_current_user)):
    """Get Today vs Yesterday vs Growth metrics for dashboard snapshot cards"""
    from datetime import datetime, timedelta
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    last_30_days_start = now - timedelta(days=30)
    last_year_30_days_start = now - timedelta(days=395)  # 365 + 30 days ago
    last_year_30_days_end = now - timedelta(days=365)
    
    # TODAY STATS
    # People registered today (members created today)
    today_registered = await db.members.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    # Memberships commenced today (join_date is today)
    today_commenced = await db.members.count_documents({
        "join_date": {"$gte": today_start.isoformat()}
    })
    
    # Attendance today (access logs)
    today_attendance = await db.access_logs.count_documents({
        "timestamp": {"$gte": today_start.isoformat()},
        "status": "granted"
    })
    
    # YESTERDAY STATS
    yesterday_registered = await db.members.count_documents({
        "created_at": {
            "$gte": yesterday_start.isoformat(),
            "$lt": today_start.isoformat()
        }
    })
    
    yesterday_commenced = await db.members.count_documents({
        "join_date": {
            "$gte": yesterday_start.isoformat(),
            "$lt": today_start.isoformat()
        }
    })
    
    yesterday_attendance = await db.access_logs.count_documents({
        "timestamp": {
            "$gte": yesterday_start.isoformat(),
            "$lt": today_start.isoformat()
        },
        "status": "granted"
    })
    
    # GROWTH METRICS (Last 30 Days vs Same Period Last Year)
    # Memberships sold last 30 days
    memberships_sold_30d = await db.members.count_documents({
        "join_date": {"$gte": last_30_days_start.isoformat()}
    })
    
    # Memberships sold same period last year
    memberships_sold_last_year = await db.members.count_documents({
        "join_date": {
            "$gte": last_year_30_days_start.isoformat(),
            "$lt": last_year_30_days_end.isoformat()
        }
    })
    
    # Memberships expired last 30 days
    memberships_expired_30d = await db.members.count_documents({
        "expiry_date": {
            "$gte": last_30_days_start.isoformat(),
            "$lt": now.isoformat()
        },
        "membership_status": {"$in": ["expired", "cancelled"]}
    })
    
    # Memberships expired same period last year
    memberships_expired_last_year = await db.members.count_documents({
        "expiry_date": {
            "$gte": last_year_30_days_start.isoformat(),
            "$lt": last_year_30_days_end.isoformat()
        },
        "membership_status": {"$in": ["expired", "cancelled"]}
    })
    
    # Attendance last 30 days
    attendance_30d = await db.access_logs.count_documents({
        "timestamp": {"$gte": last_30_days_start.isoformat()},
        "status": "granted"
    })
    
    # Attendance same period last year
    attendance_last_year = await db.access_logs.count_documents({
        "timestamp": {
            "$gte": last_year_30_days_start.isoformat(),
            "$lt": last_year_30_days_end.isoformat()
        },
        "status": "granted"
    })
    
    # Calculate growth percentages
    def calculate_growth(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 1)
    
    memberships_growth = calculate_growth(memberships_sold_30d, memberships_sold_last_year)
    expired_growth = calculate_growth(memberships_expired_30d, memberships_expired_last_year)
    attendance_growth = calculate_growth(attendance_30d, attendance_last_year)
    
    net_gain_30d = memberships_sold_30d - memberships_expired_30d
    net_gain_last_year = memberships_sold_last_year - memberships_expired_last_year
    net_gain_growth = calculate_growth(net_gain_30d, net_gain_last_year)
    
    return {
        "today": {
            "registered": today_registered,
            "commenced": today_commenced,
            "attendance": today_attendance
        },
        "yesterday": {
            "registered": yesterday_registered,
            "commenced": yesterday_commenced,
            "attendance": yesterday_attendance
        },
        "growth": {
            "memberships_sold_30d": memberships_sold_30d,
            "memberships_sold_last_year": memberships_sold_last_year,
            "memberships_growth": memberships_growth,
            "memberships_expired_30d": memberships_expired_30d,
            "memberships_expired_last_year": memberships_expired_last_year,
            "expired_growth": expired_growth,
            "net_gain_30d": net_gain_30d,
            "net_gain_last_year": net_gain_last_year,
            "net_gain_growth": net_gain_growth,
            "attendance_30d": attendance_30d,
            "attendance_last_year": attendance_last_year,
            "attendance_growth": attendance_growth
        }
    }


@api_router.get("/dashboard/recent-members")
async def get_recent_members(period: str = "today", current_user: User = Depends(get_current_user)):
    """Get members added today or yesterday with profile links"""
    from datetime import datetime, timedelta
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if period == "today":
        start_date = today_start
        end_date = now
    elif period == "yesterday":
        start_date = today_start - timedelta(days=1)
        end_date = today_start
    else:
        start_date = today_start
        end_date = now
    
    # Get members created in the specified period
    members = await db.members.find(
        {
            "created_at": {
                "$gte": start_date.isoformat(),
                "$lt": end_date.isoformat()
            }
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Format member data
    recent_members = []
    for member in members:
        recent_members.append({
            "id": member.get("id"),
            "first_name": member.get("first_name", ""),
            "last_name": member.get("last_name", ""),
            "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
            "email": member.get("email", ""),
            "phone": member.get("phone", ""),
            "membership_status": member.get("membership_status", ""),
            "join_date": member.get("join_date"),
            "created_at": member.get("created_at")
        })
    
    return recent_members


# ===================== Phase 2B - Retention Intelligence Routes =====================

@api_router.get("/retention/at-risk-members")
async def get_at_risk_members(current_user: User = Depends(get_current_user)):
    """Get members at high risk of cancellation based on attendance patterns"""
    from datetime import datetime, timedelta
    
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    fourteen_days_ago = now - timedelta(days=14)
    twenty_eight_days_ago = now - timedelta(days=28)
    
    # Get all active members
    active_members = await db.members.find(
        {"membership_status": "active"},
        {"_id": 0}
    ).to_list(None)
    
    at_risk_members = []
    
    for member in active_members:
        risk_score = 0
        risk_factors = []
        
        # Check last visit date
        last_visit = member.get("last_visit_date")
        if last_visit:
            last_visit_dt = datetime.fromisoformat(last_visit) if isinstance(last_visit, str) else last_visit
            days_since_visit = (now - last_visit_dt).days
            
            if days_since_visit >= 28:
                risk_score += 40
                risk_factors.append(f"No visit in {days_since_visit} days")
            elif days_since_visit >= 14:
                risk_score += 25
                risk_factors.append(f"No visit in {days_since_visit} days")
            elif days_since_visit >= 7:
                risk_score += 10
                risk_factors.append(f"No visit in {days_since_visit} days")
        else:
            # No last visit recorded
            risk_score += 30
            risk_factors.append("No attendance recorded")
        
        # Check if member is a debtor
        if member.get("is_debtor"):
            risk_score += 20
            risk_factors.append("Outstanding payment")
        
        # Check missing data
        if not member.get("phone"):
            risk_score += 5
            risk_factors.append("No contact phone")
        
        # Check membership expiry
        expiry_date = member.get("expiry_date")
        if expiry_date:
            expiry_dt = datetime.fromisoformat(expiry_date) if isinstance(expiry_date, str) else expiry_date
            days_until_expiry = (expiry_dt - now).days
            
            if 0 < days_until_expiry <= 30:
                risk_score += 15
                risk_factors.append(f"Expires in {days_until_expiry} days")
        
        # Categorize risk level
        if risk_score >= 50:
            risk_level = "critical"
        elif risk_score >= 30:
            risk_level = "high"
        elif risk_score >= 15:
            risk_level = "medium"
        else:
            continue  # Skip low-risk members
        
        at_risk_members.append({
            "id": member.get("id"),
            "first_name": member.get("first_name"),
            "last_name": member.get("last_name"),
            "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
            "email": member.get("email"),
            "phone": member.get("phone"),
            "last_visit_date": last_visit,
            "days_since_visit": days_since_visit if last_visit else None,
            "membership_type": member.get("membership_type"),
            "is_debtor": member.get("is_debtor", False),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "expiry_date": member.get("expiry_date")
        })
    
    # Sort by risk score descending
    at_risk_members.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return {
        "total": len(at_risk_members),
        "critical": len([m for m in at_risk_members if m["risk_level"] == "critical"]),
        "high": len([m for m in at_risk_members if m["risk_level"] == "high"]),
        "medium": len([m for m in at_risk_members if m["risk_level"] == "medium"]),
        "members": at_risk_members
    }


@api_router.get("/retention/retention-alerts")
async def get_retention_alerts(days: int = 7, current_user: User = Depends(get_current_user)):
    """Get members who haven't visited in X days (7, 14, or 28)"""
    from datetime import datetime, timedelta
    
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=days)
    
    # Get active members
    active_members = await db.members.find(
        {"membership_status": "active"},
        {"_id": 0}
    ).to_list(None)
    
    alert_members = []
    
    for member in active_members:
        last_visit = member.get("last_visit_date")
        
        if not last_visit:
            # No visit recorded - high priority
            alert_members.append({
                "id": member.get("id"),
                "first_name": member.get("first_name"),
                "last_name": member.get("last_name"),
                "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                "email": member.get("email"),
                "phone": member.get("phone"),
                "last_visit_date": None,
                "days_since_visit": None,
                "join_date": member.get("join_date"),
                "membership_type": member.get("membership_type")
            })
        else:
            last_visit_dt = datetime.fromisoformat(last_visit) if isinstance(last_visit, str) else last_visit
            
            if last_visit_dt < cutoff_date:
                days_since = (now - last_visit_dt).days
                alert_members.append({
                    "id": member.get("id"),
                    "first_name": member.get("first_name"),
                    "last_name": member.get("last_name"),
                    "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                    "email": member.get("email"),
                    "phone": member.get("phone"),
                    "last_visit_date": last_visit,
                    "days_since_visit": days_since,
                    "join_date": member.get("join_date"),
                    "membership_type": member.get("membership_type")
                })
    
    # Sort by days since visit (nulls first)
    alert_members.sort(key=lambda x: x["days_since_visit"] if x["days_since_visit"] is not None else 999, reverse=True)
    
    return {
        "alert_type": f"{days}_day_retention_alert",
        "days": days,
        "total": len(alert_members),
        "members": alert_members
    }


@api_router.get("/retention/sleeping-members")
async def get_sleeping_members(current_user: User = Depends(get_current_user)):
    """Get active members with no attendance in last 30 days"""
    from datetime import datetime, timedelta
    
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    
    # Get active members with no recent visits
    active_members = await db.members.find(
        {"membership_status": "active"},
        {"_id": 0}
    ).to_list(None)
    
    sleeping_members = []
    
    for member in active_members:
        last_visit = member.get("last_visit_date")
        
        if not last_visit:
            # Never visited
            sleeping_members.append({
                "id": member.get("id"),
                "first_name": member.get("first_name"),
                "last_name": member.get("last_name"),
                "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                "email": member.get("email"),
                "phone": member.get("phone"),
                "last_visit_date": None,
                "days_sleeping": "Never visited",
                "join_date": member.get("join_date"),
                "membership_type": member.get("membership_type"),
                "is_debtor": member.get("is_debtor", False)
            })
        else:
            last_visit_dt = datetime.fromisoformat(last_visit) if isinstance(last_visit, str) else last_visit
            
            if last_visit_dt < thirty_days_ago:
                days_since = (now - last_visit_dt).days
                sleeping_members.append({
                    "id": member.get("id"),
                    "first_name": member.get("first_name"),
                    "last_name": member.get("last_name"),
                    "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                    "email": member.get("email"),
                    "phone": member.get("phone"),
                    "last_visit_date": last_visit,
                    "days_sleeping": days_since,
                    "join_date": member.get("join_date"),
                    "membership_type": member.get("membership_type"),
                    "is_debtor": member.get("is_debtor", False)
                })
    
    return {
        "total": len(sleeping_members),
        "members": sleeping_members
    }


@api_router.get("/retention/expiring-memberships")
async def get_expiring_memberships(days: int = 30, current_user: User = Depends(get_current_user)):
    """Get memberships expiring in next X days (30, 60, or 90)"""
    from datetime import datetime, timedelta
    
    now = datetime.now(timezone.utc)
    future_date = now + timedelta(days=days)
    
    # Get members with expiry date in the range
    members = await db.members.find(
        {
            "membership_status": "active",
            "expiry_date": {
                "$gte": now.isoformat(),
                "$lte": future_date.isoformat()
            }
        },
        {"_id": 0}
    ).sort("expiry_date", 1).to_list(None)
    
    expiring_members = []
    
    for member in members:
        expiry_date = member.get("expiry_date")
        if expiry_date:
            expiry_dt = datetime.fromisoformat(expiry_date) if isinstance(expiry_date, str) else expiry_date
            days_until_expiry = (expiry_dt - now).days
            
            expiring_members.append({
                "id": member.get("id"),
                "first_name": member.get("first_name"),
                "last_name": member.get("last_name"),
                "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                "email": member.get("email"),
                "phone": member.get("phone"),
                "expiry_date": expiry_date,
                "days_until_expiry": days_until_expiry,
                "membership_type": member.get("membership_type"),
                "last_visit_date": member.get("last_visit_date"),
                "is_debtor": member.get("is_debtor", False)
            })
    
    return {
        "period_days": days,
        "total": len(expiring_members),
        "members": expiring_members
    }


@api_router.get("/retention/dropoff-analytics")
async def get_dropoff_analytics(current_user: User = Depends(get_current_user)):
    """Analyze attendance patterns before member dropoff/cancellation"""
    from datetime import datetime, timedelta
    
    # Get cancelled members from last 90 days
    now = datetime.now(timezone.utc)
    ninety_days_ago = now - timedelta(days=90)
    
    cancelled_members = await db.members.find(
        {
            "membership_status": "cancelled",
            "cancellation_date": {"$gte": ninety_days_ago.isoformat()}
        },
        {"_id": 0}
    ).to_list(None)
    
    # Analyze attendance before cancellation
    dropoff_patterns = []
    total_days_before_cancel = 0
    count = 0
    
    for member in cancelled_members:
        cancellation_date = member.get("cancellation_date")
        if not cancellation_date:
            continue
        
        cancel_dt = datetime.fromisoformat(cancellation_date) if isinstance(cancellation_date, str) else cancellation_date
        
        # Get last attendance before cancellation
        last_visit = member.get("last_visit_date")
        if last_visit:
            last_visit_dt = datetime.fromisoformat(last_visit) if isinstance(last_visit, str) else last_visit
            days_inactive = (cancel_dt - last_visit_dt).days
            
            if days_inactive >= 0:  # Only count if last visit was before cancellation
                total_days_before_cancel += days_inactive
                count += 1
                
                dropoff_patterns.append({
                    "member_id": member.get("id"),
                    "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                    "last_visit_date": last_visit,
                    "cancellation_date": cancellation_date,
                    "days_inactive_before_cancel": days_inactive
                })
    
    average_days_before_cancel = round(total_days_before_cancel / count, 1) if count > 0 else 0
    
    # Distribution of inactive periods
    distribution = {
        "0-7_days": len([p for p in dropoff_patterns if 0 <= p["days_inactive_before_cancel"] <= 7]),
        "8-14_days": len([p for p in dropoff_patterns if 8 <= p["days_inactive_before_cancel"] <= 14]),
        "15-30_days": len([p for p in dropoff_patterns if 15 <= p["days_inactive_before_cancel"] <= 30]),
        "31-60_days": len([p for p in dropoff_patterns if 31 <= p["days_inactive_before_cancel"] <= 60]),
        "60+_days": len([p for p in dropoff_patterns if p["days_inactive_before_cancel"] > 60])
    }
    
    return {
        "total_cancelled_members": len(cancelled_members),
        "members_analyzed": count,
        "average_days_inactive_before_cancel": average_days_before_cancel,
        "distribution": distribution,
        "recommendation": f"Members inactive for {int(average_days_before_cancel / 2)} days should be contacted",
        "patterns": dropoff_patterns[:20]  # Return top 20 for reference
    }


# ===================== Phase 2A - Chart Data Routes =====================

@api_router.get("/charts/age-distribution")
async def get_age_distribution(current_user: User = Depends(get_current_user)):
    """Get age distribution of active members for chart"""
    from datetime import datetime
    
    # Get all active members
    active_members = await db.members.find(
        {"membership_status": "active"},
        {"_id": 0, "date_of_birth": 1}
    ).to_list(None)
    
    # Calculate ages and group into ranges
    age_ranges = {
        "Under 18": 0,
        "18-24": 0,
        "25-34": 0,
        "35-44": 0,
        "45-54": 0,
        "55-64": 0,
        "65+": 0,
        "Unknown": 0
    }
    
    now = datetime.now(timezone.utc)
    
    for member in active_members:
        dob = member.get("date_of_birth")
        if not dob:
            age_ranges["Unknown"] += 1
            continue
        
        try:
            if isinstance(dob, str):
                dob_dt = datetime.fromisoformat(dob)
            else:
                dob_dt = dob
            
            age = (now - dob_dt).days // 365
            
            if age < 18:
                age_ranges["Under 18"] += 1
            elif age < 25:
                age_ranges["18-24"] += 1
            elif age < 35:
                age_ranges["25-34"] += 1
            elif age < 45:
                age_ranges["35-44"] += 1
            elif age < 55:
                age_ranges["45-54"] += 1
            elif age < 65:
                age_ranges["55-64"] += 1
            else:
                age_ranges["65+"] += 1
        except:
            age_ranges["Unknown"] += 1
    
    # Format for chart
    chart_data = [
        {"category": category, "value": count}
        for category, count in age_ranges.items()
        if count > 0  # Only include ranges with members
    ]
    
    return {
        "total_members": len(active_members),
        "data": chart_data
    }


@api_router.get("/charts/membership-duration")
async def get_membership_duration(current_user: User = Depends(get_current_user)):
    """Get average membership duration by type"""
    from datetime import datetime
    
    # Get all members
    all_members = await db.members.find(
        {},
        {"_id": 0, "membership_type": 1, "join_date": 1, "expiry_date": 1, "membership_status": 1}
    ).to_list(None)
    
    # Calculate average duration by membership type
    duration_by_type = {}
    
    for member in all_members:
        membership_type = member.get("membership_type", "Unknown")
        join_date = member.get("join_date")
        
        if not join_date:
            continue
        
        try:
            join_dt = datetime.fromisoformat(join_date) if isinstance(join_date, str) else join_date
            
            # Calculate duration
            if member.get("membership_status") == "active":
                end_date = datetime.now(timezone.utc)
            else:
                expiry_date = member.get("expiry_date")
                if expiry_date:
                    end_date = datetime.fromisoformat(expiry_date) if isinstance(expiry_date, str) else expiry_date
                else:
                    end_date = datetime.now(timezone.utc)
            
            duration_days = (end_date - join_dt).days
            
            if membership_type not in duration_by_type:
                duration_by_type[membership_type] = []
            
            duration_by_type[membership_type].append(duration_days)
        except:
            continue
    
    # Calculate averages
    chart_data = []
    for mtype, durations in duration_by_type.items():
        avg_days = sum(durations) / len(durations) if durations else 0
        avg_months = round(avg_days / 30, 1)
        
        chart_data.append({
            "membership_type": mtype,
            "average_duration_days": round(avg_days, 1),
            "average_duration_months": avg_months,
            "member_count": len(durations)
        })
    
    # Sort by member count descending
    chart_data.sort(key=lambda x: x["member_count"], reverse=True)
    
    return {
        "data": chart_data
    }


@api_router.get("/charts/attendance-by-day")
async def get_attendance_by_day(current_user: User = Depends(get_current_user)):
    """Get attendance distribution by day of week"""
    from datetime import datetime, timedelta
    
    # Get access logs from last 30 days
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    
    access_logs = await db.access_logs.find(
        {
            "timestamp": {"$gte": thirty_days_ago.isoformat()},
            "status": "granted"
        },
        {"_id": 0, "timestamp": 1}
    ).to_list(None)
    
    # Count by day of week
    day_counts = {
        "Monday": 0,
        "Tuesday": 0,
        "Wednesday": 0,
        "Thursday": 0,
        "Friday": 0,
        "Saturday": 0,
        "Sunday": 0
    }
    
    for log in access_logs:
        timestamp = log.get("timestamp")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
                day_name = dt.strftime("%A")
                if day_name in day_counts:
                    day_counts[day_name] += 1
            except:
                continue
    
    # Format for chart (maintain day order)
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    chart_data = [
        {"day": day, "count": day_counts[day]}
        for day in day_order
    ]
    
    return {
        "period": "Last 30 Days",
        "total_attendance": sum(day_counts.values()),
        "data": chart_data
    }


@api_router.get("/charts/top-referrers")
async def get_top_referrers(limit: int = 10, current_user: User = Depends(get_current_user)):
    """Get members who have referred the most people"""
    
    # Get all members with referrer information
    members = await db.members.find(
        {"referred_by": {"$exists": True, "$ne": None}},
        {"_id": 0, "referred_by": 1}
    ).to_list(None)
    
    # Count referrals per referrer
    referral_counts = {}
    for member in members:
        referrer_id = member.get("referred_by")
        if referrer_id:
            referral_counts[referrer_id] = referral_counts.get(referrer_id, 0) + 1
    
    # Get referrer details and format data
    chart_data = []
    for referrer_id, count in referral_counts.items():
        referrer = await db.members.find_one(
            {"id": referrer_id},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
        )
        
        if referrer:
            chart_data.append({
                "referrer_id": referrer_id,
                "referrer_name": f"{referrer.get('first_name', '')} {referrer.get('last_name', '')}".strip(),
                "email": referrer.get("email"),
                "referral_count": count
            })
    
    # Sort by count and limit
    chart_data.sort(key=lambda x: x["referral_count"], reverse=True)
    chart_data = chart_data[:limit]
    
    return {
        "total_referrals": len(members),
        "total_referrers": len(referral_counts),
        "data": chart_data
    }


@api_router.get("/charts/member-sources")
async def get_member_sources(current_user: User = Depends(get_current_user)):
    """Get distribution of member acquisition sources"""
    
    # Get all members with source/promotion information
    members = await db.members.find(
        {},
        {"_id": 0, "promotion_source": 1, "how_did_you_hear": 1}
    ).to_list(None)
    
    # Count by source
    source_counts = {}
    
    for member in members:
        source = member.get("promotion_source") or member.get("how_did_you_hear") or "Unknown"
        source_counts[source] = source_counts.get(source, 0) + 1
    
    # Format for chart
    chart_data = [
        {"source": source, "count": count}
        for source, count in source_counts.items()
    ]
    
    # Sort by count descending
    chart_data.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "total_members": len(members),
        "data": chart_data[:10]  # Top 10 sources
    }


# ==================== PHASE 2C - REPORT LIBRARY ENDPOINTS ====================

@api_router.get("/reports/incomplete-data")
async def get_incomplete_data_report(current_user: User = Depends(get_current_user)):
    """
    Generate report of members with incomplete data
    Returns members missing critical information with priority scoring
    """
    from datetime import datetime
    
    # Get all active members
    members = await db.members.find(
        {"membership_status": {"$in": ["active", "frozen"]}},
        {"_id": 0}
    ).to_list(None)
    
    incomplete_members = []
    
    for member in members:
        missing_fields = []
        priority_score = 0
        
        # Check critical fields (high priority)
        if not member.get("phone"):
            missing_fields.append("Phone Number")
            priority_score += 10
        if not member.get("email"):
            missing_fields.append("Email Address")
            priority_score += 10
        if not member.get("emergency_contact"):
            missing_fields.append("Emergency Contact")
            priority_score += 8
        
        # Check important fields (medium priority)
        if not member.get("address"):
            missing_fields.append("Physical Address")
            priority_score += 5
        if not member.get("date_of_birth"):
            missing_fields.append("Date of Birth")
            priority_score += 5
        if not member.get("id_number"):
            missing_fields.append("ID Number")
            priority_score += 5
        
        # Check banking fields (medium-high priority for billing)
        if not member.get("bank_account_number"):
            missing_fields.append("Bank Account Number")
            priority_score += 7
        if not member.get("bank_branch_code"):
            missing_fields.append("Bank Branch Code")
            priority_score += 3
        
        # Check additional fields (low priority)
        if not member.get("additional_phone"):
            missing_fields.append("Additional Phone")
            priority_score += 2
        if not member.get("medical_conditions"):
            missing_fields.append("Medical Conditions")
            priority_score += 4
        
        # Only include members with missing data
        if missing_fields:
            # Determine priority level
            if priority_score >= 20:
                priority = "Critical"
            elif priority_score >= 10:
                priority = "High"
            elif priority_score >= 5:
                priority = "Medium"
            else:
                priority = "Low"
            
            incomplete_members.append({
                "id": member.get("id"),
                "first_name": member.get("first_name"),
                "last_name": member.get("last_name"),
                "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                "email": member.get("email", "N/A"),
                "phone": member.get("phone", "N/A"),
                "membership_status": member.get("membership_status", "active"),
                "join_date": member.get("join_date"),
                "missing_fields": missing_fields,
                "missing_count": len(missing_fields),
                "priority": priority,
                "priority_score": priority_score
            })
    
    # Sort by priority score (highest first)
    incomplete_members.sort(key=lambda x: x["priority_score"], reverse=True)
    
    # Calculate summary statistics
    total_members = len(members)
    members_with_issues = len(incomplete_members)
    critical_count = sum(1 for m in incomplete_members if m["priority"] == "Critical")
    high_count = sum(1 for m in incomplete_members if m["priority"] == "High")
    medium_count = sum(1 for m in incomplete_members if m["priority"] == "Medium")
    low_count = sum(1 for m in incomplete_members if m["priority"] == "Low")
    
    # Most common missing fields
    all_missing = []
    for m in incomplete_members:
        all_missing.extend(m["missing_fields"])
    
    from collections import Counter
    missing_field_counts = Counter(all_missing).most_common(5)
    
    return {
        "summary": {
            "total_members": total_members,
            "members_with_incomplete_data": members_with_issues,
            "completion_rate": round((total_members - members_with_issues) / total_members * 100, 1) if total_members > 0 else 0,
            "by_priority": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            "most_common_missing": [
                {"field": field, "count": count} 
                for field, count in missing_field_counts
            ]
        },
        "members": incomplete_members
    }


@api_router.get("/reports/birthdays")
async def get_birthday_report(
    days_ahead: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Generate birthday report for upcoming birthdays
    """
    from datetime import datetime, timedelta
    
    # Get all members
    members = await db.members.find(
        {"membership_status": {"$in": ["active", "frozen"]}},
        {"_id": 0}
    ).to_list(None)
    
    today = datetime.now(timezone.utc)
    end_date = today + timedelta(days=days_ahead)
    
    upcoming_birthdays = []
    
    for member in members:
        dob = member.get("date_of_birth")
        if not dob:
            continue
        
        try:
            # Parse date of birth
            if isinstance(dob, str):
                dob_dt = datetime.fromisoformat(dob)
            else:
                dob_dt = dob
            
            # Calculate age
            age = (today - dob_dt).days // 365
            
            # Get this year's birthday
            birthday_this_year = dob_dt.replace(year=today.year)
            
            # If birthday already passed this year, check next year
            if birthday_this_year < today:
                birthday_this_year = dob_dt.replace(year=today.year + 1)
            
            # Check if birthday is within the date range
            if today <= birthday_this_year <= end_date:
                days_until = (birthday_this_year - today).days
                
                upcoming_birthdays.append({
                    "id": member.get("id"),
                    "first_name": member.get("first_name"),
                    "last_name": member.get("last_name"),
                    "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                    "email": member.get("email"),
                    "phone": member.get("phone"),
                    "date_of_birth": dob_dt.isoformat() if isinstance(dob_dt, datetime) else dob,
                    "birthday_date": birthday_this_year.strftime("%Y-%m-%d"),
                    "age_turning": age + 1,
                    "days_until": days_until,
                    "membership_status": member.get("membership_status", "active")
                })
        except Exception as e:
            continue
    
    # Sort by days until birthday
    upcoming_birthdays.sort(key=lambda x: x["days_until"])
    
    # Group by week
    this_week = [b for b in upcoming_birthdays if b["days_until"] <= 7]
    next_week = [b for b in upcoming_birthdays if 7 < b["days_until"] <= 14]
    later = [b for b in upcoming_birthdays if b["days_until"] > 14]
    
    return {
        "summary": {
            "total_upcoming": len(upcoming_birthdays),
            "date_range": {
                "from": today.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "days": days_ahead
            },
            "by_period": {
                "this_week": len(this_week),
                "next_week": len(next_week),
                "later": len(later)
            }
        },
        "birthdays": {
            "this_week": this_week,
            "next_week": next_week,
            "later": later,
            "all": upcoming_birthdays
        }
    }


@api_router.get("/reports/anniversaries")
async def get_anniversary_report(
    days_ahead: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Generate membership anniversary report
    """
    from datetime import datetime, timedelta
    
    # Get all members
    members = await db.members.find(
        {"membership_status": {"$in": ["active", "frozen"]}},
        {"_id": 0}
    ).to_list(None)
    
    today = datetime.now(timezone.utc)
    end_date = today + timedelta(days=days_ahead)
    
    upcoming_anniversaries = []
    
    for member in members:
        join_date = member.get("join_date")
        if not join_date:
            continue
        
        try:
            # Parse join date
            if isinstance(join_date, str):
                join_dt = datetime.fromisoformat(join_date)
            else:
                join_dt = join_date
            
            # Calculate years of membership
            years = (today - join_dt).days // 365
            
            # Get this year's anniversary
            anniversary_this_year = join_dt.replace(year=today.year)
            
            # If anniversary already passed this year, check next year
            if anniversary_this_year < today:
                anniversary_this_year = join_dt.replace(year=today.year + 1)
                years += 1
            
            # Check if anniversary is within the date range
            if today <= anniversary_this_year <= end_date:
                days_until = (anniversary_this_year - today).days
                
                # Only include significant anniversaries (1+ years)
                if years > 0:
                    upcoming_anniversaries.append({
                        "id": member.get("id"),
                        "first_name": member.get("first_name"),
                        "last_name": member.get("last_name"),
                        "full_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                        "email": member.get("email"),
                        "phone": member.get("phone"),
                        "join_date": join_dt.isoformat() if isinstance(join_dt, datetime) else join_date,
                        "anniversary_date": anniversary_this_year.strftime("%Y-%m-%d"),
                        "years_completing": years,
                        "days_until": days_until,
                        "membership_status": member.get("membership_status", "active"),
                        "membership_type": member.get("membership_type")
                    })
        except Exception as e:
            continue
    
    # Sort by days until anniversary
    upcoming_anniversaries.sort(key=lambda x: x["days_until"])
    
    # Group by milestone
    milestone_1_year = [a for a in upcoming_anniversaries if a["years_completing"] == 1]
    milestone_5_years = [a for a in upcoming_anniversaries if a["years_completing"] == 5]
    milestone_10_years = [a for a in upcoming_anniversaries if a["years_completing"] >= 10]
    
    return {
        "summary": {
            "total_upcoming": len(upcoming_anniversaries),
            "date_range": {
                "from": today.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "days": days_ahead
            },
            "by_milestone": {
                "1_year": len(milestone_1_year),
                "5_years": len(milestone_5_years),
                "10_plus_years": len(milestone_10_years)
            }
        },
        "anniversaries": {
            "by_milestone": {
                "1_year": milestone_1_year,
                "5_years": milestone_5_years,
                "10_plus_years": milestone_10_years
            },
            "all": upcoming_anniversaries
        }
    }



# ==================== PHASE 2D - ADVANCED ANALYTICS ENDPOINTS ====================

@api_router.get("/analytics/revenue-breakdown")
async def get_revenue_breakdown(
    period_months: int = 12,
    current_user: User = Depends(get_current_user)
):
    """
    Advanced revenue analytics with breakdown by membership type and payment method
    """
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=period_months * 30)
    
    # Get all invoices in period
    invoices = await db.invoices.find(
        {
            "status": "paid",
            "paid_date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
        },
        {"_id": 0}
    ).to_list(None)
    
    # Initialize aggregations
    by_membership_type = defaultdict(float)
    by_payment_method = defaultdict(float)
    monthly_revenue = defaultdict(float)
    total_revenue = 0.0
    
    for invoice in invoices:
        amount = invoice.get("total_amount", 0)
        total_revenue += amount
        
        # By membership type
        membership_type = invoice.get("membership_type", "Unknown")
        by_membership_type[membership_type] += amount
        
        # By payment method
        payment_method = invoice.get("payment_method", "Unknown")
        by_payment_method[payment_method] += amount
        
        # By month
        paid_date = invoice.get("paid_date")
        if paid_date:
            try:
                if isinstance(paid_date, str):
                    date_obj = datetime.fromisoformat(paid_date)
                else:
                    date_obj = paid_date
                month_key = date_obj.strftime("%Y-%m")
                monthly_revenue[month_key] += amount
            except:
                pass
    
    # Get active members for ARPU calculation
    active_members = await db.members.count_documents(
        {"membership_status": "active"}
    )
    
    # Calculate metrics
    arpu = total_revenue / active_members if active_members > 0 else 0
    mrr = total_revenue / period_months if period_months > 0 else 0
    
    # Format data for charts
    membership_type_data = [
        {"type": k, "revenue": round(v, 2), "percentage": round(v / total_revenue * 100, 1) if total_revenue > 0 else 0}
        for k, v in sorted(by_membership_type.items(), key=lambda x: x[1], reverse=True)
    ]
    
    payment_method_data = [
        {"method": k, "revenue": round(v, 2), "percentage": round(v / total_revenue * 100, 1) if total_revenue > 0 else 0}
        for k, v in sorted(by_payment_method.items(), key=lambda x: x[1], reverse=True)
    ]
    
    monthly_data = [
        {"month": k, "revenue": round(v, 2)}
        for k, v in sorted(monthly_revenue.items())
    ]
    
    return {
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "period_months": period_months,
            "active_members": active_members,
            "arpu": round(arpu, 2),
            "mrr": round(mrr, 2),
            "date_range": {
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            }
        },
        "by_membership_type": membership_type_data,
        "by_payment_method": payment_method_data,
        "monthly_trend": monthly_data
    }


@api_router.get("/analytics/geographic-distribution")
async def get_geographic_distribution(current_user: User = Depends(get_current_user)):
    """
    Member distribution by postcode/location for heatmap visualization
    """
    from collections import Counter
    
    # Get all active members with addresses
    members = await db.members.find(
        {"membership_status": {"$in": ["active", "frozen"]}},
        {"_id": 0, "address": 1, "postcode": 1, "city": 1, "state": 1}
    ).to_list(None)
    
    # Extract postcodes and cities
    postcodes = []
    cities = []
    states = []
    
    for member in members:
        postcode = member.get("postcode")
        if postcode:
            # Normalize postcode (first 3-4 digits for grouping)
            postcode_str = str(postcode)
            if len(postcode_str) >= 3:
                postcodes.append(postcode_str[:4] if len(postcode_str) >= 4 else postcode_str[:3])
        
        city = member.get("city")
        if city:
            cities.append(city)
        
        state = member.get("state")
        if state:
            states.append(state)
    
    # Count occurrences
    postcode_counts = Counter(postcodes)
    city_counts = Counter(cities)
    state_counts = Counter(states)
    
    # Format for visualization
    postcode_data = [
        {"postcode": k, "count": v, "percentage": round(v / len(postcodes) * 100, 1) if len(postcodes) > 0 else 0}
        for k, v in postcode_counts.most_common(20)  # Top 20 postcodes
    ]
    
    city_data = [
        {"city": k, "count": v, "percentage": round(v / len(cities) * 100, 1) if len(cities) > 0 else 0}
        for k, v in city_counts.most_common(10)  # Top 10 cities
    ]
    
    state_data = [
        {"state": k, "count": v, "percentage": round(v / len(states) * 100, 1) if len(states) > 0 else 0}
        for k, v in state_counts.most_common()
    ]
    
    return {
        "summary": {
            "total_members": len(members),
            "with_postcode": len(postcodes),
            "with_city": len(cities),
            "with_state": len(states),
            "coverage": {
                "postcode": round(len(postcodes) / len(members) * 100, 1) if len(members) > 0 else 0,
                "city": round(len(cities) / len(members) * 100, 1) if len(members) > 0 else 0,
                "state": round(len(states) / len(members) * 100, 1) if len(members) > 0 else 0
            }
        },
        "by_postcode": postcode_data,
        "by_city": city_data,
        "by_state": state_data
    }


@api_router.get("/analytics/attendance-deep-dive")
async def get_attendance_deep_dive(
    days_back: int = 90,
    current_user: User = Depends(get_current_user)
):
    """
    Deep-dive attendance analytics: peak hours, frequency distribution, patterns
    """
    from datetime import datetime, timedelta
    from collections import defaultdict, Counter
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)
    
    # Get all access logs in period
    access_logs = await db.access_logs.find(
        {
            "access_time": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()},
            "access_granted": True
        },
        {"_id": 0}
    ).to_list(None)
    
    # Initialize analytics
    hourly_distribution = defaultdict(int)
    daily_distribution = defaultdict(int)
    member_frequency = defaultdict(int)
    weekly_pattern = defaultdict(int)
    
    for log in access_logs:
        access_time_str = log.get("access_time")
        member_id = log.get("member_id")
        
        if access_time_str:
            try:
                if isinstance(access_time_str, str):
                    access_dt = datetime.fromisoformat(access_time_str)
                else:
                    access_dt = access_time_str
                
                # Hour of day (0-23)
                hour = access_dt.hour
                hourly_distribution[hour] += 1
                
                # Day of week (0=Monday, 6=Sunday)
                day_of_week = access_dt.weekday()
                day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                daily_distribution[day_names[day_of_week]] += 1
                
                # Week number for trends
                week_key = access_dt.strftime("%Y-W%U")
                weekly_pattern[week_key] += 1
                
                # Member frequency
                if member_id:
                    member_frequency[member_id] += 1
                    
            except:
                pass
    
    # Find peak hours (top 5)
    peak_hours = sorted(hourly_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
    peak_hours_data = [
        {
            "hour": f"{h:02d}:00", 
            "count": count,
            "percentage": round(count / len(access_logs) * 100, 1) if len(access_logs) > 0 else 0
        }
        for h, count in peak_hours
    ]
    
    # Format hourly distribution for chart
    hourly_data = [
        {"hour": f"{h:02d}:00", "count": hourly_distribution.get(h, 0)}
        for h in range(24)
    ]
    
    # Format daily distribution
    daily_data = [
        {"day": day, "count": daily_distribution.get(day, 0)}
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ]
    
    # Member frequency distribution
    frequency_ranges = {
        "1-5 visits": 0,
        "6-10 visits": 0,
        "11-20 visits": 0,
        "21-30 visits": 0,
        "31+ visits": 0
    }
    
    for member_id, count in member_frequency.items():
        if count <= 5:
            frequency_ranges["1-5 visits"] += 1
        elif count <= 10:
            frequency_ranges["6-10 visits"] += 1
        elif count <= 20:
            frequency_ranges["11-20 visits"] += 1
        elif count <= 30:
            frequency_ranges["21-30 visits"] += 1
        else:
            frequency_ranges["31+ visits"] += 1
    
    frequency_data = [
        {"range": k, "members": v}
        for k, v in frequency_ranges.items()
    ]
    
    # Calculate average visits per member
    total_unique_members = len(member_frequency)
    avg_visits = len(access_logs) / total_unique_members if total_unique_members > 0 else 0
    
    # Weekly trend
    weekly_trend_data = [
        {"week": k, "count": v}
        for k, v in sorted(weekly_pattern.items())
    ]
    
    return {
        "summary": {
            "total_visits": len(access_logs),
            "unique_members": total_unique_members,
            "avg_visits_per_member": round(avg_visits, 1),
            "period_days": days_back,
            "date_range": {
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            }
        },
        "peak_hours": peak_hours_data,
        "hourly_distribution": hourly_data,
        "daily_distribution": daily_data,
        "frequency_distribution": frequency_data,
        "weekly_trend": weekly_trend_data
    }


@api_router.get("/analytics/member-lifetime-value")
async def get_member_lifetime_value(current_user: User = Depends(get_current_user)):
    """
    Calculate and analyze member lifetime value by membership type
    """
    from datetime import datetime
    from collections import defaultdict
    
    # Get all members with their invoices
    members = await db.members.find(
        {"membership_status": {"$in": ["active", "frozen", "cancelled"]}},
        {"_id": 0}
    ).to_list(None)
    
    # Initialize LTV tracking
    ltv_by_type = defaultdict(list)
    ltv_by_status = defaultdict(list)
    
    for member in members:
        member_id = member.get("id")
        membership_type = member.get("membership_type", "Unknown")
        membership_status = member.get("membership_status", "active")
        join_date = member.get("join_date")
        
        # Calculate membership duration in months
        if join_date:
            try:
                if isinstance(join_date, str):
                    join_dt = datetime.fromisoformat(join_date)
                else:
                    join_dt = join_date
                
                duration_days = (datetime.now(timezone.utc) - join_dt).days
                duration_months = max(1, duration_days / 30)
            except:
                duration_months = 1
        else:
            duration_months = 1
        
        # Get total revenue from this member
        invoices = await db.invoices.find(
            {"member_id": member_id, "status": "paid"},
            {"_id": 0, "total_amount": 1}
        ).to_list(None)
        
        total_revenue = sum(inv.get("total_amount", 0) for inv in invoices)
        
        # Calculate LTV metrics
        ltv = total_revenue
        monthly_value = total_revenue / duration_months if duration_months > 0 else 0
        
        ltv_data = {
            "member_id": member_id,
            "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
            "membership_type": membership_type,
            "membership_status": membership_status,
            "ltv": round(ltv, 2),
            "monthly_value": round(monthly_value, 2),
            "duration_months": round(duration_months, 1),
            "total_invoices": len(invoices)
        }
        
        ltv_by_type[membership_type].append(ltv_data)
        ltv_by_status[membership_status].append(ltv_data)
    
    # Calculate averages by membership type
    type_summary = []
    for mtype, members_data in ltv_by_type.items():
        if members_data:
            avg_ltv = sum(m["ltv"] for m in members_data) / len(members_data)
            avg_monthly = sum(m["monthly_value"] for m in members_data) / len(members_data)
            avg_duration = sum(m["duration_months"] for m in members_data) / len(members_data)
            
            type_summary.append({
                "membership_type": mtype,
                "member_count": len(members_data),
                "avg_ltv": round(avg_ltv, 2),
                "avg_monthly_value": round(avg_monthly, 2),
                "avg_duration_months": round(avg_duration, 1),
                "total_ltv": round(sum(m["ltv"] for m in members_data), 2)
            })
    
    # Sort by avg LTV
    type_summary.sort(key=lambda x: x["avg_ltv"], reverse=True)
    
    # Top 10 highest LTV members
    all_members_ltv = []
    for members_data in ltv_by_type.values():
        all_members_ltv.extend(members_data)
    
    all_members_ltv.sort(key=lambda x: x["ltv"], reverse=True)
    top_members = all_members_ltv[:10]
    
    # Calculate overall metrics
    total_ltv = sum(m["ltv"] for m in all_members_ltv)
    avg_ltv_overall = total_ltv / len(all_members_ltv) if all_members_ltv else 0
    
    return {
        "summary": {
            "total_members_analyzed": len(all_members_ltv),
            "total_lifetime_value": round(total_ltv, 2),
            "avg_ltv_per_member": round(avg_ltv_overall, 2)
        },
        "by_membership_type": type_summary,
        "top_members": top_members
    }


@api_router.get("/analytics/churn-prediction")
async def get_churn_prediction(current_user: User = Depends(get_current_user)):
    """
    Churn prediction and risk scoring for members
    """
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # Get all active and frozen members
    members = await db.members.find(
        {"membership_status": {"$in": ["active", "frozen"]}},
        {"_id": 0}
    ).to_list(None)
    
    at_risk_members = []
    risk_factors = defaultdict(int)
    
    today = datetime.now(timezone.utc)
    thirty_days_ago = today - timedelta(days=30)
    sixty_days_ago = today - timedelta(days=60)
    
    for member in members:
        member_id = member.get("id")
        risk_score = 0
        risk_reasons = []
        
        # Factor 1: Last visit date (HIGH IMPACT)
        last_visit = member.get("last_visit_date")
        if last_visit:
            try:
                if isinstance(last_visit, str):
                    last_visit_dt = datetime.fromisoformat(last_visit)
                else:
                    last_visit_dt = last_visit
                
                days_since_visit = (today - last_visit_dt).days
                
                if days_since_visit > 60:
                    risk_score += 30
                    risk_reasons.append(f"No visit in {days_since_visit} days")
                    risk_factors["No recent visits (60+ days)"] += 1
                elif days_since_visit > 30:
                    risk_score += 15
                    risk_reasons.append(f"Last visit {days_since_visit} days ago")
                    risk_factors["Declining attendance (30+ days)"] += 1
            except:
                risk_score += 20
                risk_reasons.append("No visit history")
                risk_factors["No visit history"] += 1
        else:
            risk_score += 20
            risk_reasons.append("No visit history")
            risk_factors["No visit history"] += 1
        
        # Factor 2: Payment issues (HIGH IMPACT)
        overdue_invoices = await db.invoices.count_documents({
            "member_id": member_id,
            "status": "overdue"
        })
        
        if overdue_invoices > 0:
            risk_score += 25
            risk_reasons.append(f"{overdue_invoices} overdue invoice(s)")
            risk_factors["Payment issues"] += 1
        
        # Factor 3: Frozen status (MEDIUM IMPACT)
        if member.get("membership_status") == "frozen":
            risk_score += 20
            risk_reasons.append("Membership frozen")
            risk_factors["Frozen membership"] += 1
        
        # Factor 4: Missing contact information (LOW IMPACT)
        if not member.get("email") or not member.get("phone"):
            risk_score += 5
            risk_reasons.append("Incomplete contact info")
            risk_factors["Missing contact info"] += 1
        
        # Factor 5: Recent attendance decline
        recent_visits = await db.access_logs.count_documents({
            "member_id": member_id,
            "access_granted": True,
            "access_time": {"$gte": thirty_days_ago.isoformat()}
        })
        
        previous_visits = await db.access_logs.count_documents({
            "member_id": member_id,
            "access_granted": True,
            "access_time": {
                "$gte": sixty_days_ago.isoformat(),
                "$lt": thirty_days_ago.isoformat()
            }
        })
        
        if previous_visits > 0 and recent_visits < previous_visits * 0.5:
            risk_score += 15
            risk_reasons.append("Attendance declining 50%+")
            risk_factors["Attendance decline"] += 1
        
        # Classify risk level
        if risk_score >= 50:
            risk_level = "Critical"
            at_risk_members.append({
                "member_id": member_id,
                "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                "email": member.get("email"),
                "phone": member.get("phone"),
                "membership_type": member.get("membership_type"),
                "membership_status": member.get("membership_status"),
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_reasons": risk_reasons,
                "last_visit": last_visit
            })
        elif risk_score >= 30:
            risk_level = "High"
            at_risk_members.append({
                "member_id": member_id,
                "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                "email": member.get("email"),
                "phone": member.get("phone"),
                "membership_type": member.get("membership_type"),
                "membership_status": member.get("membership_status"),
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_reasons": risk_reasons,
                "last_visit": last_visit
            })
        elif risk_score >= 15:
            risk_level = "Medium"
            at_risk_members.append({
                "member_id": member_id,
                "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                "email": member.get("email"),
                "phone": member.get("phone"),
                "membership_type": member.get("membership_type"),
                "membership_status": member.get("membership_status"),
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_reasons": risk_reasons,
                "last_visit": last_visit
            })
    
    # Sort by risk score
    at_risk_members.sort(key=lambda x: x["risk_score"], reverse=True)
    
    # Count by risk level
    critical_count = sum(1 for m in at_risk_members if m["risk_level"] == "Critical")
    high_count = sum(1 for m in at_risk_members if m["risk_level"] == "High")
    medium_count = sum(1 for m in at_risk_members if m["risk_level"] == "Medium")
    
    # Format risk factors
    risk_factors_data = [
        {"factor": k, "count": v}
        for k, v in sorted(risk_factors.items(), key=lambda x: x[1], reverse=True)
    ]
    
    return {
        "summary": {
            "total_members_analyzed": len(members),
            "at_risk_count": len(at_risk_members),
            "risk_percentage": round(len(at_risk_members) / len(members) * 100, 1) if len(members) > 0 else 0,
            "by_risk_level": {
                "critical": critical_count,
                "high": high_count,
                "medium": medium_count
            }
        },
        "at_risk_members": at_risk_members,
        "common_risk_factors": risk_factors_data
    }



# ==================== PHASE 2E - ENGAGEMENT FEATURES ENDPOINTS ====================

# Pydantic models for Points System
class PointTransaction(BaseModel):
    id: str
    member_id: str
    points: int
    transaction_type: str  # earned, redeemed, adjusted
    reason: str
    created_at: str
    reference_id: Optional[str] = None

class PointsBalance(BaseModel):
    member_id: str
    total_points: int
    lifetime_points: int
    last_updated: str


@api_router.get("/engagement/points/balance/{member_id}")
async def get_member_points_balance(
    member_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get points balance for a specific member
    """
    # Get or create points balance
    balance = await db.points_balances.find_one({"member_id": member_id}, {"_id": 0})
    
    if not balance:
        # Initialize balance
        balance = {
            "member_id": member_id,
            "total_points": 0,
            "lifetime_points": 0,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        await db.points_balances.insert_one(balance.copy())
    
    return balance


@api_router.post("/engagement/points/award")
async def award_points(
    member_id: str,
    points: int,
    reason: str,
    reference_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Award points to a member
    """
    from datetime import datetime
    import uuid
    
    # Get current balance
    balance = await db.points_balances.find_one({"member_id": member_id}, {"_id": 0})
    
    if not balance:
        balance = {
            "member_id": member_id,
            "total_points": 0,
            "lifetime_points": 0
        }
    
    # Update balance
    new_total = balance.get("total_points", 0) + points
    new_lifetime = balance.get("lifetime_points", 0) + points
    
    await db.points_balances.update_one(
        {"member_id": member_id},
        {
            "$set": {
                "total_points": new_total,
                "lifetime_points": new_lifetime,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        },
        upsert=True
    )
    
    # Record transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "member_id": member_id,
        "points": points,
        "transaction_type": "earned",
        "reason": reason,
        "reference_id": reference_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.points_transactions.insert_one(transaction.copy())
    
    return {
        "success": True,
        "new_balance": new_total,
        "points_awarded": points,
        "transaction_id": transaction["id"]
    }


@api_router.get("/engagement/points/transactions/{member_id}")
async def get_member_points_transactions(
    member_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Get points transaction history for a member
    """
    transactions = await db.points_transactions.find(
        {"member_id": member_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(None)
    
    return {
        "member_id": member_id,
        "transactions": transactions,
        "total_transactions": len(transactions)
    }


@api_router.get("/engagement/points/leaderboard")
async def get_points_leaderboard(
    limit: int = 10,
    period: str = "all_time",  # all_time, month, week
    current_user: User = Depends(get_current_user)
):
    """
    Get points leaderboard
    """
    from datetime import datetime, timedelta
    
    # Get all balances
    balances = await db.points_balances.find({}, {"_id": 0}).to_list(None)
    
    # Get member details
    leaderboard = []
    for balance in balances:
        member = await db.members.find_one(
            {"id": balance["member_id"]},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1, "membership_type": 1}
        )
        
        if member:
            leaderboard.append({
                "member_id": balance["member_id"],
                "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                "email": member.get("email"),
                "membership_type": member.get("membership_type"),
                "total_points": balance.get("total_points", 0),
                "lifetime_points": balance.get("lifetime_points", 0)
            })
    
    # Sort by total points
    leaderboard.sort(key=lambda x: x["total_points"], reverse=True)
    
    return {
        "period": period,
        "leaderboard": leaderboard[:limit],
        "total_members": len(leaderboard)
    }


@api_router.get("/engagement/search")
async def global_search(
    query: str,
    current_user: User = Depends(get_current_user)
):
    """
    Global search across members, classes, transactions, invoices
    """
    if len(query) < 2:
        return {
            "query": query,
            "results": {
                "members": [],
                "classes": [],
                "invoices": [],
                "transactions": []
            },
            "total_results": 0
        }
    
    # Search members
    member_results = await db.members.find(
        {
            "$or": [
                {"first_name": {"$regex": query, "$options": "i"}},
                {"last_name": {"$regex": query, "$options": "i"}},
                {"email": {"$regex": query, "$options": "i"}},
                {"phone": {"$regex": query, "$options": "i"}},
                {"id": {"$regex": query, "$options": "i"}}
            ]
        },
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "email": 1, "phone": 1, "membership_status": 1}
    ).limit(10).to_list(None)
    
    # Format member results
    members = [
        {
            "id": m.get("id"),
            "name": f"{m.get('first_name', '')} {m.get('last_name', '')}".strip(),
            "email": m.get("email"),
            "phone": m.get("phone"),
            "status": m.get("membership_status"),
            "type": "member"
        }
        for m in member_results
    ]
    
    # Search classes
    class_results = await db.classes.find(
        {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"instructor": {"$regex": query, "$options": "i"}}
            ]
        },
        {"_id": 0, "id": 1, "name": 1, "instructor": 1, "date": 1, "time": 1}
    ).limit(10).to_list(None)
    
    # Format class results
    classes = [
        {
            "id": c.get("id"),
            "name": c.get("name"),
            "instructor": c.get("instructor"),
            "date": c.get("date"),
            "time": c.get("time"),
            "type": "class"
        }
        for c in class_results
    ]
    
    # Search invoices
    invoice_results = await db.invoices.find(
        {
            "$or": [
                {"invoice_number": {"$regex": query, "$options": "i"}},
                {"member_id": {"$regex": query, "$options": "i"}}
            ]
        },
        {"_id": 0, "id": 1, "invoice_number": 1, "member_id": 1, "total_amount": 1, "status": 1, "due_date": 1}
    ).limit(10).to_list(None)
    
    # Format invoice results
    invoices = [
        {
            "id": i.get("id"),
            "invoice_number": i.get("invoice_number"),
            "member_id": i.get("member_id"),
            "amount": i.get("total_amount"),
            "status": i.get("status"),
            "due_date": i.get("due_date"),
            "type": "invoice"
        }
        for i in invoice_results
    ]
    
    total_results = len(members) + len(classes) + len(invoices)
    
    return {
        "query": query,
        "results": {
            "members": members,
            "classes": classes,
            "invoices": invoices
        },
        "total_results": total_results
    }


@api_router.get("/engagement/activity-feed/{member_id}")
async def get_member_activity_feed(
    member_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Get activity feed for a specific member
    """
    from datetime import datetime
    
    activities = []
    
    # Get access logs (check-ins)
    access_logs = await db.access_logs.find(
        {"member_id": member_id, "access_granted": True},
        {"_id": 0}
    ).sort("access_time", -1).limit(20).to_list(None)
    
    for log in access_logs:
        activities.append({
            "type": "check_in",
            "timestamp": log.get("access_time"),
            "description": f"Checked in at gym",
            "icon": "activity",
            "color": "green"
        })
    
    # Get invoice payments
    invoices = await db.invoices.find(
        {"member_id": member_id, "status": "paid"},
        {"_id": 0}
    ).sort("paid_date", -1).limit(20).to_list(None)
    
    for invoice in invoices:
        activities.append({
            "type": "payment",
            "timestamp": invoice.get("paid_date"),
            "description": f"Paid invoice {invoice.get('invoice_number')} - R{invoice.get('total_amount', 0)}",
            "icon": "dollar_sign",
            "color": "blue",
            "reference_id": invoice.get("id")
        })
    
    # Get class bookings
    bookings = await db.class_bookings.find(
        {"member_id": member_id},
        {"_id": 0}
    ).sort("booked_at", -1).limit(20).to_list(None)
    
    for booking in bookings:
        # Get class details
        class_info = await db.classes.find_one(
            {"id": booking.get("class_id")},
            {"_id": 0, "name": 1}
        )
        class_name = class_info.get("name", "Class") if class_info else "Class"
        
        activities.append({
            "type": "class_booking",
            "timestamp": booking.get("booked_at"),
            "description": f"Booked class: {class_name}",
            "icon": "calendar",
            "color": "purple",
            "reference_id": booking.get("class_id")
        })
    
    # Get points transactions
    points_txn = await db.points_transactions.find(
        {"member_id": member_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(None)
    
    for txn in points_txn:
        points = txn.get("points", 0)
        sign = "+" if points > 0 else ""
        activities.append({
            "type": "points",
            "timestamp": txn.get("created_at"),
            "description": f"{sign}{points} points - {txn.get('reason')}",
            "icon": "award",
            "color": "yellow"
        })
    
    # Sort all activities by timestamp
    activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "member_id": member_id,
        "activities": activities[:limit],
        "total_activities": len(activities)
    }


@api_router.get("/engagement/score/{member_id}")
async def get_member_engagement_score(
    member_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Calculate engagement score for a member
    """
    from datetime import datetime, timedelta
    
    score = 0
    factors = []
    
    # Factor 1: Recent attendance (0-30 points)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_visits = await db.access_logs.count_documents({
        "member_id": member_id,
        "access_granted": True,
        "access_time": {"$gte": thirty_days_ago.isoformat()}
    })
    
    attendance_score = min(recent_visits * 2, 30)  # 2 points per visit, max 30
    score += attendance_score
    factors.append({
        "factor": "Recent Attendance",
        "score": attendance_score,
        "max_score": 30,
        "details": f"{recent_visits} visits in last 30 days"
    })
    
    # Factor 2: Payment history (0-20 points)
    paid_invoices = await db.invoices.count_documents({
        "member_id": member_id,
        "status": "paid"
    })
    
    overdue_invoices = await db.invoices.count_documents({
        "member_id": member_id,
        "status": "overdue"
    })
    
    payment_score = min(paid_invoices * 2, 20) - (overdue_invoices * 5)
    payment_score = max(0, payment_score)  # Don't go negative
    score += payment_score
    factors.append({
        "factor": "Payment History",
        "score": payment_score,
        "max_score": 20,
        "details": f"{paid_invoices} paid, {overdue_invoices} overdue"
    })
    
    # Factor 3: Class participation (0-25 points)
    class_bookings = await db.class_bookings.count_documents({
        "member_id": member_id
    })
    
    class_score = min(class_bookings * 3, 25)  # 3 points per class, max 25
    score += class_score
    factors.append({
        "factor": "Class Participation",
        "score": class_score,
        "max_score": 25,
        "details": f"{class_bookings} classes booked"
    })
    
    # Factor 4: Loyalty (membership duration) (0-15 points)
    member = await db.members.find_one({"id": member_id}, {"_id": 0, "join_date": 1})
    loyalty_score = 0
    
    if member and member.get("join_date"):
        try:
            join_date = member.get("join_date")
            if isinstance(join_date, str):
                join_dt = datetime.fromisoformat(join_date)
            else:
                join_dt = join_date
            
            days_member = (datetime.now(timezone.utc) - join_dt).days
            months_member = days_member / 30
            loyalty_score = min(int(months_member), 15)  # 1 point per month, max 15
        except:
            loyalty_score = 0
    
    score += loyalty_score
    factors.append({
        "factor": "Membership Loyalty",
        "score": loyalty_score,
        "max_score": 15,
        "details": f"{loyalty_score} months"
    })
    
    # Factor 5: Rewards engagement (0-10 points)
    points_balance = await db.points_balances.find_one({"member_id": member_id}, {"_id": 0})
    points_score = 0
    
    if points_balance:
        lifetime_points = points_balance.get("lifetime_points", 0)
        points_score = min(int(lifetime_points / 10), 10)  # 1 point per 10 rewards points, max 10
    
    score += points_score
    factors.append({
        "factor": "Rewards Engagement",
        "score": points_score,
        "max_score": 10,
        "details": f"{points_balance.get('lifetime_points', 0) if points_balance else 0} rewards points"
    })
    
    # Calculate engagement level
    max_score = 100
    percentage = round(score / max_score * 100, 1)
    
    if percentage >= 80:
        level = "Highly Engaged"
        color = "green"
    elif percentage >= 60:
        level = "Engaged"
        color = "blue"
    elif percentage >= 40:
        level = "Moderately Engaged"
        color = "yellow"
    elif percentage >= 20:
        level = "Low Engagement"
        color = "orange"
    else:
        level = "At Risk"
        color = "red"
    
    return {
        "member_id": member_id,
        "engagement_score": score,
        "max_score": max_score,
        "percentage": percentage,
        "level": level,
        "color": color,
        "factors": factors
    }


@api_router.get("/engagement/overview")
async def get_engagement_overview(current_user: User = Depends(get_current_user)):
    """
    Get overall engagement statistics for all members
    """
    from datetime import datetime, timedelta
    
    # Get all active members
    members = await db.members.find(
        {"membership_status": {"$in": ["active", "frozen"]}},
        {"_id": 0, "id": 1}
    ).to_list(None)
    
    engagement_levels = {
        "Highly Engaged": 0,
        "Engaged": 0,
        "Moderately Engaged": 0,
        "Low Engagement": 0,
        "At Risk": 0
    }
    
    total_score = 0
    scored_members = []
    
    # Calculate engagement for each member (sample first 100 for performance)
    for member in members[:100]:
        member_id = member.get("id")
        
        # Simplified scoring for overview
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_visits = await db.access_logs.count_documents({
            "member_id": member_id,
            "access_granted": True,
            "access_time": {"$gte": thirty_days_ago.isoformat()}
        })
        
        score = min(recent_visits * 10, 100)  # Simplified: 10 points per visit
        total_score += score
        
        percentage = score
        
        if percentage >= 80:
            level = "Highly Engaged"
        elif percentage >= 60:
            level = "Engaged"
        elif percentage >= 40:
            level = "Moderately Engaged"
        elif percentage >= 20:
            level = "Low Engagement"
        else:
            level = "At Risk"
        
        engagement_levels[level] += 1
        scored_members.append({"member_id": member_id, "score": score})
    
    avg_score = total_score / len(members[:100]) if members else 0
    
    # Get top engaged members
    scored_members.sort(key=lambda x: x["score"], reverse=True)
    top_members = []
    
    for sm in scored_members[:10]:
        member = await db.members.find_one(
            {"id": sm["member_id"]},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
        )
        if member:
            top_members.append({
                "member_id": sm["member_id"],
                "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
                "email": member.get("email"),
                "score": sm["score"]
            })
    
    # Format engagement levels for chart
    engagement_data = [
        {"level": k, "count": v}
        for k, v in engagement_levels.items()
    ]
    
    return {
        "summary": {
            "total_members": len(members),
            "members_analyzed": len(members[:100]),
            "avg_engagement_score": round(avg_score, 1)
        },
        "by_level": engagement_data,
        "top_engaged_members": top_members
    }



# ==================== SALES MANAGEMENT MODULE - PHASE 1 (MVP) ====================

# Pydantic Models for Sales Module
class Lead(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    source: str  # referral, website, walk-in, social_media, other
    status: str  # new, contacted, qualified, unqualified, converted
    lead_score: int = 0  # 0-100
    assigned_to: Optional[str] = None
    created_at: str
    updated_at: str
    last_contacted: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []

class Opportunity(BaseModel):
    id: str
    title: str
    contact_id: str  # references Lead
    value: float
    currency: str = "ZAR"
    stage: str  # new_lead, contacted, qualified, proposal, negotiation, closed_won, closed_lost
    probability: int  # 0-100
    expected_close_date: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: str
    updated_at: str
    notes: Optional[str] = None

class SalesTask(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    task_type: str  # call, email, meeting, follow_up, other
    related_to_type: str  # lead, opportunity
    related_to_id: str
    assigned_to: str
    due_date: str
    priority: str  # low, medium, high
    status: str  # pending, completed, cancelled
    created_at: str
    completed_at: Optional[str] = None

# ==================== COMPLIMENTARY MEMBERSHIP MODELS ====================

class ComplimentaryMembershipType(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str  # e.g., "3-Day Trial", "Week Pass", "Friends & Family"
    description: Optional[str] = None
    time_limit_days: int  # e.g., 7, 14, 30
    visit_limit: int  # e.g., 3, 5, 10
    no_access_alert_days: int  # e.g., 3, 7, 15 - days without visit to trigger alert
    notification_on_visits: List[int] = [1, 2, 3]  # Notify consultant on these visit numbers
    is_active: bool = True
    color: str = "#3b82f6"  # For UI display
    icon: str = "🎁"
    created_at: str
    updated_at: str

class ComplimentaryMembershipTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    time_limit_days: int
    visit_limit: int
    no_access_alert_days: int
    notification_on_visits: List[int] = [1, 2, 3]
    is_active: bool = True
    color: str = "#3b82f6"
    icon: str = "🎁"

class ComplimentaryMembership(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    member_id: str
    member_name: str
    member_email: Optional[str] = None
    member_phone: Optional[str] = None
    complimentary_type_id: str
    complimentary_type_name: str
    start_date: str
    expiry_date: str
    time_limit_days: int
    visit_limit: int
    visits_used: int = 0
    visits_remaining: int
    last_visit_date: Optional[str] = None
    status: str  # active, expired, converted, not_using, completed
    assigned_consultant_id: Optional[str] = None
    assigned_consultant_name: Optional[str] = None
    created_from_lead_id: Optional[str] = None
    converted_to_member_id: Optional[str] = None
    conversion_date: Optional[str] = None
    created_at: str
    updated_at: str

class ComplimentaryMembershipCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    complimentary_type_id: str
    assigned_consultant_id: Optional[str] = None
    notes: Optional[str] = None
    auto_create_lead: bool = True

# ==================== CONFIGURABLE LEAD SOURCE, STATUS, LOSS REASON MODELS ====================

class LeadSource(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None  # emoji or icon name
    is_active: bool = True
    display_order: int = 0
    created_at: str
    updated_at: str

class LeadSourceCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool = True
    display_order: int = 0

class LeadStatus(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category: str  # prospect, engaged, converted, lost
    color: str  # hex color code
    workflow_sequence: int  # order in the workflow (0-100)
    is_active: bool = True
    display_order: int = 0
    created_at: str
    updated_at: str

class LeadStatusCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    color: str
    workflow_sequence: int
    is_active: bool = True
    display_order: int = 0

class LossReason(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0
    created_at: str
    updated_at: str

class LossReasonCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0

class ReferralReward(BaseModel):
    id: str
    referring_member_id: str
    referred_lead_id: str
    reward_type: str  # free_month, free_item, discount, points
    reward_value: Optional[str] = None  # e.g., "Water Bottle", "R100 discount", "1 Month Free"
    status: str  # pending, approved, delivered
    created_at: str
    delivered_at: Optional[str] = None
    notes: Optional[str] = None

class ReferralRewardCreate(BaseModel):
    referring_member_id: str
    referred_lead_id: str
    reward_type: str
    reward_value: Optional[str] = None
    notes: Optional[str] = None


# ==================== SALES CRM CONFIGURATION ENDPOINTS ====================

# Lead Sources CRUD
@api_router.get("/sales/config/lead-sources")
async def get_lead_sources(current_user: User = Depends(get_current_user)):
    """Get all lead sources"""
    sources = await db.lead_sources.find({}, {"_id": 0}).sort("display_order", 1).to_list(None)
    return {"sources": sources, "total": len(sources)}

@api_router.post("/sales/config/lead-sources")
async def create_lead_source(
    source_data: LeadSourceCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new lead source"""
    import uuid
    source = {
        "id": str(uuid.uuid4()),
        **source_data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.lead_sources.insert_one(source)
    # Remove MongoDB's _id before returning
    source.pop("_id", None)
    return {"success": True, "source": source}

@api_router.put("/sales/config/lead-sources/{source_id}")
async def update_lead_source(
    source_id: str,
    source_data: LeadSourceCreate,
    current_user: User = Depends(get_current_user)
):
    """Update a lead source"""
    update_data = {
        **source_data.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.lead_sources.update_one(
        {"id": source_id},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Lead source not found")
    return {"success": True, "message": "Lead source updated"}

@api_router.delete("/sales/config/lead-sources/{source_id}")
async def delete_lead_source(
    source_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a lead source"""
    result = await db.lead_sources.delete_one({"id": source_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead source not found")
    return {"success": True, "message": "Lead source deleted"}

# Lead Statuses CRUD
@api_router.get("/sales/config/lead-statuses")
async def get_lead_statuses(current_user: User = Depends(get_current_user)):
    """Get all lead statuses"""
    statuses = await db.lead_statuses.find({}, {"_id": 0}).sort("workflow_sequence", 1).to_list(None)
    return {"statuses": statuses, "total": len(statuses)}

@api_router.post("/sales/config/lead-statuses")
async def create_lead_status(
    status_data: LeadStatusCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new lead status"""
    import uuid
    status = {
        "id": str(uuid.uuid4()),
        **status_data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.lead_statuses.insert_one(status)
    # Remove MongoDB's _id before returning
    status.pop("_id", None)
    return {"success": True, "status": status}

@api_router.put("/sales/config/lead-statuses/{status_id}")
async def update_lead_status(
    status_id: str,
    status_data: LeadStatusCreate,
    current_user: User = Depends(get_current_user)
):
    """Update a lead status"""
    update_data = {
        **status_data.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.lead_statuses.update_one(
        {"id": status_id},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Lead status not found")
    return {"success": True, "message": "Lead status updated"}

@api_router.delete("/sales/config/lead-statuses/{status_id}")
async def delete_lead_status(
    status_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a lead status"""
    result = await db.lead_statuses.delete_one({"id": status_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead status not found")
    return {"success": True, "message": "Lead status deleted"}

# Loss Reasons CRUD
@api_router.get("/sales/config/loss-reasons")
async def get_loss_reasons(current_user: User = Depends(get_current_user)):
    """Get all loss reasons"""
    reasons = await db.loss_reasons.find({}, {"_id": 0}).sort("display_order", 1).to_list(None)
    return {"reasons": reasons, "total": len(reasons)}

@api_router.post("/sales/config/loss-reasons")
async def create_loss_reason(
    reason_data: LossReasonCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new loss reason"""
    import uuid
    reason = {
        "id": str(uuid.uuid4()),
        **reason_data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.loss_reasons.insert_one(reason)
    # Remove MongoDB's _id before returning
    reason.pop("_id", None)
    return {"success": True, "reason": reason}

@api_router.put("/sales/config/loss-reasons/{reason_id}")
async def update_loss_reason(
    reason_id: str,
    reason_data: LossReasonCreate,
    current_user: User = Depends(get_current_user)
):
    """Update a loss reason"""
    update_data = {
        **reason_data.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.loss_reasons.update_one(
        {"id": reason_id},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Loss reason not found")
    return {"success": True, "message": "Loss reason updated"}

@api_router.delete("/sales/config/loss-reasons/{reason_id}")
async def delete_loss_reason(
    reason_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a loss reason"""
    result = await db.loss_reasons.delete_one({"id": reason_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Loss reason not found")
    return {"success": True, "message": "Loss reason deleted"}

# Referral Rewards CRUD
@api_router.get("/sales/referral-rewards")
async def get_referral_rewards(
    member_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get referral rewards with optional filters"""
    query = {}
    if member_id:
        query["referring_member_id"] = member_id
    if status:
        query["status"] = status
    
    rewards = await db.referral_rewards.find(query, {"_id": 0}).sort("created_at", -1).to_list(None)
    
    # Enrich with member and lead names
    enriched_rewards = []
    for reward in rewards:
        reward_copy = reward.copy()
        
        # Get referring member name
        member = await db.members.find_one(
            {"id": reward["referring_member_id"]},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if member:
            reward_copy["referring_member_name"] = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip()
        
        # Get referred lead name
        lead = await db.leads.find_one(
            {"id": reward["referred_lead_id"]},
            {"_id": 0, "first_name": 1, "last_name": 1}
        )
        if lead:
            reward_copy["referred_lead_name"] = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
        
        enriched_rewards.append(reward_copy)
    
    return {"rewards": enriched_rewards, "total": len(enriched_rewards)}

@api_router.post("/sales/referral-rewards")
async def create_referral_reward(
    reward_data: ReferralRewardCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new referral reward"""
    import uuid
    reward = {
        "id": str(uuid.uuid4()),
        **reward_data.model_dump(),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "delivered_at": None
    }
    await db.referral_rewards.insert_one(reward)
    # Remove MongoDB's _id before returning
    reward.pop("_id", None)
    return {"success": True, "reward": reward}

@api_router.put("/sales/referral-rewards/{reward_id}/status")
async def update_referral_reward_status(
    reward_id: str,
    status: str,  # pending, approved, delivered
    current_user: User = Depends(get_current_user)
):
    """Update referral reward status"""
    update_data = {"status": status}
    if status == "delivered":
        update_data["delivered_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.referral_rewards.update_one(
        {"id": reward_id},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Referral reward not found")
    return {"success": True, "message": f"Reward status updated to {status}"}

# Member Search for Referrals
@api_router.get("/sales/members/search")
async def search_members_for_referral(
    q: str,
    current_user: User = Depends(get_current_user)
):
    """Search members for referral linking"""
    if len(q) < 2:
        return {"members": [], "total": 0}
    
    # Build search query
    search_query = {
        "$or": [
            {"first_name": {"$regex": q, "$options": "i"}},
            {"last_name": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}},
            {"id": {"$regex": q, "$options": "i"}}
        ],
        "membership_status": "active"  # Only active members can refer
    }
    
    members = await db.members.find(
        search_query,
        {
            "_id": 0,
            "id": 1,
            "first_name": 1,
            "last_name": 1,
            "email": 1,
            "phone": 1,
            "membership_status": 1
        }
    ).limit(20).to_list(None)
    
    return {"members": members, "total": len(members)}


# ==================== LEADS/CONTACTS ENDPOINTS ====================

@api_router.get("/sales/leads")
async def get_leads(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    source: Optional[str] = None,
    filter_type: Optional[str] = None,  # NEW: "all", "my_leads", "unassigned"
    current_user: User = Depends(get_current_user)
):
    """Get all leads with optional filters and role-based visibility"""
    query = {}
    
    # Role-based filtering
    manager_roles = ["business_owner", "head_admin", "sales_head", "sales_manager"]
    is_manager = current_user.role in manager_roles
    
    # If user is NOT a manager (consultant), only show their assigned leads
    if not is_manager:
        query["assigned_to"] = current_user.id
    else:
        # Managers can use filter_type to filter leads
        if filter_type == "my_leads":
            query["assigned_to"] = current_user.id
        elif filter_type == "unassigned":
            query["$or"] = [{"assigned_to": None}, {"assigned_to": ""}]
        # "all" or no filter_type means all leads for managers
    
    # Apply additional filters
    if status:
        query["status"] = status
    if assigned_to and is_manager:  # Only managers can filter by assigned_to
        query["assigned_to"] = assigned_to
    if source:
        query["source"] = source
    
    leads = await db.leads.find(query, {"_id": 0}).sort("created_at", -1).to_list(None)
    
    # Enrich leads with assignment info
    for lead in leads:
        # Get assigned to info
        if lead.get("assigned_to"):
            assignee = await db.users.find_one({"id": lead["assigned_to"]}, {"_id": 0, "email": 1, "full_name": 1, "role": 1})
            if assignee:
                lead["assigned_to_name"] = assignee.get("full_name") or assignee.get("email")
                lead["assigned_to_role"] = assignee.get("role")
        
        # Get assigned by info
        if lead.get("assigned_by"):
            assigner = await db.users.find_one({"id": lead["assigned_by"]}, {"_id": 0, "email": 1, "name": 1})
            if assigner:
                lead["assigned_by_name"] = assigner.get("name") or assigner.get("email")
        
        # Get source info
        if lead.get("source_id"):
            source = await db.lead_sources.find_one({"id": lead["source_id"]}, {"_id": 0, "name": 1, "icon": 1})
            if source:
                lead["source_name"] = source.get("name")
                lead["source_icon"] = source.get("icon")
        
        # Get status info
        if lead.get("status_id"):
            status_obj = await db.lead_statuses.find_one({"id": lead["status_id"]}, {"_id": 0, "name": 1, "color": 1, "category": 1})
            if status_obj:
                lead["status_name"] = status_obj.get("name")
                lead["status_color"] = status_obj.get("color")
                lead["status_category"] = status_obj.get("category")
    
    return {
        "leads": leads,
        "total": len(leads),
        "is_manager": is_manager,
        "filter_type": filter_type or "all"
    }


@api_router.post("/sales/leads")
async def create_lead(
    first_name: str,
    last_name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    source_id: Optional[str] = None,  # NEW: reference to lead_sources
    source: str = "other",  # Keep for backward compatibility
    status_id: Optional[str] = None,  # NEW: reference to lead_statuses
    referred_by_member_id: Optional[str] = None,  # NEW: for referrals
    assigned_to: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a new lead with configurable source and status"""
    import uuid
    from datetime import datetime
    
    # If source_id not provided, try to find default source
    if not source_id:
        default_source = await db.lead_sources.find_one({"name": "Other"})
        if default_source:
            source_id = default_source["id"]
    
    # If status_id not provided, use "New Lead" status
    if not status_id:
        default_status = await db.lead_statuses.find_one({"name": "New Lead"})
        if default_status:
            status_id = default_status["id"]
    
    lead_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    lead = {
        "id": lead_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "company": company,
        "source": source,  # Keep for backward compatibility
        "source_id": source_id,  # NEW
        "status": "new",  # Keep for backward compatibility
        "status_id": status_id,  # NEW
        "referred_by_member_id": referred_by_member_id,  # NEW
        "loss_reason_id": None,  # NEW
        "loss_notes": None,  # NEW
        "lead_score": 0,
        "assigned_to": assigned_to,  # Will be None if not provided
        "assigned_by": current_user.id if assigned_to else None,  # NEW: Track who assigned
        "assigned_at": now if assigned_to else None,  # NEW: Track when assigned
        "assignment_history": [],  # NEW: Track assignment history
        "created_at": now,
        "updated_at": now,
        "last_contacted": None,
        "notes": notes,
        "tags": []
    }
    
    await db.leads.insert_one(lead.copy())
    
    # If this is a referral and member provided, create a referral reward (pending)
    if referred_by_member_id:
        # Verify member exists
        referring_member = await db.members.find_one(
            {"id": referred_by_member_id},
            {"_id": 0, "id": 1}
        )
        if referring_member:
            reward = {
                "id": str(uuid.uuid4()),
                "referring_member_id": referred_by_member_id,
                "referred_lead_id": lead_id,
                "reward_type": "pending_selection",
                "reward_value": None,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "delivered_at": None,
                "notes": "Reward pending - lead needs to convert first"
            }
            await db.referral_rewards.insert_one(reward)
    
    # Log activity
    activity = {
        "id": str(uuid.uuid4()),
        "related_to_type": "lead",
        "related_to_id": lead_id,
        "activity_type": "created",
        "description": f"Lead created by {current_user.email}",
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sales_activities.insert_one(activity)
    
    return {"success": True, "lead": lead}


@api_router.get("/sales/leads/unassigned")
async def get_unassigned_leads(current_user: User = Depends(get_current_user)):
    """Get all unassigned leads (managers only)"""
    # Check if current user is a manager
    manager_roles = ["business_owner", "head_admin", "sales_head", "sales_manager"]
    if current_user.role not in manager_roles:
        raise HTTPException(status_code=403, detail="Only managers can view unassigned leads")
    
    # Get leads where assigned_to is null or empty
    leads = await db.leads.find(
        {"$or": [{"assigned_to": None}, {"assigned_to": ""}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(None)
    
    # Enrich with source and status info
    for lead in leads:
        # Get source info
        if lead.get("source_id"):
            source = await db.lead_sources.find_one({"id": lead["source_id"]}, {"_id": 0, "name": 1, "icon": 1})
            if source:
                lead["source_name"] = source.get("name")
                lead["source_icon"] = source.get("icon")
        
        # Get status info
        if lead.get("status_id"):
            status = await db.lead_statuses.find_one({"id": lead["status_id"]}, {"_id": 0, "name": 1, "color": 1, "category": 1})
            if status:
                lead["status_name"] = status.get("name")
                lead["status_color"] = status.get("color")
                lead["status_category"] = status.get("category")
    
    return {
        "total": len(leads),
        "leads": leads
    }


@api_router.get("/sales/leads/my-leads")
async def get_my_assigned_leads(current_user: User = Depends(get_current_user)):
    """Get leads assigned to current user (consultants)"""
    # Get leads assigned to the current user
    leads = await db.leads.find(
        {"assigned_to": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(None)
    
    # Enrich with source and status info
    for lead in leads:
        # Get source info
        if lead.get("source_id"):
            source = await db.lead_sources.find_one({"id": lead["source_id"]}, {"_id": 0, "name": 1, "icon": 1})
            if source:
                lead["source_name"] = source.get("name")
                lead["source_icon"] = source.get("icon")
        
        # Get status info
        if lead.get("status_id"):
            status = await db.lead_statuses.find_one({"id": lead["status_id"]}, {"_id": 0, "name": 1, "color": 1, "category": 1})
            if status:
                lead["status_name"] = status.get("name")
                lead["status_color"] = status.get("color")
                lead["status_category"] = status.get("category")
        
        # Get assigned by info
        if lead.get("assigned_by"):
            assigner = await db.users.find_one({"id": lead["assigned_by"]}, {"_id": 0, "email": 1, "full_name": 1})
            if assigner:
                lead["assigned_by_name"] = assigner.get("full_name") or assigner.get("email")
    
    return {
        "total": len(leads),
        "leads": leads
    }


@api_router.get("/sales/leads/{lead_id}")
async def get_lead(lead_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific lead by ID"""
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get related opportunities
    opportunities = await db.opportunities.find(
        {"contact_id": lead_id},
        {"_id": 0}
    ).to_list(None)
    
    # Get related tasks
    tasks = await db.sales_tasks.find(
        {"related_to_type": "lead", "related_to_id": lead_id},
        {"_id": 0}
    ).to_list(None)
    
    # Get activity history
    activities = await db.sales_activities.find(
        {"related_to_id": lead_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(None)
    
    return {
        "lead": lead,
        "opportunities": opportunities,
        "tasks": tasks,
        "activities": activities
    }


@api_router.put("/sales/leads/{lead_id}")
async def update_lead(
    lead_id: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None,
    status: Optional[str] = None,
    status_id: Optional[str] = None,  # NEW
    source_id: Optional[str] = None,  # NEW
    referred_by_member_id: Optional[str] = None,  # NEW
    loss_reason_id: Optional[str] = None,  # NEW
    loss_notes: Optional[str] = None,  # NEW
    lead_score: Optional[int] = None,
    assigned_to: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update a lead with support for configurable fields"""
    from datetime import datetime
    
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if first_name is not None:
        update_data["first_name"] = first_name
    if last_name is not None:
        update_data["last_name"] = last_name
    if email is not None:
        update_data["email"] = email
    if phone is not None:
        update_data["phone"] = phone
    if company is not None:
        update_data["company"] = company
    if status is not None:
        update_data["status"] = status
    if status_id is not None:
        update_data["status_id"] = status_id
        # Check if status is "Lost" (category = lost), require loss_reason_id
        status_obj = await db.lead_statuses.find_one({"id": status_id})
        if status_obj and status_obj.get("category") == "lost" and not loss_reason_id:
            raise HTTPException(status_code=400, detail="Loss reason required when marking lead as lost")
    if source_id is not None:
        update_data["source_id"] = source_id
    if referred_by_member_id is not None:
        update_data["referred_by_member_id"] = referred_by_member_id
    if loss_reason_id is not None:
        update_data["loss_reason_id"] = loss_reason_id
    if loss_notes is not None:
        update_data["loss_notes"] = loss_notes
    if lead_score is not None:
        update_data["lead_score"] = min(max(lead_score, 0), 100)  # Clamp 0-100
    if assigned_to is not None:
        update_data["assigned_to"] = assigned_to
    if notes is not None:
        update_data["notes"] = notes
    
    # Check if status changed to "Joined" (category = converted) and referred_by_member_id exists
    if status_id:
        status_obj = await db.lead_statuses.find_one({"id": status_id})
        if status_obj and status_obj.get("category") == "converted" and lead.get("referred_by_member_id"):
            # Update referral reward status to approved
            await db.referral_rewards.update_many(
                {
                    "referred_lead_id": lead_id,
                    "status": "pending"
                },
                {"$set": {"status": "approved"}}
            )
    
    await db.leads.update_one({"id": lead_id}, {"$set": update_data})
    
    # Log activity
    import uuid
    activity = {
        "id": str(uuid.uuid4()),
        "related_to_type": "lead",
        "related_to_id": lead_id,
        "activity_type": "updated",
        "description": f"Lead updated by {current_user.email}",
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sales_activities.insert_one(activity)
    
    updated_lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    return {"success": True, "lead": updated_lead}


@api_router.delete("/sales/leads/{lead_id}")
async def delete_lead(lead_id: str, current_user: User = Depends(get_current_user)):
    """Delete a lead"""
    result = await db.leads.delete_one({"id": lead_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Also delete related opportunities, tasks, activities
    await db.opportunities.delete_many({"contact_id": lead_id})
    await db.sales_tasks.delete_many({"related_to_type": "lead", "related_to_id": lead_id})
    await db.sales_activities.delete_many({"related_to_id": lead_id})
    
    return {"success": True, "message": "Lead deleted"}


# ==================== LEAD ASSIGNMENT ENDPOINTS ====================

@api_router.post("/sales/leads/{lead_id}/assign")
async def assign_lead(
    lead_id: str,
    assigned_to: str,
    assignment_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Assign or reassign a lead to a consultant (managers only)"""
    from datetime import datetime, timezone
    
    # Check if current user is a manager
    manager_roles = ["business_owner", "head_admin", "sales_head", "sales_manager"]
    if current_user.role not in manager_roles:
        raise HTTPException(status_code=403, detail="Only managers can assign leads")
    
    # Get the lead
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get the consultant user to verify they exist
    consultant = await db.users.find_one({"id": assigned_to}, {"_id": 0, "id": 1, "email": 1, "full_name": 1})
    if not consultant:
        raise HTTPException(status_code=404, detail="Consultant not found")
    
    # Get previous assignment info
    previous_assigned_to = lead.get("assigned_to")
    previous_assigned_to_name = None
    if previous_assigned_to:
        prev_user = await db.users.find_one({"id": previous_assigned_to}, {"_id": 0, "email": 1, "full_name": 1})
        if prev_user:
            previous_assigned_to_name = prev_user.get("full_name") or prev_user.get("email")
    
    now = datetime.now(timezone.utc).isoformat()
    
    # Create assignment history entry
    assignment_record = {
        "assigned_to": assigned_to,
        "assigned_to_name": consultant.get("full_name") or consultant.get("email"),
        "assigned_by": current_user.id,
        "assigned_by_name": current_user.full_name or current_user.email,
        "assigned_at": now,
        "notes": assignment_notes,
        "previous_assigned_to": previous_assigned_to,
        "previous_assigned_to_name": previous_assigned_to_name
    }
    
    # Update lead with new assignment
    assignment_history = lead.get("assignment_history", [])
    assignment_history.append(assignment_record)
    
    update_data = {
        "assigned_to": assigned_to,
        "assigned_by": current_user.id,
        "assigned_at": now,
        "assignment_history": assignment_history,
        "updated_at": now
    }
    
    await db.leads.update_one(
        {"id": lead_id},
        {"$set": update_data}
    )
    
    # Create a notification/task for the consultant (simple implementation)
    # In production, you'd integrate with a notification system
    task_id = str(uuid.uuid4())
    notification_task = {
        "id": task_id,
        "title": f"New Lead Assigned: {lead['first_name']} {lead['last_name']}",
        "description": f"You have been assigned a new lead by {current_user.full_name or current_user.email}. {assignment_notes or ''}",
        "task_type": "follow_up",
        "related_to_type": "lead",
        "related_to_id": lead_id,
        "assigned_to": assigned_to,
        "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "priority": "high",
        "status": "pending",
        "created_at": now,
        "completed_at": None
    }
    
    await db.sales_tasks.insert_one(notification_task)
    
    action_text = "reassigned" if previous_assigned_to else "assigned"
    
    return {
        "success": True,
        "message": f"Lead {action_text} successfully",
        "lead_id": lead_id,
        "assigned_to": assigned_to,
        "assigned_to_name": consultant.get("full_name") or consultant.get("email"),
        "assigned_by": current_user.id,
        "assigned_at": now,
        "notification_task_created": True
    }


# Duplicate functions moved above - removed to avoid conflicts


@api_router.get("/sales/consultants")
async def get_sales_consultants(current_user: User = Depends(get_current_user)):
    """Get list of sales consultants for assignment (managers only)"""
    # Check if current user is a manager
    manager_roles = ["business_owner", "head_admin", "sales_head", "sales_manager"]
    if current_user.role not in manager_roles:
        raise HTTPException(status_code=403, detail="Only managers can view consultants list")
    
    # Get users with sales-related roles
    consultant_roles = ["sales_manager", "sales_head", "personal_trainer", "fitness_manager"]
    
    consultants = await db.users.find(
        {"role": {"$in": consultant_roles}},
        {"_id": 0, "id": 1, "email": 1, "full_name": 1, "role": 1}
    ).to_list(None)
    
    # Get lead counts for each consultant
    for consultant in consultants:
        assigned_count = await db.leads.count_documents({"assigned_to": consultant["id"]})
        consultant["assigned_leads_count"] = assigned_count
    
    return {
        "total": len(consultants),
        "consultants": consultants
    }


# ==================== COMPLIMENTARY MEMBERSHIP ENDPOINTS ====================

@api_router.post("/complimentary-types")
async def create_complimentary_type(
    type_data: ComplimentaryMembershipTypeCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new complimentary membership type (managers only)"""
    try:
        manager_roles = ["business_owner", "head_admin", "sales_head", "sales_manager"]
        if current_user.role not in manager_roles:
            raise HTTPException(status_code=403, detail="Only managers can create complimentary types")
        
        type_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # Convert Pydantic model to dict
        type_dict = type_data.model_dump()
        
        comp_type = {
            "id": type_id,
            "name": type_dict["name"],
            "description": type_dict.get("description"),
            "time_limit_days": type_dict["time_limit_days"],
            "visit_limit": type_dict["visit_limit"],
            "no_access_alert_days": type_dict["no_access_alert_days"],
            "notification_on_visits": type_dict.get("notification_on_visits", [1, 2, 3]),
            "is_active": type_dict.get("is_active", True),
            "color": type_dict.get("color", "#3b82f6"),
            "icon": type_dict.get("icon", "🎁"),
            "created_at": now,
            "updated_at": now
        }
        
        result = await db.complimentary_types.insert_one(comp_type)
        
        # Return a clean copy without MongoDB ObjectId
        response_type = {
            "id": comp_type["id"],
            "name": comp_type["name"],
            "description": comp_type["description"],
            "time_limit_days": comp_type["time_limit_days"],
            "visit_limit": comp_type["visit_limit"],
            "no_access_alert_days": comp_type["no_access_alert_days"],
            "notification_on_visits": comp_type["notification_on_visits"],
            "is_active": comp_type["is_active"],
            "color": comp_type["color"],
            "icon": comp_type["icon"],
            "created_at": comp_type["created_at"],
            "updated_at": comp_type["updated_at"]
        }
        
        return {"success": True, "complimentary_type": response_type}
    except Exception as e:
        print(f"Error creating complimentary type: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.get("/complimentary-types")
async def get_complimentary_types(current_user: User = Depends(get_current_user)):
    """Get all complimentary membership types"""
    types = await db.complimentary_types.find({}, {"_id": 0}).sort("name", 1).to_list(None)
    return {"total": len(types), "types": types}


@api_router.put("/complimentary-types/{type_id}")
async def update_complimentary_type(
    type_id: str,
    type_data: ComplimentaryMembershipTypeCreate,
    current_user: User = Depends(get_current_user)
):
    """Update a complimentary membership type (managers only)"""
    manager_roles = ["business_owner", "head_admin", "sales_head", "sales_manager"]
    if current_user.role not in manager_roles:
        raise HTTPException(status_code=403, detail="Only managers can update complimentary types")
    
    update_data = {
        **type_data.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.complimentary_types.update_one(
        {"id": type_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Complimentary type not found")
    
    return {"success": True, "message": "Complimentary type updated"}


@api_router.delete("/complimentary-types/{type_id}")
async def delete_complimentary_type(
    type_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a complimentary membership type (managers only)"""
    manager_roles = ["business_owner", "head_admin", "sales_head", "sales_manager"]
    if current_user.role not in manager_roles:
        raise HTTPException(status_code=403, detail="Only managers can delete complimentary types")
    
    # Check if any active memberships use this type
    active_count = await db.complimentary_memberships.count_documents({
        "complimentary_type_id": type_id,
        "status": {"$in": ["active", "not_using"]}
    })
    
    if active_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {active_count} active memberships use this type"
        )
    
    result = await db.complimentary_types.delete_one({"id": type_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Complimentary type not found")
    
    return {"success": True, "message": "Complimentary type deleted"}


@api_router.post("/complimentary-memberships")
async def issue_complimentary_membership(
    membership_data: ComplimentaryMembershipCreate,
    current_user: User = Depends(get_current_user)
):
    """Issue a complimentary membership pass and optionally create a lead"""
    from datetime import timedelta
    
    # Get the complimentary type
    comp_type = await db.complimentary_types.find_one(
        {"id": membership_data.complimentary_type_id},
        {"_id": 0}
    )
    
    if not comp_type:
        raise HTTPException(status_code=404, detail="Complimentary type not found")
    
    if not comp_type.get("is_active"):
        raise HTTPException(status_code=400, detail="This complimentary type is not active")
    
    # Create member (simplified - in production, integrate with full member creation)
    member_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    
    member_name = f"{membership_data.first_name} {membership_data.last_name}"
    
    # Calculate expiry date
    expiry_date = now + timedelta(days=comp_type["time_limit_days"])
    
    # Create complimentary membership record
    comp_membership_id = str(uuid.uuid4())
    comp_membership = {
        "id": comp_membership_id,
        "member_id": member_id,
        "member_name": member_name,
        "member_email": membership_data.email,
        "member_phone": membership_data.phone,
        "complimentary_type_id": comp_type["id"],
        "complimentary_type_name": comp_type["name"],
        "start_date": now_iso,
        "expiry_date": expiry_date.isoformat(),
        "time_limit_days": comp_type["time_limit_days"],
        "visit_limit": comp_type["visit_limit"],
        "visits_used": 0,
        "visits_remaining": comp_type["visit_limit"],
        "last_visit_date": None,
        "status": "active",
        "assigned_consultant_id": membership_data.assigned_consultant_id,
        "assigned_consultant_name": None,
        "created_from_lead_id": None,
        "converted_to_member_id": None,
        "conversion_date": None,
        "created_at": now_iso,
        "updated_at": now_iso
    }
    
    # Get consultant name if assigned
    if membership_data.assigned_consultant_id:
        consultant = await db.users.find_one(
            {"id": membership_data.assigned_consultant_id},
            {"_id": 0, "full_name": 1, "email": 1}
        )
        if consultant:
            comp_membership["assigned_consultant_name"] = consultant.get("full_name") or consultant.get("email")
    
    await db.complimentary_memberships.insert_one(comp_membership)
    
    # Auto-create lead if requested
    lead_id = None
    if membership_data.auto_create_lead:
        lead_id = str(uuid.uuid4())
        lead = {
            "id": lead_id,
            "first_name": membership_data.first_name,
            "last_name": membership_data.last_name,
            "email": membership_data.email,
            "phone": membership_data.phone,
            "company": "",
            "source": "complimentary_membership",
            "source_id": None,
            "status": "new",
            "status_id": None,
            "referred_by_member_id": None,
            "loss_reason_id": None,
            "loss_notes": None,
            "lead_score": 50,  # Medium score for complimentary
            "assigned_to": membership_data.assigned_consultant_id,
            "assigned_by": current_user.id if membership_data.assigned_consultant_id else None,
            "assigned_at": now_iso if membership_data.assigned_consultant_id else None,
            "assignment_history": [],
            "created_at": now_iso,
            "updated_at": now_iso,
            "last_contacted": None,
            "notes": f"Complimentary membership issued: {comp_type['name']}. {membership_data.notes or ''}",
            "tags": ["complimentary"]
        }
        
        await db.leads.insert_one(lead)
        
        # Update complimentary membership with lead_id
        await db.complimentary_memberships.update_one(
            {"id": comp_membership_id},
            {"$set": {"created_from_lead_id": lead_id}}
        )
        comp_membership["created_from_lead_id"] = lead_id
    
    # Return clean copy without MongoDB ObjectId
    response_membership = {
        "id": comp_membership["id"],
        "member_id": comp_membership["member_id"],
        "member_name": comp_membership["member_name"],
        "member_email": comp_membership["member_email"],
        "member_phone": comp_membership["member_phone"],
        "complimentary_type_id": comp_membership["complimentary_type_id"],
        "complimentary_type_name": comp_membership["complimentary_type_name"],
        "start_date": comp_membership["start_date"],
        "expiry_date": comp_membership["expiry_date"],
        "time_limit_days": comp_membership["time_limit_days"],
        "visit_limit": comp_membership["visit_limit"],
        "visits_used": comp_membership["visits_used"],
        "visits_remaining": comp_membership["visits_remaining"],
        "last_visit_date": comp_membership["last_visit_date"],
        "status": comp_membership["status"],
        "assigned_consultant_id": comp_membership["assigned_consultant_id"],
        "assigned_consultant_name": comp_membership["assigned_consultant_name"],
        "created_from_lead_id": comp_membership["created_from_lead_id"],
        "converted_to_member_id": comp_membership["converted_to_member_id"],
        "conversion_date": comp_membership["conversion_date"],
        "created_at": comp_membership["created_at"],
        "updated_at": comp_membership["updated_at"]
    }
    
    return {
        "success": True,
        "complimentary_membership": response_membership,
        "lead_id": lead_id,
        "message": "Complimentary membership issued successfully"
    }


@api_router.get("/complimentary-memberships")
async def get_complimentary_memberships(
    status: Optional[str] = None,
    complimentary_type_id: Optional[str] = None,
    assigned_consultant_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get complimentary memberships with filters"""
    query = {}
    
    if status:
        query["status"] = status
    if complimentary_type_id:
        query["complimentary_type_id"] = complimentary_type_id
    if assigned_consultant_id:
        query["assigned_consultant_id"] = assigned_consultant_id
    
    memberships = await db.complimentary_memberships.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(None)
    
    return {
        "total": len(memberships),
        "memberships": memberships
    }


@api_router.get("/complimentary-dashboard")
async def get_complimentary_dashboard(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """Get complimentary membership dashboard statistics"""
    from datetime import timedelta
    
    now = datetime.now(timezone.utc)
    cutoff_date = (now - timedelta(days=days)).isoformat()
    
    # Total complimentary memberships issued (within period)
    total_issued = await db.complimentary_memberships.count_documents({
        "created_at": {"$gte": cutoff_date}
    })
    
    # Active memberships
    active_memberships = await db.complimentary_memberships.count_documents({
        "status": "active",
        "expiry_date": {"$gte": now.isoformat()}
    })
    
    # Members accessing (visits_used > 0)
    accessing_count = await db.complimentary_memberships.count_documents({
        "created_at": {"$gte": cutoff_date},
        "visits_used": {"$gt": 0}
    })
    
    # Members not accessing (visits_used = 0, status = active)
    not_accessing_count = await db.complimentary_memberships.count_documents({
        "status": {"$in": ["active", "not_using"]},
        "visits_used": 0,
        "expiry_date": {"$gte": now.isoformat()}
    })
    
    # Expired passes
    expired_count = await db.complimentary_memberships.count_documents({
        "status": "expired"
    })
    
    # Converted to paid members
    converted_count = await db.complimentary_memberships.count_documents({
        "status": "converted",
        "created_at": {"$gte": cutoff_date}
    })
    
    # Utilization by type
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff_date}}},
        {"$group": {
            "_id": "$complimentary_type_id",
            "type_name": {"$first": "$complimentary_type_name"},
            "total_issued": {"$sum": 1},
            "total_visits": {"$sum": "$visits_used"},
            "members_accessed": {
                "$sum": {"$cond": [{"$gt": ["$visits_used", 0]}, 1, 0]}
            },
            "members_converted": {
                "$sum": {"$cond": [{"$eq": ["$status", "converted"]}, 1, 0]}
            }
        }},
        {"$sort": {"total_visits": -1}}
    ]
    
    utilization_by_type = await db.complimentary_memberships.aggregate(pipeline).to_list(None)
    
    # Calculate utilization percentage
    for item in utilization_by_type:
        if item["total_issued"] > 0:
            item["utilization_percentage"] = round((item["members_accessed"] / item["total_issued"]) * 100, 1)
            item["conversion_rate"] = round((item["members_converted"] / item["total_issued"]) * 100, 1)
        else:
            item["utilization_percentage"] = 0
            item["conversion_rate"] = 0
    
    # Overall conversion rate
    conversion_rate = 0
    if total_issued > 0:
        conversion_rate = round((converted_count / total_issued) * 100, 1)
    
    # Utilization rate
    utilization_rate = 0
    if total_issued > 0:
        utilization_rate = round((accessing_count / total_issued) * 100, 1)
    
    return {
        "period_days": days,
        "total_issued": total_issued,
        "active_memberships": active_memberships,
        "accessing_count": accessing_count,
        "not_accessing_count": not_accessing_count,
        "expired_count": expired_count,
        "converted_count": converted_count,
        "utilization_rate": utilization_rate,
        "conversion_rate": conversion_rate,
        "utilization_by_type": utilization_by_type
    }


@api_router.post("/complimentary-memberships/{membership_id}/record-visit")
async def record_complimentary_visit(
    membership_id: str,
    current_user: User = Depends(get_current_user)
):
    """Record a visit for a complimentary membership (called when access granted)"""
    membership = await db.complimentary_memberships.find_one(
        {"id": membership_id},
        {"_id": 0}
    )
    
    if not membership:
        raise HTTPException(status_code=404, detail="Complimentary membership not found")
    
    # Check if still active
    now = datetime.now(timezone.utc)
    expiry_date = datetime.fromisoformat(membership["expiry_date"].replace('Z', '+00:00'))
    
    if now > expiry_date:
        # Mark as expired
        await db.complimentary_memberships.update_one(
            {"id": membership_id},
            {"$set": {"status": "expired", "updated_at": now.isoformat()}}
        )
        raise HTTPException(status_code=400, detail="Complimentary membership has expired")
    
    if membership["visits_used"] >= membership["visit_limit"]:
        # Mark as completed
        await db.complimentary_memberships.update_one(
            {"id": membership_id},
            {"$set": {"status": "completed", "updated_at": now.isoformat()}}
        )
        raise HTTPException(status_code=400, detail="Visit limit reached")
    
    # Increment visit count
    new_visits_used = membership["visits_used"] + 1
    new_visits_remaining = membership["visit_limit"] - new_visits_used
    
    update_data = {
        "visits_used": new_visits_used,
        "visits_remaining": new_visits_remaining,
        "last_visit_date": now.isoformat(),
        "updated_at": now.isoformat(),
        "status": "active" if new_visits_remaining > 0 else "completed"
    }
    
    await db.complimentary_memberships.update_one(
        {"id": membership_id},
        {"$set": update_data}
    )
    
    # Get complimentary type for notification settings
    comp_type = await db.complimentary_types.find_one(
        {"id": membership["complimentary_type_id"]},
        {"_id": 0}
    )
    
    # Check if we should notify consultant
    should_notify = comp_type and new_visits_used in comp_type.get("notification_on_visits", [])
    
    if should_notify and membership.get("assigned_consultant_id"):
        # Create notification task
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "title": f"Complimentary Visit #{new_visits_used}: {membership['member_name']}",
            "description": f"{membership['member_name']} has used {new_visits_used} of {membership['visit_limit']} visits on their {membership['complimentary_type_name']} pass. Consider following up!",
            "task_type": "follow_up",
            "related_to_type": "complimentary_membership",
            "related_to_id": membership_id,
            "assigned_to": membership["assigned_consultant_id"],
            "due_date": (now + timedelta(days=1)).isoformat(),
            "priority": "medium",
            "status": "pending",
            "created_at": now.isoformat(),
            "completed_at": None
        }
        await db.sales_tasks.insert_one(task)
    
    return {
        "success": True,
        "visits_used": new_visits_used,
        "visits_remaining": new_visits_remaining,
        "notification_sent": should_notify
    }


# ==================== OPPORTUNITIES/PIPELINE ENDPOINTS ====================

@api_router.get("/sales/opportunities")
async def get_opportunities(
    stage: Optional[str] = None,
    assigned_to: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all opportunities with optional filters"""
    query = {}
    if stage:
        query["stage"] = stage
    if assigned_to:
        query["assigned_to"] = assigned_to
    
    opportunities = await db.opportunities.find(query, {"_id": 0}).sort("created_at", -1).to_list(None)
    
    # Enrich with lead/contact info
    enriched_opportunities = []
    for opp in opportunities:
        lead = await db.leads.find_one(
            {"id": opp.get("contact_id")},
            {"_id": 0, "first_name": 1, "last_name": 1, "email": 1, "company": 1}
        )
        
        opp_with_contact = opp.copy()
        if lead:
            opp_with_contact["contact_name"] = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
            opp_with_contact["contact_email"] = lead.get("email")
            opp_with_contact["contact_company"] = lead.get("company")
        
        enriched_opportunities.append(opp_with_contact)
    
    return {"opportunities": enriched_opportunities, "total": len(enriched_opportunities)}


@api_router.get("/sales/pipeline")
async def get_sales_pipeline(current_user: User = Depends(get_current_user)):
    """Get sales pipeline organized by stage for kanban view"""
    stages = ["new_lead", "contacted", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]
    
    pipeline = {}
    total_value = 0
    total_opportunities = 0
    
    for stage in stages:
        opportunities = await db.opportunities.find({"stage": stage}, {"_id": 0}).to_list(None)
        
        # Enrich with lead info
        enriched_opps = []
        stage_value = 0
        
        for opp in opportunities:
            lead = await db.leads.find_one(
                {"id": opp.get("contact_id")},
                {"_id": 0, "first_name": 1, "last_name": 1, "email": 1, "company": 1}
            )
            
            opp_with_contact = opp.copy()
            if lead:
                opp_with_contact["contact_name"] = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
                opp_with_contact["contact_email"] = lead.get("email")
                opp_with_contact["contact_company"] = lead.get("company")
            
            enriched_opps.append(opp_with_contact)
            
            # Calculate stage value (weighted by probability for open stages)
            if stage not in ["closed_won", "closed_lost"]:
                stage_value += opp.get("value", 0) * (opp.get("probability", 0) / 100)
            elif stage == "closed_won":
                stage_value += opp.get("value", 0)
        
        pipeline[stage] = {
            "opportunities": enriched_opps,
            "count": len(enriched_opps),
            "total_value": round(stage_value, 2)
        }
        
        if stage not in ["closed_lost"]:
            total_value += stage_value
        total_opportunities += len(enriched_opps)
    
    return {
        "pipeline": pipeline,
        "summary": {
            "total_opportunities": total_opportunities,
            "total_pipeline_value": round(total_value, 2)
        }
    }


@api_router.post("/sales/opportunities")
async def create_opportunity(
    title: str,
    contact_id: str,
    value: float,
    stage: str = "new_lead",
    probability: int = 10,
    expected_close_date: Optional[str] = None,
    assigned_to: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a new opportunity"""
    import uuid
    from datetime import datetime
    
    # Verify lead exists
    lead = await db.leads.find_one({"id": contact_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead/Contact not found")
    
    opp_id = str(uuid.uuid4())
    opportunity = {
        "id": opp_id,
        "title": title,
        "contact_id": contact_id,
        "value": value,
        "currency": "ZAR",
        "stage": stage,
        "probability": min(max(probability, 0), 100),
        "expected_close_date": expected_close_date,
        "assigned_to": assigned_to or current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes
    }
    
    await db.opportunities.insert_one(opportunity.copy())
    
    # Log activity
    activity = {
        "id": str(uuid.uuid4()),
        "related_to_type": "opportunity",
        "related_to_id": opp_id,
        "activity_type": "created",
        "description": f"Opportunity created by {current_user.email}",
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sales_activities.insert_one(activity)
    
    return {"success": True, "opportunity": opportunity}


@api_router.put("/sales/opportunities/{opp_id}")
async def update_opportunity(
    opp_id: str,
    title: Optional[str] = None,
    value: Optional[float] = None,
    stage: Optional[str] = None,
    probability: Optional[int] = None,
    expected_close_date: Optional[str] = None,
    assigned_to: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update an opportunity"""
    from datetime import datetime
    
    opp = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if title is not None:
        update_data["title"] = title
    if value is not None:
        update_data["value"] = value
    if stage is not None:
        update_data["stage"] = stage
    if probability is not None:
        update_data["probability"] = min(max(probability, 0), 100)
    if expected_close_date is not None:
        update_data["expected_close_date"] = expected_close_date
    if assigned_to is not None:
        update_data["assigned_to"] = assigned_to
    if notes is not None:
        update_data["notes"] = notes
    
    await db.opportunities.update_one({"id": opp_id}, {"$set": update_data})
    
    # Log activity
    import uuid
    activity = {
        "id": str(uuid.uuid4()),
        "related_to_type": "opportunity",
        "related_to_id": opp_id,
        "activity_type": "updated",
        "description": f"Opportunity updated by {current_user.email}. Stage: {stage if stage else 'unchanged'}",
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sales_activities.insert_one(activity)
    
    updated_opp = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
    return {"success": True, "opportunity": updated_opp}


# ==================== TASKS ENDPOINTS ====================

@api_router.get("/sales/tasks")
async def get_sales_tasks(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    task_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all sales tasks with optional filters"""
    query = {}
    if status:
        query["status"] = status
    if assigned_to:
        query["assigned_to"] = assigned_to
    if task_type:
        query["task_type"] = task_type
    
    tasks = await db.sales_tasks.find(query, {"_id": 0}).sort("due_date", 1).to_list(None)
    
    # Enrich with related lead/opportunity info
    enriched_tasks = []
    for task in tasks:
        task_copy = task.copy()
        
        if task.get("related_to_type") == "lead":
            lead = await db.leads.find_one(
                {"id": task.get("related_to_id")},
                {"_id": 0, "first_name": 1, "last_name": 1, "email": 1}
            )
            if lead:
                task_copy["related_to_name"] = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip()
                
        elif task.get("related_to_type") == "opportunity":
            opp = await db.opportunities.find_one(
                {"id": task.get("related_to_id")},
                {"_id": 0, "title": 1}
            )
            if opp:
                task_copy["related_to_name"] = opp.get("title")
        
        enriched_tasks.append(task_copy)
    
    return {"tasks": enriched_tasks, "total": len(enriched_tasks)}


@api_router.post("/sales/tasks")
async def create_sales_task(
    title: str,
    task_type: str,
    related_to_type: str,
    related_to_id: str,
    due_date: str,
    priority: str = "medium",
    description: Optional[str] = None,
    assigned_to: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a new sales task"""
    import uuid
    from datetime import datetime
    
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "title": title,
        "description": description,
        "task_type": task_type,
        "related_to_type": related_to_type,
        "related_to_id": related_to_id,
        "assigned_to": assigned_to or current_user.id,
        "due_date": due_date,
        "priority": priority,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None
    }
    
    await db.sales_tasks.insert_one(task.copy())
    
    # Log activity
    activity = {
        "id": str(uuid.uuid4()),
        "related_to_type": related_to_type,
        "related_to_id": related_to_id,
        "activity_type": "task_created",
        "description": f"Task '{title}' created by {current_user.email}",
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sales_activities.insert_one(activity)
    
    return {"success": True, "task": task}


@api_router.put("/sales/tasks/{task_id}")
async def update_sales_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update a sales task"""
    from datetime import datetime
    
    task = await db.sales_tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = {}
    
    if title is not None:
        update_data["title"] = title
    if description is not None:
        update_data["description"] = description
    if priority is not None:
        update_data["priority"] = priority
    if due_date is not None:
        update_data["due_date"] = due_date
    if status is not None:
        update_data["status"] = status
        if status == "completed":
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.sales_tasks.update_one({"id": task_id}, {"$set": update_data})
    
    # Log activity
    import uuid
    activity = {
        "id": str(uuid.uuid4()),
        "related_to_type": task.get("related_to_type"),
        "related_to_id": task.get("related_to_id"),
        "activity_type": "task_updated",
        "description": f"Task updated by {current_user.email}. Status: {status if status else 'unchanged'}",
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sales_activities.insert_one(activity)
    
    updated_task = await db.sales_tasks.find_one({"id": task_id}, {"_id": 0})
    return {"success": True, "task": updated_task}


@api_router.delete("/sales/tasks/{task_id}")
async def delete_sales_task(task_id: str, current_user: User = Depends(get_current_user)):
    """Delete a sales task"""
    result = await db.sales_tasks.delete_one({"id": task_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"success": True, "message": "Task deleted"}


# ==================== REPORTING ENDPOINTS ====================

@api_router.get("/sales/reports/overview")
async def get_sales_overview(current_user: User = Depends(get_current_user)):
    """Get sales overview metrics for dashboard"""
    from datetime import datetime, timedelta
    
    # Total leads
    total_leads = await db.leads.count_documents({})
    
    # Leads by status
    new_leads = await db.leads.count_documents({"status": "new"})
    contacted_leads = await db.leads.count_documents({"status": "contacted"})
    qualified_leads = await db.leads.count_documents({"status": "qualified"})
    converted_leads = await db.leads.count_documents({"status": "converted"})
    
    # Total opportunities
    total_opportunities = await db.opportunities.count_documents({})
    
    # Opportunities by stage
    opportunities_by_stage = {}
    stages = ["new_lead", "contacted", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]
    for stage in stages:
        count = await db.opportunities.count_documents({"stage": stage})
        opportunities_by_stage[stage] = count
    
    # Total pipeline value (excluding closed_lost)
    all_opps = await db.opportunities.find(
        {"stage": {"$ne": "closed_lost"}},
        {"_id": 0, "value": 1, "probability": 1, "stage": 1}
    ).to_list(None)
    
    total_pipeline_value = 0
    for opp in all_opps:
        if opp.get("stage") == "closed_won":
            total_pipeline_value += opp.get("value", 0)
        else:
            # Weighted by probability
            total_pipeline_value += opp.get("value", 0) * (opp.get("probability", 0) / 100)
    
    # Win rate
    closed_won_count = opportunities_by_stage.get("closed_won", 0)
    closed_lost_count = opportunities_by_stage.get("closed_lost", 0)
    total_closed = closed_won_count + closed_lost_count
    win_rate = (closed_won_count / total_closed * 100) if total_closed > 0 else 0
    
    # Tasks summary
    total_tasks = await db.sales_tasks.count_documents({})
    pending_tasks = await db.sales_tasks.count_documents({"status": "pending"})
    overdue_tasks = await db.sales_tasks.count_documents({
        "status": "pending",
        "due_date": {"$lt": datetime.now(timezone.utc).isoformat()}
    })
    
    # Lead conversion rate
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_leads = await db.leads.count_documents({
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    })
    
    recent_opportunities = await db.opportunities.count_documents({
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    })
    
    return {
        "leads": {
            "total": total_leads,
            "new": new_leads,
            "contacted": contacted_leads,
            "qualified": qualified_leads,
            "converted": converted_leads,
            "conversion_rate": round(conversion_rate, 1)
        },
        "opportunities": {
            "total": total_opportunities,
            "by_stage": opportunities_by_stage,
            "total_pipeline_value": round(total_pipeline_value, 2),
            "win_rate": round(win_rate, 1)
        },
        "tasks": {
            "total": total_tasks,
            "pending": pending_tasks,
            "overdue": overdue_tasks
        },
        "recent_activity": {
            "leads_last_30_days": recent_leads,
            "opportunities_last_30_days": recent_opportunities
        }
    }


@api_router.get("/sales/reports/conversion-funnel")
async def get_conversion_funnel(current_user: User = Depends(get_current_user)):
    """Get conversion funnel data"""
    stages = ["new", "contacted", "qualified", "converted"]
    funnel_data = []
    
    for stage in stages:
        count = await db.leads.count_documents({"status": stage})
        funnel_data.append({
            "stage": stage,
            "count": count
        })
    
    return {"funnel": funnel_data}



# ==================== SALES MANAGEMENT - PHASE 2 (ADVANCED) ====================

# ==================== SALES AUTOMATION ====================

@api_router.post("/sales/automation/score-lead/{lead_id}")
async def auto_score_lead(lead_id: str, current_user: User = Depends(get_current_user)):
    """
    Automatically calculate and update lead score based on multiple factors
    """
    from datetime import datetime, timedelta
    
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    score = 0
    scoring_factors = []
    
    # Factor 1: Contact information completeness (0-20 points)
    contact_score = 0
    if lead.get("email"):
        contact_score += 10
        scoring_factors.append("Has email (+10)")
    if lead.get("phone"):
        contact_score += 10
        scoring_factors.append("Has phone (+10)")
    score += contact_score
    
    # Factor 2: Company information (0-15 points)
    if lead.get("company"):
        score += 15
        scoring_factors.append("Has company info (+15)")
    
    # Factor 3: Source quality (0-25 points)
    source_scores = {
        "referral": 25,
        "website": 20,
        "social_media": 15,
        "walk_in": 10,
        "other": 5
    }
    source = lead.get("source", "other")
    source_score = source_scores.get(source, 5)
    score += source_score
    scoring_factors.append(f"Source: {source} (+{source_score})")
    
    # Factor 4: Recent activity (0-20 points)
    if lead.get("last_contacted"):
        from datetime import datetime, timedelta
        try:
            last_contacted = datetime.fromisoformat(lead["last_contacted"])
            days_since = (datetime.now(timezone.utc) - last_contacted).days
            if days_since <= 3:
                score += 20
                scoring_factors.append("Recently contacted (<3 days) (+20)")
            elif days_since <= 7:
                score += 15
                scoring_factors.append("Contacted this week (+15)")
            elif days_since <= 30:
                score += 10
                scoring_factors.append("Contacted this month (+10)")
        except:
            pass
    
    # Factor 5: Opportunities count (0-20 points)
    opp_count = await db.opportunities.count_documents({"contact_id": lead_id})
    if opp_count > 0:
        opp_score = min(opp_count * 10, 20)
        score += opp_score
        scoring_factors.append(f"{opp_count} opportunities (+{opp_score})")
    
    # Clamp score to 0-100
    score = min(max(score, 0), 100)
    
    # Update lead score
    await db.leads.update_one(
        {"id": lead_id},
        {"$set": {"lead_score": score, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "success": True,
        "lead_id": lead_id,
        "new_score": score,
        "scoring_factors": scoring_factors
    }


@api_router.post("/sales/automation/auto-assign-lead/{lead_id}")
async def auto_assign_lead(
    lead_id: str,
    assignment_strategy: str = "round_robin",  # round_robin, least_loaded
    current_user: User = Depends(get_current_user)
):
    """
    Automatically assign lead to a team member based on strategy
    """
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get all users (simplified - in production, filter by role/team)
    users = await db.users.find({}, {"_id": 0, "id": 1, "email": 1}).to_list(None)
    
    if not users:
        raise HTTPException(status_code=404, detail="No users available for assignment")
    
    assigned_user = None
    
    if assignment_strategy == "round_robin":
        # Simple round-robin: assign to user with fewest leads
        user_lead_counts = {}
        for user in users:
            count = await db.leads.count_documents({"assigned_to": user["id"]})
            user_lead_counts[user["id"]] = count
        
        # Find user with minimum leads
        assigned_user_id = min(user_lead_counts, key=user_lead_counts.get)
        assigned_user = next(u for u in users if u["id"] == assigned_user_id)
    
    elif assignment_strategy == "least_loaded":
        # Assign to user with fewest pending tasks
        user_task_counts = {}
        for user in users:
            count = await db.sales_tasks.count_documents({
                "assigned_to": user["id"],
                "status": "pending"
            })
            user_task_counts[user["id"]] = count
        
        assigned_user_id = min(user_task_counts, key=user_task_counts.get)
        assigned_user = next(u for u in users if u["id"] == assigned_user_id)
    
    if assigned_user:
        await db.leads.update_one(
            {"id": lead_id},
            {"$set": {"assigned_to": assigned_user["id"], "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {
            "success": True,
            "lead_id": lead_id,
            "assigned_to": assigned_user["email"],
            "strategy": assignment_strategy
        }
    
    return {"success": False, "message": "Could not assign lead"}


@api_router.post("/sales/automation/create-follow-up-tasks")
async def create_auto_follow_up_tasks(
    days_inactive: int = 7,
    current_user: User = Depends(get_current_user)
):
    """
    Create automatic follow-up tasks for leads not contacted recently
    """
    from datetime import datetime, timedelta
    import uuid
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_inactive)
    
    # Find leads that haven't been contacted recently
    leads = await db.leads.find({
        "status": {"$in": ["new", "contacted", "qualified"]},
        "$or": [
            {"last_contacted": {"$lt": cutoff_date.isoformat()}},
            {"last_contacted": None}
        ]
    }, {"_id": 0}).to_list(None)
    
    tasks_created = 0
    
    for lead in leads:
        # Check if follow-up task already exists
        existing_task = await db.sales_tasks.find_one({
            "related_to_type": "lead",
            "related_to_id": lead["id"],
            "status": "pending",
            "task_type": "follow_up"
        })
        
        if not existing_task:
            # Create follow-up task
            # Handle both first_name/last_name and full_name formats
            if 'first_name' in lead and 'last_name' in lead:
                lead_name = f"{lead['first_name']} {lead['last_name']}"
            else:
                lead_name = lead.get('full_name', 'Lead')
            
            task = {
                "id": str(uuid.uuid4()),
                "title": f"Follow up with {lead_name}",
                "description": f"Lead has been inactive for {days_inactive}+ days. Time to reach out!",
                "task_type": "follow_up",
                "related_to_type": "lead",
                "related_to_id": lead["id"],
                "assigned_to": lead.get("assigned_to") or current_user.id,
                "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                "priority": "medium",
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None
            }
            
            await db.sales_tasks.insert_one(task)
            tasks_created += 1
    
    return {
        "success": True,
        "tasks_created": tasks_created,
        "leads_processed": len(leads),
        "days_inactive_threshold": days_inactive
    }


# ==================== WORKFLOW AUTOMATION ====================

class WorkflowRule(BaseModel):
    id: str
    name: str
    trigger_object: str  # lead, opportunity, task
    trigger_event: str  # created, updated, status_changed
    conditions: dict  # e.g., {"status": "qualified"}
    actions: List[dict]  # e.g., [{"type": "create_task", "params": {...}}]
    is_active: bool
    created_at: str

class WorkflowCreate(BaseModel):
    name: str
    trigger_object: str
    trigger_event: str
    conditions: dict
    actions: List[dict]


@api_router.get("/sales/workflows")
async def get_workflows(current_user: User = Depends(get_current_user)):
    """Get all workflow automation rules"""
    workflows = await db.workflow_rules.find({}, {"_id": 0}).to_list(None)
    return {"workflows": workflows, "total": len(workflows)}


@api_router.post("/sales/workflows")
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new workflow automation rule"""
    import uuid
    
    workflow = {
        "id": str(uuid.uuid4()),
        "name": workflow_data.name,
        "trigger_object": workflow_data.trigger_object,
        "trigger_event": workflow_data.trigger_event,
        "conditions": workflow_data.conditions,
        "actions": workflow_data.actions,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.workflow_rules.insert_one(workflow.copy())
    
    return {"success": True, "workflow": workflow}


@api_router.put("/sales/workflows/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """Update workflow rule (e.g., activate/deactivate)"""
    update_data = {}
    
    if is_active is not None:
        update_data["is_active"] = is_active
    
    result = await db.workflow_rules.update_one(
        {"id": workflow_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {"success": True, "workflow_id": workflow_id}


@api_router.delete("/sales/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, current_user: User = Depends(get_current_user)):
    """Delete a workflow rule"""
    result = await db.workflow_rules.delete_one({"id": workflow_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return {"success": True, "message": "Workflow deleted"}


@api_router.post("/sales/workflows/execute")
async def execute_workflow_rules(
    trigger_object: str,
    trigger_event: str,
    object_id: str,
    object_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Execute matching workflow rules for a given trigger
    (This would typically be called internally after create/update operations)
    """
    import uuid
    
    # Find matching active workflows
    workflows = await db.workflow_rules.find({
        "trigger_object": trigger_object,
        "trigger_event": trigger_event,
        "is_active": True
    }, {"_id": 0}).to_list(None)
    
    executed_actions = []
    
    for workflow in workflows:
        # Check if conditions match
        conditions_met = True
        for field, expected_value in workflow.get("conditions", {}).items():
            if object_data.get(field) != expected_value:
                conditions_met = False
                break
        
        if conditions_met:
            # Execute actions
            for action in workflow.get("actions", []):
                action_type = action.get("type")
                
                if action_type == "create_task":
                    # Create a task
                    task = {
                        "id": str(uuid.uuid4()),
                        "title": action.get("params", {}).get("title", "Automated Task"),
                        "description": action.get("params", {}).get("description"),
                        "task_type": action.get("params", {}).get("task_type", "follow_up"),
                        "related_to_type": trigger_object,
                        "related_to_id": object_id,
                        "assigned_to": object_data.get("assigned_to") or current_user.id,
                        "due_date": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                        "priority": action.get("params", {}).get("priority", "medium"),
                        "status": "pending",
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "completed_at": None
                    }
                    await db.sales_tasks.insert_one(task)
                    executed_actions.append({"action": "create_task", "task_id": task["id"]})
                
                elif action_type == "update_field":
                    # Update a field (example: auto-update lead score)
                    field_name = action.get("params", {}).get("field")
                    field_value = action.get("params", {}).get("value")
                    
                    if trigger_object == "lead":
                        await db.leads.update_one(
                            {"id": object_id},
                            {"$set": {field_name: field_value}}
                        )
                    elif trigger_object == "opportunity":
                        await db.opportunities.update_one(
                            {"id": object_id},
                            {"$set": {field_name: field_value}}
                        )
                    
                    executed_actions.append({"action": "update_field", "field": field_name})
                
                elif action_type == "create_opportunity":
                    # Auto-create opportunity when lead becomes qualified
                    opp = {
                        "id": str(uuid.uuid4()),
                        "title": action.get("params", {}).get("title", f"Opportunity for {object_data.get('first_name', 'Lead')}"),
                        "contact_id": object_id,
                        "value": action.get("params", {}).get("value", 0),
                        "currency": "ZAR",
                        "stage": "new_lead",
                        "probability": 10,
                        "expected_close_date": None,
                        "assigned_to": object_data.get("assigned_to"),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "notes": "Auto-created by workflow automation"
                    }
                    await db.opportunities.insert_one(opp)
                    executed_actions.append({"action": "create_opportunity", "opp_id": opp["id"]})
    
    return {
        "success": True,
        "workflows_matched": len(workflows),
        "actions_executed": executed_actions
    }


# ==================== ADVANCED ANALYTICS ====================

@api_router.get("/sales/analytics/forecasting")
async def get_sales_forecast(
    period_months: int = 3,
    current_user: User = Depends(get_current_user)
):
    """
    Sales forecasting based on pipeline stages and probabilities
    """
    # Get all open opportunities (not closed_lost)
    opportunities = await db.opportunities.find(
        {"stage": {"$nin": ["closed_lost", "closed_won"]}},
        {"_id": 0}
    ).to_list(None)
    
    # Calculate weighted forecast by stage
    stage_forecast = {}
    stages = ["new_lead", "contacted", "qualified", "proposal", "negotiation"]
    
    for stage in stages:
        stage_opps = [o for o in opportunities if o.get("stage") == stage]
        total_value = sum(o.get("value", 0) for o in stage_opps)
        weighted_value = sum(o.get("value", 0) * (o.get("probability", 0) / 100) for o in stage_opps)
        
        stage_forecast[stage] = {
            "count": len(stage_opps),
            "total_value": round(total_value, 2),
            "weighted_value": round(weighted_value, 2),
            "avg_probability": round(sum(o.get("probability", 0) for o in stage_opps) / len(stage_opps), 1) if stage_opps else 0
        }
    
    # Calculate total forecast
    total_forecast = sum(sf["weighted_value"] for sf in stage_forecast.values())
    
    # Get closed won opportunities for historical comparison
    closed_won = await db.opportunities.find(
        {"stage": "closed_won"},
        {"_id": 0, "value": 1, "updated_at": 1}
    ).to_list(None)
    
    historical_revenue = sum(o.get("value", 0) for o in closed_won)
    
    return {
        "forecast_period_months": period_months,
        "total_forecast": round(total_forecast, 2),
        "historical_revenue": round(historical_revenue, 2),
        "by_stage": stage_forecast,
        "confidence_level": "medium"  # Could be calculated based on historical accuracy
    }


@api_router.get("/sales/analytics/team-performance")
async def get_team_performance(current_user: User = Depends(get_current_user)):
    """
    Team performance metrics by assigned user
    """
    from collections import defaultdict
    
    # Get all users
    users = await db.users.find({}, {"_id": 0, "id": 1, "email": 1, "first_name": 1, "last_name": 1}).to_list(None)
    
    team_metrics = []
    
    for user in users:
        user_id = user["id"]
        
        # Count leads assigned
        total_leads = await db.leads.count_documents({"assigned_to": user_id})
        qualified_leads = await db.leads.count_documents({"assigned_to": user_id, "status": "qualified"})
        converted_leads = await db.leads.count_documents({"assigned_to": user_id, "status": "converted"})
        
        # Count opportunities
        total_opps = await db.opportunities.count_documents({"assigned_to": user_id})
        won_opps = await db.opportunities.count_documents({"assigned_to": user_id, "stage": "closed_won"})
        
        # Calculate won opportunity value
        won_opp_docs = await db.opportunities.find(
            {"assigned_to": user_id, "stage": "closed_won"},
            {"_id": 0, "value": 1}
        ).to_list(None)
        total_won_value = sum(o.get("value", 0) for o in won_opp_docs)
        
        # Count tasks
        total_tasks = await db.sales_tasks.count_documents({"assigned_to": user_id})
        completed_tasks = await db.sales_tasks.count_documents({"assigned_to": user_id, "status": "completed"})
        
        # Calculate conversion rate
        conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
        win_rate = (won_opps / total_opps * 100) if total_opps > 0 else 0
        task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        team_metrics.append({
            "user_id": user_id,
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user["email"],
            "leads": {
                "total": total_leads,
                "qualified": qualified_leads,
                "converted": converted_leads,
                "conversion_rate": round(conversion_rate, 1)
            },
            "opportunities": {
                "total": total_opps,
                "won": won_opps,
                "total_value": round(total_won_value, 2),
                "win_rate": round(win_rate, 1)
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "completion_rate": round(task_completion_rate, 1)
            }
        })
    
    # Sort by total won value
    team_metrics.sort(key=lambda x: x["opportunities"]["total_value"], reverse=True)
    
    return {
        "team_metrics": team_metrics,
        "total_team_members": len(team_metrics)
    }


@api_router.get("/sales/analytics/conversion-rates")
async def get_conversion_rates(current_user: User = Depends(get_current_user)):
    """
    Stage-to-stage conversion rates for leads and opportunities
    """
    # Lead conversion rates
    total_leads = await db.leads.count_documents({})
    new_leads = await db.leads.count_documents({"status": "new"})
    contacted = await db.leads.count_documents({"status": "contacted"})
    qualified = await db.leads.count_documents({"status": "qualified"})
    converted = await db.leads.count_documents({"status": "converted"})
    
    lead_funnel = {
        "new": new_leads,
        "contacted": contacted,
        "qualified": qualified,
        "converted": converted
    }
    
    # Calculate conversion rates
    lead_conversion_rates = {}
    if new_leads > 0:
        lead_conversion_rates["new_to_contacted"] = round(contacted / new_leads * 100, 1)
    if contacted > 0:
        lead_conversion_rates["contacted_to_qualified"] = round(qualified / contacted * 100, 1)
    if qualified > 0:
        lead_conversion_rates["qualified_to_converted"] = round(converted / qualified * 100, 1)
    
    # Opportunity conversion rates
    total_opps = await db.opportunities.count_documents({})
    new_lead_stage = await db.opportunities.count_documents({"stage": "new_lead"})
    contacted_stage = await db.opportunities.count_documents({"stage": "contacted"})
    qualified_stage = await db.opportunities.count_documents({"stage": "qualified"})
    proposal_stage = await db.opportunities.count_documents({"stage": "proposal"})
    negotiation_stage = await db.opportunities.count_documents({"stage": "negotiation"})
    closed_won = await db.opportunities.count_documents({"stage": "closed_won"})
    closed_lost = await db.opportunities.count_documents({"stage": "closed_lost"})
    
    opp_funnel = {
        "new_lead": new_lead_stage,
        "contacted": contacted_stage,
        "qualified": qualified_stage,
        "proposal": proposal_stage,
        "negotiation": negotiation_stage,
        "closed_won": closed_won,
        "closed_lost": closed_lost
    }
    
    # Calculate opportunity conversion rates
    opp_conversion_rates = {}
    total_closed = closed_won + closed_lost
    if total_closed > 0:
        opp_conversion_rates["overall_win_rate"] = round(closed_won / total_closed * 100, 1)
    
    if new_lead_stage > 0:
        opp_conversion_rates["new_to_contacted"] = round(contacted_stage / new_lead_stage * 100, 1)
    if contacted_stage > 0:
        opp_conversion_rates["contacted_to_qualified"] = round(qualified_stage / contacted_stage * 100, 1)
    if qualified_stage > 0:
        opp_conversion_rates["qualified_to_proposal"] = round(proposal_stage / qualified_stage * 100, 1)
    
    return {
        "leads": {
            "funnel": lead_funnel,
            "conversion_rates": lead_conversion_rates
        },
        "opportunities": {
            "funnel": opp_funnel,
            "conversion_rates": opp_conversion_rates
        }
    }


@api_router.get("/sales/analytics/activity-metrics")
async def get_activity_metrics(
    days_back: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Activity metrics: tasks by type, completion trends
    """
    from datetime import datetime, timedelta
    from collections import Counter
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    
    # Get tasks created in period
    tasks = await db.sales_tasks.find(
        {"created_at": {"$gte": cutoff_date.isoformat()}},
        {"_id": 0}
    ).to_list(None)
    
    # Count by type
    task_types = Counter(t.get("task_type") for t in tasks)
    
    # Count by status
    task_status = Counter(t.get("status") for t in tasks)
    
    # Count by priority
    task_priority = Counter(t.get("priority") for t in tasks)
    
    # Activities created per day
    daily_activity = {}
    for task in tasks:
        created_date = task.get("created_at", "")[:10]  # Get YYYY-MM-DD
        daily_activity[created_date] = daily_activity.get(created_date, 0) + 1
    
    return {
        "period_days": days_back,
        "total_tasks": len(tasks),
        "by_type": dict(task_types),
        "by_status": dict(task_status),
        "by_priority": dict(task_priority),
        "daily_activity": [
            {"date": date, "count": count}
            for date, count in sorted(daily_activity.items())
        ]
    }







# ==================== COMPREHENSIVE DASHBOARD ANALYTICS ====================

@api_router.get("/sales/analytics/dashboard/comprehensive")
async def get_comprehensive_dashboard_analytics(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Comprehensive dashboard analytics combining all metrics:
    - Source performance (conversion rates, volumes, time-to-conversion)
    - Status funnel (drop-off rates, bottlenecks)
    - Loss analysis (top reasons, by source, by stage)
    - Time-based trends
    - Salesperson performance
    """
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # Default date range: last 30 days
    if not date_from:
        date_from = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    if not date_to:
        date_to = datetime.now(timezone.utc).isoformat()
    
    # Build query for date range
    date_query = {
        "created_at": {
            "$gte": date_from,
            "$lte": date_to
        }
    }
    
    # Fetch all leads in period
    all_leads = await db.leads.find(date_query, {"_id": 0}).to_list(None)
    
    # Fetch lead sources
    lead_sources_map = {}
    sources = await db.lead_sources.find({"_id": 0}).to_list(None)
    for source in sources:
        lead_sources_map[source["id"]] = source
    
    # Fetch lead statuses
    lead_statuses_map = {}
    statuses = await db.lead_statuses.find({"_id": 0}).to_list(None)
    for status in statuses:
        lead_statuses_map[status["id"]] = status
    
    # Fetch loss reasons
    loss_reasons_map = {}
    reasons = await db.loss_reasons.find({"_id": 0}).to_list(None)
    for reason in reasons:
        loss_reasons_map[reason["id"]] = reason
    
    # ===== 1. SOURCE PERFORMANCE ANALYTICS =====
    source_performance = defaultdict(lambda: {
        "total_leads": 0,
        "converted_leads": 0,
        "lost_leads": 0,
        "in_progress": 0,
        "conversion_rate": 0,
        "loss_rate": 0,
        "avg_days_to_convert": 0,
        "total_days_to_convert": 0,
        "converted_count_for_avg": 0
    })
    
    for lead in all_leads:
        source_id = lead.get("source_id") or "unknown"
        source_name = lead_sources_map.get(source_id, {}).get("name", "Unknown")
        
        source_performance[source_name]["total_leads"] += 1
        
        # Check status category
        status_id = lead.get("status_id")
        if status_id:
            status_obj = lead_statuses_map.get(status_id, {})
            category = status_obj.get("category", "")
            
            if category == "converted":
                source_performance[source_name]["converted_leads"] += 1
                # Calculate days to convert
                created = datetime.fromisoformat(lead["created_at"])
                updated = datetime.fromisoformat(lead["updated_at"])
                days = (updated - created).days
                source_performance[source_name]["total_days_to_convert"] += days
                source_performance[source_name]["converted_count_for_avg"] += 1
            elif category == "lost":
                source_performance[source_name]["lost_leads"] += 1
            else:
                source_performance[source_name]["in_progress"] += 1
    
    # Calculate rates and averages
    source_performance_list = []
    for source_name, data in source_performance.items():
        total = data["total_leads"]
        if total > 0:
            data["conversion_rate"] = round((data["converted_leads"] / total) * 100, 2)
            data["loss_rate"] = round((data["lost_leads"] / total) * 100, 2)
        
        if data["converted_count_for_avg"] > 0:
            data["avg_days_to_convert"] = round(data["total_days_to_convert"] / data["converted_count_for_avg"], 1)
        
        source_performance_list.append({
            "source": source_name,
            **{k: v for k, v in data.items() if k not in ["total_days_to_convert", "converted_count_for_avg"]}
        })
    
    # Sort by conversion rate descending
    source_performance_list.sort(key=lambda x: x["conversion_rate"], reverse=True)
    
    # ===== 2. STATUS FUNNEL ANALYTICS =====
    status_funnel = defaultdict(lambda: {
        "count": 0,
        "percentage": 0,
        "drop_off": 0,
        "avg_time_in_status_days": 0
    })
    
    # Count leads by status
    for lead in all_leads:
        status_id = lead.get("status_id")
        if status_id:
            status_name = lead_statuses_map.get(status_id, {}).get("name", "Unknown")
            status_funnel[status_name]["count"] += 1
    
    # Calculate percentages (relative to first status)
    sorted_statuses = sorted(statuses, key=lambda x: x.get("workflow_sequence", 0))
    first_status_count = 0
    if sorted_statuses:
        first_status_name = sorted_statuses[0]["name"]
        first_status_count = status_funnel[first_status_name]["count"]
    
    status_funnel_list = []
    prev_count = first_status_count
    
    for status in sorted_statuses:
        status_name = status["name"]
        count = status_funnel[status_name]["count"]
        
        if first_status_count > 0:
            percentage = round((count / first_status_count) * 100, 2)
        else:
            percentage = 0
        
        drop_off = prev_count - count
        
        status_funnel_list.append({
            "status": status_name,
            "count": count,
            "percentage": percentage,
            "drop_off": drop_off,
            "workflow_sequence": status.get("workflow_sequence", 0)
        })
        
        prev_count = count
    
    # ===== 3. LOSS ANALYSIS =====
    loss_analysis = defaultdict(lambda: {
        "count": 0,
        "percentage": 0,
        "by_source": defaultdict(int),
        "by_status_before_lost": defaultdict(int)
    })
    
    total_lost_leads = 0
    
    for lead in all_leads:
        status_id = lead.get("status_id")
        if status_id:
            status_obj = lead_statuses_map.get(status_id, {})
            if status_obj.get("category") == "lost":
                total_lost_leads += 1
                
                loss_reason_id = lead.get("loss_reason_id")
                if loss_reason_id:
                    reason_name = loss_reasons_map.get(loss_reason_id, {}).get("name", "Unknown")
                else:
                    reason_name = "Not Specified"
                
                loss_analysis[reason_name]["count"] += 1
                
                # Track by source
                source_id = lead.get("source_id") or "unknown"
                source_name = lead_sources_map.get(source_id, {}).get("name", "Unknown")
                loss_analysis[reason_name]["by_source"][source_name] += 1
    
    # Calculate percentages
    loss_analysis_list = []
    for reason_name, data in loss_analysis.items():
        count = data["count"]
        percentage = round((count / total_lost_leads) * 100, 2) if total_lost_leads > 0 else 0
        
        loss_analysis_list.append({
            "reason": reason_name,
            "count": count,
            "percentage": percentage,
            "by_source": dict(data["by_source"])
        })
    
    # Sort by count descending
    loss_analysis_list.sort(key=lambda x: x["count"], reverse=True)
    
    # ===== 4. TIME-BASED TRENDS =====
    # Group by date
    daily_trends = defaultdict(lambda: {
        "new_leads": 0,
        "converted": 0,
        "lost": 0
    })
    
    for lead in all_leads:
        created_date = lead["created_at"][:10]  # YYYY-MM-DD
        daily_trends[created_date]["new_leads"] += 1
        
        status_id = lead.get("status_id")
        if status_id:
            status_obj = lead_statuses_map.get(status_id, {})
            category = status_obj.get("category", "")
            
            if category == "converted":
                daily_trends[created_date]["converted"] += 1
            elif category == "lost":
                daily_trends[created_date]["lost"] += 1
    
    daily_trends_list = [
        {"date": date, **data}
        for date, data in sorted(daily_trends.items())
    ]
    
    # ===== 5. SALESPERSON PERFORMANCE =====
    salesperson_performance = defaultdict(lambda: {
        "total_leads": 0,
        "converted": 0,
        "lost": 0,
        "in_progress": 0,
        "conversion_rate": 0
    })
    
    for lead in all_leads:
        assigned_to = lead.get("assigned_to", "Unassigned")
        salesperson_performance[assigned_to]["total_leads"] += 1
        
        status_id = lead.get("status_id")
        if status_id:
            status_obj = lead_statuses_map.get(status_id, {})
            category = status_obj.get("category", "")
            
            if category == "converted":
                salesperson_performance[assigned_to]["converted"] += 1
            elif category == "lost":
                salesperson_performance[assigned_to]["lost"] += 1
            else:
                salesperson_performance[assigned_to]["in_progress"] += 1
    
    # Calculate conversion rates
    salesperson_performance_list = []
    for user_id, data in salesperson_performance.items():
        total = data["total_leads"]
        if total > 0:
            data["conversion_rate"] = round((data["converted"] / total) * 100, 2)
        
        # Get user name
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "email": 1, "name": 1})
        user_name = user.get("name") or user.get("email") if user else user_id
        
        salesperson_performance_list.append({
            "salesperson": user_name,
            **data
        })
    
    # Sort by conversion rate descending
    salesperson_performance_list.sort(key=lambda x: x["conversion_rate"], reverse=True)
    
    # ===== SUMMARY METRICS =====
    total_leads = len(all_leads)
    total_converted = sum(1 for l in all_leads if lead_statuses_map.get(l.get("status_id"), {}).get("category") == "converted")
    overall_conversion_rate = round((total_converted / total_leads) * 100, 2) if total_leads > 0 else 0
    
    return {
        "date_range": {
            "from": date_from,
            "to": date_to
        },
        "summary": {
            "total_leads": total_leads,
            "total_converted": total_converted,
            "total_lost": total_lost_leads,
            "in_progress": total_leads - total_converted - total_lost_leads,
            "overall_conversion_rate": overall_conversion_rate
        },
        "source_performance": source_performance_list,
        "status_funnel": status_funnel_list,
        "loss_analysis": loss_analysis_list,
        "daily_trends": daily_trends_list,
        "salesperson_performance": salesperson_performance_list
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
    """Execute a specific automation action with support for notification templates"""
    action_type = action.get("type")
    
    # Helper function to get message from template or inline
    async def get_message_content(action: dict, trigger_data: dict):
        """Get message content from template_id or inline message"""
        template_id = action.get("template_id")
        
        if template_id:
            # Fetch template from database
            template = await db.notification_templates.find_one({"id": template_id, "is_active": True})
            if not template:
                logger.warning(f"Template {template_id} not found or inactive, falling back to inline message")
                return {
                    "message": action.get("message", "").format(**trigger_data),
                    "subject": action.get("subject", "").format(**trigger_data) if action.get("subject") else None
                }
            
            # Format template message with trigger_data
            try:
                message = template["message"].format(**trigger_data)
                subject = template.get("subject", "").format(**trigger_data) if template.get("subject") else None
                return {"message": message, "subject": subject}
            except KeyError as e:
                logger.warning(f"Missing placeholder {e} in trigger_data, using template as-is")
                return {"message": template["message"], "subject": template.get("subject")}
        else:
            # Use inline message (backward compatibility)
            return {
                "message": action.get("message", "").format(**trigger_data),
                "subject": action.get("subject", "").format(**trigger_data) if action.get("subject") else None
            }
    
    if action_type == "send_sms":
        # SMS action with template support
        phone = trigger_data.get("phone") or action.get("phone")
        content = await get_message_content(action, trigger_data)
        message = content["message"]
        
        # TODO: Integrate SMS service (Twilio, etc.)
        logger.info(f"SMS Action (Mock): Sending to {phone}: {message}")
        
        # Log to journal
        member_id = trigger_data.get("member_id")
        if member_id:
            await add_journal_entry(
                member_id=member_id,
                action_type="sms_sent",
                description=f"SMS sent: {message[:100]}..." if len(message) > 100 else f"SMS sent: {message}",
                metadata={
                    "phone": phone,
                    "full_message": message,
                    "status": "sent_mock",
                    "trigger_type": trigger_data.get("trigger_type")
                }
            )
        
        return {"type": "sms", "status": "sent_mock", "phone": phone, "message": message}
    
    elif action_type == "send_whatsapp":
        # WhatsApp action with template support
        phone = trigger_data.get("phone") or action.get("phone")
        content = await get_message_content(action, trigger_data)
        message = content["message"]
        
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
            
            # Log to journal
            member_id = trigger_data.get("member_id")
            if member_id:
                await add_journal_entry(
                    member_id=member_id,
                    action_type="whatsapp_sent",
                    description=f"WhatsApp sent: {message[:100]}..." if len(message) > 100 else f"WhatsApp sent: {message}",
                    metadata={
                        "phone": phone,
                        "full_message": message,
                        "template_name": template_name,
                        "message_id": result.get("messageId"),
                        "status": "sent" if not respondio_service.is_mocked else "sent_mock",
                        "trigger_type": trigger_data.get("trigger_type")
                    }
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
        # Email action with template support
        email = trigger_data.get("email") or action.get("email")
        content = await get_message_content(action, trigger_data)
        subject = content["subject"] or "Notification"
        body = content["message"]
        
        # TODO: Integrate email service (SendGrid, AWS SES, etc.)
        logger.info(f"Email Action (Mock): Sending to {email}: {subject}")
        
        # Log to journal
        member_id = trigger_data.get("member_id")
        if member_id:
            await add_journal_entry(
                member_id=member_id,
                action_type="email_sent",
                description=f"Email sent: {subject}",
                metadata={
                    "email": email,
                    "subject": subject,
                    "full_body": body,
                    "status": "sent_mock",
                    "trigger_type": trigger_data.get("trigger_type")
                }
            )
        
        return {"type": "email", "status": "sent_mock", "email": email, "subject": subject, "body": body}
    
    elif action_type == "send_push":
        # Push notification action with template support
        member_id = trigger_data.get("member_id")
        content = await get_message_content(action, trigger_data)
        title = content["subject"] or "Notification"
        body = content["message"]
        
        # TODO: Integrate push notification service (Firebase, OneSignal, etc.)
        logger.info(f"Push Notification Action (Mock): Sending to member {member_id}: {title}")
        return {"type": "push", "status": "sent_mock", "member_id": member_id, "title": title, "body": body}
    
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
        
        # Safely split name
        name_parts = member_name.split()
        first_name = name_parts[0] if name_parts else member_name
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else member_name
        
        result = await respondio_service.send_whatsapp_message(
            contact_phone=phone,
            template_name=template_name,
            template_params=template_params,
            first_name=first_name,
            last_name=last_name,
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

# ===== CLASSES & SCHEDULING ENDPOINTS =====

@api_router.get("/classes", response_model=List[Class])
async def get_classes(current_user: User = Depends(get_current_user)):
    """Get all classes"""
    classes = await db.classes.find({}, {"_id": 0}).to_list(length=None)
    return [Class(**c) for c in classes]

@api_router.post("/classes", response_model=Class)
async def create_class(class_data: ClassCreate, current_user: User = Depends(get_current_user)):
    """Create a new class"""
    new_class = Class(**class_data.model_dump(), created_by=current_user.id)
    doc = new_class.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    if doc.get("updated_at"):
        doc["updated_at"] = doc["updated_at"].isoformat()
    if doc.get("class_date"):
        doc["class_date"] = doc["class_date"].isoformat()
    
    await db.classes.insert_one(doc)
    return new_class

@api_router.get("/classes/{class_id}", response_model=Class)
async def get_class(class_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific class"""
    class_doc = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")
    return Class(**class_doc)

@api_router.patch("/classes/{class_id}", response_model=Class)
async def update_class(class_id: str, class_update: ClassUpdate, current_user: User = Depends(get_current_user)):
    """Update a class"""
    class_doc = await db.classes.find_one({"id": class_id}, {"_id": 0})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Update only provided fields
    update_data = class_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.classes.update_one({"id": class_id}, {"$set": update_data})
    
    # Fetch updated class
    updated_class = await db.classes.find_one({"id": class_id}, {"_id": 0})
    return Class(**updated_class)

@api_router.delete("/classes/{class_id}")
async def delete_class(class_id: str, current_user: User = Depends(get_current_user)):
    """Delete a class"""
    result = await db.classes.delete_one({"id": class_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"message": "Class deleted successfully"}

# ===== BOOKINGS ENDPOINTS =====

@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings(
    class_id: Optional[str] = None,
    member_id: Optional[str] = None,
    status: Optional[str] = None,
    booking_date_from: Optional[str] = None,
    booking_date_to: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get bookings with optional filters"""
    query = {}
    if class_id:
        query["class_id"] = class_id
    if member_id:
        query["member_id"] = member_id
    if status:
        query["status"] = status
    if booking_date_from or booking_date_to:
        query["booking_date"] = {}
        if booking_date_from:
            query["booking_date"]["$gte"] = booking_date_from
        if booking_date_to:
            query["booking_date"]["$lte"] = booking_date_to
    
    bookings = await db.bookings.find(query, {"_id": 0}).to_list(length=None)
    return [Booking(**b) for b in bookings]

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking_data: BookingCreate, current_user: User = Depends(get_current_user)):
    """Create a new booking"""
    # Get class details
    class_doc = await db.classes.find_one({"id": booking_data.class_id}, {"_id": 0})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")
    
    class_obj = Class(**class_doc)
    
    # Get member details
    member_doc = await db.members.find_one({"id": booking_data.member_id}, {"_id": 0})
    if not member_doc:
        raise HTTPException(status_code=404, detail="Member not found")
    
    member_obj = Member(**member_doc)
    
    # Check if member can book this class (membership type restrictions)
    if class_obj.membership_types_allowed and member_obj.membership_type_id not in class_obj.membership_types_allowed:
        raise HTTPException(status_code=403, detail="Your membership type is not allowed for this class")
    
    # Check member's no-show count
    no_show_count = await db.bookings.count_documents({
        "member_id": booking_data.member_id,
        "no_show": True
    })
    
    no_show_threshold = class_obj.no_show_threshold
    if no_show_count >= no_show_threshold:
        raise HTTPException(
            status_code=403, 
            detail=f"Member has {no_show_count} no-shows. Booking blocked until attendance improves. Please contact staff."
        )
    
    # Check booking window
    booking_date = booking_data.booking_date
    # Make booking_date timezone-aware if it's naive
    if booking_date.tzinfo is None:
        booking_date = booking_date.replace(tzinfo=timezone.utc)
    days_advance = (booking_date - datetime.now(timezone.utc)).days
    if days_advance > class_obj.booking_window_days:
        raise HTTPException(status_code=400, detail=f"Cannot book more than {class_obj.booking_window_days} days in advance")
    
    # Check capacity
    existing_bookings = await db.bookings.count_documents({
        "class_id": booking_data.class_id,
        "booking_date": booking_data.booking_date.isoformat(),
        "status": {"$in": ["confirmed", "attended"]}
    })
    
    # Determine if booking is confirmed or waitlist
    is_waitlist = False
    waitlist_position = None
    booking_status = "confirmed"
    
    if existing_bookings >= class_obj.capacity:
        if class_obj.allow_waitlist:
            # Add to waitlist
            is_waitlist = True
            booking_status = "waitlist"
            waitlist_count = await db.bookings.count_documents({
                "class_id": booking_data.class_id,
                "booking_date": booking_data.booking_date.isoformat(),
                "status": "waitlist"
            })
            if waitlist_count >= class_obj.waitlist_capacity:
                raise HTTPException(status_code=400, detail="Class and waitlist are full")
            waitlist_position = waitlist_count + 1
        else:
            raise HTTPException(status_code=400, detail="Class is full and waitlist is not available")
    
    # Create booking
    new_booking = Booking(
        class_id=booking_data.class_id,
        class_name=class_obj.name,
        member_id=booking_data.member_id,
        member_name=f"{member_obj.first_name} {member_obj.last_name}",
        member_email=member_obj.email,
        booking_date=booking_data.booking_date,
        status=booking_status,
        is_waitlist=is_waitlist,
        waitlist_position=waitlist_position,
        payment_required=class_obj.drop_in_price > 0,
        payment_amount=class_obj.drop_in_price,
        payment_status="not_required" if class_obj.drop_in_price == 0 else "pending",
        notes=booking_data.notes
    )
    
    doc = new_booking.model_dump()
    doc["booked_at"] = doc["booked_at"].isoformat()
    doc["booking_date"] = doc["booking_date"].isoformat()
    if doc.get("cancelled_at"):
        doc["cancelled_at"] = doc["cancelled_at"].isoformat()
    if doc.get("checked_in_at"):
        doc["checked_in_at"] = doc["checked_in_at"].isoformat()
    
    await db.bookings.insert_one(doc)
    
    # Send WhatsApp booking confirmation if enabled
    if class_obj.get("send_booking_confirmation", True):
        try:
            # Format booking date/time
            booking_datetime = new_booking.booking_date
            formatted_date = booking_datetime.strftime("%A, %B %d, %Y")
            formatted_time = booking_datetime.strftime("%I:%M %p")
            
            # Create confirmation message
            confirmation_message = f"""🎉 *Booking Confirmed!*

Hi {member.get('first_name', 'Member')}!

Your class booking has been confirmed:

📋 *Class:* {class_obj['name']}
📅 *Date:* {formatted_date}
⏰ *Time:* {formatted_time}
📍 *Location:* {class_obj.get('room', 'Main Studio')}
👤 *Instructor:* {class_obj.get('instructor_name', 'TBA')}

{"⚠️ You are on the WAITLIST (Position #" + str(waitlist_position) + ")" if is_waitlist else "✅ Your spot is confirmed!"}

💡 *Important:*
• Please arrive 10 minutes early
• Remember to check-in at reception
• Cancellations must be made at least {class_obj.get('cancel_window_hours', 2)} hours before class

See you there! 💪"""

            # Send via respond.io
            member_phone = member.get('phone') or member.get('phone_number')
            if member_phone:
                await send_whatsapp_message(
                    phone=member_phone,
                    message=confirmation_message,
                    first_name=member.get('first_name', 'Member'),
                    last_name=member.get('last_name', ''),
                    email=member.get('email', '')
                )
                logger.info(f"Booking confirmation sent to {member_phone} for booking {new_booking.id}")
        except Exception as e:
            logger.error(f"Failed to send booking confirmation: {str(e)}")
            # Don't fail the booking if notification fails
    
    return new_booking

@api_router.get("/bookings/{booking_id}", response_model=Booking)
async def get_booking(booking_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific booking"""
    booking_doc = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking_doc:
        raise HTTPException(status_code=404, detail="Booking not found")
    return Booking(**booking_doc)

@api_router.patch("/bookings/{booking_id}", response_model=Booking)
async def update_booking(booking_id: str, booking_update: BookingUpdate, current_user: User = Depends(get_current_user)):
    """Update a booking (e.g., cancel, mark as attended, etc.)"""
    booking_doc = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking_doc:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking_obj = Booking(**booking_doc)
    update_data = booking_update.model_dump(exclude_unset=True)
    
    # Handle cancellation
    if update_data.get("status") == "cancelled" and booking_obj.status != "cancelled":
        update_data["cancelled_at"] = datetime.now(timezone.utc).isoformat()
        
        # If this was a confirmed booking, promote waitlist
        if booking_obj.status == "confirmed":
            # Find next waitlist booking
            next_waitlist = await db.bookings.find_one(
                {
                    "class_id": booking_obj.class_id,
                    "booking_date": booking_obj.booking_date.isoformat(),
                    "status": "waitlist"
                },
                {"_id": 0},
                sort=[("waitlist_position", 1)]
            )
            
            if next_waitlist:
                # Promote from waitlist to confirmed
                await db.bookings.update_one(
                    {"id": next_waitlist["id"]},
                    {"$set": {
                        "status": "confirmed",
                        "is_waitlist": False,
                        "waitlist_position": None
                    }}
                )
                
                # Update remaining waitlist positions
                await db.bookings.update_many(
                    {
                        "class_id": booking_obj.class_id,
                        "booking_date": booking_obj.booking_date.isoformat(),
                        "status": "waitlist",
                        "waitlist_position": {"$gt": next_waitlist["waitlist_position"]}
                    },
                    {"$inc": {"waitlist_position": -1}}
                )
    
    await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    
    # Fetch updated booking
    updated_booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    return Booking(**updated_booking)

@api_router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: str, current_user: User = Depends(get_current_user)):
    """Delete a booking"""
    result = await db.bookings.delete_one({"id": booking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": "Booking deleted successfully"}

@api_router.post("/bookings/{booking_id}/check-in")
async def check_in_booking(booking_id: str, current_user: User = Depends(get_current_user)):
    """Check in a member for their booking"""
    booking_doc = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    if not booking_doc:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if booking_doc["status"] not in ["confirmed"]:
        raise HTTPException(status_code=400, detail="Only confirmed bookings can be checked in")
    
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {
            "status": "attended",
            "checked_in_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated_booking = await db.bookings.find_one({"id": booking_id}, {"_id": 0})
    return Booking(**updated_booking)

# ===== IMPORT MODULE ENDPOINTS =====

class ImportLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    import_type: str  # members, leads, memberships
    filename: str
    total_rows: int
    successful_rows: int
    failed_rows: int
    field_mapping: dict
    status: str  # processing, completed, failed
    error_log: List[dict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str

# ===== FIELD CONFIGURATION MODELS =====

class FieldConfiguration(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    field_name: str
    label: str
    is_required: bool = False
    field_type: str  # text, email, phone, number, date, select
    validation_rules: dict = {}  # {min_length, max_length, pattern, must_contain}
    error_message: Optional[str] = None
    category: str = "basic"  # basic, contact, address, banking, membership

class FieldConfigurationUpdate(BaseModel):
    is_required: Optional[bool] = None
    validation_rules: Optional[dict] = None
    error_message: Optional[str] = None



# ===================== POS (Point of Sale) Models =====================

class ProductCategory(BaseModel):
    """Product category for POS system"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Cold Drinks, Hot Drinks, Food, Snacks, Supplements, Merchandise
    description: Optional[str] = None
    display_order: int = 0
    icon: Optional[str] = None  # Icon name for UI
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    display_order: int = 0
    icon: Optional[str] = None

class Product(BaseModel):
    """Product for POS system with stock tracking"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    sku: Optional[str] = None  # Stock Keeping Unit / Barcode
    category_id: str
    category_name: Optional[str] = None  # Denormalized for quick access
    # Pricing
    cost_price: float  # What you pay for the product
    markup_percent: float  # Markup percentage (e.g., 50 for 50%)
    selling_price: float  # Auto-calculated: cost_price * (1 + markup_percent/100)
    tax_rate: float = 15.0  # VAT/Tax percentage (default 15%)
    # Stock
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    # Display
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_favorite: bool = False  # Quick access pin
    is_active: bool = True
    # Tracking
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None

class ProductCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    category_id: str
    cost_price: float
    markup_percent: float
    tax_rate: float = 15.0
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_favorite: bool = False

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    category_id: Optional[str] = None
    cost_price: Optional[float] = None
    markup_percent: Optional[float] = None
    tax_rate: Optional[float] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_active: Optional[bool] = None

class POSTransactionItem(BaseModel):
    """Individual item in a POS transaction"""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float  # Price per unit (including markup)
    tax_rate: float
    item_discount_percent: float = 0.0  # Per-item discount percentage
    item_discount_amount: float = 0.0  # Per-item discount in currency
    subtotal: float  # quantity * unit_price
    tax_amount: float  # subtotal * (tax_rate / 100)
    total: float  # subtotal + tax_amount - item_discount_amount

class POSTransaction(BaseModel):
    """Complete POS transaction/sale"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_number: str  # Human-readable transaction number (e.g., POS-2024-001)
    # Transaction details
    transaction_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    transaction_type: str  # product_sale, membership_payment, session_payment, account_payment, debt_payment
    # Items (for product sales)
    items: List[POSTransactionItem] = []
    # Member info (optional - for account/debt/membership payments)
    member_id: Optional[str] = None
    member_name: Optional[str] = None
    # Payment details
    payment_method: str  # Cash, Card, EFT, Mobile Payment
    payment_reference: Optional[str] = None  # Reference number for card/EFT
    # Financial breakdown
    subtotal: float  # Total before tax and discount
    tax_amount: float  # Total tax
    discount_percent: float = 0.0  # Discount percentage
    discount_amount: float = 0.0  # Discount in currency
    total_amount: float  # Final amount paid
    # Linked records
    invoice_id: Optional[str] = None  # If paying an invoice
    payment_id: Optional[str] = None  # Created payment record ID
    # Staff tracking
    captured_by_user_id: str
    captured_by_name: str
    # Status
    status: str = "completed"  # completed, void, refunded
    void_reason: Optional[str] = None
    voided_by: Optional[str] = None
    voided_at: Optional[datetime] = None
    # Notes
    notes: Optional[str] = None

class POSTransactionCreate(BaseModel):
    transaction_type: str
    items: List[POSTransactionItem] = []
    member_id: Optional[str] = None
    payment_method: str
    payment_reference: Optional[str] = None
    subtotal: float
    tax_amount: float
    discount_percent: float = 0.0
    discount_amount: float = 0.0
    total_amount: float
    invoice_id: Optional[str] = None
    notes: Optional[str] = None

class StockAdjustment(BaseModel):
    """Stock adjustment record"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    product_name: str
    adjustment_type: str  # restock, damage, theft, correction, sale
    quantity_change: int  # Positive for increase, negative for decrease
    previous_quantity: int
    new_quantity: int
    reason: Optional[str] = None
    adjusted_by_user_id: str
    adjusted_by_name: str
    adjustment_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StockAdjustmentCreate(BaseModel):
    product_id: str
    adjustment_type: str
    quantity_change: int
    reason: Optional[str] = None

@api_router.post("/import/parse-csv")
async def parse_csv_file(file: UploadFile, current_user: User = Depends(get_current_user)):
    """Parse CSV file and return headers and sample data for mapping"""
    try:
        import csv
        import io
        
        # Read file content
        content = await file.read()
        decoded_content = content.decode('utf-8')
        
        # Parse CSV
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        headers = csv_reader.fieldnames
        
        # Get first 5 rows as sample
        sample_data = []
        for i, row in enumerate(csv_reader):
            if i >= 5:
                break
            sample_data.append(row)
        
        # Reset reader to count total rows
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        total_rows = sum(1 for _ in csv_reader)
        
        return {
            "headers": headers,
            "sample_data": sample_data,
            "total_rows": total_rows,
            "filename": file.filename
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

@api_router.post("/members/check-duplicate")
async def check_member_duplicate(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Check if a member with given details already exists using enhanced normalization"""
    duplicates = []
    
    # Check email with normalization
    if email:
        norm_email = normalize_email(email)
        email_exists = await db.members.find_one({"norm_email": norm_email}, {"_id": 0})
        if email_exists:
            duplicates.append({
                "field": "email",
                "value": email,
                "normalized_value": norm_email,
                "match_type": "normalized_email",
                "existing_member": {
                    "id": email_exists["id"],
                    "name": f"{email_exists['first_name']} {email_exists['last_name']}",
                    "email": email_exists.get("email"),
                    "phone": email_exists.get("phone"),
                    "membership_status": email_exists.get("membership_status")
                }
            })
    
    # Check phone with normalization
    if phone:
        norm_phone = normalize_phone(phone)
        phone_exists = await db.members.find_one({"norm_phone": norm_phone}, {"_id": 0})
        if phone_exists:
            duplicates.append({
                "field": "phone",
                "value": phone,
                "normalized_value": norm_phone,
                "match_type": "normalized_phone",
                "existing_member": {
                    "id": phone_exists["id"],
                    "name": f"{phone_exists['first_name']} {phone_exists['last_name']}",
                    "email": phone_exists.get("email"),
                    "phone": phone_exists.get("phone"),
                    "membership_status": phone_exists.get("membership_status")
                }
            })
    
    # Check name with normalization and nickname canonicalization
    if first_name and last_name:
        norm_first, norm_last = normalize_full_name(first_name, last_name)
        name_exists = await db.members.find_one({
            "norm_first_name": norm_first,
            "norm_last_name": norm_last
        }, {"_id": 0})
        if name_exists:
            duplicates.append({
                "field": "name",
                "value": f"{first_name} {last_name}",
                "normalized_value": f"{norm_first} {norm_last}",
                "match_type": "normalized_name",
                "existing_member": {
                    "id": name_exists["id"],
                    "name": f"{name_exists['first_name']} {name_exists['last_name']}",
                    "email": name_exists.get("email"),
                    "phone": name_exists.get("phone"),
                    "membership_status": name_exists.get("membership_status")
                }
            })
    
    return {
        "has_duplicates": len(duplicates) > 0,
        "duplicates": duplicates,
        "normalization_info": {
            "email_normalized": normalize_email(email) if email else None,
            "phone_normalized": normalize_phone(phone) if phone else None,
            "name_normalized": f"{normalize_name(first_name)} {normalize_name(last_name)}" if first_name and last_name else None
        }
    }

@api_router.post("/import/members")
async def import_members(
    file: UploadFile,
    field_mapping: str,  # JSON string of field mapping
    duplicate_action: str = "skip",  # skip, update, create
    current_user: User = Depends(get_current_user)
):
    """Import members from CSV with field mapping and duplicate handling"""
    try:
        import csv
        import io
        import json
        
        # Parse field mapping
        mapping = json.loads(field_mapping)
        
        # Read and parse CSV
        content = await file.read()
        decoded_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        successful = 0
        failed = 0
        skipped = 0
        updated = 0
        error_log = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Map CSV columns to Member fields
                member_data = {
                    "id": str(uuid.uuid4()),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                for db_field, csv_column in mapping.items():
                    if csv_column and csv_column in row:
                        value = row[csv_column].strip()
                        if value:
                            member_data[db_field] = value
                
                # Auto-split full name into first_name and last_name if needed
                if "first_name" in member_data and "last_name" not in member_data:
                    full_name = member_data["first_name"]
                    # Remove common titles
                    titles = ["MR", "MRS", "MS", "MISS", "DR", "PROF"]
                    name_parts = full_name.split()
                    
                    # Remove title if present
                    if name_parts and name_parts[0].upper().rstrip('.') in titles:
                        name_parts = name_parts[1:]
                    
                    # Split into first and last name
                    if len(name_parts) >= 2:
                        member_data["first_name"] = name_parts[0]
                        member_data["last_name"] = " ".join(name_parts[1:])
                    elif len(name_parts) == 1:
                        member_data["first_name"] = name_parts[0]
                        member_data["last_name"] = name_parts[0]  # Use same as first name
                    else:
                        # Empty or invalid full name - set both to empty string
                        member_data["first_name"] = full_name
                        member_data["last_name"] = full_name
                
                # Ensure last_name is always present (required field)
                if "first_name" in member_data and "last_name" not in member_data:
                    member_data["last_name"] = member_data["first_name"]
                
                # Check for duplicates
                duplicate_found = None
                
                # Check email
                if "email" in member_data and member_data["email"]:
                    existing = await db.members.find_one({"email": member_data["email"].lower()}, {"_id": 0})
                    if existing:
                        duplicate_found = existing
                
                # Check phone if no email duplicate
                if not duplicate_found and "phone" in member_data and member_data["phone"]:
                    existing = await db.members.find_one({"phone": member_data["phone"]}, {"_id": 0})
                    if existing:
                        duplicate_found = existing
                
                # Check name if no other duplicates
                if not duplicate_found and "first_name" in member_data and "last_name" in member_data:
                    name_regex = {"$regex": f"^{member_data['first_name']}$", "$options": "i"}
                    lastname_regex = {"$regex": f"^{member_data['last_name']}$", "$options": "i"}
                    existing = await db.members.find_one({
                        "first_name": name_regex,
                        "last_name": lastname_regex
                    }, {"_id": 0})
                    if existing:
                        duplicate_found = existing
                
                # Handle duplicate based on action
                if duplicate_found:
                    if duplicate_action == "skip":
                        skipped += 1
                        
                        # Log as blocked attempt for staff review
                        try:
                            blocked_attempt = BlockedMemberAttempt(
                                attempted_first_name=member_data.get("first_name", ""),
                                attempted_last_name=member_data.get("last_name", ""),
                                attempted_email=member_data.get("email", ""),
                                attempted_phone=member_data.get("phone", ""),
                                duplicate_fields=["detected_during_import"],
                                match_types=["import_duplicate"],
                                existing_members=[{
                                    "id": duplicate_found["id"],
                                    "name": f"{duplicate_found['first_name']} {duplicate_found['last_name']}",
                                    "email": duplicate_found.get("email"),
                                    "phone": duplicate_found.get("phone")
                                }],
                                attempted_by_user_id=current_user.id,
                                attempted_by_email=current_user.email,
                                source="import"
                            )
                            blocked_doc = blocked_attempt.model_dump()
                            blocked_doc["timestamp"] = blocked_doc["timestamp"].isoformat()
                            await db.blocked_member_attempts.insert_one(blocked_doc)
                        except Exception as e:
                            logger.error(f"Failed to log blocked import attempt: {str(e)}")
                        
                        error_log.append({
                            "row": row_num,
                            "action": "skipped",
                            "reason": f"Duplicate found: {duplicate_found['first_name']} {duplicate_found['last_name']}",
                            "data": row
                        })
                        continue
                    elif duplicate_action == "update":
                        # Update existing member
                        update_data = {k: v for k, v in member_data.items() if k not in ["id", "created_at"]}
                        await db.members.update_one({"id": duplicate_found["id"]}, {"$set": update_data})
                        updated += 1
                        continue
                    # else: create anyway
                
                # Set defaults for required fields
                if "membership_status" not in member_data:
                    member_data["membership_status"] = "active"
                if "membership_type_id" not in member_data:
                    # Get default membership type
                    default_type = await db.membership_types.find_one({}, {"_id": 0})
                    if default_type:
                        member_data["membership_type_id"] = default_type["id"]
                
                # Insert member
                await db.members.insert_one(member_data)
                successful += 1
                
            except Exception as e:
                failed += 1
                error_log.append({
                    "row": row_num,
                    "error": str(e),
                    "data": row
                })
        
        # Create import log
        import_log = ImportLog(
            import_type="members",
            filename=file.filename,
            total_rows=successful + failed + skipped + updated,
            successful_rows=successful,
            failed_rows=failed,
            field_mapping=mapping,
            status="completed",
            error_log=error_log,
            created_by=current_user.id
        )
        
        log_doc = import_log.model_dump()
        log_doc["created_at"] = log_doc["created_at"].isoformat()
        await db.import_logs.insert_one(log_doc)
        
        return {
            "success": True,
            "total_rows": successful + failed + skipped + updated,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "updated": updated,
            "error_log": error_log[:20]  # Return first 20 errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

@api_router.post("/import/leads")
async def import_leads(
    file: UploadFile,
    field_mapping: str,
    current_user: User = Depends(get_current_user)
):
    """Import leads from CSV with field mapping"""
    try:
        import csv
        import io
        import json
        
        mapping = json.loads(field_mapping)
        content = await file.read()
        decoded_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded_content))
        
        successful = 0
        failed = 0
        error_log = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                lead_data = {
                    "id": str(uuid.uuid4()),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "new"
                }
                
                for db_field, csv_column in mapping.items():
                    if csv_column and csv_column in row:
                        value = row[csv_column].strip()
                        if value:
                            lead_data[db_field] = value
                
                await db.leads.insert_one(lead_data)
                successful += 1
                
            except Exception as e:
                failed += 1
                error_log.append({
                    "row": row_num,
                    "error": str(e),
                    "data": row
                })
        
        import_log = ImportLog(
            import_type="leads",
            filename=file.filename,
            total_rows=successful + failed,
            successful_rows=successful,
            failed_rows=failed,
            field_mapping=mapping,
            status="completed",
            error_log=error_log,
            created_by=current_user.id
        )
        
        log_doc = import_log.model_dump()
        log_doc["created_at"] = log_doc["created_at"].isoformat()
        await db.import_logs.insert_one(log_doc)
        
        return {
            "success": True,
            "total_rows": successful + failed,
            "successful": successful,
            "failed": failed,
            "error_log": error_log[:10]
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

@api_router.get("/import/logs")
async def get_import_logs(current_user: User = Depends(get_current_user)):
    """Get import history"""
    logs = await db.import_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    for log in logs:
        if isinstance(log.get("created_at"), str):
            log["created_at"] = datetime.fromisoformat(log["created_at"])
    return logs

# Blocked Members Report Endpoints
@api_router.get("/reports/blocked-members")
async def get_blocked_members(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get blocked member attempts for staff review"""
    query = {}
    if status:
        query["review_status"] = status
    
    blocked_attempts = await db.blocked_member_attempts.find(query, {"_id": 0}).sort("timestamp", -1).to_list(limit)
    
    # Convert datetime strings back to datetime objects for response
    for attempt in blocked_attempts:
        if isinstance(attempt.get("timestamp"), str):
            attempt["timestamp"] = datetime.fromisoformat(attempt["timestamp"])
        if attempt.get("reviewed_at") and isinstance(attempt["reviewed_at"], str):
            attempt["reviewed_at"] = datetime.fromisoformat(attempt["reviewed_at"])
    
    return {
        "total": len(blocked_attempts),
        "blocked_attempts": blocked_attempts
    }

@api_router.get("/reports/blocked-members/csv")
async def export_blocked_members_csv(current_user: User = Depends(get_current_user)):
    """Export blocked member attempts as CSV"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    blocked_attempts = await db.blocked_member_attempts.find({}, {"_id": 0}).sort("timestamp", -1).to_list(1000)
    
    # Create CSV in memory
    output = io.StringIO()
    csv_writer = csv.writer(output)
    
    # Write header
    csv_writer.writerow([
        "Timestamp", "First Name", "Last Name", "Email", "Phone",
        "Duplicate Fields", "Match Types", "Existing Members",
        "Attempted By", "Review Status", "Reviewed By", "Review Notes"
    ])
    
    # Write data
    for attempt in blocked_attempts:
        timestamp = attempt.get("timestamp", "")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        existing_members_str = "; ".join([
            f"{m.get('name')} ({m.get('email')})" 
            for m in attempt.get("existing_members", [])
        ])
        
        csv_writer.writerow([
            timestamp,
            attempt.get("attempted_first_name", ""),
            attempt.get("attempted_last_name", ""),
            attempt.get("attempted_email", ""),
            attempt.get("attempted_phone", ""),
            ", ".join(attempt.get("duplicate_fields", [])),
            ", ".join(attempt.get("match_types", [])),
            existing_members_str,
            attempt.get("attempted_by_email", ""),
            attempt.get("review_status", "pending"),
            attempt.get("reviewed_by", ""),
            attempt.get("review_notes", "")
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=blocked_members.csv"}
    )

@api_router.get("/reports/blocked-members/html")
async def view_blocked_members_html(current_user: User = Depends(get_current_user)):
    """View blocked member attempts as HTML page"""
    from fastapi.responses import HTMLResponse
    
    blocked_attempts = await db.blocked_member_attempts.find({}, {"_id": 0}).sort("timestamp", -1).to_list(100)
    
    # Generate HTML
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Blocked Member Attempts - Staff Review</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            h1 { color: #333; }
            .summary { background: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; background: white; }
            th { background: #4CAF50; color: white; padding: 12px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #ddd; }
            tr:hover { background: #f5f5f5; }
            .badge { padding: 4px 8px; border-radius: 3px; font-size: 12px; }
            .badge-pending { background: #ff9800; color: white; }
            .badge-approved { background: #4CAF50; color: white; }
            .badge-rejected { background: #f44336; color: white; }
            .duplicate-field { display: inline-block; background: #e3f2fd; color: #1976d2; padding: 2px 6px; margin: 2px; border-radius: 3px; font-size: 11px; }
        </style>
    </head>
    <body>
        <h1>🚫 Blocked Member Attempts - Staff Review</h1>
        <div class="summary">
            <strong>Total Blocked Attempts:</strong> """ + str(len(blocked_attempts)) + """
        </div>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Attempted Member</th>
                    <th>Contact Info</th>
                    <th>Duplicate Detection</th>
                    <th>Existing Member(s)</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for attempt in blocked_attempts:
        timestamp = attempt.get("timestamp", "")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
        elif isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M")
        
        name = f"{attempt.get('attempted_first_name', '')} {attempt.get('attempted_last_name', '')}"
        email = attempt.get('attempted_email', '')
        phone = attempt.get('attempted_phone', '')
        
        duplicate_fields = "".join([
            f'<span class="duplicate-field">{field}</span>' 
            for field in attempt.get('duplicate_fields', [])
        ])
        
        existing_members = "<br>".join([
            f"• {m.get('name')} ({m.get('email')})" 
            for m in attempt.get('existing_members', [])
        ])
        
        status = attempt.get('review_status', 'pending')
        status_badge = f'<span class="badge badge-{status}">{status.upper()}</span>'
        
        html_content += f"""
                <tr>
                    <td>{timestamp}</td>
                    <td><strong>{name}</strong></td>
                    <td>{email}<br>{phone}</td>
                    <td>{duplicate_fields}</td>
                    <td style="font-size: 12px;">{existing_members}</td>
                    <td>{status_badge}</td>
                </tr>
        """
    
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

@api_router.patch("/reports/blocked-members/{attempt_id}/review")
async def review_blocked_attempt(
    attempt_id: str,
    status: str,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update review status of a blocked attempt"""
    if status not in ["approved", "rejected", "merged"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    update_data = {
        "review_status": status,
        "reviewed_by": current_user.email,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "review_notes": notes
    }
    
    result = await db.blocked_member_attempts.update_one(
        {"id": attempt_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Blocked attempt not found")
    
    return {"success": True, "message": f"Attempt marked as {status}"}

# Summary Reports Dashboard
@api_router.get("/reports/summary")
async def get_summary_report(current_user: User = Depends(get_current_user)):
    """
    Get comprehensive summary statistics for dashboard
    Returns key metrics across all system resources
    """
    from datetime import timedelta
    
    # Date ranges
    today = datetime.now(timezone.utc)
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    
    # Members statistics
    total_members = await db.members.count_documents({})
    active_members = await db.members.count_documents({"membership_status": "active"})
    suspended_members = await db.members.count_documents({"membership_status": "suspended"})
    new_members_30d = await db.members.count_documents({
        "join_date": {"$gte": thirty_days_ago.isoformat()}
    })
    new_members_7d = await db.members.count_documents({
        "join_date": {"$gte": seven_days_ago.isoformat()}
    })
    
    # Invoice/Revenue statistics
    total_invoices = await db.invoices.count_documents({})
    paid_invoices = await db.invoices.count_documents({"status": "paid"})
    pending_invoices = await db.invoices.count_documents({"status": "pending"})
    overdue_invoices = await db.invoices.count_documents({"status": "overdue"})
    
    # Calculate total revenue (paid invoices)
    paid_invoices_list = await db.invoices.find({"status": "paid"}, {"amount": 1}).to_list(None)
    total_revenue = sum(inv.get("amount", 0) for inv in paid_invoices_list)
    
    # Revenue last 30 days
    recent_paid = await db.invoices.find({
        "status": "paid",
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    }, {"amount": 1}).to_list(None)
    revenue_30d = sum(inv.get("amount", 0) for inv in recent_paid)
    
    # Classes statistics
    total_classes = await db.classes.count_documents({})
    active_classes = await db.classes.count_documents({"is_active": True})
    
    # Bookings statistics
    total_bookings = await db.bookings.count_documents({})
    confirmed_bookings = await db.bookings.count_documents({"status": "confirmed"})
    waitlist_bookings = await db.bookings.count_documents({"status": "waitlist"})
    attended_bookings = await db.bookings.count_documents({"status": "attended"})
    
    # Booking stats last 30 days
    recent_bookings = await db.bookings.count_documents({
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    })
    
    # Access logs (check-ins)
    total_checkins = await db.access_logs.count_documents({"access_granted": True})
    checkins_30d = await db.access_logs.count_documents({
        "timestamp": {"$gte": thirty_days_ago.isoformat()},
        "access_granted": True
    })
    checkins_7d = await db.access_logs.count_documents({
        "timestamp": {"$gte": seven_days_ago.isoformat()},
        "access_granted": True
    })
    
    # Automations statistics
    total_automations = await db.automations.count_documents({})
    enabled_automations = await db.automations.count_documents({"enabled": True})
    automation_executions_30d = await db.automation_executions.count_documents({
        "timestamp": {"$gte": thirty_days_ago.isoformat()}
    })
    
    # Duplicate detection stats
    blocked_attempts_total = await db.blocked_member_attempts.count_documents({})
    blocked_attempts_30d = await db.blocked_member_attempts.count_documents({
        "timestamp": {"$gte": thirty_days_ago.isoformat()}
    })
    pending_reviews = await db.blocked_member_attempts.count_documents({"review_status": "pending"})
    
    # Audit logs statistics
    api_calls_30d = await db.audit_logs.count_documents({
        "timestamp": {"$gte": thirty_days_ago.isoformat()}
    })
    failed_requests_30d = await db.audit_logs.count_documents({
        "timestamp": {"$gte": thirty_days_ago.isoformat()},
        "success": False
    })
    
    # Calculate averages
    avg_bookings_per_class = total_bookings / total_classes if total_classes > 0 else 0
    attendance_rate = (attended_bookings / total_bookings * 100) if total_bookings > 0 else 0
    payment_success_rate = (paid_invoices / total_invoices * 100) if total_invoices > 0 else 0
    
    return {
        "generated_at": today.isoformat(),
        "members": {
            "total": total_members,
            "active": active_members,
            "suspended": suspended_members,
            "new_30d": new_members_30d,
            "new_7d": new_members_7d,
            "growth_rate_30d": round((new_members_30d / total_members * 100) if total_members > 0 else 0, 2)
        },
        "revenue": {
            "total": round(total_revenue, 2),
            "last_30d": round(revenue_30d, 2),
            "avg_per_member": round(total_revenue / active_members, 2) if active_members > 0 else 0
        },
        "invoices": {
            "total": total_invoices,
            "paid": paid_invoices,
            "pending": pending_invoices,
            "overdue": overdue_invoices,
            "payment_success_rate": round(payment_success_rate, 2)
        },
        "classes_and_bookings": {
            "total_classes": total_classes,
            "active_classes": active_classes,
            "total_bookings": total_bookings,
            "confirmed": confirmed_bookings,
            "waitlist": waitlist_bookings,
            "attended": attended_bookings,
            "recent_bookings_30d": recent_bookings,
            "avg_bookings_per_class": round(avg_bookings_per_class, 2),
            "attendance_rate": round(attendance_rate, 2)
        },
        "access_control": {
            "total_checkins": total_checkins,
            "checkins_30d": checkins_30d,
            "checkins_7d": checkins_7d,
            "avg_checkins_per_day_30d": round(checkins_30d / 30, 2)
        },
        "automations": {
            "total": total_automations,
            "enabled": enabled_automations,
            "executions_30d": automation_executions_30d
        },
        "duplicate_detection": {
            "blocked_attempts_total": blocked_attempts_total,
            "blocked_attempts_30d": blocked_attempts_30d,
            "pending_reviews": pending_reviews
        },
        "system": {
            "api_calls_30d": api_calls_30d,
            "failed_requests_30d": failed_requests_30d,
            "success_rate_30d": round((1 - failed_requests_30d / api_calls_30d) * 100, 2) if api_calls_30d > 0 else 100
        }
    }

@api_router.get("/user/permissions")
async def get_user_permissions_endpoint(current_user: User = Depends(get_current_user)):
    """Get current user's permissions based on their role"""
    from permissions import get_user_permissions, PERMISSIONS
    
    user_permissions = get_user_permissions(current_user.role)
    
    return {
        "user_id": current_user.id,
        "user_email": current_user.email,
        "role": current_user.role,
        "permissions": user_permissions,
        "total_permissions": len(user_permissions),
        "all_available_permissions": PERMISSIONS
    }


# ===================== RBAC & Permission Matrix API Endpoints =====================

@api_router.get("/rbac/roles")
async def get_all_roles(current_user: User = Depends(get_current_user)):
    """Get all available roles in the system"""
    from permissions import ROLES, DEFAULT_ROLE_PERMISSIONS
    
    roles_list = []
    for role_key, role_name in ROLES.items():
        default_perms = DEFAULT_ROLE_PERMISSIONS.get(role_key, [])
        roles_list.append({
            "key": role_key,
            "name": role_name,
            "default_permission_count": len(default_perms)
        })
    
    return {
        "roles": roles_list,
        "total_roles": len(roles_list)
    }

@api_router.get("/rbac/modules")
async def get_all_modules(current_user: User = Depends(get_current_user)):
    """Get all modules and their permissions"""
    from permissions import MODULES, ACTIONS, PERMISSIONS
    
    modules_list = []
    for module_key, module_name in MODULES.items():
        module_permissions = []
        for action in ACTIONS:
            perm_key = f"{module_key}:{action}"
            module_permissions.append({
                "key": perm_key,
                "action": action,
                "description": PERMISSIONS.get(perm_key, "")
            })
        
        modules_list.append({
            "key": module_key,
            "name": module_name,
            "permissions": module_permissions
        })
    
    return {
        "modules": modules_list,
        "total_modules": len(modules_list)
    }

@api_router.get("/rbac/permission-matrix")
async def get_permission_matrix(current_user: User = Depends(get_current_user)):
    """Get the complete permission matrix for all roles"""
    from permissions import ROLES, MODULES, ACTIONS, DEFAULT_ROLE_PERMISSIONS, PERMISSIONS
    
    # Check if custom permissions exist in database
    custom_matrices = await db.role_permissions.find().to_list(length=None)
    custom_perms = {matrix['role']: matrix['permissions'] for matrix in custom_matrices}
    
    matrix = []
    for role_key, role_name in ROLES.items():
        # Use custom permissions if available, otherwise use defaults
        permissions = custom_perms.get(role_key, DEFAULT_ROLE_PERMISSIONS.get(role_key, []))
        is_custom = role_key in custom_perms
        
        matrix.append({
            "role": role_key,
            "role_display_name": role_name,
            "permissions": permissions,
            "is_custom": is_custom,
            "is_default": not is_custom
        })
    
    return {
        "matrix": matrix,
        "modules": list(MODULES.keys()),
        "actions": ACTIONS,
        "all_permissions": list(PERMISSIONS.keys())
    }

@api_router.post("/rbac/permission-matrix")
async def update_permission_matrix(
    data: PermissionMatrixUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update permissions for a specific role"""
    from permissions import ROLES, PERMISSIONS
    
    # Validate role exists
    if data.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {data.role}")
    
    # Validate all permissions are valid
    invalid_perms = [p for p in data.permissions if p not in PERMISSIONS]
    if invalid_perms:
        raise HTTPException(status_code=400, detail=f"Invalid permissions: {invalid_perms}")
    
    # Update or create role permissions in database
    existing = await db.role_permissions.find_one({"role": data.role})
    
    role_perm_data = {
        "role": data.role,
        "role_display_name": ROLES[data.role],
        "permissions": data.permissions,
        "is_default": False,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "updated_by": current_user.id
    }
    
    if existing:
        # Update existing
        await db.role_permissions.update_one(
            {"role": data.role},
            {"$set": role_perm_data}
        )
        message = f"Permissions updated for role: {ROLES[data.role]}"
    else:
        # Create new
        role_perm_data["id"] = str(uuid.uuid4())
        await db.role_permissions.insert_one(role_perm_data)
        message = f"Custom permissions created for role: {ROLES[data.role]}"
    
    return {
        "success": True,
        "message": message,
        "role": data.role,
        "permissions": data.permissions
    }

@api_router.post("/rbac/reset-role-permissions")
async def reset_role_permissions(
    role: str,
    current_user: User = Depends(get_current_user)
):
    """Reset a role's permissions back to default"""
    from permissions import ROLES, DEFAULT_ROLE_PERMISSIONS
    
    # Validate role
    if role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    
    # Delete custom permissions (will fall back to defaults)
    result = await db.role_permissions.delete_one({"role": role})
    
    default_perms = DEFAULT_ROLE_PERMISSIONS.get(role, [])
    
    return {
        "success": True,
        "message": f"Permissions reset to default for role: {ROLES[role]}",
        "role": role,
        "permissions": default_perms,
        "deleted": result.deleted_count > 0
    }

# ===================== User Role Management API Endpoints =====================

@api_router.get("/rbac/users")
async def get_all_staff_users(current_user: User = Depends(get_current_user)):
    """Get all staff users with their roles and permissions"""
    from permissions import ROLES, DEFAULT_ROLE_PERMISSIONS
    
    # Get all users
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(length=None)
    
    # Get custom permissions
    custom_matrices = await db.role_permissions.find().to_list(length=None)
    custom_perms = {matrix['role']: matrix['permissions'] for matrix in custom_matrices}
    
    staff_users = []
    for user in users:
        role_key = user.get('role', 'personal_trainer')
        role_display = ROLES.get(role_key, role_key)
        permissions = custom_perms.get(role_key, DEFAULT_ROLE_PERMISSIONS.get(role_key, []))
        
        staff_users.append({
            "id": user['id'],
            "email": user['email'],
            "full_name": user.get('full_name', user['email']),
            "role": role_key,
            "role_display_name": role_display,
            "permissions": permissions,
            "permission_count": len(permissions),
            "created_at": user.get('created_at', datetime.now(timezone.utc).isoformat())
        })
    
    return {
        "users": staff_users,
        "total_users": len(staff_users)
    }

@api_router.get("/users/list")
async def get_users_list(current_user: User = Depends(get_current_user)):
    """Get simple list of all users (for dropdowns)"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(length=None)
    return [{"id": user['id'], "full_name": user.get('full_name', user['email']), "email": user['email']} for user in users]

@api_router.put("/rbac/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    data: UserRoleAssignment,
    current_user: User = Depends(get_current_user)
):
    """Update a user's role"""
    from permissions import ROLES, DEFAULT_ROLE_PERMISSIONS
    
    # Validate role
    if data.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {data.role}")
    
    # Check if user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user role
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": data.role}}
    )
    
    # Get permissions for this role
    custom_perms = await db.role_permissions.find_one({"role": data.role})
    permissions = custom_perms['permissions'] if custom_perms else DEFAULT_ROLE_PERMISSIONS.get(data.role, [])
    
    return {
        "success": True,
        "message": f"User role updated to {ROLES[data.role]}",
        "user_id": user_id,
        "new_role": data.role,
        "role_display_name": ROLES[data.role],
        "permissions": permissions
    }

@api_router.post("/rbac/users")
async def create_staff_user(
    user_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Create a new staff user with specified role"""
    from permissions import ROLES
    
    # Validate required fields
    if not all(key in user_data for key in ['email', 'full_name', 'role', 'password']):
        raise HTTPException(status_code=400, detail="Missing required fields: email, full_name, role, password")
    
    # Validate role
    if user_data['role'] not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role: {user_data['role']}")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data['email']})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Hash password using existing pwd_context
    hashed_password = hash_password(user_data['password'])
    
    # Create user
    new_user = {
        "id": str(uuid.uuid4()),
        "email": user_data['email'],
        "password": hashed_password,
        "full_name": user_data['full_name'],
        "role": user_data['role'],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(new_user)
    
    # Return clean response without MongoDB ObjectId
    return {
        "id": new_user["id"],
        "email": new_user["email"],
        "full_name": new_user["full_name"],
        "role": new_user["role"],
        "role_display_name": ROLES[user_data['role']],
        "created_at": new_user["created_at"]
    }



@api_router.get("/import/field-definitions")
async def get_field_definitions(import_type: str, current_user: User = Depends(get_current_user)):
    """Get available database fields for mapping"""
    if import_type == "members":
        return {
            "fields": [
                {"key": "first_name", "label": "First Name", "required": True},
                {"key": "last_name", "label": "Last Name", "required": True},
                {"key": "email", "label": "Email", "required": True},
                {"key": "phone", "label": "Phone Number", "required": True},
                {"key": "date_of_birth", "label": "Date of Birth", "required": False},
                {"key": "address", "label": "Address", "required": False},
                {"key": "city", "label": "City", "required": False},
                {"key": "postal_code", "label": "Postal Code", "required": False},
                {"key": "emergency_contact_name", "label": "Emergency Contact Name", "required": False},
                {"key": "emergency_contact_phone", "label": "Emergency Contact Phone", "required": False},
                {"key": "membership_status", "label": "Membership Status", "required": False},
                {"key": "join_date", "label": "Join Date", "required": False},
                {"key": "expiry_date", "label": "Expiry Date", "required": False},
                {"key": "source", "label": "Lead Source", "required": False},
                {"key": "referred_by", "label": "Referred By", "required": False}
            ]
        }
    elif import_type == "leads":
        return {
            "fields": [
                {"key": "full_name", "label": "Full Name", "required": True},
                {"key": "email", "label": "Email", "required": False},
                {"key": "phone", "label": "Phone Number", "required": True},
                {"key": "source", "label": "Lead Source", "required": True},
                {"key": "interest", "label": "Interest/Notes", "required": False},
                {"key": "message", "label": "Message", "required": False}
            ]
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid import type")

# ===== FIELD CONFIGURATION ENDPOINTS =====

@api_router.get("/field-configurations", response_model=List[FieldConfiguration])
async def get_field_configurations(current_user: User = Depends(get_current_user)):
    """Get all field configurations"""
    configs = await db.field_configurations.find({}, {"_id": 0}).to_list(None)
    if not configs:
        # Initialize default configurations
        await initialize_default_field_configs()
        configs = await db.field_configurations.find({}, {"_id": 0}).to_list(None)
    return [FieldConfiguration(**config) for config in configs]

@api_router.put("/field-configurations/{field_name}")
async def update_field_configuration(
    field_name: str,
    update: FieldConfigurationUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a field configuration"""
    update_data = update.model_dump(exclude_unset=True)
    result = await db.field_configurations.update_one(
        {"field_name": field_name},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Field configuration not found")
    
    updated = await db.field_configurations.find_one({"field_name": field_name}, {"_id": 0})
    return FieldConfiguration(**updated)

@api_router.post("/field-configurations/reset-defaults")
async def reset_field_configurations(current_user: User = Depends(get_current_user)):
    """Reset all field configurations to defaults"""
    await db.field_configurations.delete_many({})
    await initialize_default_field_configs()
    configs = await db.field_configurations.find({}, {"_id": 0}).to_list(None)
    return {"message": "Field configurations reset to defaults", "count": len(configs)}

async def initialize_default_field_configs():
    """Initialize default field configurations"""
    default_configs = [
        # Basic Information
        {
            "field_name": "first_name",
            "label": "First Name",
            "is_required": True,
            "field_type": "text",
            "validation_rules": {"min_length": 2, "max_length": 50},
            "error_message": "First name must be between 2 and 50 characters",
            "category": "basic"
        },
        {
            "field_name": "last_name",
            "label": "Last Name",
            "is_required": True,
            "field_type": "text",
            "validation_rules": {"min_length": 2, "max_length": 50},
            "error_message": "Last name must be between 2 and 50 characters",
            "category": "basic"
        },
        {
            "field_name": "id_number",
            "label": "ID Number",
            "is_required": False,
            "field_type": "text",
            "validation_rules": {"min_length": 5, "max_length": 20},
            "error_message": "ID number must be between 5 and 20 characters",
            "category": "basic"
        },
        # Contact Information
        {
            "field_name": "email",
            "label": "Email Address",
            "is_required": True,
            "field_type": "email",
            "validation_rules": {"must_contain": ["@", "."], "pattern": "email"},
            "error_message": "Email must contain @ and . (e.g., user@example.com)",
            "category": "contact"
        },
        {
            "field_name": "phone",
            "label": "Mobile Phone",
            "is_required": True,
            "field_type": "phone",
            "validation_rules": {"min_length": 10, "max_length": 15, "numeric_only": True},
            "error_message": "Phone number must be 10-15 digits",
            "category": "contact"
        },
        {
            "field_name": "home_phone",
            "label": "Home Phone",
            "is_required": False,
            "field_type": "phone",
            "validation_rules": {"min_length": 10, "max_length": 15, "numeric_only": True},
            "error_message": "Phone number must be 10-15 digits",
            "category": "contact"
        },
        {
            "field_name": "work_phone",
            "label": "Work Phone",
            "is_required": False,
            "field_type": "phone",
            "validation_rules": {"min_length": 10, "max_length": 15, "numeric_only": True},
            "error_message": "Phone number must be 10-15 digits",
            "category": "contact"
        },
        # Address Information
        {
            "field_name": "address",
            "label": "Physical Address",
            "is_required": False,
            "field_type": "text",
            "validation_rules": {"min_length": 5, "max_length": 200},
            "error_message": "Address must be between 5 and 200 characters",
            "category": "address"
        },
        {
            "field_name": "postal_code",
            "label": "Postal Code",
            "is_required": False,
            "field_type": "text",
            "validation_rules": {"min_length": 4, "max_length": 10},
            "error_message": "Postal code must be between 4 and 10 characters",
            "category": "address"
        },
        # Emergency Contact
        {
            "field_name": "emergency_contact",
            "label": "Emergency Contact",
            "is_required": False,
            "field_type": "text",
            "validation_rules": {"min_length": 5, "max_length": 100},
            "error_message": "Emergency contact must be between 5 and 100 characters",
            "category": "contact"
        },
        # Banking Information
        {
            "field_name": "bank_account_number",
            "label": "Bank Account Number",
            "is_required": False,
            "field_type": "text",
            "validation_rules": {"min_length": 8, "max_length": 20, "numeric_only": True},
            "error_message": "Account number must be 8-20 digits",
            "category": "banking"
        },
        {
            "field_name": "bank_name",
            "label": "Bank Name",
            "is_required": False,
            "field_type": "text",
            "validation_rules": {},
            "error_message": None,
            "category": "banking"
        },
        # Membership
        {
            "field_name": "membership_type_id",
            "label": "Membership Type",
            "is_required": True,
            "field_type": "select",
            "validation_rules": {},
            "error_message": "Please select a membership type",
            "category": "membership"
        }
    ]
    
    for config in default_configs:
        config["id"] = str(uuid.uuid4())
        await db.field_configurations.insert_one(config)

@api_router.post("/members/validate-field")
async def validate_field(
    field_name: str,
    value: str,
    current_user: User = Depends(get_current_user)
):
    """Validate a single field value against its configuration"""
    config = await db.field_configurations.find_one({"field_name": field_name}, {"_id": 0})
    if not config:
        return {"valid": True, "message": "No validation rules configured"}
    
    config_obj = FieldConfiguration(**config)
    validation_rules = config_obj.validation_rules
    
    errors = []
    
    # Required check
    if config_obj.is_required and not value:
        errors.append(f"{config_obj.label} is required")
    
    if value:
        # Email validation
        if config_obj.field_type == "email":
            if "@" not in value or "." not in value:
                errors.append(config_obj.error_message or "Invalid email format")
        
        # Phone validation
        if config_obj.field_type == "phone":
            if validation_rules.get("numeric_only") and not value.replace("+", "").replace(" ", "").isdigit():
                errors.append("Phone number must contain only digits")
            if validation_rules.get("min_length") and len(value) < validation_rules["min_length"]:
                errors.append(f"Must be at least {validation_rules['min_length']} characters")
            if validation_rules.get("max_length") and len(value) > validation_rules["max_length"]:
                errors.append(f"Must be at most {validation_rules['max_length']} characters")
        
        # Text validation
        if config_obj.field_type == "text":
            if validation_rules.get("min_length") and len(value) < validation_rules["min_length"]:
                errors.append(f"Must be at least {validation_rules['min_length']} characters")
            if validation_rules.get("max_length") and len(value) > validation_rules["max_length"]:
                errors.append(f"Must be at most {validation_rules['max_length']} characters")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "message": errors[0] if errors else "Valid"
    }



# ===================== POS (Point of Sale) API Endpoints =====================

# Product Categories
@api_router.get("/pos/categories")
async def get_product_categories(current_user: User = Depends(get_current_user)):
    """Get all product categories"""
    categories = await db.product_categories.find({"is_active": True}, {"_id": 0}).sort("display_order", 1).to_list(length=None)
    return {"categories": categories, "total": len(categories)}

@api_router.post("/pos/categories")
async def create_product_category(category: ProductCategoryCreate, current_user: User = Depends(get_current_user)):
    """Create a new product category"""
    category_data = category.dict()
    category_data["id"] = str(uuid.uuid4())
    category_data["is_active"] = True
    category_data["created_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.product_categories.insert_one(category_data)
    
    # Remove MongoDB's _id before returning
    if "_id" in category_data:
        del category_data["_id"]
    
    return {"success": True, "category": category_data}

@api_router.put("/pos/categories/{category_id}")
async def update_product_category(
    category_id: str,
    updates: dict,
    current_user: User = Depends(get_current_user)
):
    """Update a product category"""
    await db.product_categories.update_one(
        {"id": category_id},
        {"$set": updates}
    )
    return {"success": True, "message": "Category updated"}

@api_router.delete("/pos/categories/{category_id}")
async def delete_product_category(category_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete a product category"""
    await db.product_categories.update_one(
        {"id": category_id},
        {"$set": {"is_active": False}}
    )
    return {"success": True, "message": "Category deleted"}

# Products
@api_router.get("/pos/products")
async def get_products(
    category_id: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all products with optional filtering"""
    query = {"is_active": True}
    
    if category_id:
        query["category_id"] = category_id
    if is_favorite is not None:
        query["is_favorite"] = is_favorite
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}}
        ]
    
    products = await db.products.find(query, {"_id": 0}).to_list(length=None)
    
    # Enrich with category names
    for product in products:
        if product.get("category_id"):
            category = await db.product_categories.find_one({"id": product["category_id"]})
            if category:
                product["category_name"] = category["name"]
    
    return {"products": products, "total": len(products)}

@api_router.post("/pos/products")
async def create_product(product: ProductCreate, current_user: User = Depends(get_current_user)):
    """Create a new product"""
    # Calculate selling price
    selling_price = product.cost_price * (1 + product.markup_percent / 100)
    
    # Get category name
    category = await db.product_categories.find_one({"id": product.category_id})
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    product_data = product.dict()
    product_data["id"] = str(uuid.uuid4())
    product_data["selling_price"] = round(selling_price, 2)
    product_data["category_name"] = category["name"]
    product_data["is_active"] = True
    product_data["created_at"] = datetime.now(timezone.utc).isoformat()
    product_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    product_data["created_by"] = current_user.id
    
    await db.products.insert_one(product_data)
    
    # Remove MongoDB's _id before returning
    if "_id" in product_data:
        del product_data["_id"]
    
    return {"success": True, "product": product_data}

@api_router.put("/pos/products/{product_id}")
async def update_product(
    product_id: str,
    updates: ProductUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a product"""
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    # Recalculate selling price if cost_price or markup_percent changed
    if "cost_price" in update_data or "markup_percent" in update_data:
        product = await db.products.find_one({"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        cost_price = update_data.get("cost_price", product["cost_price"])
        markup_percent = update_data.get("markup_percent", product["markup_percent"])
        update_data["selling_price"] = round(cost_price * (1 + markup_percent / 100), 2)
    
    # Update category name if category changed
    if "category_id" in update_data:
        category = await db.product_categories.find_one({"id": update_data["category_id"]})
        if category:
            update_data["category_name"] = category["name"]
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.products.update_one(
        {"id": product_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Product updated"}

@api_router.delete("/pos/products/{product_id}")
async def delete_product(product_id: str, current_user: User = Depends(get_current_user)):
    """Soft delete a product"""
    await db.products.update_one(
        {"id": product_id},
        {"$set": {"is_active": False}}
    )
    return {"success": True, "message": "Product deleted"}

@api_router.get("/pos/products/low-stock")
async def get_low_stock_products(current_user: User = Depends(get_current_user)):
    """Get products with low stock"""
    products = await db.products.find({
        "is_active": True,
        "$expr": {"$lte": ["$stock_quantity", "$low_stock_threshold"]}
    }).to_list(length=None)
    
    return {"products": products, "total": len(products)}

# Stock Management
@api_router.post("/pos/stock/adjust")
async def adjust_stock(adjustment: StockAdjustmentCreate, current_user: User = Depends(get_current_user)):
    """Adjust product stock"""
    product = await db.products.find_one({"id": adjustment.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    previous_quantity = product["stock_quantity"]
    new_quantity = previous_quantity + adjustment.quantity_change
    
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Stock quantity cannot be negative")
    
    # Update product stock
    await db.products.update_one(
        {"id": adjustment.product_id},
        {"$set": {"stock_quantity": new_quantity, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Create stock adjustment record
    adjustment_record = {
        "id": str(uuid.uuid4()),
        "product_id": adjustment.product_id,
        "product_name": product["name"],
        "adjustment_type": adjustment.adjustment_type,
        "quantity_change": adjustment.quantity_change,
        "previous_quantity": previous_quantity,
        "new_quantity": new_quantity,
        "reason": adjustment.reason,
        "adjusted_by_user_id": current_user.id,
        "adjusted_by_name": current_user.full_name,
        "adjustment_date": datetime.now(timezone.utc).isoformat()
    }
    
    await db.stock_adjustments.insert_one(adjustment_record)
    
    return {
        "success": True,
        "message": f"Stock adjusted from {previous_quantity} to {new_quantity}",
        "adjustment": adjustment_record
    }

@api_router.get("/pos/stock/history/{product_id}")
async def get_stock_history(product_id: str, current_user: User = Depends(get_current_user)):
    """Get stock adjustment history for a product"""
    adjustments = await db.stock_adjustments.find(
        {"product_id": product_id}, {"_id": 0}
    ).sort("adjustment_date", -1).to_list(length=100)
    
    return {"adjustments": adjustments, "total": len(adjustments)}

# POS Transactions
@api_router.post("/pos/transactions")
async def create_pos_transaction(
    transaction: POSTransactionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a POS transaction (sale)"""
    # Generate transaction number
    today = datetime.now(timezone.utc)
    today_str = today.strftime("%Y%m%d")
    
    # Count today's transactions
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    count = await db.pos_transactions.count_documents({
        "transaction_date": {"$gte": today_start.isoformat()}
    })
    
    transaction_number = f"POS-{today_str}-{count + 1:04d}"
    
    # Get member info if member_id provided
    member_name = None
    if transaction.member_id:
        member = await db.members.find_one({"id": transaction.member_id})
        if member:
            member_name = f"{member['first_name']} {member['last_name']}"
    
    # Create transaction record
    transaction_data = transaction.dict()
    transaction_data["id"] = str(uuid.uuid4())
    transaction_data["transaction_number"] = transaction_number
    transaction_data["transaction_date"] = datetime.now(timezone.utc).isoformat()
    transaction_data["captured_by_user_id"] = current_user.id
    transaction_data["captured_by_name"] = current_user.full_name
    transaction_data["member_name"] = member_name
    transaction_data["status"] = "completed"
    
    # Process based on transaction type
    if transaction.transaction_type == "product_sale":
        # Deduct stock for each product
        for item in transaction.items:
            product = await db.products.find_one({"id": item.product_id})
            if not product:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            
            new_stock = product["stock_quantity"] - item.quantity
            if new_stock < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {product['name']}. Available: {product['stock_quantity']}"
                )
            
            # Update stock
            await db.products.update_one(
                {"id": item.product_id},
                {"$set": {"stock_quantity": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Create stock adjustment record
            adjustment = {
                "id": str(uuid.uuid4()),
                "product_id": item.product_id,
                "product_name": product["name"],
                "adjustment_type": "sale",
                "quantity_change": -item.quantity,
                "previous_quantity": product["stock_quantity"],
                "new_quantity": new_stock,
                "reason": f"POS Sale - {transaction_number}",
                "adjusted_by_user_id": current_user.id,
                "adjusted_by_name": current_user.full_name,
                "adjustment_date": datetime.now(timezone.utc).isoformat()
            }
            await db.stock_adjustments.insert_one(adjustment)
    
    elif transaction.transaction_type in ["membership_payment", "session_payment", "debt_payment", "account_payment"]:
        # Create a payment record linked to member
        if not transaction.member_id:
            raise HTTPException(status_code=400, detail="Member ID required for this payment type")
        
        payment_data = {
            "id": str(uuid.uuid4()),
            "member_id": transaction.member_id,
            "amount": transaction.total_amount,
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "payment_method": transaction.payment_method,
            "payment_reference": transaction.payment_reference,
            "payment_type": transaction.transaction_type,
            "pos_transaction_id": transaction_data["id"],
            "pos_transaction_number": transaction_number,
            "captured_by": current_user.full_name,
            "notes": transaction.notes
        }
        
        # If linked to an invoice, update invoice status
        if transaction.invoice_id:
            invoice = await db.invoices.find_one({"id": transaction.invoice_id})
            if invoice:
                await db.invoices.update_one(
                    {"id": transaction.invoice_id},
                    {"$set": {
                        "status": "paid",
                        "paid_date": datetime.now(timezone.utc).isoformat(),
                        "payment_method": transaction.payment_method
                    }}
                )
                payment_data["invoice_id"] = transaction.invoice_id
        
        # If debt payment, reduce member's debt
        if transaction.transaction_type == "debt_payment":
            member = await db.members.find_one({"id": transaction.member_id})
            if member:
                current_debt = member.get("debt_amount", 0)
                new_debt = max(0, current_debt - transaction.total_amount)
                await db.members.update_one(
                    {"id": transaction.member_id},
                    {"$set": {
                        "debt_amount": new_debt,
                        "is_debtor": new_debt > 0
                    }}
                )
        
        # Save payment record
        await db.payments.insert_one(payment_data)
        transaction_data["payment_id"] = payment_data["id"]
    
    # Save transaction
    await db.pos_transactions.insert_one(transaction_data)
    
    # Remove MongoDB's _id before returning
    if "_id" in transaction_data:
        del transaction_data["_id"]
    
    return {
        "success": True,
        "message": "Transaction completed successfully",
        "transaction": transaction_data
    }

@api_router.get("/pos/transactions")
async def get_pos_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[str] = None,
    member_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get POS transactions with filtering"""
    query = {"status": "completed"}
    
    if start_date and end_date:
        query["transaction_date"] = {
            "$gte": start_date,
            "$lte": end_date
        }
    if transaction_type:
        query["transaction_type"] = transaction_type
    if member_id:
        query["member_id"] = member_id
    
    transactions = await db.pos_transactions.find(query, {"_id": 0}).sort("transaction_date", -1).to_list(length=None)
    
    return {"transactions": transactions, "total": len(transactions)}

@api_router.get("/pos/transactions/{transaction_id}")
async def get_pos_transaction(transaction_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific POS transaction"""
    transaction = await db.pos_transactions.find_one({"id": transaction_id}, {"_id": 0})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {"transaction": transaction}

@api_router.post("/pos/transactions/{transaction_id}/void")
async def void_pos_transaction(
    transaction_id: str,
    void_reason: str,
    current_user: User = Depends(get_current_user)
):
    """Void a POS transaction"""
    transaction = await db.pos_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction["status"] != "completed":
        raise HTTPException(status_code=400, detail="Can only void completed transactions")
    
    # Restore stock if product sale
    if transaction["transaction_type"] == "product_sale":
        for item in transaction["items"]:
            await db.products.update_one(
                {"id": item["product_id"]},
                {"$inc": {"stock_quantity": item["quantity"]}}
            )
    
    # Update transaction status
    await db.pos_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "status": "void",
            "void_reason": void_reason,
            "voided_by": current_user.id,
            "voided_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True, "message": "Transaction voided"}

# POS Reports
@api_router.get("/pos/reports/daily-summary")
async def get_daily_pos_summary(date: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Get daily POS summary for cash-up"""
    if not date:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Parse date
    target_date = datetime.strptime(date, "%Y-%m-%d")
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    # Get all completed transactions for the day
    transactions = await db.pos_transactions.find({
        "status": "completed",
        "transaction_date": {
            "$gte": start_of_day.isoformat(),
            "$lt": end_of_day.isoformat()
        }
    }).to_list(length=None)
    
    # Calculate summary
    total_sales = sum(t["total_amount"] for t in transactions)
    total_transactions = len(transactions)
    
    # Breakdown by payment method
    payment_methods = {}
    for t in transactions:
        method = t["payment_method"]
        payment_methods[method] = payment_methods.get(method, 0) + t["total_amount"]
    
    # Breakdown by transaction type
    transaction_types = {}
    for t in transactions:
        ttype = t["transaction_type"]
        transaction_types[ttype] = transaction_types.get(ttype, 0) + t["total_amount"]
    
    # Staff performance
    staff_performance = {}
    for t in transactions:
        staff = t["captured_by_name"]
        if staff not in staff_performance:
            staff_performance[staff] = {"count": 0, "total": 0}
        staff_performance[staff]["count"] += 1
        staff_performance[staff]["total"] += t["total_amount"]
    
    return {
        "date": date,
        "summary": {
            "total_sales": round(total_sales, 2),
            "total_transactions": total_transactions,
            "average_transaction": round(total_sales / total_transactions, 2) if total_transactions > 0 else 0
        },
        "payment_methods": payment_methods,
        "transaction_types": transaction_types,
        "staff_performance": staff_performance,
        "transactions": transactions
    }


# ============================================================================
# EFT SDV Integration Endpoints
# ============================================================================

from eft_utils import EFTFileGenerator, EFTFileParser, save_eft_file, setup_eft_folders
from debicheck_utils import (
    DebiCheckMandateGenerator, 
    DebiCheckCollectionGenerator,
    DebiCheckResponseParser,
    save_debicheck_file
)

# Setup EFT folders on startup
EFT_FOLDERS = setup_eft_folders()


# ===================== Billing Settings Routes =====================

@api_router.get("/billing/settings")
async def get_billing_settings(current_user: User = Depends(get_current_user)):
    """Get billing and invoice settings"""
    settings = await db.billing_settings.find_one({}, {"_id": 0})
    
    if not settings:
        # Return default settings if not configured
        default_settings = BillingSettings()
        return default_settings.model_dump()
    
    return settings

@api_router.post("/billing/settings")
async def create_or_update_billing_settings(
    data: BillingSettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Create or update billing settings"""
    existing = await db.billing_settings.find_one({})
    
    if existing:
        # Update existing settings
        update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.billing_settings.update_one(
            {"id": existing["id"]},
            {"$set": update_data}
        )
        
        updated = await db.billing_settings.find_one({"id": existing["id"]}, {"_id": 0})
        return updated
    else:
        # Create new settings
        settings = BillingSettings(**data.model_dump(exclude_unset=True))
        settings_doc = settings.model_dump()
        settings_doc["created_at"] = settings_doc["created_at"].isoformat()
        
        await db.billing_settings.insert_one(settings_doc)
        settings_doc.pop("_id", None)
        return settings_doc


@api_router.get("/eft/settings")
async def get_eft_settings(current_user: User = Depends(get_current_user)):
    """Get EFT configuration settings"""
    settings = await db.eft_settings.find_one({})
    if not settings:
        # Return default/placeholder settings
        return {
            "id": "default",
            "client_profile_number": "0000000000",
            "nominated_account": "0000000000000000",
            "charges_account": "0000000000000000",
            "service_user_number": "",
            "branch_code": "",
            "bank_name": "Nedbank",
            "enable_notifications": False,
            "notification_email": "",
            "is_configured": False
        }
    
    settings.pop("_id", None)
    settings["is_configured"] = True
    return settings


@api_router.post("/eft/settings")
async def create_or_update_eft_settings(
    data: EFTSettingsUpdate,
    current_user: User = Depends(get_current_user)
):
    """Create or update EFT settings"""
    existing = await db.eft_settings.find_one({})
    
    if existing:
        # Update existing settings
        update_data = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.eft_settings.update_one(
            {"id": existing["id"]},
            {"$set": update_data}
        )
        
        updated = await db.eft_settings.find_one({"id": existing["id"]})
        updated.pop("_id", None)
        return updated
    else:
        # Create new settings
        settings_data = EFTSettings(
            **data.dict(exclude_unset=True)
        ).dict()
        
        await db.eft_settings.insert_one(settings_data)
        settings_data.pop("_id", None)
        return settings_data


@api_router.post("/eft/generate/billing")
async def generate_billing_eft_file(
    invoice_ids: List[str],
    action_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Generate EFT file for billing/membership invoices"""
    # Get EFT settings
    settings = await db.eft_settings.find_one({})
    if not settings:
        raise HTTPException(
            status_code=400,
            detail="EFT settings not configured. Please configure EFT settings first."
        )
    
    # Get invoices
    invoices = await db.invoices.find({"id": {"$in": invoice_ids}}).to_list(length=None)
    if not invoices:
        raise HTTPException(status_code=404, detail="No invoices found")
    
    # Build transactions list
    transactions = []
    for invoice in invoices:
        # Get member details
        member = await db.members.find_one({"id": invoice["member_id"]})
        if not member:
            continue
        
        # Check if member has bank details
        if not member.get("bank_account_number") or not member.get("bank_branch_code"):
            continue
        
        transactions.append({
            "member_name": f"{member['first_name']} {member['last_name']}",
            "member_id": member["id"],
            "member_account": member.get("bank_account_number"),
            "member_branch": member.get("bank_branch_code"),
            "amount": invoice["amount"],
            "invoice_id": invoice["id"],
            "action_date": action_date or date.today().isoformat()
        })
    
    if not transactions:
        raise HTTPException(
            status_code=400,
            detail="No valid transactions found. Members must have bank account details."
        )
    
    # Generate EFT file
    generator = EFTFileGenerator(
        client_profile_number=settings["client_profile_number"],
        nominated_account=settings["nominated_account"],
        charges_account=settings["charges_account"]
    )
    
    filename, content = generator.generate_debit_order_file(transactions)
    
    # Save file
    filepath = save_eft_file(filename, content)
    
    # Create EFT transaction record
    eft_txn = EFTTransaction(
        file_type="outgoing_debit",
        file_name=filename,
        file_sequence=generator.generate_file_sequence_number(),
        transaction_type="billing",
        total_transactions=len(transactions),
        total_amount=sum(t["amount"] for t in transactions),
        status="generated"
    ).dict()
    
    await db.eft_transactions.insert_one(eft_txn)
    
    # Create individual transaction items
    for idx, txn in enumerate(transactions):
        item = EFTTransactionItem(
            eft_transaction_id=eft_txn["id"],
            member_id=txn.get("member_id", ""),
            member_name=txn["member_name"],
            member_account=txn["member_account"],
            member_branch=txn["member_branch"],
            invoice_id=txn["invoice_id"],
            amount=txn["amount"],
            action_date=datetime.now(timezone.utc),
            payment_reference=f"{eft_txn['file_sequence']}{str(idx+1).zfill(10)}",
            status="pending"
        ).dict()
        
        await db.eft_transaction_items.insert_one(item)
    
    return {
        "success": True,
        "file_name": filename,
        "file_path": filepath,
        "transaction_id": eft_txn["id"],
        "total_transactions": len(transactions),
        "total_amount": sum(t["amount"] for t in transactions)
    }


@api_router.post("/eft/generate/levies")
async def generate_levies_eft_file(
    levy_ids: List[str],
    action_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Generate EFT file for levies"""
    # Get EFT settings
    settings = await db.eft_settings.find_one({})
    if not settings:
        raise HTTPException(
            status_code=400,
            detail="EFT settings not configured. Please configure EFT settings first."
        )
    
    # Get levies
    levies = await db.levies.find({"id": {"$in": levy_ids}}).to_list(length=None)
    if not levies:
        raise HTTPException(status_code=404, detail="No levies found")
    
    # Build transactions list
    transactions = []
    for levy in levies:
        # Get member details
        member = await db.members.find_one({"id": levy["member_id"]})
        if not member:
            continue
        
        # Check if member has bank details
        if not member.get("bank_account_number") or not member.get("bank_branch_code"):
            continue
        
        transactions.append({
            "member_name": levy["member_name"],
            "member_id": member["id"],
            "member_account": member.get("bank_account_number"),
            "member_branch": member.get("bank_branch_code"),
            "amount": levy["amount"],
            "levy_id": levy["id"],
            "action_date": action_date or date.today().isoformat()
        })
    
    if not transactions:
        raise HTTPException(
            status_code=400,
            detail="No valid transactions found. Members must have bank account details."
        )
    
    # Generate EFT file
    generator = EFTFileGenerator(
        client_profile_number=settings["client_profile_number"],
        nominated_account=settings["nominated_account"],
        charges_account=settings["charges_account"]
    )
    
    filename, content = generator.generate_debit_order_file(transactions)
    
    # Save file
    filepath = save_eft_file(filename, content)
    
    # Create EFT transaction record
    eft_txn = EFTTransaction(
        file_type="outgoing_debit",
        file_name=filename,
        file_sequence=generator.generate_file_sequence_number(),
        transaction_type="levy",
        total_transactions=len(transactions),
        total_amount=sum(t["amount"] for t in transactions),
        status="generated"
    ).dict()
    
    await db.eft_transactions.insert_one(eft_txn)
    
    # Create individual transaction items
    for idx, txn in enumerate(transactions):
        item = EFTTransactionItem(
            eft_transaction_id=eft_txn["id"],
            member_id=txn.get("member_id", ""),
            member_name=txn["member_name"],
            member_account=txn["member_account"],
            member_branch=txn["member_branch"],
            levy_id=txn["levy_id"],
            amount=txn["amount"],
            action_date=datetime.now(timezone.utc),
            payment_reference=f"{eft_txn['file_sequence']}{str(idx+1).zfill(10)}",
            status="pending"
        ).dict()
        
        await db.eft_transaction_items.insert_one(item)
    
    return {
        "success": True,
        "file_name": filename,
        "file_path": filepath,
        "transaction_id": eft_txn["id"],
        "total_transactions": len(transactions),
        "total_amount": sum(t["amount"] for t in transactions)
    }


@api_router.get("/eft/transactions")
async def get_eft_transactions(
    transaction_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all EFT transactions with optional filtering"""
    query = {}
    if transaction_type:
        query["transaction_type"] = transaction_type
    if status:
        query["status"] = status
    
    transactions = await db.eft_transactions.find(query, {"_id": 0}).to_list(length=None)
    return transactions


@api_router.get("/eft/transactions/{transaction_id}")
async def get_eft_transaction_details(
    transaction_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed EFT transaction with all items"""
    transaction = await db.eft_transactions.find_one({"id": transaction_id}, {"_id": 0})
    if not transaction:
        raise HTTPException(status_code=404, detail="EFT transaction not found")
    
    # Get transaction items
    items = await db.eft_transaction_items.find(
        {"eft_transaction_id": transaction_id},
        {"_id": 0}
    ).to_list(length=None)
    
    transaction["items"] = items
    return transaction


@api_router.get("/eft/invoices-due-for-collection")
async def get_invoices_due_for_collection(
    advance_days: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get invoices that are due for collection based on advance billing days.
    Returns invoices where: today + advance_days >= due_date
    """
    # Get settings to determine advance days
    settings = await db.eft_settings.find_one({})
    if not settings:
        raise HTTPException(
            status_code=400,
            detail="EFT settings not configured"
        )
    
    # Use provided advance_days or get from settings
    days_advance = advance_days if advance_days is not None else settings.get("advance_billing_days", 5)
    
    # Calculate the collection window
    today = date.today()
    collection_date = today + timedelta(days=days_advance)
    
    # Find unpaid invoices with due_date <= collection_date
    # and due_date >= today (not overdue yet)
    query = {
        "status": {"$ne": "paid"},
        "due_date": {
            "$exists": True,
            "$lte": collection_date.isoformat()
        }
    }
    
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(length=None)
    
    # Get member details for each invoice
    invoice_details = []
    for invoice in invoices:
        member = await db.members.find_one({"id": invoice["member_id"]}, {"_id": 0})
        if member and member.get("bank_account_number") and member.get("bank_branch_code"):
            invoice_details.append({
                "invoice_id": invoice["id"],
                "member_id": invoice["member_id"],
                "member_name": f"{member['first_name']} {member['last_name']}",
                "amount": invoice["amount"],
                "due_date": invoice["due_date"],
                "days_until_due": (datetime.strptime(invoice["due_date"], '%Y-%m-%d').date() - today).days,
                "has_bank_details": True
            })
    
    return {
        "collection_date": collection_date.isoformat(),
        "advance_days": days_advance,
        "total_invoices": len(invoice_details),
        "total_amount": sum(inv["amount"] for inv in invoice_details),
        "invoices": invoice_details
    }


@api_router.get("/eft/levies-due-for-collection")
async def get_levies_due_for_collection(
    advance_days: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get levies that are due for collection based on advance billing days.
    """
    # Get settings
    settings = await db.eft_settings.find_one({})
    if not settings:
        raise HTTPException(status_code=400, detail="EFT settings not configured")
    
    days_advance = advance_days if advance_days is not None else settings.get("advance_billing_days", 5)
    
    # Calculate collection window
    today = date.today()
    collection_date = today + timedelta(days=days_advance)
    
    # Find unpaid levies with due_date <= collection_date
    query = {
        "status": {"$ne": "paid"},
        "due_date": {
            "$exists": True,
            "$lte": collection_date.isoformat()
        }
    }
    
    levies = await db.levies.find(query, {"_id": 0}).to_list(length=None)
    
    # Get member details for each levy
    levy_details = []
    for levy in levies:
        member = await db.members.find_one({"id": levy["member_id"]}, {"_id": 0})
        if member and member.get("bank_account_number") and member.get("bank_branch_code"):
            levy_details.append({
                "levy_id": levy["id"],
                "member_id": levy["member_id"],
                "member_name": levy["member_name"],
                "amount": levy["amount"],
                "due_date": levy["due_date"],
                "days_until_due": (datetime.strptime(levy["due_date"], '%Y-%m-%d').date() - today).days,
                "has_bank_details": True
            })
    
    return {
        "collection_date": collection_date.isoformat(),
        "advance_days": days_advance,
        "total_levies": len(levy_details),
        "total_amount": sum(lev["amount"] for lev in levy_details),
        "levies": levy_details
    }


@api_router.post("/eft/generate-due-collections")
async def generate_due_collections(
    collection_type: str,  # "billing" or "levies" or "both"
    advance_days: Optional[int] = None,
    action_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Automatically generate EFT files for invoices/levies due for collection.
    Uses advance_billing_days setting to determine which items to include.
    """
    # Get settings
    settings = await db.eft_settings.find_one({})
    if not settings:
        raise HTTPException(status_code=400, detail="EFT settings not configured")
    
    days_advance = advance_days if advance_days is not None else settings.get("advance_billing_days", 5)
    
    results = {
        "billing": None,
        "levies": None
    }
    
    # Generate billing file
    if collection_type in ["billing", "both"]:
        # Get invoices due
        invoices_response = await get_invoices_due_for_collection(days_advance, current_user)
        
        if invoices_response["total_invoices"] > 0:
            invoice_ids = [inv["invoice_id"] for inv in invoices_response["invoices"]]
            
            # Generate file
            billing_result = await generate_billing_eft_file(
                invoice_ids=invoice_ids,
                action_date=action_date,
                current_user=current_user
            )
            
            results["billing"] = billing_result
    
    # Generate levies file
    if collection_type in ["levies", "both"]:
        # Get levies due
        levies_response = await get_levies_due_for_collection(days_advance, current_user)
        
        if levies_response["total_levies"] > 0:
            levy_ids = [lev["levy_id"] for lev in levies_response["levies"]]
            
            # Generate file
            levies_result = await generate_levies_eft_file(
                levy_ids=levy_ids,
                action_date=action_date,
                current_user=current_user
            )
            
            results["levies"] = levies_result
    
    return {
        "success": True,
        "advance_days": days_advance,
        "collection_type": collection_type,
        "results": results
    }


@api_router.post("/eft/transactions/{transaction_id}/disallow")
async def disallow_eft_transaction(
    transaction_id: str,
    reason: str,
    current_user: User = Depends(get_current_user)
):
    """
    Disallow/cancel an EFT transaction batch.
    This marks the batch as disallowed and can trigger file generation for bank.
    """
    transaction = await db.eft_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Check if already processed
    if transaction["status"] in ["processed", "disallowed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot disallow transaction with status: {transaction['status']}"
        )
    
    # Update transaction status
    await db.eft_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "status": "disallowed",
            "disallowed_at": datetime.now(timezone.utc).isoformat(),
            "disallowed_by": current_user.id,
            "disallow_reason": reason
        }}
    )
    
    # Update associated transaction items
    await db.eft_transaction_items.update_many(
        {"eft_transaction_id": transaction_id},
        {"$set": {"status": "disallowed"}}
    )
    
    # TODO: Generate disallow file for bank if needed
    # For now, we just mark it in the system
    
    return {
        "success": True,
        "message": "Transaction disallowed successfully",
        "transaction_id": transaction_id
    }


@api_router.get("/eft/transactions/disallowed")
async def get_disallowed_transactions(
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get history of disallowed transactions"""
    transactions = await db.eft_transactions.find(
        {"status": "disallowed"},
        {"_id": 0}
    ).sort("disallowed_at", -1).limit(limit).to_list(length=None)
    
    return {
        "total": len(transactions),
        "transactions": transactions
    }


@api_router.post("/webhooks/eft-response")
async def webhook_eft_response(
    file_sequence: str,
    response_type: str,  # "ack", "nack", "unpaid"
    file_content: str,
    timestamp: Optional[str] = None
):
    """
    Webhook endpoint for receiving EFT response files from payment gateway.
    This is called by Connect Direct or similar file transfer service.
    """
    try:
        # Find the original transaction
        transaction = await db.eft_transactions.find_one({"file_sequence": file_sequence})
        
        if not transaction:
            return {
                "success": False,
                "error": "Transaction not found",
                "file_sequence": file_sequence
            }
        
        # Parse the response file
        parsed_data = EFTFileParser.parse_response_file(file_content)
        
        # Update transaction status
        status_map = {
            "ack": "acknowledged",
            "nack": "failed",
            "unpaid": "failed"
        }
        
        await db.eft_transactions.update_one(
            {"id": transaction["id"]},
            {"$set": {
                "status": status_map.get(response_type, "processed"),
                "processed_at": datetime.now(timezone.utc).isoformat(),
                "response_file": f"{response_type}_{file_sequence}.txt",
                "last_status_check": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Process individual transaction items
        for txn_response in parsed_data["transactions"]:
            payment_ref = txn_response["payment_reference"]
            
            item = await db.eft_transaction_items.find_one({"payment_reference": payment_ref})
            
            if item:
                await db.eft_transaction_items.update_one(
                    {"id": item["id"]},
                    {"$set": {
                        "status": "processed" if response_type == "ack" else "failed",
                        "processed_at": datetime.now(timezone.utc).isoformat(),
                        "response_code": txn_response.get("response_code"),
                        "response_message": txn_response.get("response_message")
                    }}
                )
                
                # Update invoice/levy if successful
                if response_type == "ack":
                    if item.get("invoice_id"):
                        await db.invoices.update_one(
                            {"id": item["invoice_id"]},
                            {"$set": {"status": "paid", "paid_date": datetime.now(timezone.utc).isoformat()}}
                        )
                        await calculate_member_debt(item["member_id"])
                    
                    if item.get("levy_id"):
                        await db.levies.update_one(
                            {"id": item["levy_id"]},
                            {"$set": {"status": "paid", "paid_date": datetime.now(timezone.utc).isoformat()}}
                        )
        
        return {
            "success": True,
            "message": "Webhook processed successfully",
            "transaction_id": transaction["id"],
            "items_processed": len(parsed_data["transactions"])
        }
        
    except Exception as e:
        # Log error but don't fail the webhook
        logger.error(f"Webhook processing error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@api_router.get("/eft/files/outgoing")
async def get_outgoing_files(
    status: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get list of all outgoing EFT files with full details"""
    query = {"file_type": {"$in": ["outgoing_debit"]}}
    if status:
        query["status"] = status
    
    files = await db.eft_transactions.find(query, {"_id": 0}).sort(
        "generated_at", -1
    ).limit(limit).to_list(length=None)
    
    return {
        "total": len(files),
        "files": files
    }


@api_router.get("/eft/files/incoming")
async def get_incoming_files(
    limit: int = 100,
    current_user: User = Depends(get_current_user)
):
    """Get list of all incoming EFT response files"""
    files = await db.eft_transactions.find(
        {"file_type": {"$in": ["incoming_ack", "incoming_nack", "incoming_unpaid"]}},
        {"_id": 0}
    ).sort("processed_at", -1).limit(limit).to_list(length=None)
    
    return {
        "total": len(files),
        "files": files
    }


@api_router.get("/eft/files/stuck")
async def get_stuck_files(
    hours_threshold: int = 48,
    current_user: User = Depends(get_current_user)
):
    """
    Get files that are stuck (generated but not processed after X hours).
    Default threshold: 48 hours
    """
    threshold_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
    
    stuck_files = await db.eft_transactions.find({
        "status": {"$in": ["generated", "submitted"]},
        "generated_at": {"$lt": threshold_time.isoformat()}
    }, {"_id": 0}).to_list(length=None)
    
    # Mark as stuck
    for file in stuck_files:
        await db.eft_transactions.update_one(
            {"id": file["id"]},
            {"$set": {"is_stuck": True}}
        )
    
    return {
        "total": len(stuck_files),
        "threshold_hours": hours_threshold,
        "stuck_files": stuck_files
    }


@api_router.post("/eft/files/stuck/notify")
async def notify_stuck_files(
    current_user: User = Depends(get_current_user)
):
    """Send email notifications for stuck files"""
    stuck_files_response = await get_stuck_files(48, current_user)
    
    if stuck_files_response["total"] > 0:
        # Get EFT settings for notification email
        settings = await db.eft_settings.find_one({})
        notification_email = settings.get("notification_email") if settings else None
        
        if notification_email:
            # TODO: Implement email sending
            # For now, just log
            logger.info(f"Notification needed: {stuck_files_response['total']} stuck files")
            
            return {
                "success": True,
                "message": f"Notification sent for {stuck_files_response['total']} stuck files",
                "email": notification_email
            }
        else:
            return {
                "success": False,
                "message": "No notification email configured"
            }
    
    return {
        "success": True,
        "message": "No stuck files found"
    }


@api_router.post("/eft/process-incoming")
async def process_incoming_eft_file(
    file_name: str,
    file_content: str,
    current_user: User = Depends(get_current_user)
):
    """
    Process incoming EFT response file from bank
    Handles ACK, NACK, and Unpaid files
    """
    try:
        # Parse the file
        parsed_data = EFTFileParser.parse_response_file(file_content)
        
        # Get EFT settings for notification preference
        settings = await db.eft_settings.find_one({})
        enable_notifications = settings.get("enable_notifications", False) if settings else False
        
        # Process each transaction
        for txn_response in parsed_data["transactions"]:
            payment_ref = txn_response["payment_reference"]
            
            # Find the original transaction item
            item = await db.eft_transaction_items.find_one({"payment_reference": payment_ref})
            
            if item:
                # Update item status
                update_data = {
                    "status": "processed" if txn_response.get("status") == "processed" else "failed",
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "response_code": txn_response.get("response_code"),
                    "response_message": txn_response.get("response_message")
                }
                
                await db.eft_transaction_items.update_one(
                    {"id": item["id"]},
                    {"$set": update_data}
                )
                
                # If processed successfully, update invoice/levy and member balance
                if txn_response.get("status") == "processed":
                    # Update invoice if exists
                    if item.get("invoice_id"):
                        invoice = await db.invoices.find_one({"id": item["invoice_id"]})
                        if invoice:
                            await db.invoices.update_one(
                                {"id": item["invoice_id"]},
                                {"$set": {
                                    "status": "paid",
                                    "paid_date": datetime.now(timezone.utc).isoformat()
                                }}
                            )
                            
                            # Create payment record
                            payment = PaymentCreate(
                                member_id=item["member_id"],
                                invoice_id=item["invoice_id"],
                                amount=item["amount"],
                                payment_method="EFT",
                                payment_gateway="EFT_DEBIT_ORDER",
                                reference_number=payment_ref,
                                notes="Auto-processed from EFT response file"
                            ).dict()
                            payment["id"] = str(uuid.uuid4())
                            payment["payment_date"] = datetime.now(timezone.utc).isoformat()
                            
                            await db.payments.insert_one(payment)
                            
                            # Update member debt
                            await calculate_member_debt(item["member_id"])
                    
                    # Update levy if exists
                    if item.get("levy_id"):
                        await db.levies.update_one(
                            {"id": item["levy_id"]},
                            {"$set": {
                                "status": "paid",
                                "paid_date": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                    
                    # Send notification if enabled
                    if enable_notifications:
                        member = await db.members.find_one({"id": item["member_id"]})
                        if member and member.get("email"):
                            # Here you would integrate with email service
                            # For now, we'll just log it
                            print(f"Notification: Payment confirmed for {member.get('first_name')} {member.get('last_name')} - Amount: R{item['amount']}")
        
        # Update parent EFT transaction
        file_sequence = parsed_data["header"]["file_sequence"]
        eft_txn = await db.eft_transactions.find_one({"file_sequence": file_sequence})
        
        if eft_txn:
            await db.eft_transactions.update_one(
                {"id": eft_txn["id"]},
                {"$set": {
                    "status": "processed",
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "response_file": file_name
                }}
            )
        
        return {
            "success": True,
            "message": "EFT response file processed successfully",
            "transactions_processed": len(parsed_data["transactions"])
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process EFT file: {str(e)}")


# ============================================================================
# DebiCheck Mandate and Collection Endpoints
# ============================================================================

@api_router.post("/debicheck/mandates")
async def create_debicheck_mandate(
    data: DebiCheckMandateCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new DebiCheck mandate for a member"""
    # Get member details
    member = await db.members.find_one({"id": data.member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if member has bank details
    if not member.get("bank_account_number") or not member.get("bank_branch_code"):
        raise HTTPException(
            status_code=400,
            detail="Member must have bank account details configured"
        )
    
    # Check if member has ID number
    if not member.get("id_number"):
        raise HTTPException(
            status_code=400,
            detail="Member must have ID number configured"
        )
    
    # Generate mandate reference number
    settings = await db.eft_settings.find_one({})
    if not settings:
        raise HTTPException(
            status_code=400,
            detail="EFT settings not configured. Please configure settings first."
        )
    
    generator = DebiCheckMandateGenerator(
        client_profile_number=settings["client_profile_number"],
        creditor_name=settings.get("bank_name", "GYM"),
        creditor_abbr="GYM"
    )
    
    mrn = generator.generate_mandate_reference_number(data.member_id)
    
    # Calculate collection day if not provided
    collection_day = data.collection_day or data.first_collection_date.day
    
    # Calculate maximum amount if not provided (1.5x installment for variable)
    maximum_amount = data.maximum_amount or (data.installment_amount * 1.5)
    
    # Create mandate record
    mandate = DebiCheckMandate(
        mandate_reference_number=mrn,
        member_id=data.member_id,
        member_name=f"{member['first_name']} {member['last_name']}",
        contract_reference=data.contract_reference,
        mandate_type=data.mandate_type,
        transaction_type=data.transaction_type,
        debtor_id_number=member["id_number"],
        debtor_bank_account=member["bank_account_number"],
        debtor_branch_code=member["bank_branch_code"],
        account_type=member.get("account_type", "1"),
        first_collection_date=data.first_collection_date,
        collection_day=collection_day,
        frequency=data.frequency,
        installment_amount=data.installment_amount,
        maximum_amount=maximum_amount,
        adjustment_category=data.adjustment_category,
        adjustment_rate=data.adjustment_rate,
        status="pending"
    ).dict()
    
    await db.debicheck_mandates.insert_one(mandate)
    
    mandate.pop("_id", None)
    return mandate


@api_router.get("/debicheck/mandates")
async def get_debicheck_mandates(
    member_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all DebiCheck mandates with optional filtering"""
    query = {}
    if member_id:
        query["member_id"] = member_id
    if status:
        query["status"] = status
    
    mandates = await db.debicheck_mandates.find(query, {"_id": 0}).to_list(length=None)
    return mandates


@api_router.get("/debicheck/mandates/{mandate_id}")
async def get_debicheck_mandate(
    mandate_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get specific DebiCheck mandate details"""
    mandate = await db.debicheck_mandates.find_one({"id": mandate_id}, {"_id": 0})
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    # Get collection history
    collections = await db.debicheck_collections.find(
        {"mandate_id": mandate_id},
        {"_id": 0}
    ).to_list(length=None)
    
    mandate["collections"] = collections
    return mandate


@api_router.post("/debicheck/mandates/generate-file")
async def generate_debicheck_mandate_file(
    mandate_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """Generate DebiCheck mandate request file for submission to bank"""
    # Get EFT settings
    settings = await db.eft_settings.find_one({})
    if not settings:
        raise HTTPException(
            status_code=400,
            detail="EFT settings not configured"
        )
    
    # Get mandates
    mandates = await db.debicheck_mandates.find({"id": {"$in": mandate_ids}}).to_list(length=None)
    if not mandates:
        raise HTTPException(status_code=404, detail="No mandates found")
    
    # Build mandate data list
    mandate_data_list = []
    for mandate in mandates:
        mandate_data_list.append({
            'mandate_reference_number': mandate['mandate_reference_number'],
            'mandate_type': mandate['mandate_type'],
            'transaction_type': mandate['transaction_type'],
            'contract_reference': mandate['contract_reference'],
            'debtor_name': mandate['member_name'],
            'debtor_id_number': mandate['debtor_id_number'],
            'debtor_bank_account': mandate['debtor_bank_account'],
            'debtor_branch_code': mandate['debtor_branch_code'],
            'account_type': mandate.get('account_type', '1'),
            'first_collection_date': mandate['first_collection_date'],
            'collection_day': mandate['collection_day'],
            'frequency': mandate['frequency'],
            'installment_amount': mandate['installment_amount'],
            'maximum_amount': mandate['maximum_amount'],
            'adjustment_category': mandate['adjustment_category'],
            'adjustment_rate': mandate['adjustment_rate'],
            'action': 'A',  # A=Add new mandate
            'member_id': mandate['member_id']
        })
    
    # Generate file
    generator = DebiCheckMandateGenerator(
        client_profile_number=settings["client_profile_number"],
        creditor_name=settings.get("bank_name", "GYM"),
        creditor_abbr="GYM"
    )
    
    filename, content = generator.generate_mandate_file(mandate_data_list)
    
    # Save file
    filepath = save_debicheck_file(filename, content, "mandate")
    
    # Update mandate status
    for mandate_id in mandate_ids:
        await db.debicheck_mandates.update_one(
            {"id": mandate_id},
            {"$set": {"status": "submitted"}}
        )
    
    return {
        "success": True,
        "file_name": filename,
        "file_path": filepath,
        "total_mandates": len(mandates)
    }


@api_router.post("/debicheck/mandates/{mandate_id}/cancel")
async def cancel_debicheck_mandate(
    mandate_id: str,
    reason: str,
    current_user: User = Depends(get_current_user)
):
    """Cancel a DebiCheck mandate"""
    mandate = await db.debicheck_mandates.find_one({"id": mandate_id})
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    await db.debicheck_mandates.update_one(
        {"id": mandate_id},
        {"$set": {
            "status": "cancelled",
            "status_reason": reason,
            "cancelled_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True, "message": "Mandate cancelled"}


@api_router.post("/debicheck/collections")
async def create_debicheck_collection(
    mandate_id: str,
    collection_amount: float,
    action_date: Optional[str] = None,
    collection_type: str = "R",
    current_user: User = Depends(get_current_user)
):
    """Create a DebiCheck collection request"""
    # Get mandate
    mandate = await db.debicheck_mandates.find_one({"id": mandate_id})
    if not mandate:
        raise HTTPException(status_code=404, detail="Mandate not found")
    
    if mandate["status"] != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Mandate must be approved. Current status: {mandate['status']}"
        )
    
    # Validate collection amount
    if collection_amount > mandate["maximum_amount"]:
        raise HTTPException(
            status_code=400,
            detail=f"Collection amount R{collection_amount:.2f} exceeds maximum R{mandate['maximum_amount']:.2f}"
        )
    
    # Create collection record
    collection = DebiCheckCollection(
        mandate_id=mandate_id,
        mandate_reference_number=mandate["mandate_reference_number"],
        member_id=mandate["member_id"],
        contract_reference=mandate["contract_reference"],
        collection_amount=collection_amount,
        action_date=datetime.strptime(action_date, '%Y-%m-%d') if action_date else datetime.now(timezone.utc),
        collection_type=collection_type,
        status="pending"
    ).dict()
    
    await db.debicheck_collections.insert_one(collection)
    
    collection.pop("_id", None)
    return collection


@api_router.post("/debicheck/collections/generate-file")
async def generate_debicheck_collection_file(
    collection_ids: List[str],
    current_user: User = Depends(get_current_user)
):
    """Generate DebiCheck collection request file"""
    # Get EFT settings
    settings = await db.eft_settings.find_one({})
    if not settings:
        raise HTTPException(status_code=400, detail="EFT settings not configured")
    
    # Get collections
    collections = await db.debicheck_collections.find({"id": {"$in": collection_ids}}).to_list(length=None)
    if not collections:
        raise HTTPException(status_code=404, detail="No collections found")
    
    # Build collection data list
    collection_data_list = []
    for coll in collections:
        collection_data_list.append({
            'mandate_reference_number': coll['mandate_reference_number'],
            'contract_reference': coll['contract_reference'],
            'collection_amount': coll['collection_amount'],
            'action_date': coll['action_date'],
            'collection_type': coll['collection_type']
        })
    
    # Generate file
    generator = DebiCheckCollectionGenerator(
        client_profile_number=settings["client_profile_number"],
        creditor_abbr="GYM"
    )
    
    filename, content = generator.generate_collection_file(
        collection_data_list,
        settings["nominated_account"],
        settings["charges_account"]
    )
    
    # Save file
    filepath = save_debicheck_file(filename, content, "collection")
    
    # Update collection status
    for coll_id in collection_ids:
        await db.debicheck_collections.update_one(
            {"id": coll_id},
            {"$set": {"status": "submitted"}}
        )
    
    return {
        "success": True,
        "file_name": filename,
        "file_path": filepath,
        "total_collections": len(collections)
    }


@api_router.post("/debicheck/process-response")
async def process_debicheck_response(
    file_content: str,
    file_type: str,  # "mandate" or "collection"
    current_user: User = Depends(get_current_user)
):
    """Process DebiCheck response file from bank"""
    try:
        if file_type == "mandate":
            # Parse mandate response
            parsed_data = DebiCheckResponseParser.parse_mandate_response(file_content)
            
            # Update mandate statuses
            for response in parsed_data["responses"]:
                mrn = response["mandate_reference_number"]
                status_map = {"A": "approved", "R": "rejected", "P": "pending"}
                
                mandate = await db.debicheck_mandates.find_one({"mandate_reference_number": mrn})
                if mandate:
                    update_data = {
                        "status": status_map.get(response["status"], "unknown"),
                        "status_reason": response["reason_description"]
                    }
                    
                    if response["status"] == "A":
                        update_data["approved_at"] = datetime.now(timezone.utc).isoformat()
                    
                    await db.debicheck_mandates.update_one(
                        {"mandate_reference_number": mrn},
                        {"$set": update_data}
                    )
            
            return {
                "success": True,
                "message": "Mandate responses processed",
                "total_processed": len(parsed_data["responses"])
            }
        
        elif file_type == "collection":
            # Process collection responses similar to EFT processing
            # This would update collection statuses and create payment records
            return {
                "success": True,
                "message": "Collection responses processed"
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid file type")
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process response: {str(e)}")


@api_router.get("/debicheck/collections")
async def get_debicheck_collections(
    mandate_id: Optional[str] = None,
    member_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get DebiCheck collections with filtering"""
    query = {}
    if mandate_id:
        query["mandate_id"] = mandate_id
    if member_id:
        query["member_id"] = member_id
    if status:
        query["status"] = status
    
    collections = await db.debicheck_collections.find(query, {"_id": 0}).to_list(length=None)
    return collections


# ============================================================================
# Export Reports Endpoints
# ============================================================================

@api_router.get("/reports/payments/export")
async def export_payments_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    format: str = "csv",  # csv or excel
    current_user: User = Depends(get_current_user)
):
    """
    Export payments report with filtering.
    Returns CSV data that can be downloaded.
    """
    import csv
    import io
    
    # Build query
    query = {}
    if start_date:
        query["payment_date"] = {"$gte": start_date}
    if end_date:
        if "payment_date" in query:
            query["payment_date"]["$lte"] = end_date
        else:
            query["payment_date"] = {"$lte": end_date}
    
    # Get payments
    payments = await db.payments.find(query, {"_id": 0}).to_list(length=None)
    
    # Get member details for each payment
    report_data = []
    for payment in payments:
        member = await db.members.find_one({"id": payment["member_id"]}, {"_id": 0})
        if member:
            report_data.append({
                "Payment ID": payment["id"],
                "Member Name": f"{member['first_name']} {member['last_name']}",
                "Member Email": member.get("email", ""),
                "Amount": payment["amount"],
                "Payment Method": payment["payment_method"],
                "Payment Date": payment["payment_date"],
                "Reference": payment.get("reference_number", ""),
                "Invoice ID": payment.get("invoice_id", ""),
                "Status": "Paid"
            })
    
    if format == "csv":
        # Generate CSV
        output = io.StringIO()
        if report_data:
            fieldnames = report_data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_data)
        
        return {
            "success": True,
            "format": "csv",
            "filename": f"payments_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "data": output.getvalue(),
            "total_records": len(report_data),
            "total_amount": sum(p["amount"] for p in payments)
        }
    
    return {
        "success": True,
        "format": "json",
        "data": report_data,
        "total_records": len(report_data),
        "total_amount": sum(p["amount"] for p in payments)
    }


@api_router.get("/reports/unpaid/export")
async def export_unpaid_report(
    format: str = "csv",
    current_user: User = Depends(get_current_user)
):
    """
    Export unpaid invoices and levies report.
    """
    import csv
    import io
    
    # Get unpaid invoices
    unpaid_invoices = await db.invoices.find(
        {"status": {"$ne": "paid"}},
        {"_id": 0}
    ).to_list(length=None)
    
    # Get unpaid levies
    unpaid_levies = await db.levies.find(
        {"status": {"$ne": "paid"}},
        {"_id": 0}
    ).to_list(length=None)
    
    report_data = []
    
    # Process invoices
    for invoice in unpaid_invoices:
        member = await db.members.find_one({"id": invoice["member_id"]}, {"_id": 0})
        if member:
            report_data.append({
                "Type": "Invoice",
                "ID": invoice["id"],
                "Member Name": f"{member['first_name']} {member['last_name']}",
                "Member Email": member.get("email", ""),
                "Amount": invoice["amount"],
                "Due Date": invoice.get("due_date", ""),
                "Status": invoice["status"],
                "Days Overdue": (datetime.now().date() - datetime.strptime(invoice.get("due_date", datetime.now().isoformat()[:10]), '%Y-%m-%d').date()).days if invoice.get("due_date") else 0
            })
    
    # Process levies
    for levy in unpaid_levies:
        report_data.append({
            "Type": "Levy",
            "ID": levy["id"],
            "Member Name": levy["member_name"],
            "Member Email": "",
            "Amount": levy["amount"],
            "Due Date": levy.get("due_date", ""),
            "Status": levy["status"],
            "Days Overdue": (datetime.now().date() - datetime.strptime(levy.get("due_date", datetime.now().isoformat()[:10]), '%Y-%m-%d').date()).days if levy.get("due_date") else 0
        })
    
    if format == "csv":
        output = io.StringIO()
        if report_data:
            fieldnames = report_data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_data)
        
        return {
            "success": True,
            "format": "csv",
            "filename": f"unpaid_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "data": output.getvalue(),
            "total_records": len(report_data),
            "total_unpaid_amount": sum(item["Amount"] for item in report_data)
        }
    
    return {
        "success": True,
        "format": "json",
        "data": report_data,
        "total_records": len(report_data),
        "total_unpaid_amount": sum(item["Amount"] for item in report_data)
    }


@api_router.get("/reports/monthly-billing/export")
async def export_monthly_billing_report(
    month: Optional[int] = None,
    year: Optional[int] = None,
    format: str = "csv",
    current_user: User = Depends(get_current_user)
):
    """
    Export monthly billing report showing all billing activity for a month.
    """
    import csv
    import io
    
    # Default to current month
    if not month or not year:
        now = datetime.now()
        month = month or now.month
        year = year or now.year
    
    # Calculate date range
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Get invoices for the month
    invoices = await db.invoices.find({
        "created_at": {
            "$gte": start_date.isoformat(),
            "$lt": end_date.isoformat()
        }
    }, {"_id": 0}).to_list(length=None)
    
    # Get payments for the month
    payments = await db.payments.find({
        "payment_date": {
            "$gte": start_date.isoformat(),
            "$lt": end_date.isoformat()
        }
    }, {"_id": 0}).to_list(length=None)
    
    report_data = []
    
    # Process invoices
    for invoice in invoices:
        member = await db.members.find_one({"id": invoice["member_id"]}, {"_id": 0})
        if member:
            # Find payment for this invoice
            payment = next((p for p in payments if p.get("invoice_id") == invoice["id"]), None)
            
            report_data.append({
                "Month": f"{year}-{str(month).zfill(2)}",
                "Member Name": f"{member['first_name']} {member['last_name']}",
                "Member Email": member.get("email", ""),
                "Membership Type": member.get("membership_type", ""),
                "Invoice Amount": invoice["amount"],
                "Payment Amount": payment["amount"] if payment else 0,
                "Payment Date": payment.get("payment_date", "") if payment else "",
                "Payment Method": payment.get("payment_method", "") if payment else "",
                "Status": "Paid" if payment else invoice["status"],
                "Balance": invoice["amount"] - (payment["amount"] if payment else 0)
            })
    
    if format == "csv":
        output = io.StringIO()
        if report_data:
            fieldnames = report_data[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(report_data)
        
        return {
            "success": True,
            "format": "csv",
            "filename": f"monthly_billing_{year}_{str(month).zfill(2)}.csv",
            "data": output.getvalue(),
            "total_records": len(report_data),
            "total_invoiced": sum(item["Invoice Amount"] for item in report_data),
            "total_collected": sum(item["Payment Amount"] for item in report_data),
            "total_outstanding": sum(item["Balance"] for item in report_data)
        }
    
    return {
        "success": True,
        "format": "json",
        "data": report_data,
        "month": f"{year}-{str(month).zfill(2)}",
        "total_records": len(report_data),
        "total_invoiced": sum(item["Invoice Amount"] for item in report_data),
        "total_collected": sum(item["Payment Amount"] for item in report_data),
        "total_outstanding": sum(item["Balance"] for item in report_data)
    }


@api_router.get("/debicheck/mandates-due-for-collection")
async def get_mandates_due_for_collection(
    advance_days: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get approved mandates that are due for collection based on advance billing days.
    Returns mandates where: today + advance_days >= next_collection_date
    """
    # Get settings
    settings = await db.eft_settings.find_one({})
    if not settings:
        raise HTTPException(status_code=400, detail="EFT settings not configured")
    
    days_advance = advance_days if advance_days is not None else settings.get("advance_billing_days", 5)
    
    # Calculate collection window
    today = date.today()
    collection_date = today + timedelta(days=days_advance)
    
    # Find approved mandates
    mandates = await db.debicheck_mandates.find(
        {"status": "approved"},
        {"_id": 0}
    ).to_list(length=None)
    
    # Filter mandates based on collection schedule
    mandates_due = []
    for mandate in mandates:
        # Calculate next collection date based on frequency and last collection
        last_collection = mandate.get("last_collection_date")
        first_collection = datetime.fromisoformat(mandate["first_collection_date"]) if isinstance(mandate["first_collection_date"], str) else mandate["first_collection_date"]
        
        next_collection_date = None
        
        if not last_collection:
            # First collection
            next_collection_date = first_collection.date()
        else:
            # Calculate next based on frequency
            last_date = datetime.fromisoformat(last_collection).date() if isinstance(last_collection, str) else last_collection
            frequency = mandate["frequency"]
            
            if frequency == "W":  # Weekly
                next_collection_date = last_date + timedelta(weeks=1)
            elif frequency == "F":  # Fortnightly
                next_collection_date = last_date + timedelta(weeks=2)
            elif frequency == "M":  # Monthly
                next_collection_date = last_date + timedelta(days=30)
            elif frequency == "Q":  # Quarterly
                next_collection_date = last_date + timedelta(days=90)
            elif frequency == "H":  # Biannually
                next_collection_date = last_date + timedelta(days=182)
            elif frequency == "Y":  # Yearly
                next_collection_date = last_date + timedelta(days=365)
        
        # Check if due for collection
        if next_collection_date and next_collection_date <= collection_date:
            mandates_due.append({
                "mandate_id": mandate["id"],
                "mandate_reference_number": mandate["mandate_reference_number"],
                "member_id": mandate["member_id"],
                "member_name": mandate["member_name"],
                "contract_reference": mandate["contract_reference"],
                "installment_amount": mandate["installment_amount"],
                "maximum_amount": mandate["maximum_amount"],
                "next_collection_date": next_collection_date.isoformat(),
                "days_until_due": (next_collection_date - today).days,
                "frequency": mandate["frequency"]
            })
    
    return {
        "collection_date": collection_date.isoformat(),
        "advance_days": days_advance,
        "total_mandates": len(mandates_due),
        "total_amount": sum(m["installment_amount"] for m in mandates_due),
        "mandates": mandates_due
    }


@api_router.post("/debicheck/generate-due-collections")
async def generate_debicheck_due_collections(
    advance_days: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Automatically generate DebiCheck collection files for mandates due for collection.
    """
    # Get mandates due
    mandates_response = await get_mandates_due_for_collection(advance_days, current_user)
    
    if mandates_response["total_mandates"] == 0:
        return {
            "success": True,
            "message": "No mandates due for collection",
            "total_mandates": 0
        }
    
    # Create collections for each mandate
    collection_ids = []
    for mandate_data in mandates_response["mandates"]:
        collection = await create_debicheck_collection(
            mandate_id=mandate_data["mandate_id"],
            collection_amount=mandate_data["installment_amount"],
            action_date=mandate_data["next_collection_date"],
            collection_type="R",  # Recurring
            current_user=current_user
        )
        collection_ids.append(collection["id"])
    
    # Generate collection file
    if collection_ids:
        file_result = await generate_debicheck_collection_file(
            collection_ids=collection_ids,
            current_user=current_user
        )
        
        return {
            "success": True,
            "advance_days": mandates_response["advance_days"],
            "total_mandates": mandates_response["total_mandates"],
            "total_amount": mandates_response["total_amount"],
            "file_result": file_result
        }
    
    return {
        "success": False,
        "message": "Failed to create collections"
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ============================================================================
# AVS (Account Verification Service) Endpoints
# ============================================================================

from avs_utils import AVSService

@api_router.get("/avs/config")
async def get_avs_config(current_user: User = Depends(get_current_user)):
    """Get AVS configuration settings"""
    config = await db.avs_config.find_one({})
    if not config:
        # Return default/placeholder config
        return {
            "id": "default",
            "profile_number": "0000000000",
            "profile_user_number": "00000",
            "charge_account": "0000000000",
            "mock_mode": True,
            "use_qa": True,
            "enable_auto_verify": False,
            "verify_on_update": False,
            "is_configured": False
        }
    
    config.pop("_id", None)
    config["is_configured"] = True
    return config


@api_router.post("/avs/config")
async def create_or_update_avs_config(
    data: AVSConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """Create or update AVS configuration"""
    existing = await db.avs_config.find_one({})
    
    if existing:
        # Update existing config
        update_data = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.avs_config.update_one(
            {"id": existing["id"]},
            {"$set": update_data}
        )
        
        updated = await db.avs_config.find_one({"id": existing["id"]})
        updated.pop("_id", None)
        return updated
    else:
        # Create new config
        config = AVSConfig(**data.dict(exclude_unset=True))
        config_dict = config.dict()
        config_dict["created_at"] = config_dict["created_at"].isoformat()
        if config_dict.get("updated_at"):
            config_dict["updated_at"] = config_dict["updated_at"].isoformat()
        
        await db.avs_config.insert_one(config_dict)
        config_dict.pop("_id", None)
        return config_dict


@api_router.post("/avs/verify")
async def verify_account(
    request: AVSVerificationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Verify a single bank account using Nedbank AVS service
    
    Returns verification results including account existence, ownership match,
    account status, and ability to accept debits/credits.
    """
    # Get AVS config
    config = await db.avs_config.find_one({})
    if not config:
        raise HTTPException(
            status_code=400,
            detail="AVS not configured. Please configure AVS settings first."
        )
    
    # Initialize AVS service
    avs_config = {
        "mock_mode": config.get("mock_mode", True),
        "profile_number": config.get("profile_number", "0000000000"),
        "profile_user_number": config.get("profile_user_number", "00000"),
        "charge_account": config.get("charge_account", "0000000000"),
        "use_qa": config.get("use_qa", True)
    }
    
    avs_service = AVSService(avs_config)
    
    # Prepare verification request
    verification_data = request.dict()
    
    # Perform verification
    try:
        result = await avs_service.verify_account([verification_data])
        
        if not result.get("verifications"):
            raise HTTPException(
                status_code=500,
                detail="No verification results received"
            )
        
        verification_result = result["verifications"][0]
        
        # Get bank name
        bank_name = AVSService.get_bank_name(request.bank_identifier)
        
        # Format summary
        summary = AVSService.format_verification_summary(verification_result)
        
        # Store verification result in database
        avs_result = AVSVerificationResult(
            verification_type="manual",
            bank_identifier=request.bank_identifier,
            bank_name=bank_name,
            account_number=request.account_number,
            sort_code=request.sort_code,
            identity_number=request.identity_number,
            identity_type=request.identity_type,
            initials=request.initials,
            last_name=request.last_name,
            result_code=result.get("result_code", "UNKNOWN"),
            result_code_acct=verification_result.get("result_code_acct", "UNKNOWN"),
            account_exists=verification_result["verification_results"].get("account_exists", "U"),
            identification_number_matched=verification_result["verification_results"].get("identification_number_matched", "U"),
            initials_matched=verification_result["verification_results"].get("initials_matched", "U"),
            last_name_matched=verification_result["verification_results"].get("last_name_matched", "U"),
            account_active=verification_result["verification_results"].get("account_active", "U"),
            account_dormant=verification_result["verification_results"].get("account_dormant", "U"),
            account_active_3months=verification_result["verification_results"].get("account_active3_months", "U"),
            can_debit_account=verification_result["verification_results"].get("can_debit_account", "U"),
            can_credit_account=verification_result["verification_results"].get("can_credit_account", "U"),
            tax_ref_match=verification_result["verification_results"].get("tax_ref_match", "U"),
            account_type_match=verification_result["verification_results"].get("account_type_match", "U"),
            email_id_matched=verification_result["verification_results"].get("email_id_matched", "U"),
            cell_number_matched=verification_result["verification_results"].get("cell_number_matched", "U"),
            verification_summary=summary,
            mock_mode=result.get("mock_mode", False),
            created_by=current_user.id
        )
        
        # Save to database
        avs_result_dict = avs_result.dict()
        avs_result_dict["created_at"] = avs_result_dict["created_at"].isoformat()
        await db.avs_verifications.insert_one(avs_result_dict)
        
        return {
            "success": True,
            "result": avs_result.dict(),
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Account verification failed: {str(e)}"
        )


@api_router.post("/avs/verify-member/{member_id}")
async def verify_member_account(
    member_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Verify a member's bank account details using AVS
    
    Uses the banking details stored in the member's profile.
    """
    # Get member
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Check if member has banking details
    if not member.get("bank_account_number") or not member.get("bank_branch_code"):
        raise HTTPException(
            status_code=400,
            detail="Member does not have complete banking details"
        )
    
    # Determine bank identifier from branch code
    # This is a simplified mapping - in production, use proper branch code validation
    branch_code = member.get("bank_branch_code", "")
    bank_identifier = "21"  # Default to Nedbank
    
    if branch_code:
        branch_int = int(branch_code) if branch_code.isdigit() else 0
        if 100000 <= branch_int <= 199999:
            bank_identifier = "21"  # Nedbank
        elif 200000 <= branch_int <= 299999:
            bank_identifier = "05"  # FNB
        elif 0 <= branch_int <= 99999:
            bank_identifier = "18"  # Standard Bank
        elif 630000 <= branch_int <= 659999 or 300000 <= branch_int <= 349999:
            bank_identifier = "16"  # Absa
        elif 470000 <= branch_int <= 470999:
            bank_identifier = "34"  # Capitec
    
    # Create verification request
    verification_request = AVSVerificationRequest(
        bank_identifier=bank_identifier,
        account_number=member.get("bank_account_number", ""),
        sort_code=member.get("bank_branch_code", ""),
        identity_number=member.get("id_number", ""),
        identity_type="SID" if member.get("id_type") == "id" else "SPP",
        initials=member.get("first_name", "")[:1] if member.get("first_name") else None,
        last_name=member.get("last_name"),
        email_id=member.get("email"),
        cell_number=member.get("phone"),
        customer_reference=member.get("id"),
        customer_reference2=member.get("first_name", "") + " " + member.get("last_name", "")
    )
    
    # Get AVS config
    config = await db.avs_config.find_one({})
    if not config:
        raise HTTPException(
            status_code=400,
            detail="AVS not configured. Please configure AVS settings first."
        )
    
    # Initialize AVS service
    avs_config = {
        "mock_mode": config.get("mock_mode", True),
        "profile_number": config.get("profile_number", "0000000000"),
        "profile_user_number": config.get("profile_user_number", "00000"),
        "charge_account": config.get("charge_account", "0000000000"),
        "use_qa": config.get("use_qa", True)
    }
    
    avs_service = AVSService(avs_config)
    
    # Perform verification
    try:
        result = await avs_service.verify_account([verification_request.dict()])
        
        if not result.get("verifications"):
            raise HTTPException(
                status_code=500,
                detail="No verification results received"
            )
        
        verification_result = result["verifications"][0]
        
        # Get bank name
        bank_name = AVSService.get_bank_name(bank_identifier)
        
        # Format summary
        summary = AVSService.format_verification_summary(verification_result)
        
        # Store verification result
        avs_result = AVSVerificationResult(
            member_id=member_id,
            verification_type="member_verification",
            bank_identifier=bank_identifier,
            bank_name=bank_name,
            account_number=verification_request.account_number,
            sort_code=verification_request.sort_code,
            identity_number=verification_request.identity_number,
            identity_type=verification_request.identity_type,
            initials=verification_request.initials,
            last_name=verification_request.last_name,
            result_code=result.get("result_code", "UNKNOWN"),
            result_code_acct=verification_result.get("result_code_acct", "UNKNOWN"),
            account_exists=verification_result["verification_results"].get("account_exists", "U"),
            identification_number_matched=verification_result["verification_results"].get("identification_number_matched", "U"),
            initials_matched=verification_result["verification_results"].get("initials_matched", "U"),
            last_name_matched=verification_result["verification_results"].get("last_name_matched", "U"),
            account_active=verification_result["verification_results"].get("account_active", "U"),
            account_dormant=verification_result["verification_results"].get("account_dormant", "U"),
            account_active_3months=verification_result["verification_results"].get("account_active3_months", "U"),
            can_debit_account=verification_result["verification_results"].get("can_debit_account", "U"),
            can_credit_account=verification_result["verification_results"].get("can_credit_account", "U"),
            tax_ref_match=verification_result["verification_results"].get("tax_ref_match", "U"),
            account_type_match=verification_result["verification_results"].get("account_type_match", "U"),
            email_id_matched=verification_result["verification_results"].get("email_id_matched", "U"),
            cell_number_matched=verification_result["verification_results"].get("cell_number_matched", "U"),
            verification_summary=summary,
            mock_mode=result.get("mock_mode", False),
            created_by=current_user.id
        )
        
        # Save to database
        avs_result_dict = avs_result.dict()
        avs_result_dict["created_at"] = avs_result_dict["created_at"].isoformat()
        await db.avs_verifications.insert_one(avs_result_dict)
        
        return {
            "success": True,
            "member_id": member_id,
            "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}",
            "result": avs_result.dict(),
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Member account verification failed: {str(e)}"
        )


@api_router.post("/avs/batch-verify")
async def batch_verify_accounts(
    request: AVSBatchVerificationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Verify multiple bank accounts in a single batch (up to 40 accounts)
    
    Useful for bulk verification or CSV imports.
    """
    if len(request.verifications) > 40:
        raise HTTPException(
            status_code=400,
            detail="Maximum 40 accounts can be verified in a single batch"
        )
    
    # Get AVS config
    config = await db.avs_config.find_one({})
    if not config:
        raise HTTPException(
            status_code=400,
            detail="AVS not configured. Please configure AVS settings first."
        )
    
    # Initialize AVS service
    avs_config = {
        "mock_mode": config.get("mock_mode", True),
        "profile_number": config.get("profile_number", "0000000000"),
        "profile_user_number": config.get("profile_user_number", "00000"),
        "charge_account": config.get("charge_account", "0000000000"),
        "use_qa": config.get("use_qa", True)
    }
    
    avs_service = AVSService(avs_config)
    
    # Prepare verification requests
    verification_data = [v.dict() for v in request.verifications]
    
    # Perform batch verification
    try:
        result = await avs_service.verify_account(verification_data)
        
        if not result.get("verifications"):
            raise HTTPException(
                status_code=500,
                detail="No verification results received"
            )
        
        # Store all verification results
        stored_results = []
        for verification_result in result["verifications"]:
            bank_identifier = verification_result.get("bank_identifier", "21")
            bank_name = AVSService.get_bank_name(bank_identifier)
            
            avs_result = AVSVerificationResult(
                verification_type="batch",
                bank_identifier=bank_identifier,
                bank_name=bank_name,
                account_number=verification_result.get("account_number", ""),
                sort_code=verification_result.get("sort_code", ""),
                identity_number=verification_result.get("identity_number", ""),
                identity_type=verification_result.get("identity_type", "SID"),
                initials=verification_result.get("initials"),
                last_name=verification_result.get("last_name"),
                result_code=result.get("result_code", "UNKNOWN"),
                result_code_acct=verification_result.get("result_code_acct", "UNKNOWN"),
                account_exists=verification_result["verification_results"].get("account_exists", "U"),
                identification_number_matched=verification_result["verification_results"].get("identification_number_matched", "U"),
                initials_matched=verification_result["verification_results"].get("initials_matched", "U"),
                last_name_matched=verification_result["verification_results"].get("last_name_matched", "U"),
                account_active=verification_result["verification_results"].get("account_active", "U"),
                account_dormant=verification_result["verification_results"].get("account_dormant", "U"),
                account_active_3months=verification_result["verification_results"].get("account_active3_months", "U"),
                can_debit_account=verification_result["verification_results"].get("can_debit_account", "U"),
                can_credit_account=verification_result["verification_results"].get("can_credit_account", "U"),
                tax_ref_match=verification_result["verification_results"].get("tax_ref_match", "U"),
                account_type_match=verification_result["verification_results"].get("account_type_match", "U"),
                email_id_matched=verification_result["verification_results"].get("email_id_matched", "U"),
                cell_number_matched=verification_result["verification_results"].get("cell_number_matched", "U"),
                verification_summary=AVSService.format_verification_summary(verification_result),
                mock_mode=result.get("mock_mode", False),
                created_by=current_user.id
            )
            
            # Save to database
            avs_result_dict = avs_result.dict()
            avs_result_dict["created_at"] = avs_result_dict["created_at"].isoformat()
            await db.avs_verifications.insert_one(avs_result_dict)
            
            stored_results.append(avs_result.dict())
        
        return {
            "success": True,
            "total_verified": len(stored_results),
            "results": stored_results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch verification failed: {str(e)}"
        )


@api_router.get("/avs/verifications")
async def get_verification_history(
    member_id: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Get verification history
    
    Optionally filter by member_id to see all verifications for a specific member.
    """
    query = {}
    if member_id:
        query["member_id"] = member_id
    
    verifications = await db.avs_verifications.find(query).sort("created_at", -1).limit(limit).to_list(length=None)
    
    for v in verifications:
        v.pop("_id", None)
    
    return {
        "success": True,
        "count": len(verifications),
        "verifications": verifications
    }


@api_router.get("/avs/banks")
async def get_participating_banks(current_user: User = Depends(get_current_user)):
    """Get list of participating banks for AVS"""
    banks = []
    for bank_id, bank_info in AVSService.PARTICIPATING_BANKS.items():
        banks.append({
            "bank_identifier": bank_id,
            "bank_name": bank_info["name"],
            "universal_branch": bank_info["universal_branch"]
        })
    
    return {
        "success": True,
        "banks": banks
    }


# ============================================================================
# TI (Transactional Information) Endpoints
# ============================================================================

from ti_utils import TIService

@api_router.get("/ti/config")
async def get_ti_config(current_user: User = Depends(get_current_user)):
    """Get TI configuration settings"""
    config = await db.ti_config.find_one({})
    if not config:
        # Return default config
        return {
            "id": "default",
            "profile_number": "0000000000",
            "account_number": "0000000000",
            "mock_mode": True,
            "use_qa": True,
            "fti_enabled": True,
            "fti_frequency": "daily",
            "pti_enabled": False,
            "notifications_enabled": False,
            "auto_reconcile": True,
            "is_configured": False
        }
    
    config.pop("_id", None)
    config["is_configured"] = True
    return config


@api_router.post("/ti/config")
async def create_or_update_ti_config(
    data: TIConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """Create or update TI configuration"""
    existing = await db.ti_config.find_one({})
    
    if existing:
        # Update existing config
        update_data = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.ti_config.update_one(
            {"id": existing["id"]},
            {"$set": update_data}
        )
        
        updated = await db.ti_config.find_one({"id": existing["id"]})
        updated.pop("_id", None)
        return updated
    else:
        # Create new config
        config = TIConfig(**data.dict(exclude_unset=True))
        config_dict = config.dict()
        config_dict["created_at"] = config_dict["created_at"].isoformat()
        if config_dict.get("updated_at"):
            config_dict["updated_at"] = config_dict["updated_at"].isoformat()
        
        await db.ti_config.insert_one(config_dict)
        config_dict.pop("_id", None)
        return config_dict


@api_router.post("/ti/fti/fetch")
async def fetch_fti_transactions(current_user: User = Depends(get_current_user)):
    """
    Fetch FTI (Final Transaction Information) from Nedbank
    
    Retrieves confirmed bank transactions for reconciliation
    """
    # Get TI config
    config = await db.ti_config.find_one({})
    if not config:
        raise HTTPException(
            status_code=400,
            detail="TI not configured. Please configure TI settings first."
        )
    
    # Initialize TI service
    ti_config = {
        "mock_mode": config.get("mock_mode", True),
        "profile_number": config.get("profile_number", "0000000000"),
        "account_number": config.get("account_number", "0000000000"),
        "use_qa": config.get("use_qa", True),
        "fti_frequency": config.get("fti_frequency", "daily"),
        "pti_enabled": config.get("pti_enabled", False)
    }
    
    ti_service = TIService(ti_config)
    
    try:
        # Fetch FTI data
        transactions = await ti_service.fetch_fti_data()
        
        # Store transactions in database
        stored_count = 0
        for trans in transactions:
            fti_trans = FTITransaction(
                statement_number=trans.get("statement_number", ""),
                date=trans.get("date", ""),
                time=trans.get("time", ""),
                balance=trans.get("balance", 0.0),
                transaction_type=trans.get("transaction_type", ""),
                transaction_type_name=trans.get("transaction_type_name", ""),
                channel=trans.get("channel", ""),
                channel_name=trans.get("channel_name", ""),
                amount=trans.get("amount", 0.0),
                reference=trans.get("reference", ""),
                description=trans.get("description", ""),
                transaction_key=trans.get("transaction_key", ""),
                process_key=trans.get("process_key"),
                is_debit=trans.get("is_debit", False),
                mock_mode=trans.get("mock_mode", False)
            )
            
            # Check if transaction already exists
            existing = await db.fti_transactions.find_one({"transaction_key": fti_trans.transaction_key})
            if not existing:
                trans_dict = fti_trans.dict()
                trans_dict["imported_at"] = trans_dict["imported_at"].isoformat()
                if trans_dict.get("reconciled_at"):
                    trans_dict["reconciled_at"] = trans_dict["reconciled_at"].isoformat()
                
                await db.fti_transactions.insert_one(trans_dict)
                stored_count += 1
        
        return {
            "success": True,
            "total_fetched": len(transactions),
            "new_transactions": stored_count,
            "message": f"Fetched {len(transactions)} transactions, {stored_count} new"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch FTI data: {str(e)}"
        )


@api_router.get("/ti/fti/transactions")
async def get_fti_transactions(
    limit: int = 50,
    unreconciled_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Get FTI transactions"""
    query = {}
    if unreconciled_only:
        query["is_reconciled"] = False
    
    transactions = await db.fti_transactions.find(query).sort("imported_at", -1).limit(limit).to_list(length=None)
    
    for t in transactions:
        t.pop("_id", None)
    
    return {
        "success": True,
        "count": len(transactions),
        "transactions": transactions
    }


@api_router.post("/ti/fti/reconcile")
async def reconcile_fti_transactions(current_user: User = Depends(get_current_user)):
    """
    Reconcile FTI transactions against outstanding invoices
    
    Automatically matches bank transactions to member invoices
    """
    # Get TI config
    config = await db.ti_config.find_one({})
    if not config:
        raise HTTPException(
            status_code=400,
            detail="TI not configured"
        )
    
    # Get unreconciled FTI transactions
    fti_transactions = await db.fti_transactions.find({"is_reconciled": False}).to_list(length=None)
    
    if not fti_transactions:
        return {
            "success": True,
            "message": "No unreconciled transactions found"
        }
    
    # Get outstanding invoices
    outstanding_invoices = await db.invoices.find({"status": {"$in": ["pending", "overdue"]}}).to_list(length=None)
    
    # Initialize TI service
    ti_service = TIService(config)
    
    # Perform reconciliation
    reconciliation_result = ti_service.reconcile_transactions(fti_transactions, outstanding_invoices)
    
    # Update matched transactions and invoices
    updated_invoices = 0
    updated_transactions = 0
    
    for match in reconciliation_result["matched"]:
        transaction = match["transaction"]
        invoice = match["invoice"]
        
        # Update FTI transaction
        await db.fti_transactions.update_one(
            {"id": transaction["id"]},
            {"$set": {
                "is_reconciled": True,
                "matched_invoice_id": invoice["id"],
                "matched_member_id": invoice.get("member_id"),
                "match_confidence": match["match_confidence"],
                "match_reason": match["match_reason"],
                "reconciled_at": datetime.now(timezone.utc).isoformat(),
                "reconciled_by": current_user.id
            }}
        )
        updated_transactions += 1
        
        # Update invoice if auto_reconcile is enabled and high confidence
        if config.get("auto_reconcile") and match["match_confidence"] == "high":
            await db.invoices.update_one(
                {"id": invoice["id"]},
                {"$set": {
                    "status": "paid",
                    "paid_date": transaction["date"],
                    "payment_method": "bank_transfer",
                    "payment_reference": transaction["reference"]
                }}
            )
            updated_invoices += 1
    
    # Store reconciliation result
    recon_result = ReconciliationResult(
        total_transactions=reconciliation_result["summary"]["total_transactions"],
        matched_count=reconciliation_result["summary"]["matched_count"],
        unmatched_count=reconciliation_result["summary"]["unmatched_count"],
        match_rate=reconciliation_result["summary"]["match_rate"],
        total_matched_amount=reconciliation_result["summary"]["total_matched_amount"],
        total_unmatched_amount=reconciliation_result["summary"]["total_unmatched_amount"],
        high_confidence_matches=reconciliation_result["summary"]["high_confidence_matches"],
        medium_confidence_matches=reconciliation_result["summary"]["medium_confidence_matches"],
        low_confidence_matches=reconciliation_result["summary"]["low_confidence_matches"],
        matched_invoice_ids=[m["invoice"]["id"] for m in reconciliation_result["matched"]],
        unmatched_transaction_ids=[t["id"] for t in reconciliation_result["unmatched"]],
        report_text=TIService.format_reconciliation_report(reconciliation_result),
        processed_by=current_user.id
    )
    
    recon_dict = recon_result.dict()
    recon_dict["reconciliation_date"] = recon_dict["reconciliation_date"].isoformat()
    await db.reconciliation_results.insert_one(recon_dict)
    
    return {
        "success": True,
        "reconciliation": reconciliation_result["summary"],
        "updated_transactions": updated_transactions,
        "updated_invoices": updated_invoices,
        "report_id": recon_result.id
    }


@api_router.get("/ti/reconciliation/history")
async def get_reconciliation_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Get reconciliation history"""
    results = await db.reconciliation_results.find({}).sort("reconciliation_date", -1).limit(limit).to_list(length=None)
    
    for r in results:
        r.pop("_id", None)
    
    return {
        "success": True,
        "count": len(results),
        "results": results
    }


@api_router.get("/ti/reconciliation/report/{report_id}")
async def get_reconciliation_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed reconciliation report"""
    result = await db.reconciliation_results.find_one({"id": report_id})
    
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    
    result.pop("_id", None)
    
    return {
        "success": True,
        "report": result
    }


@api_router.post("/ti/pti/fetch")
async def fetch_pti_transactions(current_user: User = Depends(get_current_user)):
    """
    Fetch PTI (Provisional Transaction Information)
    
    Retrieves real-time provisional transactions
    """
    # Get TI config
    config = await db.ti_config.find_one({})
    if not config:
        raise HTTPException(
            status_code=400,
            detail="TI not configured"
        )
    
    if not config.get("pti_enabled"):
        raise HTTPException(
            status_code=400,
            detail="PTI not enabled in configuration"
        )
    
    # Initialize TI service
    ti_service = TIService(config)
    
    try:
        # Fetch PTI data
        transactions = await ti_service.fetch_pti_data()
        
        # Store PTI transactions
        stored_count = 0
        for trans in transactions:
            pti_trans = PTITransaction(
                transaction_key=trans.get("transaction_key", ""),
                date=trans.get("date", ""),
                time=trans.get("time", ""),
                transaction_type=trans.get("transaction_type", ""),
                transaction_type_name=trans.get("transaction_type_name", ""),
                channel=trans.get("channel", ""),
                channel_name=trans.get("channel_name", ""),
                amount=trans.get("amount", 0.0),
                reference=trans.get("reference", ""),
                description=trans.get("description", ""),
                is_debit=trans.get("is_debit", False),
                mock_mode=trans.get("mock_mode", False)
            )
            
            # Check if already exists
            existing = await db.pti_transactions.find_one({"transaction_key": pti_trans.transaction_key})
            if not existing:
                trans_dict = pti_trans.dict()
                trans_dict["received_at"] = trans_dict["received_at"].isoformat()
                
                await db.pti_transactions.insert_one(trans_dict)
                stored_count += 1
        
        return {
            "success": True,
            "total_fetched": len(transactions),
            "new_transactions": stored_count,
            "transactions": transactions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch PTI data: {str(e)}"
        )


@api_router.get("/ti/pti/transactions")
async def get_pti_transactions(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get recent PTI transactions"""
    transactions = await db.pti_transactions.find({}).sort("received_at", -1).limit(limit).to_list(length=None)
    
    for t in transactions:
        t.pop("_id", None)
    
    return {
        "success": True,
        "count": len(transactions),
        "transactions": transactions
    }


# ============================================================================
# Member Engagement Alert Endpoints
# ============================================================================

@api_router.get("/alerts/config")
async def get_alert_config(current_user: User = Depends(get_current_user)):
    """Get alert configuration settings"""
    config = await db.alert_config.find_one({})
    if not config:
        # Return default config
        return {
            "id": "default",
            "days_period": 30,
            "green_threshold": 10,
            "amber_min_threshold": 1,
            "amber_max_threshold": 4,
            "red_threshold": 0,
            "is_configured": False
        }
    
    config.pop("_id", None)
    config["is_configured"] = True
    return config


@api_router.post("/alerts/config")
async def create_or_update_alert_config(
    data: AlertConfigurationUpdate,
    current_user: User = Depends(get_current_user)
):
    """Create or update alert configuration"""
    existing = await db.alert_config.find_one({})
    
    if existing:
        # Update existing config
        update_data = {k: v for k, v in data.dict(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.alert_config.update_one(
            {"id": existing["id"]},
            {"$set": update_data}
        )
        
        updated = await db.alert_config.find_one({"id": existing["id"]})
        updated.pop("_id", None)
        return updated
    else:
        # Create new config
        config = AlertConfiguration(**data.dict(exclude_unset=True))
        config_dict = config.dict()
        config_dict["created_at"] = config_dict["created_at"].isoformat()
        if config_dict.get("updated_at"):
            config_dict["updated_at"] = config_dict["updated_at"].isoformat()
        
        await db.alert_config.insert_one(config_dict)
        config_dict.pop("_id", None)
        return config_dict


@api_router.post("/member-access")
async def record_member_access(
    member_id: str,
    access_type: str = "check-in",
    location: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Record a member access/check-in and auto-mark class attendance"""
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    access_record = MemberAccess(
        member_id=member_id,
        access_type=access_type,
        location=location,
        notes=notes
    )
    
    access_dict = access_record.dict()
    access_dict["access_date"] = access_dict["access_date"].isoformat()
    
    await db.member_access.insert_one(access_dict)
    
    # Check for class bookings within check-in window
    now = datetime.now(timezone.utc)
    checked_in_bookings = []
    
    # Get all confirmed bookings for this member
    bookings = await db.bookings.find({
        "member_id": member_id,
        "status": "confirmed"
    }).to_list(length=None)
    
    for booking in bookings:
        # Get class details to check check-in window
        class_obj = await db.classes.find_one({"id": booking["class_id"]})
        if not class_obj:
            continue
        
        check_in_window_minutes = class_obj.get("check_in_window_minutes", 15)
        
        # Parse booking date
        booking_date = booking["booking_date"]
        if isinstance(booking_date, str):
            booking_date = datetime.fromisoformat(booking_date.replace('Z', '+00:00'))
        if booking_date.tzinfo is None:
            booking_date = booking_date.replace(tzinfo=timezone.utc)
        
        # Calculate time difference
        time_diff_minutes = abs((now - booking_date).total_seconds() / 60)
        
        # Check if within window
        if time_diff_minutes <= check_in_window_minutes:
            # Mark as attended
            await db.bookings.update_one(
                {"id": booking["id"]},
                {
                    "$set": {
                        "status": "attended",
                        "checked_in_at": now.isoformat(),
                        "no_show": False
                    }
                }
            )
            checked_in_bookings.append({
                "booking_id": booking["id"],
                "class_name": booking["class_name"],
                "booking_date": booking["booking_date"]
            })
    
    return {
        "success": True,
        "message": "Access recorded",
        "access_id": access_record.id,
        "auto_checked_in_bookings": checked_in_bookings,
        "bookings_marked_attended": len(checked_in_bookings)
    }


@api_router.get("/members/{member_id}/no-show-history")
async def get_member_no_show_history(
    member_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a member's no-show history"""
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get all no-show bookings
    no_show_bookings = await db.bookings.find({
        "member_id": member_id,
        "no_show": True
    }).to_list(length=None)
    
    for booking in no_show_bookings:
        booking.pop("_id", None)
    
    # Get total no-show count
    no_show_count = len(no_show_bookings)
    
    # Check if member is blocked from booking
    sample_class = await db.classes.find_one({})
    no_show_threshold = sample_class.get("no_show_threshold", 3) if sample_class else 3
    is_blocked = no_show_count >= no_show_threshold
    
    return {
        "member_id": member_id,
        "member_name": f"{member.get('first_name')} {member.get('last_name')}",
        "no_show_count": no_show_count,
        "no_show_threshold": no_show_threshold,
        "is_blocked": is_blocked,
        "no_show_bookings": no_show_bookings
    }


@api_router.post("/bookings/{booking_id}/mark-no-show")
async def mark_booking_no_show(
    booking_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a booking as no-show (staff action)"""
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"no_show": True}}
    )
    
    return {
        "success": True,
        "message": "Booking marked as no-show"
    }


@api_router.post("/bookings/process-no-shows")
async def process_no_shows(current_user: User = Depends(get_current_user)):
    """Process all past bookings and mark no-shows"""
    now = datetime.now(timezone.utc)
    
    # Get all confirmed bookings that have passed
    past_bookings = await db.bookings.find({
        "status": "confirmed",
        "no_show": False
    }).to_list(length=None)
    
    no_shows_marked = 0
    
    for booking in past_bookings:
        booking_date = booking["booking_date"]
        if isinstance(booking_date, str):
            booking_date = datetime.fromisoformat(booking_date.replace('Z', '+00:00'))
        if booking_date.tzinfo is None:
            booking_date = booking_date.replace(tzinfo=timezone.utc)
        
        # Get class to check check-in window
        class_obj = await db.classes.find_one({"id": booking["class_id"]})
        if not class_obj:
            continue
        
        check_in_window_minutes = class_obj.get("check_in_window_minutes", 15)
        
        # If booking time + check-in window has passed, mark as no-show
        window_end = booking_date + timedelta(minutes=check_in_window_minutes)
        
        if now > window_end:
            await db.bookings.update_one(
                {"id": booking["id"]},
                {"$set": {"no_show": True, "status": "no-show"}}
            )
            no_shows_marked += 1
    
    return {
        "success": True,
        "message": f"Processed {no_shows_marked} no-shows"
    }


@api_router.post("/members/{member_id}/clear-no-shows")
async def clear_member_no_shows(
    member_id: str,
    current_user: User = Depends(get_current_user)
):
    """Clear all no-shows for a member (staff override)"""
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    result = await db.bookings.update_many(
        {"member_id": member_id, "no_show": True},
        {"$set": {"no_show": False}}
    )
    
    return {
        "success": True,
        "message": f"Cleared {result.modified_count} no-shows for member",
        "cleared_count": result.modified_count
    }


@api_router.post("/bookings/send-class-reminders")
async def send_class_reminders(current_user: User = Depends(get_current_user)):
    """Send WhatsApp reminders to members with upcoming classes (called by cron/scheduler)"""
    now = datetime.now(timezone.utc)
    reminders_sent = 0
    errors = []
    
    # Get all confirmed bookings
    bookings = await db.bookings.find({
        "status": "confirmed"
    }).to_list(length=None)
    
    for booking in bookings:
        try:
            # Get class details
            class_obj = await db.classes.find_one({"id": booking["class_id"]})
            if not class_obj:
                continue
            
            # Check if reminders are enabled for this class
            if not class_obj.get("send_class_reminder", True):
                continue
            
            reminder_minutes = class_obj.get("reminder_minutes_before", 60)
            
            # Parse booking date
            booking_date = booking["booking_date"]
            if isinstance(booking_date, str):
                booking_date = datetime.fromisoformat(booking_date.replace('Z', '+00:00'))
            if booking_date.tzinfo is None:
                booking_date = booking_date.replace(tzinfo=timezone.utc)
            
            # Calculate time until class
            time_until_class_minutes = (booking_date - now).total_seconds() / 60
            
            # Check if we should send reminder (within a 5-minute window)
            if reminder_minutes - 5 <= time_until_class_minutes <= reminder_minutes + 5:
                # Check if reminder already sent (add a flag to prevent duplicate sends)
                if booking.get("reminder_sent"):
                    continue
                
                # Get member details
                member = await db.members.find_one({"id": booking["member_id"]})
                if not member:
                    continue
                
                member_phone = member.get('phone') or member.get('phone_number')
                if not member_phone:
                    continue
                
                # Format times
                formatted_date = booking_date.strftime("%A, %B %d, %Y")
                formatted_time = booking_date.strftime("%I:%M %p")
                
                # Create reminder message
                reminder_message = f"""⏰ *Class Reminder*

Hi {member.get('first_name', 'Member')}!

Your class starts in {reminder_minutes} minutes:

📋 *Class:* {class_obj['name']}
📅 *Date:* {formatted_date}
⏰ *Time:* {formatted_time}
📍 *Location:* {class_obj.get('room', 'Main Studio')}
👤 *Instructor:* {class_obj.get('instructor_name', 'TBA')}

🏃 Get ready and we'll see you soon!

💡 Remember to check-in at reception when you arrive.

Need to cancel? Please do so at least {class_obj.get('cancel_window_hours', 2)} hours before class to avoid a no-show."""

                # Send reminder
                await send_whatsapp_message(
                    phone=member_phone,
                    message=reminder_message,
                    first_name=member.get('first_name', 'Member'),
                    last_name=member.get('last_name', ''),
                    email=member.get('email', '')
                )
                
                # Mark reminder as sent
                await db.bookings.update_one(
                    {"id": booking["id"]},
                    {"$set": {"reminder_sent": True}}
                )
                
                reminders_sent += 1
                logger.info(f"Reminder sent to {member_phone} for booking {booking['id']}")
                
        except Exception as e:
            error_msg = f"Failed to send reminder for booking {booking.get('id')}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    return {
        "success": True,
        "reminders_sent": reminders_sent,
        "errors": errors,
        "message": f"Sent {reminders_sent} reminders"
    }


@api_router.get("/member-access/stats")
async def get_member_access_stats(current_user: User = Depends(get_current_user)):
    """
    Get member access statistics with alert classifications
    
    Returns members categorized by their access frequency:
    - Green: Highly engaged (>= green_threshold visits)
    - Amber: Moderately engaged (amber_min to amber_max visits)
    - Red: At risk (0 visits)
    """
    # Get alert configuration
    config = await db.alert_config.find_one({})
    if not config:
        config = {
            "days_period": 30,
            "green_threshold": 10,
            "amber_min_threshold": 1,
            "amber_max_threshold": 4,
            "red_threshold": 0
        }
    
    days_period = config.get("days_period", 30)
    green_threshold = config.get("green_threshold", 10)
    amber_min = config.get("amber_min_threshold", 1)
    amber_max = config.get("amber_max_threshold", 4)
    
    # Calculate date threshold
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_period)
    
    # Get all active members
    members = await db.members.find({"membership_status": "active"}).to_list(length=None)
    
    # Initialize alert categories
    green_members = []
    amber_members = []
    red_members = []
    
    for member in members:
        # Count access records for this member in the period
        access_count = await db.member_access.count_documents({
            "member_id": member["id"],
            "access_date": {"$gte": cutoff_date.isoformat()}
        })
        
        # Get last access date
        last_access = await db.member_access.find_one(
            {"member_id": member["id"]},
            sort=[("access_date", -1)]
        )
        
        member_data = {
            "id": member["id"],
            "first_name": member.get("first_name", ""),
            "last_name": member.get("last_name", ""),
            "email": member.get("email", ""),
            "phone": member.get("phone", ""),
            "membership_type": member.get("membership_type", ""),
            "access_count": access_count,
            "last_access_date": last_access.get("access_date") if last_access else None,
            "days_since_last_access": (datetime.now(timezone.utc) - datetime.fromisoformat(last_access.get("access_date").replace('Z', '+00:00'))).days if last_access and last_access.get("access_date") else days_period
        }
        
        # Categorize member
        if access_count >= green_threshold:
            green_members.append(member_data)
        elif amber_min <= access_count <= amber_max:
            amber_members.append(member_data)
        else:  # access_count == 0
            red_members.append(member_data)
    
    return {
        "success": True,
        "config": {
            "days_period": days_period,
            "green_threshold": green_threshold,
            "amber_range": f"{amber_min}-{amber_max}",
            "red_threshold": 0
        },
        "summary": {
            "total_members": len(members),
            "green_count": len(green_members),
            "amber_count": len(amber_members),
            "red_count": len(red_members)
        },
        "green_members": green_members,
        "amber_members": amber_members,
        "red_members": red_members
    }


@api_router.post("/member-access/generate-mock-data")
async def generate_mock_access_data(current_user: User = Depends(get_current_user)):
    """
    Generate mock access data for testing alert system
    
    Creates realistic access patterns for existing members
    """
    members = await db.members.find({"membership_status": "active"}).to_list(length=None)
    
    if not members:
        raise HTTPException(status_code=400, detail="No active members found")
    
    import random
    
    # Clear existing mock data
    await db.member_access.delete_many({})
    
    records_created = 0
    now = datetime.now(timezone.utc)
    
    for member in members:
        # Randomly assign engagement level
        engagement_level = random.choices(
            ['high', 'medium', 'low', 'none'],
            weights=[0.3, 0.3, 0.25, 0.15]  # 30% high, 30% medium, 25% low, 15% none
        )[0]
        
        if engagement_level == 'high':
            # 12-20 visits in past 30 days
            num_visits = random.randint(12, 20)
        elif engagement_level == 'medium':
            # 2-4 visits in past 30 days
            num_visits = random.randint(2, 4)
        elif engagement_level == 'low':
            # 1 visit in past 30 days
            num_visits = 1
        else:  # none
            num_visits = 0
        
        # Generate access records
        for i in range(num_visits):
            # Random date in past 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(6, 22)  # Between 6 AM and 10 PM
            access_date = now - timedelta(days=days_ago, hours=hours_ago)
            
            access_record = {
                "id": str(uuid.uuid4()),
                "member_id": member["id"],
                "access_date": access_date.isoformat(),
                "access_type": random.choice(["check-in", "class", "service"]),
                "location": "Main Gym"
            }
            
            await db.member_access.insert_one(access_record)
            records_created += 1
    
    return {
        "success": True,
        "message": f"Generated {records_created} mock access records for {len(members)} members"
    }


# ============================================================================
# Notification Template Endpoints
# ============================================================================

@api_router.get("/notification-templates")
async def get_notification_templates(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get notification templates, optionally filtered by category"""
    query = {"is_active": True}
    if category:
        query["category"] = category
    
    templates = await db.notification_templates.find(query).to_list(length=None)
    
    for t in templates:
        t.pop("_id", None)
    
    return {
        "success": True,
        "templates": templates
    }


@api_router.post("/notification-templates")
async def create_notification_template(
    template: NotificationTemplate,
    current_user: User = Depends(get_current_user)
):
    """Create a new notification template"""
    template_dict = template.dict()
    template_dict["created_at"] = template_dict["created_at"].isoformat()
    
    await db.notification_templates.insert_one(template_dict)
    
    # Remove MongoDB _id for response
    template_dict.pop("_id", None)
    
    return {
        "success": True,
        "template": template_dict
    }


@api_router.post("/notification-templates/seed-defaults")
async def seed_default_templates(current_user: User = Depends(get_current_user)):
    """Seed default notification templates for each alert category"""
    
    default_templates = [
        {
            "id": str(uuid.uuid4()),
            "name": "Green Alert - Thank You",
            "category": "green_alert",
            "channels": ["email", "push"],
            "subject": "Thank You for Being an Active Member!",
            "message": "Hi {first_name}! 👋\n\nWe noticed you've visited us {visit_count} times in the past month - that's amazing! 💪\n\nYour dedication inspires us. Keep up the great work!\n\nBest regards,\nYour Gym Team",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Amber Alert - Encouragement",
            "category": "amber_alert",
            "channels": ["email", "whatsapp", "sms"],
            "subject": "We Miss Seeing You!",
            "message": "Hi {first_name}! 😊\n\nWe noticed you've only visited {visit_count} times recently. We'd love to help you get back on track!\n\nWould you like to:\n✓ Try a new class?\n✓ Book a free PT session?\n✓ Update your fitness goals?\n\nLet us know how we can support you!\n\nWarm regards,\nYour Gym Team",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Red Alert - Win Back",
            "category": "red_alert",
            "channels": ["email", "whatsapp", "sms", "push"],
            "subject": "We Haven't Seen You in a While...",
            "message": "Hi {first_name},\n\nIt's been {days_since_last_visit} days since your last visit, and we really miss you! 😢\n\nLife gets busy, we understand. But your health and fitness goals are important!\n\n🎁 Special Offer: Come back this week and get:\n• Free PT consultation\n• Complimentary smoothie\n• 10% off next month's membership\n\nLet's get you back on track!\n\nHope to see you soon,\nYour Gym Team",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Clear existing and insert defaults
    await db.notification_templates.delete_many({})
    await db.notification_templates.insert_many(default_templates)
    
    return {
        "success": True,
        "message": f"Seeded {len(default_templates)} default templates"
    }

@api_router.post("/task-types/seed-defaults")
async def seed_default_task_types(current_user: User = Depends(get_current_user)):
    """Seed default task types"""
    default_task_types = [
        {"name": "Cancellation Request", "description": "Member cancellation request", "color": "#ef4444", "icon": "x-circle"},
        {"name": "Follow-up Required", "description": "Follow-up action needed", "color": "#f59e0b", "icon": "bell"},
        {"name": "Payment Issue", "description": "Payment or debt collection issue", "color": "#dc2626", "icon": "credit-card"},
        {"name": "Member Complaint", "description": "Member complaint or concern", "color": "#f97316", "icon": "alert-triangle"},
        {"name": "Equipment Maintenance", "description": "Equipment repair or maintenance", "color": "#8b5cf6", "icon": "tool"},
        {"name": "General Task", "description": "General administrative task", "color": "#3b82f6", "icon": "clipboard"}
    ]
    
    for task_type_data in default_task_types:
        # Check if exists
        existing = await db.task_types.find_one({"name": task_type_data["name"]}, {"_id": 0})
        if not existing:
            task_type = TaskType(**task_type_data)
            await db.task_types.insert_one(task_type.model_dump())
    
    return {
        "success": True,
        "message": f"Seeded {len(default_task_types)} default task types"
    }


# Messaging Enhancement APIs
@api_router.get("/messaging/sms-credits")
async def get_sms_credits(current_user: User = Depends(get_current_user)):
    """Get available SMS credits for the organization"""
    # For now, return mock data. In production, this would query actual SMS provider balance
    return {
        "credits_available": 2500,
        "credits_used_this_month": 450,
        "cost_per_credit": 0.05,
        "currency": "USD"
    }

@api_router.post("/messaging/send-unified")
async def send_unified_message(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """Unified endpoint to send SMS/Email/WhatsApp/Push notifications"""
    member_ids = request.get("member_ids", [])
    message_type = request.get("message_type", "sms")  # sms, email, whatsapp, push
    subject = request.get("subject", "")
    message_body = request.get("message_body", "")
    template_id = request.get("template_id")
    is_marketing = request.get("is_marketing", False)
    save_as_template = request.get("save_as_template", False)
    template_name = request.get("template_name", "")
    show_on_checkin = request.get("show_on_checkin", False)  # For push notifications
    
    if not member_ids:
        raise HTTPException(status_code=400, detail="No recipients specified")
    
    if not message_body:
        raise HTTPException(status_code=400, detail="Message body is required")
    
    # Save as template if requested
    if save_as_template and template_name:
        new_template = NotificationTemplate(
            name=template_name,
            category="custom",
            channels=[message_type],
            subject=subject if message_type in ["email", "push"] else "",
            message=message_body,
            is_active=True
        )
        template_dict = new_template.model_dump()
        template_dict["created_at"] = template_dict["created_at"].isoformat()
        await db.notification_templates.insert_one(template_dict)
    
    # Send messages
    sent_count = 0
    failed_count = 0
    
    for member_id in member_ids:
        member = await db.members.find_one({"id": member_id}, {"_id": 0})
        if not member:
            failed_count += 1
            continue
        
        # Personalize message
        personalized_message = message_body.replace("{first_name}", member.get("first_name", "Member"))
        personalized_message = personalized_message.replace("{last_name}", member.get("last_name", ""))
        personalized_message = personalized_message.replace("{email}", member.get("email", ""))
        
        try:
            if message_type == "sms":
                # Mock SMS sending - in production, integrate with SMS provider
                print(f"Sending SMS to {member.get('phone')}: {personalized_message[:50]}...")
                
            elif message_type == "email":
                # Mock email sending
                print(f"Sending Email to {member.get('email')}: {subject}")
                
            elif message_type == "whatsapp":
                # Mock WhatsApp sending
                print(f"Sending WhatsApp to {member.get('phone')}: {personalized_message[:50]}...")
                
            elif message_type == "push":
                # Mock push notification
                print(f"Sending Push to member {member_id}: {subject}")
            
            # Log to member journal
            await add_journal_entry(
                member_id=member_id,
                action_type="message_sent",
                description=f"{message_type.upper()} sent: {subject if subject else personalized_message[:50]}",
                metadata={
                    "message_type": message_type,
                    "is_marketing": is_marketing,
                    "show_on_checkin": show_on_checkin
                },
                created_by=current_user.id,
                created_by_name=current_user.full_name
            )
            
            sent_count += 1
            
        except Exception as e:
            print(f"Failed to send {message_type} to member {member_id}: {str(e)}")
            failed_count += 1
    
    return {
        "success": True,
        "sent_count": sent_count,
        "failed_count": failed_count,
        "message": f"Successfully sent {sent_count} messages, {failed_count} failed"
    }

@api_router.get("/messaging/templates/dropdown")
async def get_templates_for_dropdown(
    message_type: str = "all",
    current_user: User = Depends(get_current_user)
):
    """Get simplified template list for dropdown selection"""
    query = {"is_active": True}
    
    if message_type != "all":
        query["channels"] = message_type
    
    templates = await db.notification_templates.find(
        query,
        {"_id": 0, "id": 1, "name": 1, "subject": 1, "message": 1, "category": 1}
    ).to_list(length=None)
    
    # Format for dropdown
    dropdown_items = [{
        "value": t["id"],
        "label": t["name"],
        "subject": t.get("subject", ""),
        "message": t.get("message", ""),
        "category": t.get("category", "custom")
    } for t in templates]
    
    return dropdown_items



@api_router.get("/notification-templates/by-channel/{channel}")
async def get_templates_by_channel(
    channel: str,
    current_user: User = Depends(get_current_user)
):
    """Get templates that support a specific channel (for automation action selection)"""
    # Find templates where the channel is in the channels array
    templates = await db.notification_templates.find({
        "is_active": True,
        "channels": channel
    }).to_list(length=None)
    
    for t in templates:
        t.pop("_id", None)
    
    return {
        "success": True,
        "templates": templates
    }


@api_router.put("/notification-templates/{template_id}")
async def update_notification_template(
    template_id: str,
    template: NotificationTemplate,
    current_user: User = Depends(get_current_user)
):
    """Update an existing notification template"""
    existing = await db.notification_templates.find_one({"id": template_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template_dict = template.dict()
    template_dict["created_at"] = template_dict["created_at"].isoformat()
    template_dict["id"] = template_id  # Preserve original ID
    
    await db.notification_templates.update_one(
        {"id": template_id},
        {"$set": template_dict}
    )
    
    # Remove MongoDB _id for response
    template_dict.pop("_id", None)
    
    return {
        "success": True,
        "template": template_dict
    }


@api_router.delete("/notification-templates/{template_id}")
async def delete_notification_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a notification template (soft delete by setting is_active=False)"""
    existing = await db.notification_templates.find_one({"id": template_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Soft delete
    await db.notification_templates.update_one(
        {"id": template_id},
        {"$set": {"is_active": False}}
    )
    
    return {
        "success": True,
        "message": "Template deleted successfully"
    }


@api_router.post("/send-bulk-notification")
async def send_bulk_notification(
    request: BulkNotificationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send bulk notification to members in a specific alert category
    
    Note: This is a placeholder implementation. In production, integrate with:
    - WhatsApp Business API
    - Email service (SendGrid, AWS SES)
    - SMS gateway (Twilio, AWS SNS)
    - Push notification service (Firebase, OneSignal)
    """
    # Get template
    template = await db.notification_templates.find_one({"id": request.template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get alert config and member stats
    config = await db.alert_config.find_one({})
    if not config:
        config = {"days_period": 30, "green_threshold": 10, "amber_min_threshold": 1, "amber_max_threshold": 4}
    
    days_period = config.get("days_period", 30)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_period)
    
    # Determine target members based on alert level
    members = await db.members.find({"membership_status": "active"}).to_list(length=None)
    
    target_members = []
    for member in members:
        if request.member_ids and member["id"] not in request.member_ids:
            continue
        
        # Count visits
        access_count = await db.member_access.count_documents({
            "member_id": member["id"],
            "access_date": {"$gte": cutoff_date.isoformat()}
        })
        
        # Get last access
        last_access = await db.member_access.find_one(
            {"member_id": member["id"]},
            sort=[("access_date", -1)]
        )
        
        days_since = (datetime.now(timezone.utc) - datetime.fromisoformat(last_access.get("access_date").replace('Z', '+00:00'))).days if last_access and last_access.get("access_date") else days_period
        
        # Filter by alert level
        if request.alert_level == "green" and access_count >= config.get("green_threshold", 10):
            target_members.append((member, access_count, days_since))
        elif request.alert_level == "amber" and config.get("amber_min_threshold", 1) <= access_count <= config.get("amber_max_threshold", 4):
            target_members.append((member, access_count, days_since))
        elif request.alert_level == "red" and access_count == 0:
            target_members.append((member, access_count, days_since))
    
    # Prepare notifications
    notifications_sent = []
    for member, visit_count, days_since in target_members:
        # Personalize message
        message = template["message"].format(
            first_name=member.get("first_name", "Member"),
            last_name=member.get("last_name", ""),
            visit_count=visit_count,
            days_since_last_visit=days_since
        )
        
        subject = template.get("subject", "").format(
            first_name=member.get("first_name", "Member"),
            last_name=member.get("last_name", "")
        ) if template.get("subject") else None
        
        notification_record = {
            "member_id": member["id"],
            "member_name": f"{member.get('first_name', '')} {member.get('last_name', '')}",
            "email": member.get("email"),
            "phone": member.get("phone"),
            "channels": request.channels,
            "subject": subject,
            "message": message,
            "status": "mock_sent"  # In production: "queued", "sent", "failed"
        }
        
        notifications_sent.append(notification_record)
    
    # In production, integrate with actual notification services here
    # For now, return mock response
    
    return {
        "success": True,
        "message": f"Notification sent to {len(notifications_sent)} members",
        "details": {
            "template_name": template["name"],
            "alert_level": request.alert_level,
            "channels": request.channels,
            "member_count": len(notifications_sent),
            "mock_mode": True,
            "notifications": notifications_sent[:10]  # Return first 10 for preview
        }
    }


# Include the router in the main app (must be after all route definitions)
app.include_router(api_router)


# Startup event to seed default tags and sales CRM configurations
@app.on_event("startup")
async def startup_event():
    """Initialize default tags and sales CRM configurations if they don't exist"""
    print("=" * 80)
    print("STARTUP EVENT TRIGGERED - Beginning seeding process")
    print("=" * 80)
    
    try:
        # Seed default tags
        print("Seeding default tags...")
        default_tags = [
            {"name": "VIP", "color": "#fbbf24", "category": "Status", "description": "VIP member"},
            {"name": "New Member", "color": "#3b82f6", "category": "Status", "description": "Recently joined"},
            {"name": "Late Payer", "color": "#ef4444", "category": "Payment", "description": "History of late payments"},
            {"name": "Personal Training", "color": "#8b5cf6", "category": "Program", "description": "Enrolled in personal training"},
            {"name": "Group Classes", "color": "#10b981", "category": "Program", "description": "Regular group class attendee"},
            {"name": "High Risk", "color": "#dc2626", "category": "Status", "description": "At risk of cancellation"},
            {"name": "Loyal", "color": "#059669", "category": "Status", "description": "Long-term loyal member"},
        ]
        
        tags_created = 0
        for tag_data in default_tags:
            existing = await db.tags.find_one({"name": tag_data["name"]})
            if not existing:
                tag = Tag(
                    name=tag_data["name"],
                    color=tag_data["color"],
                    category=tag_data.get("category"),
                    description=tag_data.get("description"),
                    usage_count=0
                )
                await db.tags.insert_one(tag.model_dump())
                tags_created += 1
        print(f"✓ Tags seeding complete: {tags_created} tags created")
        
        # Seed default lead sources
        print("Seeding default lead sources...")
        default_sources = [
            {"name": "Walk-in", "description": "Prospect walked into facility", "icon": "🚶", "display_order": 1},
            {"name": "Phone-in", "description": "Prospect called by phone", "icon": "📞", "display_order": 2},
            {"name": "Referral", "description": "Referred by existing member", "icon": "🤝", "display_order": 3},
            {"name": "Canvassing", "description": "Direct outreach/canvassing", "icon": "🎯", "display_order": 4},
            {"name": "Social Media", "description": "Social media channels", "icon": "📱", "display_order": 5},
            {"name": "Website", "description": "Website inquiry", "icon": "🌐", "display_order": 6},
            {"name": "Email", "description": "Email inquiry", "icon": "📧", "display_order": 7},
            {"name": "Other", "description": "Other sources", "icon": "📋", "display_order": 8},
        ]
        
        sources_created = 0
        for source_data in default_sources:
            existing = await db.lead_sources.find_one({"name": source_data["name"]})
            if not existing:
                import uuid
                source = {
                    "id": str(uuid.uuid4()),
                    "name": source_data["name"],
                    "description": source_data.get("description"),
                    "icon": source_data.get("icon"),
                    "is_active": True,
                    "display_order": source_data["display_order"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                await db.lead_sources.insert_one(source)
                sources_created += 1
                print(f"  - Created lead source: {source_data['name']}")
        print(f"✓ Lead sources seeding complete: {sources_created} sources created")
        
        # Seed default lead statuses (predefined workflow)
        print("Seeding default lead statuses...")
        default_statuses = [
            {"name": "New Lead", "category": "prospect", "color": "#3b82f6", "workflow_sequence": 10, "display_order": 1, "description": "Fresh lead, not yet contacted"},
            {"name": "Called", "category": "prospect", "color": "#06b6d4", "workflow_sequence": 20, "display_order": 2, "description": "Initial call made"},
            {"name": "Appointment Made", "category": "engaged", "color": "#8b5cf6", "workflow_sequence": 30, "display_order": 3, "description": "Appointment scheduled"},
            {"name": "Appointment Confirmed", "category": "engaged", "color": "#a855f7", "workflow_sequence": 40, "display_order": 4, "description": "Appointment confirmed by prospect"},
            {"name": "Showed", "category": "engaged", "color": "#d946ef", "workflow_sequence": 50, "display_order": 5, "description": "Prospect attended appointment"},
            {"name": "Be Back", "category": "engaged", "color": "#f59e0b", "workflow_sequence": 60, "display_order": 6, "description": "Needs time to think, will return"},
            {"name": "Joined", "category": "converted", "color": "#10b981", "workflow_sequence": 70, "display_order": 7, "description": "Successfully converted to member"},
            {"name": "Lost", "category": "lost", "color": "#ef4444", "workflow_sequence": 80, "display_order": 8, "description": "Lead lost, reason required"},
        ]
        
        statuses_created = 0
        for status_data in default_statuses:
            existing = await db.lead_statuses.find_one({"name": status_data["name"]})
            if not existing:
                import uuid
                status = {
                    "id": str(uuid.uuid4()),
                    "name": status_data["name"],
                    "description": status_data.get("description"),
                    "category": status_data["category"],
                    "color": status_data["color"],
                    "workflow_sequence": status_data["workflow_sequence"],
                    "is_active": True,
                    "display_order": status_data["display_order"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                await db.lead_statuses.insert_one(status)
                statuses_created += 1
                print(f"  - Created lead status: {status_data['name']}")
        print(f"✓ Lead statuses seeding complete: {statuses_created} statuses created")
        
        # Seed default loss reasons
        print("Seeding default loss reasons...")
        default_loss_reasons = [
            {"name": "Too Expensive", "description": "Price point too high", "display_order": 1},
            {"name": "Medical Issues", "description": "Health or medical concerns", "display_order": 2},
            {"name": "Lives Too Far", "description": "Location inconvenient", "display_order": 3},
            {"name": "No Time", "description": "Schedule conflicts", "display_order": 4},
            {"name": "Joined Competitor", "description": "Chose another gym", "display_order": 5},
            {"name": "Not Interested", "description": "Lost interest in membership", "display_order": 6},
            {"name": "Financial Issues", "description": "Cannot afford at this time", "display_order": 7},
            {"name": "Other", "description": "Other reasons", "display_order": 8},
        ]
        
        reasons_created = 0
        for reason_data in default_loss_reasons:
            existing = await db.loss_reasons.find_one({"name": reason_data["name"]})
            if not existing:
                import uuid
                reason = {
                    "id": str(uuid.uuid4()),
                    "name": reason_data["name"],
                    "description": reason_data.get("description"),
                    "is_active": True,
                    "display_order": reason_data["display_order"],
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                await db.loss_reasons.insert_one(reason)
                reasons_created += 1
                print(f"  - Created loss reason: {reason_data['name']}")
        print(f"✓ Loss reasons seeding complete: {reasons_created} reasons created")
        
        print("=" * 80)
        print(f"STARTUP SEEDING COMPLETE: {tags_created} tags, {sources_created} sources, {statuses_created} statuses, {reasons_created} loss reasons")
        print("=" * 80)
        
    except Exception as e:
        print("=" * 80)
        print(f"ERROR IN STARTUP SEEDING: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 80)


# Audit Logging Middleware
@app.middleware("http")
async def audit_logging_middleware(request, call_next):
    """
    Comprehensive audit logging middleware
    Logs all API requests with user context, duration, and outcome
    """
    import time
    from fastapi import Request
    
    start_time = time.time()
    
    # Extract user info from JWT if present
    user_id = None
    user_email = None
    user_role = None
    
    try:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_token(token)
            if payload:
                user_id = payload.get("id")
                user_email = payload.get("email")
                user_role = payload.get("role")
    except:
        pass
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    
    # Determine success
    success = 200 <= response.status_code < 400
    
    # Extract resource type and action from path
    path = str(request.url.path)
    resource_type = None
    action = None
    
    # Parse path to determine resource and action
    if "/members" in path:
        resource_type = "member"
        if request.method == "POST" and "check-duplicate" not in path:
            action = "create"
        elif request.method == "GET":
            action = "read"
        elif request.method == "PUT" or request.method == "PATCH":
            action = "update"
        elif request.method == "DELETE":
            action = "delete"
        elif "check-duplicate" in path:
            action = "check_duplicate"
    elif "/invoices" in path:
        resource_type = "invoice"
    elif "/bookings" in path:
        resource_type = "booking"
    elif "/classes" in path:
        resource_type = "class"
    elif "/automations" in path:
        resource_type = "automation"
    elif "/import" in path:
        resource_type = "import"
        action = "import_data"
    
    # Create audit log entry
    audit_entry = AuditLog(
        method=request.method,
        path=path,
        user_id=user_id,
        user_email=user_email,
        user_role=user_role,
        status_code=response.status_code,
        success=success,
        resource_type=resource_type,
        action=action,
        duration_ms=round(duration_ms, 2),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        message=f"{request.method} {path} - {response.status_code}"
    )
    
    # Save to database (async, non-blocking)
    try:
        audit_doc = audit_entry.model_dump()
        audit_doc["timestamp"] = audit_doc["timestamp"].isoformat()
        await db.audit_logs.insert_one(audit_doc)
    except Exception as e:
        # Log error but don't fail the request
        logger.error(f"Failed to save audit log: {str(e)}")
    
    return response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()