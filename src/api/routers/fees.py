from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user, require_role
from src.core.enums import UserRole
from src.database.connection import get_db
from src.domain.common.schemas import MessageResponse
from src.domain.fees.crud import fee_crud
from src.domain.fees.schemas import FeeCreate, FeePayment, FeeResponse, FeeUpdate
from src.domain.fees.service import FeeService
from src.domain.users.models import User

# NOTE: this router used to have `dependencies=[Depends(require_role(UserRole.ADMIN))]`
# at the APIRouter level, meaning *every* route -- including reads -- was
# admin-only. That meant a student/parent could never see their own fee
# dues through the API at all, only office staff could look anything up.
# The blanket dependency is now removed and each route declares its own
# access level individually: admin-only where it should stay that way
# (create/pay/pending/update/delete -- financial-record changes), and
# self-service where a student needs to see their own data.
router = APIRouter(prefix="/fees", tags=["Fees"])


@router.post("", response_model=FeeResponse)
async def create_fee(
    data: FeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    return await FeeService.create_fee(db, data, user_id=current_user.id)


@router.get("", response_model=list[FeeResponse])
async def list_fees(
    session_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    # get_all() returns (items, total) - was previously returned directly
    # against a `list[FeeResponse]` response_model, a shape mismatch
    # (FastAPI would try to validate the raw tuple as the list).
    # When session_id is provided, filter fees to that session's enrollments.
    if session_id:
        from sqlalchemy import select

        from src.domain.operations.models import StudentClass
        from src.domain.fees.models import Fee

        sc_ids = list(
            (
                await db.execute(
                    select(StudentClass.id).filter_by(
                        academic_sessions_id=session_id,
                    )
                )
            ).scalars().all()
        )
        if not sc_ids:
            return []
        items = list(
            (
                await db.execute(
                    select(Fee).filter(
                        Fee.student_class_id.in_(sc_ids),
                    )
                )
            ).scalars().all()
        )
        return items
    items, _total = await fee_crud.get_all(db)
    return items


@router.post("/{fee_id}/pay", response_model=FeeResponse)
async def pay_fee(
    fee_id: str,
    payment: FeePayment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    """Records a payment against a fee."""
    return await FeeService.record_payment(db, fee_id, payment, user_id=current_user.id)


@router.get("/pending", response_model=list[FeeResponse])
async def pending_fees(
    session_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    if session_id:
        from sqlalchemy import select

        from src.domain.operations.models import StudentClass
        from src.domain.fees.models import Fee

        sc_ids = list(
            (
                await db.execute(
                    select(StudentClass.id).filter_by(
                        academic_sessions_id=session_id,
                    )
                )
            ).scalars().all()
        )
        if not sc_ids:
            return []
        items = list(
            (
                await db.execute(
                    select(Fee).filter(
                        Fee.student_class_id.in_(sc_ids),
                        Fee.status.in_(["PENDING", "OVERDUE"]),
                    )
                )
            ).scalars().all()
        )
        return items
    return await FeeService.get_pending(db)


@router.get("/my", response_model=list[FeeResponse])
async def get_my_fees(
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    """A student's own fee records. Was missing entirely -- every /fees
    route required ADMIN, so there was no self-service way for a student
    (or a parent account acting for one) to see their own dues.
    """
    return await FeeService.get_my_fees(db, current_user)


@router.get("/student/{student_class_id}", response_model=list[FeeResponse])
async def get_fees_for_student(
    student_class_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Admin: list every fee record for a given student enrollment (by
    internal id). For a student's own records, use GET /fees/my instead.
    """
    return await FeeService.get_by_student(db, student_class_id)


# NOTE: this must come after the more specific "/pending", "/my", and
# "/student/{student_class_id}" routes above, otherwise those would be
# swallowed by GET /fees/{fee_id} (all single-segment GETs would collide
# with "/pending" and "/my" specifically).
@router.get("/{fee_id}", response_model=FeeResponse)
async def get_fee(
    fee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single fee record by its fee_id. Admin can fetch any; a
    student may only fetch one of their own (previously admin-only with no
    ownership concept, so a student could never fetch even their own fee
    by id).
    """
    return await FeeService.get_fee_for_user(db, fee_id, current_user)


@router.put("/{fee_id}", response_model=FeeResponse)
async def update_fee(
    fee_id: str,
    data: FeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Update a fee's due_date/discount/fine/remarks/is_active. Was missing --
    the only way to change a fee record at all was via /pay, which only
    ever adjusts paid_amount.
    """
    return await FeeService.update_fee(db, fee_id, data, user_id=current_user.id)


@router.delete("/{fee_id}", response_model=MessageResponse)
async def deactivate_fee(
    fee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Deactivate a fee record (e.g. it was raised in error). Was missing entirely."""
    await FeeService.deactivate_fee(db, fee_id, user_id=current_user.id)
    return MessageResponse(message="Fee deactivated")
