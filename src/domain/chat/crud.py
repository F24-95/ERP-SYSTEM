from src.database.base_crud import AsyncBaseCRUD
from src.domain.chat.models import ChatMessage, ChatRoom

chat_room_crud = AsyncBaseCRUD[ChatRoom](ChatRoom)
chat_message_crud = AsyncBaseCRUD[ChatMessage](ChatMessage)
