from pydantic import BaseModel


class BaseResponse(BaseModel):
    id: int
    is_active: bool | None = None

    model_config = {"from_attributes": True}


class SubjectBase(BaseModel):
    subject_code: str
    subject_name: str
    description: str | None = None
    display_order: int = 1
    subject_type: str = "Core"


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    subject_code: str | None = None
    subject_name: str | None = None
    description: str | None = None
    display_order: int | None = None
    subject_type: str | None = None
    is_active: bool | None = None


class SubjectResponse(SubjectBase):
    id: int
    is_active: bool

    model_config = {"from_attributes": True}


class TopicBase(BaseModel):
    ka_topic_id: str
    topic_name: str
    description: str | None = None
    display_order: int = 1
    subject_id: int
    classroom_id: int | None = None


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    topic_name: str | None = None
    description: str | None = None
    display_order: int | None = None
    classroom_id: int | None = None
    is_active: bool | None = None


class TopicResponse(TopicBase, BaseResponse):
    topic_id: str
