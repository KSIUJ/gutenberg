import math
from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from enum import IntEnum
from struct import Struct
from typing import List, Any, Type, Union, Tuple

from django.templatetags.tz import utc

from ipp.constants import TagEnum, SectionEnum, ValueTagsEnum
from ipp.exceptions import FieldOrderError, InvalidTagError, MissingFieldError, BadRequestError

TAG_STRUCT = Struct('>B')
LENGTH_STRUCT = Struct('>h')


class ParserState:
    def __init__(self):
        self.current_name = None
        self.current_tag = SectionEnum.END

    def read_field_header(self, readable):
        data = readable.read(TAG_STRUCT.size)
        if len(data) < TAG_STRUCT.size:
            self.current_tag = SectionEnum.END
            return
        self.current_tag, = TAG_STRUCT.unpack(data)
        if SectionEnum.is_section_tag(self.current_tag):
            return
        length, = LENGTH_STRUCT.unpack(readable.read(LENGTH_STRUCT.size))
        self.current_name = readable.read(length).decode('utf-8', errors='ignore').replace('-', '_')

    def is_next_set_attr(self):
        return \
            (not self.current_name) and \
            (self.current_tag not in [TagEnum.member_attr_name, TagEnum.end_collection]) and \
            (not SectionEnum.is_section_tag(self.current_tag))


class IppField(ABC):
    def __init__(self, required=False, default=None, order=None):
        self.required = required
        self.default = default
        self.order = order

    @abstractmethod
    def write(self, writable, name, value):
        raise NotImplementedError()

    @abstractmethod
    def read(self, readable, state: ParserState):
        raise NotImplementedError()

    @classmethod
    def get_tag(cls):
        if hasattr(cls, '_tag'):
            return cls._tag
        return 9999999


class IppFieldsStruct:
    def __init__(self, use_defaults=True, **kwargs):
        self.proto_fields = self._get_proto_fields()

        for name, val in kwargs.items():
            if name not in self.proto_fields:
                raise TypeError("got an unexpected keyword argument '{}'".format(name))
            setattr(self, name, val)
        for name, val in self.proto_fields.items():
            if name not in self.__dict__:
                if not val.default and val.required:
                    raise TypeError("missing required keyword argument '{}'".format(name))
                if use_defaults:
                    setattr(self, name, val.default)
                else:
                    setattr(self, name, None)

    @classmethod
    def _validate(cls, read_fields: OrderedDict):
        proto_fields = cls._get_proto_fields()
        for name, val in proto_fields.items():
            if name not in read_fields:
                if val.required:
                    raise MissingFieldError("missing required keyword argument '{}'".format(name))
        previous = None
        for name in read_fields:
            if previous:
                o1 = proto_fields[previous].order
                o2 = proto_fields[name].order
                o1 = o1 if o1 else math.inf
                o2 = o2 if o2 else math.inf
                if o1 > o2:
                    raise FieldOrderError("field {} before {}".format(previous, name))
            previous = name

    @classmethod
    def _get_proto_fields(cls):
        all_fields = dir(cls)
        return {name: getattr(cls, name) for name in all_fields if isinstance(getattr(cls, name), IppField)}

    def __str__(self):
        return '\n'.join('   {}: {}'.format(field, getattr(self, field)) for field in self._get_proto_fields())


class ValueField(IppField, ABC):
    @abstractmethod
    def write_value(self, writable, value):
        writable.write(LENGTH_STRUCT.pack(len(value)))
        writable.write(value)

    def write(self, writable, name, value):
        writable.write(TAG_STRUCT.pack(self.get_tag()))
        writable.write(LENGTH_STRUCT.pack(len(name)))
        writable.write(name.replace('_', '-').encode('utf-8'))
        self.write_value(writable, value)

    @abstractmethod
    def read_value(self, readable):
        length, = LENGTH_STRUCT.unpack(readable.read(LENGTH_STRUCT.size))
        return readable.read(length)

    def read(self, readable, state: ParserState):
        if self.get_tag() and state.current_tag != self.get_tag():
            raise InvalidTagError()
        value = self.read_value(readable)
        state.read_field_header(readable)
        return value


class StructField(ValueField, ABC):
    struct = None

    def write_value(self, writable, value):
        super().write_value(writable, self.struct.pack(*value))

    def read_value(self, readable):
        data = super().read_value(readable)
        if self.struct.size != len(data):
            raise ValueError
        return self.struct.unpack(data)


class NullField(ValueField):
    _tag = None

    def write_value(self, writable, value):
        raise NotImplementedError("unsupported")

    def read_value(self, readable):
        _ = super().read_value(readable)
        return None


class UnknownField(ValueField):
    _tag = ValueTagsEnum.unknown

    def write_value(self, writable, value):
        super().write_value(writable, b'')

    def read_value(self, readable):
        _ = super().read_value(readable)
        return None


class BooleanField(StructField):
    struct = Struct('>b')

    def write_value(self, writable, value):
        assert isinstance(value, bool)
        super().write_value(writable, (1 if value else 0,))

    def read_value(self, readable):
        val, = super().read_value(readable)
        return [False, True][val]

    _tag = TagEnum.boolean


class IntegerField(StructField):
    struct = Struct('>i')
    _tag = TagEnum.integer

    def write_value(self, writable, value):
        if isinstance(value, IntEnum):
            value = value.value
        assert isinstance(value, int)
        super().write_value(writable, (value,))

    def read_value(self, readable):
        return super().read_value(readable)[0]


class EnumField(IntegerField):
    _tag = TagEnum.enum


class TextField(ValueField, ABC):
    def write_value(self, writable, value):
        assert isinstance(value, str)
        super().write_value(writable, value.encode('utf-8'))

    def read_value(self, readable):
        return super().read_value(readable).decode('utf-8', errors='ignore')


class OctetStringField(ValueField):
    _tag = TagEnum.octet_str

    def write_value(self, writable, value):
        assert isinstance(value, bytes)
        super().write_value(writable, value)

    def read_value(self, readable):
        return super().read_value(readable)


class TextWLField(TextField):
    _tag = TagEnum.text_without_language


class NameWLField(TextField):
    _tag = TagEnum.name_without_language


class KeywordField(TextField):
    _tag = TagEnum.keyword


class UriField(TextField):
    _tag = TagEnum.uri


class CharsetField(TextField):
    _tag = TagEnum.charset


class NaturalLangField(TextField):
    _tag = TagEnum.natural_language


class MimeTypeField(TextField):
    _tag = TagEnum.mime_media_type


class DateTimeField(StructField):
    _tag = TagEnum.datetime
    struct = Struct('>hbbbbbbbbb')

    def write_value(self, writable, value):
        assert isinstance(value, datetime)
        utc_value = utc(value)
        super().write_value(writable,
                            (utc_value.year, utc_value.month, utc_value.day, utc_value.hour,
                             utc_value.minute, utc_value.second, utc_value.microsecond // 100000, 0x2b, 0, 0))

    def read_value(self, readable):
        year, month, day, hour, minute, second, deci_second, tz_direction, tz_diff_h, tz_diff_m = super().read_value(
            readable)
        tz_direction = 1 if tz_direction == 0x2b else -1
        return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second,
                        microsecond=deci_second * 100000,
                        tzinfo=timezone(offset=timedelta(hours=tz_direction * tz_diff_h,
                                                         minutes=tz_direction * tz_diff_m)))


@dataclass
class Resolution:
    class Units(IntEnum):
        UNKNOWN = 0
        DOTS_PER_INCH = 3
        DOTS_PER_CM = 4

    x: int
    y: int
    unit: Units


class ResolutionField(StructField):
    _tag = TagEnum.resolution
    struct = Struct('>iib')

    def write_value(self, writable, value):
        assert isinstance(value, Resolution)
        super().write_value(writable, (value.x, value.y, value.unit))

    def read_value(self, readable):
        return Resolution(*super().read_value(readable))


@dataclass
class IntRange:
    lower: int
    upper: int


class IntRangeField(StructField):
    struct = Struct('>ii')
    _tag = TagEnum.range_of_integer

    def write_value(self, writable, value):
        assert isinstance(value, IntRange)
        super().write_value(writable, (value.lower, value.upper))

    def read_value(self, readable):
        return IntRange(*super().read_value(readable))


class OneSetField(IppField):
    def __init__(self, accepted_fields: List[IppField], *args, **kwargs):
        self.accepted_fields = accepted_fields
        self.tag_ids_map = {field.get_tag(): field for field in accepted_fields}
        super().__init__(*args, **kwargs)

    def write(self, writable, name: str, value: List[Union[Tuple[Type[ValueField], Any], Any]]):
        for idx, val in enumerate(value):
            if isinstance(val, tuple):
                field = val[0]()
                v = val[1]
            else:
                field = self.accepted_fields[0]
                v = val
            if idx == 0:
                field.write(writable, name, v)
            else:
                field.write(writable, '', v)

    def read(self, readable, state: ParserState):
        values = []
        while True:
            if state.current_tag not in self.tag_ids_map:
                raise InvalidTagError(state.current_tag)
            field = self.tag_ids_map[state.current_tag]
            val = field.read(readable, state)
            values.append((field.__class__, val))
            if not state.is_next_set_attr():
                return values


class UnionField(IppField):
    def __init__(self, accepted_fields: List[IppField], *args, **kwargs):
        self.accepted_fields = accepted_fields
        self.tag_ids_map = {field.get_tag(): field for field in accepted_fields}
        super().__init__(*args, **kwargs)

    def write(self, writable, name: str, value: Union[Tuple[Type[ValueField], Any, Any]]):
        if isinstance(value, tuple):
            field = value[0]()
            v = value[1]
        else:
            field = self.accepted_fields[0]
            v = value
        field.write(writable, name, v)

    def read(self, readable, state: ParserState):
        if state.current_tag not in self.tag_ids_map:
            raise InvalidTagError(state.current_tag)
        field = self.tag_ids_map[state.current_tag]
        return field.read(readable, state)


class Collection(IppFieldsStruct):
    def write(self, writable):
        fields = [(name, clazz, getattr(self, name)) for name, clazz in self.proto_fields.items() if
                  getattr(self, name)]
        fields = sorted(fields, key=lambda x: x[1].order if x[1].order else math.inf)
        for name, field, value in fields:
            writable.write(TAG_STRUCT.pack(TagEnum.member_attr_name))
            writable.write(LENGTH_STRUCT.pack(0))
            writable.write(LENGTH_STRUCT.pack(len(name)))
            writable.write(name.replace('_', '-').encode('utf-8'))
            field.write(writable, '', value)

    @classmethod
    def read(cls, readable, state: ParserState):
        fields = cls._get_proto_fields()
        read_fields = OrderedDict()
        while True:
            if state.current_tag == TagEnum.end_collection:
                cls._validate(read_fields)
                return cls(**read_fields)
            if state.current_tag == TagEnum.member_attr_name:
                length, = LENGTH_STRUCT.unpack(readable.read(LENGTH_STRUCT.size))
                name = readable.read(length).decode('utf-8', errors='ignore').replace('-', '_')
                field = fields.get(name)
                state.read_field_header(readable)
                if not field:
                    NullField().read(readable, state)
                    continue
                read_fields[name] = field.read(readable, state)
            else:
                raise BadRequestError("Invalid collection tag")


class CollectionField(IppField):
    _tag = TagEnum.begin_collection

    def __init__(self, collection_type: Type[Collection], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collection_type = collection_type

    def write(self, writable, name, value):
        writable.write(TAG_STRUCT.pack(self.get_tag()))
        writable.write(LENGTH_STRUCT.pack(len(name)))
        writable.write(name.replace('_', '-').encode('utf-8'))
        writable.write(LENGTH_STRUCT.pack(0))

        value.write(writable)

        writable.write(TAG_STRUCT.pack(TagEnum.end_collection))
        writable.write(LENGTH_STRUCT.pack(0))
        writable.write(LENGTH_STRUCT.pack(0))

    def read(self, readable, state: ParserState):
        if state.current_tag != self.get_tag():
            raise InvalidTagError()
        readable.read(LENGTH_STRUCT.size)
        state.read_field_header(readable)
        val = self.collection_type.read(readable, state)
        if state.current_tag != TagEnum.end_collection:
            raise InvalidTagError()
        readable.read(LENGTH_STRUCT.size)
        state.read_field_header(readable)
        return val
