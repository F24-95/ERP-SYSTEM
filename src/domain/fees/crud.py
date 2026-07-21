from src.database.base_crud import AsyncBaseCRUD
from src.domain.fees.models import Fee


class FeeCRUD(AsyncBaseCRUD[Fee]):
    """No bespoke queries needed — everything fees/service.py needs
    (get_by_filters, exists, paginate, ...) is provided by AsyncBaseCRUD.
    """


fee_crud = FeeCRUD(Fee)
