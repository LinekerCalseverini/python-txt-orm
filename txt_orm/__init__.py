from abc import ABC
from typing import List, Dict, Any, Callable
from pathlib import Path


from .fields import Field, FieldInstance
from .utils import asciify, count_lines


class Model(ABC):
    __fields__: Dict[str, Field]
    __table: 'TextDB | None'
    __index: int | None
    __size: int = 0

    def __init__(self, **kwargs) -> None:
        if '__fields__' not in self.__class__.__dict__:
            raise AttributeError(
                f'Fields not defined for {self.__class__.__name__}')

        for field, factory in self.__fields__.items():
            if field not in kwargs:
                continue

            setattr(self, field, factory.build(kwargs.get(field)))

        self.__table = None
        self.__index = None

        if '__table' in kwargs:
            self.__table = kwargs['__table']

        if '__index' in kwargs:
            self.__index = kwargs['__index']

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.__dict__ and __name in self.__fields__:
            field_value: FieldInstance = getattr(self, __name)
            field_value.value = __value

            if '_Model__table' not in self.__dict__:
                return

            if not isinstance(self.__table, TextDB):
                return

            if self.__index is None:
                return

            self.__table.update(
                self.__index, **{__name: str(field_value)}
            )
            return

        return super().__setattr__(__name, __value)

    def __str__(self) -> str:
        key_values = ','.join([
            f'{k}={repr(v)}' for k, v in self.__dict__.items()
            if 'Model' not in k
        ])
        return f'{self.__class__.__name__}({key_values})'

    def __repr__(self) -> str:
        return str(self)

    @classmethod
    def size(cls) -> int:
        if not cls.__fields__:
            return 0

        if cls.__size:
            return cls.__size

        total_size = 0
        for field in cls.__fields__.values():
            total_size += field.size

        total_size += len(cls.__fields__.keys()) - 1

        cls.__size = total_size
        return total_size


class TextDB:
    files: Dict[str, 'TextDB'] = {}
    filename: str
    cursor: int = 0
    num_lines = 0
    actions: List[Callable] = []
    __model__: type

    def __new__(cls, *args) -> 'TextDB':
        filename: str = args[0]
        if not isinstance(filename, str):
            raise AttributeError('Filename must be a string.')

        file = Path(filename)
        if not file.parent.exists():
            file.parent.mkdir(parents=True)

        if filename not in cls.files:
            cls.files[filename] = super().__new__(cls)

            if '__model__' not in cls.__dict__:
                raise AttributeError(f'Model not defined for {cls.__name__}')

        return cls.files[filename]

    def __init__(self, filename: str) -> None:
        if 'filename' not in self.__dict__:
            self.filename = filename
            self.__load()

    def __load(self) -> None:
        file = Path(self.filename)
        if not file.exists():
            file.touch()
            return

        self.num_lines = count_lines(self.filename)

    def __goto_line(self, line_number: int) -> None:
        if line_number in [0, 1]:
            self.cursor = 0
            return

        model: Model = self.__model__
        len_lines = model.size()  # type: ignore
        if line_number > self.num_lines:
            self.cursor = len_lines * self.num_lines + 1
            return

        self.cursor = (line_number - 1) * (len_lines + 2)

    def __readline(self):
        with open(self.filename, encoding='ascii') as f:
            f.seek(self.cursor)
            line = f.readline()
            return line

    def __write(self, text: str):
        ascii_text = asciify(text)
        with open(self.filename, 'r+', encoding='ascii') as f:
            f.seek(self.cursor)
            f.write(ascii_text)

    def __appendline(self, text: str):
        with open(self.filename, 'a', encoding='ascii') as f:
            f.write(asciify(text) + '\n')

        self.num_lines += 1

    def __parse_line(self, line) -> Dict[str, Any]:
        fields = {}
        start_index = 0
        model: Model = self.__model__  # type: ignore
        for field_name, field in model.__fields__.items():
            end_index = start_index + field.size + 1
            stringified_field = line[start_index:end_index].strip()
            fields.update({field_name: stringified_field})
            start_index = end_index
        return fields

    def get(self, index: int) -> Model | None:
        if index > self.num_lines:
            return None

        self.__goto_line(index)
        line = self.__readline()

        kwargs = self.__parse_line(line)
        return self.__model__(__table=self, __index=index, **kwargs)

    def insert(self, instance: Model):
        def f():
            data: Dict[str, str] = {}
            for k, v in instance.__dict__.items():
                if 'Model' in k:
                    continue

                if k not in instance.__fields__:
                    continue

                data.update({k: str(v)})

            self.__appendline(' '.join(data.values()))

        self.actions.append(f)

    def update(self, index: int, **kwargs):
        def f():
            self.__goto_line(index)
            model: Model = self.__model__
            previous_field_size = 0
            for k, v in model.__fields__.items():
                field_size = model.__fields__[k].size

                if 'Model' in k:
                    continue

                if previous_field_size:
                    self.cursor += previous_field_size + 1

                previous_field_size = field_size

                if k not in kwargs:
                    continue

                if k not in kwargs:
                    continue

                v = kwargs[k]
                if len(v) > field_size:
                    v = v[:field_size]

                if len(v) < field_size:
                    padding = ' ' * (field_size - len(v))
                    v = v + padding

                self.__write(v)

        self.actions.append(f)

    def select(self, **kwargs):
        for i in range(1, self.num_lines + 1):
            model = self.get(i)
            if model is None:
                continue

            table_model: Model = self.__model__
            assertions: List[bool] = []
            for k, v in kwargs.items():
                value = v
                field_size = table_model.__fields__[k].size
                if len(value) > field_size:
                    value = value[:field_size]

                assertions.append(asciify(value) in str(getattr(model, k)))

            if all(assertions):
                yield model

    def commit(self) -> None:
        for action in self.actions:
            action()

        self.actions = []
