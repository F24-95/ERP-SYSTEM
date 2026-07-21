from src.database.base_crud import AsyncBaseCRUD
from src.domain.attachments.models import Attachment


class AttachmentCRUD(AsyncBaseCRUD[Attachment]):
    def __init__(self):
        super().__init__(Attachment)


attachment_crud = AttachmentCRUD()
