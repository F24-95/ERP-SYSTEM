from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import (
    AuthorizationException,
    BusinessLogicException,
    ResourceNotFoundException,
)
from src.core.id_generators import generate_fee_code
from src.core.logger import get_logger
from src.domain.fees.crud import fee_crud
from src.domain.fees.models import Fee
from src.domain.fees.schemas import FeeCreate, FeePayment, FeeUpdate
from src.domain.operations.models import StudentClass
from src.domain.users.models import User

logger = get_logger(__name__)


class FeeService:
    @staticmethod
    async def create_fee(db: AsyncSession, data: FeeCreate, user_id: int):
        existing = await fee_crud.get_by_filters(
            db,
            student_class_id=data.student_class_id,
            fee_month=data.fee_month,
            fee_year=data.fee_year,
        )
        if existing:
            raise BusinessLogicException(
                "Fee already exists for this student/month/year",
            )
        # fee_id is server-generated, matching the legacy Column(default=generate_fee_code)
        # behavior instead of trusting a client-supplied value.
        fee = await fee_crud.create(
            db,
            {**data.model_dump(), "fee_id": generate_fee_code(), "created_by": user_id},
        )
        logger.info(f"Fee created: {fee.fee_id}")
        return fee

    @staticmethod
    async def _get_by_fee_id_or_raise(db: AsyncSession, fee_id: str) -> Fee:
        fee = await fee_crud.get_by(db, fee_id=fee_id)
        if not fee:
            raise ResourceNotFoundException(f"Fee with fee_id={fee_id} not found")
        return fee

    @staticmethod
    async def get_fee(db: AsyncSession, fee_id: str) -> Fee:
        return await FeeService._get_by_fee_id_or_raise(db, fee_id)

    @staticmethod
    async def get_fee_for_user(
        db: AsyncSession,
        fee_id: str,
        current_user: User,
    ) -> Fee:
        """Fetch fee record verifying ownership if requested by a student."""
        fee = await FeeService._get_by_fee_id_or_raise(db, fee_id)
        if current_user.role == UserRole.ADMIN:
            return fee
        if current_user.role == UserRole.STUDENT:
            owns = await db.scalar(
                select(StudentClass).filter_by(
                    id=fee.student_class_id,
                    student_id=current_user.id,
                ),
            )
            if not owns:
                raise AuthorizationException("You can only view your own fee records")
            return fee
        raise AuthorizationException("Permission denied")

    @staticmethod
    async def get_my_fees(db: AsyncSession, current_user: User) -> list[Fee]:
        """Fetch all fee records for the logged-in student."""
        student_class_ids = (
            await db.scalars(
                select(StudentClass.id).filter_by(student_id=current_user.id),
            )
        ).all()
        if not student_class_ids:
            return []
        all_fees: list[Fee] = []
        for scid in student_class_ids:
            all_fees.extend(await fee_crud.get_by_filters(db, student_class_id=scid))
        return all_fees

    @staticmethod
    async def update_fee(
        db: AsyncSession,
        fee_id: str,
        data: FeeUpdate,
        user_id: int,
    ) -> Fee:
        fee = await FeeService._get_by_fee_id_or_raise(db, fee_id)
        payload = data.model_dump(exclude_unset=True)
        if not payload:
            return fee
        payload["updated_by"] = user_id
        updated = await fee_crud.update(db, fee.id, payload)
        logger.info(f"Fee updated: {fee_id}")
        return updated

    @staticmethod
    async def deactivate_fee(db: AsyncSession, fee_id: str, user_id: int) -> None:
        fee = await FeeService._get_by_fee_id_or_raise(db, fee_id)
        await fee_crud.update(db, fee.id, {"is_active": False, "updated_by": user_id})
        logger.info(f"Fee deactivated: {fee_id}")

    @staticmethod
    async def get_by_student(db: AsyncSession, student_class_id: int) -> list[Fee]:
        return await fee_crud.get_by_filters(db, student_class_id=student_class_id)

    @staticmethod
    async def record_payment(
        db: AsyncSession,
        fee_id: str,
        payment: FeePayment,
        user_id: int,
    ):
        """Record payment with atomic row locking (with_for_update) and exact Decimal arithmetic."""
        stmt = select(Fee).filter_by(fee_id=fee_id).with_for_update()
        fee = await db.scalar(stmt)
        if not fee:
            raise ResourceNotFoundException(f"Fee with fee_id={fee_id} not found")

        total_amount = Decimal(str(fee.total_amount or 0))
        fine_amount = Decimal(str(fee.fine_amount or 0))
        discount_amount = Decimal(str(fee.discount_amount or 0))
        paid_amount = Decimal(str(fee.paid_amount or 0))
        payment_amount = Decimal(str(payment.amount))

        total_due = total_amount + fine_amount - discount_amount
        outstanding = total_due - paid_amount

        if payment_amount <= Decimal("0"):
            raise BusinessLogicException("Payment amount must be greater than zero")

        if payment_amount > outstanding:
            raise BusinessLogicException(
                f"Payment {payment_amount} exceeds outstanding {outstanding}",
            )

        new_paid = paid_amount + payment_amount
        status = "PAID" if new_paid >= total_due else "PARTIAL"

        updates = {
            "paid_amount": new_paid,
            "status": status,
            "updated_by": user_id,
            "remarks": payment.remarks or fee.remarks,
        }
        if status == "PAID":
            updates["paid_date"] = date.today()

        updated = await fee_crud.update(db, fee.id, updates)
        logger.info(f"Payment recorded for {fee_id}: {payment.amount}, status={status}")
        return updated

    @staticmethod
    async def get_pending(db: AsyncSession):
        return await fee_crud.get_by_filters(db, status="PENDING")
