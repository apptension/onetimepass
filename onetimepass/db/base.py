from .models import DatabaseSchema


class BaseDB:
    def read(self) -> DatabaseSchema:
        raise NotImplementedError

    def write(self, data: DatabaseSchema):
        raise NotImplementedError
