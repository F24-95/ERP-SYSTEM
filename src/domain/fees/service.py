from datetime import date

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
        """Was previously admin-only at the router level with no ownership
        concept at all, so there was no way for a student to ever fetch
        even their own fee record by id. Admin sees any fee; a student may
        only fetch a fee that belongs to one of their own enrollments.
        """
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
        """Was missing entirely -- the whole /fees router required ADMIN
        for every route, so a student/parent had no way to see their own
        dues at all (only office staff could look anything up, and only by
        an internal student_class_id they'd have no way to know).
        """
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
        fee = await fee_crud.get_by_filters(db, fee_id=fee_id)
        if not fee:
            raise ResourceNotFoundException(f"Fee with fee_id={fee_id} not found")
        fee = fee[0] if isinstance(fee, list) else fee
        outstanding = float(
            fee.total_amount + fee.fine_amount - fee.discount_amount - fee.paid_amount,
        )
        if float(payment.amount) > outstanding:
            raise BusinessLogicException(
                f"Payment {payment.amount} exceeds outstanding {outstanding}",
            )
        new_paid = float(fee.paid_amount) + float(payment.amount)
        status = (
            "PAID"
            if new_paid
            >= float(fee.total_amount + fee.fine_amount - fee.discount_amount)
            else "PARTIAL"
        )
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
