from abc import ABC
from typing import List, Dict, Any, Callable
from pathlib import Path


class Model(ABC):
    __fields__: List[str]
    __table: 'TextDB | None'
    __index: int | None

    def __init__(self, **kwargs) -> None:
        if '__fields__' not in self.__class__.__dict__:
            raise AttributeError(
                f'Fields not defined for {self.__class__.__name__}')

        for field in self.__fields__:
            setattr(self, field, kwargs.get(field))

        self.__table = None
        self.__index = None

        if 'table' in kwargs:
            self.__table = kwargs['table']

        if 'index' in kwargs:
            self.__index = kwargs['index']

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.__fields__:
            if '_Model__table' in self.__dict__:
                if isinstance(self.__table, TextDB):
                    if self.__index is not None:
                        self.__table.update(self.__index, **{__name: __value})

        return super().__setattr__(__name, __value)

    def __str__(self) -> str:
        key_values = ','.join([
            f'{k}={v}' for k, v in self.__dict__.items()
            if 'Model' not in k
        ])
        return f'{self.__class__.__name__}({key_values})'

    def __repr__(self) -> str:
        return str(self)


class TextDB:
    files: Dict[str, 'TextDB'] = {}
    filename: str
    cursor: int = 0
    num_lines = 0
    len_lines = 0
    loaded: bool
    actions: List[Callable] = []
    __fields__: Dict[str, int]
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

            if '__fields__' not in cls.__dict__:
                raise AttributeError(f'Fields not defined for {cls.__name__}')

            if '__model__' not in cls.__dict__:
                raise AttributeError(f'Model not defined for {cls.__name__}')

        return cls.files[filename]

    def __init__(self, filename: str) -> None:
        if 'filename' not in self.__dict__:
            self.filename = filename
            start_char = 0
            self.columns_start_position = {}
            for k, v in self.__fields__.items():
                self.columns_start_position.update({
                    k: start_char
                })
                start_char += v + 1

            self.len_lines = sum([v + 1 for v in self.__fields__.values()]) + 1
            self.__load()

    def __load(self) -> None:
        file = Path(self.filename)
        if not file.exists():
            file.touch()
            return

        self.num_lines = 0
        with open(self.filename, encoding='ascii') as f:
            self.num_lines = len(f.readlines())

    def __goto_line(self, line_number: int) -> None:
        if line_number in [0, 1]:
            self.cursor = 0
            return

        if line_number > self.num_lines:
            self.cursor = (self.len_lines) * self.num_lines + 1
            return

        self.cursor = (line_number - 1) * (self.len_lines)

    def __readline(self):
        with open(self.filename, encoding='ascii') as f:
            f.seek(self.cursor)
            line = f.readline()
            return line

    def __asciify(self, text: str) -> str:
        new_string = ''
        for char in text:
            char_lower = char.lower()
            if char_lower in 'àâãá':
                new_string += 'a' if char.islower() else 'A'
                continue
            if char_lower == 'ç':
                new_string += 'c' if char.islower() else 'C'
                continue
            if char_lower in 'éê':
                new_string += 'e' if char.islower() else 'E'
                continue
            if char_lower == 'í':
                new_string += 'i' if char.islower() else 'I'
                continue
            if char_lower in 'óõô':
                new_string += 'o' if char.islower() else 'O'
                continue
            if char_lower in 'úü':
                new_string += 'u' if char.islower() else 'U'
                continue

            new_string += char

        return new_string

    def __write(self, text: str):
        ascii_text = self.__asciify(text)
        with open(self.filename, 'r+', encoding='ascii') as f:
            f.seek(self.cursor)
            f.write(ascii_text)

    def __appendline(self, text: str):
        with open(self.filename, 'a', encoding='ascii') as f:
            f.write(self.__asciify(text) + '\n')

        self.num_lines += 1

    def __parse_line(self, line) -> Dict[str, Any]:
        fields = {}
        start_index = 0
        for field, size in self.__fields__.items():
            end_index = start_index + size + 1
            stringified_field = line[start_index:end_index].strip()
            fields.update({field: stringified_field})
            start_index = end_index
        return fields

    def get(self, index: int) -> Model | None:
        if index > self.num_lines:
            return None

        self.__goto_line(index)
        line = self.__readline()

        kwargs = self.__parse_line(line)
        return self.__model__(table=self, index=index, **kwargs)

    def insert(self, instance: Model):
        def f():
            data: Dict[str, str] = {}
            for k, v in instance.__dict__.items():
                if 'Model' in k:
                    continue

                if k not in self.__fields__:
                    raise AttributeError(f'Unknown column: {k}')

                field_size = self.__fields__[k]
                if len(v) > field_size:
                    v = v[:field_size]

                padding = ' ' * (field_size - len(v))
                data[k] = v + padding

            self.__appendline(' '.join(data.values()))

        self.actions.append(f)

    def update(self, index: int, **kwargs):
        def f():
            self.__goto_line(index)
            cursor = self.cursor
            for k, v in kwargs.items():
                field_size = self.__fields__[k]
                self.cursor = cursor + self.columns_start_position[k]
                if len(v) > field_size:
                    v = v[:field_size]

                padding = ' ' * (field_size - len(v))
                v = v + padding
                self.__write(v)

        self.actions.append(f)

    def select(self, **kwargs):
        for i in range(1, self.num_lines + 1):
            model = self.get(i)
            if model is None:
                continue
            assertions: List[bool] = []
            for k, v in kwargs.items():
                value = v
                field_size = self.__fields__[k]
                if len(value) > field_size:
                    value = value[:field_size]

                assertions.append(self.__asciify(value) in getattr(model, k))

            if all(assertions):
                yield model

    def commit(self) -> None:
        for action in self.actions:
            action()

        self.actions = []
