from src.database.base_crud import AsyncBaseCRUD
from src.domain.study_material.models import StudyMaterial


class StudyMaterialCRUD(AsyncBaseCRUD[StudyMaterial]):
    pass


study_material_crud = StudyMaterialCRUD(StudyMaterial)
