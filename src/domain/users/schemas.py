from datetime import date

from pydantic import BaseModel, EmailStr, Field

from src.core.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    phone: str = Field(..., max_length=20)
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class AdminUserCreate(UserBase):
    password: str = Field(..., min_length=8)
    # Allows admin to specify things


class UserResponse(UserBase):
    id: int
    public_id: str
    is_active: bool
    student_id: str | None = None
    teacher_id: str | None = None
    admin_id: str | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    phone: str | None = Field(None, max_length=20)
    is_active: bool | None = None


# ====================
# Profile admin CRUD -- were missing entirely. Only the flat profile row
# auto-created at user-creation time existed; there was no way to fetch,
# edit, or deactivate a profile on its own afterwards (e.g. fixing a
# misspelled student_name, or updating a teacher's department).
# ====================


class StudentProfileUpdate(BaseModel):
    student_name: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    blood_group: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    parent_name: str | None = None
    parent_phone: str | None = None
    ka_student_id: str | None = None
    is_active: bool | None = None


class StudentProfileResponse(BaseModel):
    id: int
    user_id: int
    public_id: str
    admission_number: str | None = None
    registration_number: str | None = None
    student_name: str
    gender: str | None = None
    date_of_birth: date | None = None
    blood_group: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    parent_name: str | None = None
    parent_phone: str | None = None
    ka_student_id: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class TeacherProfileUpdate(BaseModel):
    teacher_name: str | None = None
    gender: str | None = None
    designation: str | None = None
    department: str | None = None
    experience_years: float | None = None
    is_active: bool | None = None


class TeacherProfileResponse(BaseModel):
    id: int
    user_id: int
    public_id: str
    teacher_name: str
    gender: str | None = None
    employee_code: str | None = None
    designation: str | None = None
    department: str | None = None
    experience_years: float | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class AdminProfileUpdate(BaseModel):
    admin_name: str | None = None
    department: str | None = None
    is_super_admin: bool | None = None
    is_active: bool | None = None


class AdminProfileResponse(BaseModel):
    id: int
    user_id: int
    public_id: str
    admin_name: str
    department: str | None = None
    is_super_admin: bool
    is_active: bool

    model_config = {"from_attributes": True}
