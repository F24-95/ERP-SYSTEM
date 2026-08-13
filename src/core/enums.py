import enum

# ============================================================
# BUSINESS CONSTANTS
# ============================================================
MAX_NAME_LENGTH = 120
MAX_PHONE_LENGTH = 10
MAX_EMAIL_LENGTH = 255
MAX_CODE_LENGTH = 30
MAX_STATUS_LENGTH = 30
MAX_TITLE_LENGTH = 200
MAX_FILE_PATH = 500

# BUSINESS PREFIX
STUDENT_PREFIX = "STU"
TEACHER_PREFIX = "TEA"
ADMIN_PREFIX = "ADM"
MATERIAL_PREFIX = "MAT"
NOTICE_PREFIX = "NOT"
ASSIGNMENT_PREFIX = "ASN"
EXAM_PREFIX = "EXM"
FEE_PREFIX = "FEE"
RECEIPT_PREFIX = "RCPT"
CHAT_PREFIX = "CHT"
TIMETABLE_PREFIX = "TT"
AVAILABILITY_PREFIX = "TA"
REGISTRATION_PREFIX = "REG"
TOPIC_PREFIX = "TPC"
ZOOM_FILE_PREFIX = "ZMF"
EMPLOYEE_PREFIX = "EMP"
ADMISSION_PREFIX = "ADN"

# ============================================================
# ENUMS
# ============================================================


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"


class Gender(str, enum.Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class UserStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    BLOCKED = "Blocked"


class AssignmentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    DELETED = "DELETED"


class ExamStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class FeeStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class NoticeType(str, enum.Enum):
    GENERAL = "GENERAL"
    ACADEMIC = "ACADEMIC"
    EXAM = "EXAM"
    FEE = "FEE"
    EVENT = "EVENT"


class NoticeAudience(str, enum.Enum):
    ALL = "ALL"
    CLASS = "CLASS"
    SECTION = "SECTION"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class MaterialType(str, enum.Enum):
    PDF = "PDF"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    LINK = "LINK"
    OTHER = "OTHER"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"
    LEAVE = "Leave"
    HOLIDAY = "Holiday"


class PromotionType(str, enum.Enum):
    PROMOTED = "PROMOTED"
    RETAINED = "RETAINED"
    TRANSFERRED = "TRANSFERRED"


class LectureStatus(str, enum.Enum):
    SCHEDULED = "Scheduled"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
