from src.database.base_crud import AsyncBaseCRUD
from src.domain.notices.models import Notice


class NoticeCRUD(AsyncBaseCRUD[Notice]):
    pass


notice_crud = NoticeCRUD(Notice)
