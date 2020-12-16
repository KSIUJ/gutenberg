import math
import struct
from abc import ABC
from collections import OrderedDict
from datetime import datetime
from struct import Struct
from typing import Tuple, List, Type, Any, Iterable

from ipp.constants import SectionEnum, StatusCodeEnum
from ipp.exceptions import InvalidCharsetError, BadRequestError, UnsupportedIppVersionError, BadRequestIDError, \
    InvalidGroupError
from ipp.fields import CharsetField, NaturalLangField, TAG_STRUCT, IppFieldsStruct, \
    ParserState, OneSetField, KeywordField, NameWLField, NullField


def ipp_timestamp(date: datetime):
    return ((date.weekday() * 7 + date.hour) * 60 + date.minute) * 60 + date.second


class AttributeGroup(IppFieldsStruct):
    _filter = None
    _permanent_members = []
    _default_filter = ['all']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def write_to(self, writable, requested_attrs: List[str] = None):
        fields = [(name, clazz, getattr(self, name)) for name, clazz in self._filter_fields(requested_attrs).items() if
                  getattr(self, name)]
        fields = sorted(fields, key=lambda x: x[1].order if x[1].order else math.inf)
        for name, field, value in fields:
            field.write(writable, name, value)

    @classmethod
    def read_from(cls, readable, state: ParserState):
        fields = cls._get_proto_fields()
        read_fields = OrderedDict()
        state.read_field_header(readable)
        while True:
            if SectionEnum.is_section_tag(state.current_tag):
                cls._validate(read_fields)
                return cls(**read_fields)
            if state.current_name:
                field_name = state.current_name
                field = fields.get(field_name)
                if not field:
                    NullField().read(readable, state)
                    continue
                read_fields[field_name] = field.read(readable, state)
            else:
                pass

    @classmethod
    def _filter_fields(cls, requested_attrs: List[str]):
        fields = cls._get_proto_fields()
        if requested_attrs is None:
            requested_attrs = cls._default_filter
        if 'all' in requested_attrs or cls._filter in requested_attrs:
            return fields
        return {k: v for k, v in fields.items() if
                k.replace('_', '-') in requested_attrs or k in cls._permanent_members}

    @classmethod
    def get_tag(cls):
        if hasattr(cls, '_tag'):
            return cls._tag
        return None


class MergedGroup(AttributeGroup, ABC):
    merged_groups: List[AttributeGroup] = []

    @classmethod
    def _get_proto_fields(cls):
        fields = {}
        for group in cls.merged_groups:
            fields.update(group._get_proto_fields())
        return fields

    @classmethod
    def _filter_fields(cls, requested_attrs: List[str]):
        fields = {}
        if requested_attrs is None:
            requested_attrs = cls._default_filter
        for group in cls.merged_groups:
            fields.update(group._filter_fields(requested_attrs))
        return fields


class BaseOperationGroup(AttributeGroup):
    _tag = SectionEnum.operation
    _permanent_members = ['attributes_charset', 'attributes_natural_language']

    attributes_charset = CharsetField(required=True, default='utf-8', order=-2)
    attributes_natural_language = NaturalLangField(required=True, default='en', order=-1)
    requesting_user_name = NameWLField()
    requested_attributes = OneSetField(accepted_fields=[KeywordField()])

    @classmethod
    def _validate(cls, read_fields: OrderedDict):
        super()._validate(read_fields)
        if read_fields['attributes_charset'] != 'utf-8':
            raise InvalidCharsetError(read_fields['attributes_charset'])


class IppMessage:
    HEADER_STRUCT = Struct('>bbhi')
    IPP2_0 = (2, 0)
    IPP1_1 = (1, 1)
    IPP_VERSIONS = {
        IPP1_1, IPP2_0
    }

    def __init__(self, version: Tuple[int, int] = IPP2_0,
                 opid_or_status: int = StatusCodeEnum.ok, request_id: int = 0):
        self.version = version
        self.opid_or_status = opid_or_status
        self.request_id = request_id


class IppRequest(IppMessage):
    def __init__(self, http_request, version: Tuple[int, int] = IppMessage.IPP2_0,
                 opid_or_status: int = StatusCodeEnum.ok,
                 request_id: int = 0):
        super().__init__(version, opid_or_status, request_id)
        self._parser_state = ParserState()
        self._parser_state.read_field_header(http_request)
        self._http_request = http_request

    @classmethod
    def from_http_request(cls, request):
        try:
            version_major, version_minor, opid_or_status, request_id = cls.HEADER_STRUCT.unpack(
                request.read(cls.HEADER_STRUCT.size))
        except struct.error as ex:
            raise BadRequestError(ex)
        return cls(request, (version_major, version_minor), opid_or_status, request_id)

    def validate(self):
        if self.version not in self.IPP_VERSIONS:
            raise UnsupportedIppVersionError('{}.{}'.format(*self.version))
        if self.request_id <= 0:
            raise BadRequestIDError(str(self.request_id))
        return True

    def next_group_tag(self):
        return self._parser_state.current_tag

    def has_next(self):
        return self._parser_state.current_tag != SectionEnum.END

    def read_group(self, attribute_group_type: Type[AttributeGroup]) -> Any:
        if self._parser_state.current_tag != attribute_group_type.get_tag():
            raise InvalidGroupError(
                "Expected {}, got {}".format(attribute_group_type.get_tag(), self._parser_state.current_tag))
        return attribute_group_type.read_from(self._http_request, self._parser_state)

    def http_request(self):
        return self._http_request


class IppResponse(IppMessage):
    def __init__(self, version: Tuple[int, int], opid_or_status: int, request_id: int,
                 attribute_groups=None, requested_attrs=None):
        super().__init__(version, opid_or_status, request_id)
        if attribute_groups is None:
            attribute_groups = list()
        self._attribute_groups = attribute_groups
        self._requested_attrs = requested_attrs

    def add_attribute_group(self, attr_group: AttributeGroup):
        self._attribute_groups.append(attr_group)

    def write_to(self, writable):
        writable.write(self.HEADER_STRUCT.pack(self.version[0], self.version[1], self.opid_or_status, self.request_id))
        for group in self._attribute_groups:
            writable.write(TAG_STRUCT.pack(group.get_tag()))
            group.write_to(writable, self._requested_attrs)
        writable.write(TAG_STRUCT.pack(SectionEnum.END))


def minimal_valid_response(request: IppRequest, status: int = StatusCodeEnum.ok):
    return IppResponse(request.version, status, request.request_id, [BaseOperationGroup()])


def response_for(request: IppRequest, attr_groups: List[AttributeGroup], status: int = StatusCodeEnum.ok,
                 requested_attrs_oneset=None):
    return IppResponse(request.version, status, request.request_id, attr_groups,
                       [kv[1] for kv in requested_attrs_oneset] if isinstance(requested_attrs_oneset,
                                                                              Iterable) else None)
