from src.database.base_crud import AsyncBaseCRUD
from src.domain.id_cards.models import StudentIDCard

student_id_card_crud = AsyncBaseCRUD[StudentIDCard](StudentIDCard)
