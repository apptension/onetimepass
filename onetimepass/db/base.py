import abc

from .models import DatabaseSchema


class BaseDB(abc.ABC):
    @abc.abstractmethod
    def read(self) -> DatabaseSchema:
        pass

    @abc.abstractmethod
    def write(self, data: DatabaseSchema):
        pass
