from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class FeeBase(BaseModel):
    academic_sessions_id: int
    student_class_id: int
    fee_month: int = Field(ge=1, le=12)
    fee_year: int
    total_amount: Decimal = Field(max_digits=10, decimal_places=2)
    due_date: date
    remarks: str | None = None


class FeeCreate(FeeBase):
    # fee_id is intentionally NOT accepted from the client: the legacy
    # project generated it server-side (Column default=generate_fee_code).
    # Preserving that behavior here — see FeeService.create_fee.
    discount_amount: Decimal = Field(default=0, ge=0)
    fine_amount: Decimal = Field(default=0, ge=0)


class BaseResponse(BaseModel):
    id: int
    is_active: bool
    model_config = {"from_attributes": True}


class FeeResponse(BaseResponse, FeeBase):
    fee_id: str
    paid_amount: Decimal
    discount_amount: Decimal
    fine_amount: Decimal
    paid_date: date | None = None
    status: str


class FeePayment(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    remarks: str | None = None


class FeeUpdate(BaseModel):
    """Deliberately narrow: total_amount/paid_amount/status are not editable
    here since they're derived through FeeService.record_payment's business
    logic (outstanding-amount checks, status transitions). Only the fields
    an admin would legitimately correct after the fact are exposed.
    """

    due_date: date | None = None
    discount_amount: Decimal | None = Field(default=None, ge=0)
    fine_amount: Decimal | None = Field(default=None, ge=0)
    remarks: str | None = None
    is_active: bool | None = None
