from abc import ABC, abstractmethod, abstractproperty


class FieldInstance(ABC):
    @abstractproperty
    def value(self): pass
    @value.setter
    def value(self, value) -> None: pass
    @abstractmethod
    def __str__(self) -> str: pass
    @abstractmethod
    def __repr__(self) -> str: pass


class Field(ABC):
    @abstractproperty
    def size(self) -> int: pass
    @abstractmethod
    def build(self, value) -> FieldInstance: pass


class CharFieldInstance(FieldInstance):
    def __init__(self, size: int, value: str) -> None:
        self._value = ''
        self.size = size
        self.value = value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value) -> None:
        if not isinstance(value, str):
            raise ValueError('Value must be a string')

        self._value = value

    def __str__(self) -> str:
        if len(self.value) > self.size:
            return self.value[:self.size]

        if len(self.value) < self.size:
            padding = ' ' * (self.size - len(self.value))
            return self.value + padding

        return self.value

    def __repr__(self) -> str:
        return f'"{self._value}"'


class CharField(Field):
    def __init__(self, size: int) -> None:
        self._size = size

    @property
    def size(self) -> int:
        return self._size

    def build(self, value: str) -> CharFieldInstance:
        return CharFieldInstance(self.size, value)


class PositiveIntegerFieldInstance(FieldInstance):
    def __init__(self, size: int, value: int) -> None:
        self._value = 0
        self._size = size
        self.value = value

    @property
    def size(self) -> int:
        return self._size

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value) -> None:
        if not isinstance(value, int):
            raise ValueError('Value must be an integer')

        if value < 0:
            raise ValueError('Value must be a positive integer')

        if value > 2**32 - 1:
            raise ValueError('Value must be an 32-bit positive integer')

        self._value = value

    def __str__(self) -> str:
        string_value = str(self.value)
        padding = ' ' * (self.size - len(string_value))
        return padding + string_value

    def __repr__(self) -> str:
        return str(self.value)


class PositiveIntegerField(Field):
    def __init__(self) -> None:
        self._size = 10

    @property
    def size(self) -> int:
        return self._size

    def build(self, value: str) -> PositiveIntegerFieldInstance:
        new_value = int(value) if value else 0
        return PositiveIntegerFieldInstance(self.size, new_value)
