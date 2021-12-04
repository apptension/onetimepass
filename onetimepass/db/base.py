class BaseDB:
    def read(self) -> dict:
        raise NotImplementedError

    def write(self, data: dict):
        raise NotImplementedError
