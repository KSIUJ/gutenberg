import datetime
import io
import struct
from collections import OrderedDict
from unittest import TestCase

from ipp.constants import SectionEnum, TagEnum, StatusCodeEnum, OperationEnum
from ipp.exceptions import InvalidCharsetError, UnsupportedIppVersionError, BadRequestIDError, BadRequestError, \
    InvalidGroupError
from ipp.fields import IntegerField, TAG_STRUCT, ParserState
from ipp.proto import ipp_timestamp, AttributeGroup, MergedGroup, BaseOperationGroup, IppRequest, IppResponse
from ipp.tests.utils import as_terminated_buffer, DNR, len_tag, read_buffer


class IppTimestampTests(TestCase):
    def test_timestamp(self):
        dt = datetime.datetime.utcfromtimestamp(12345678)
        stamp = ipp_timestamp(dt)
        self.assertEqual(stamp, 202878)


class AttributeGroupTests(TestCase):
    class TestAttributeGroup(AttributeGroup):
        _filter = 'test-filter'
        _permanent_members = 'field_a'
        _default_filter = 'field-b'
        _tag = SectionEnum.operation

        field_a = IntegerField(default=1)
        field_b = IntegerField(default=2)
        field_c = IntegerField(default=3)

    def test_read(self):
        # test reading an attribute group, validation is not tested as it is already inherited from IppFieldsStruct.
        buffer = as_terminated_buffer(
            TAG_STRUCT.pack(SectionEnum.operation),

            TAG_STRUCT.pack(TagEnum.integer),
            len_tag(7),
            b'field-a',
            len_tag(4),
            struct.pack('>i', 123456),

            TAG_STRUCT.pack(TagEnum.integer),
            len_tag(7),
            b'field-b',
            len_tag(4),
            struct.pack('>i', 234567),

            TAG_STRUCT.pack(TagEnum.integer),
            len_tag(7),
            b'field-c',
            len_tag(4),
            struct.pack('>i', 345678),

            # unknown field - should be ignored.
            TAG_STRUCT.pack(TagEnum.text_without_language),
            len_tag(7),
            b'field-x',
            len_tag(7),
            b'unknown'
        )

        state = ParserState()
        state.read_field_header(buffer)

        val = self.TestAttributeGroup.read_from(buffer, state)
        self.assertEqual(val.field_a, 123456)
        self.assertEqual(val.field_b, 234567)
        self.assertEqual(val.field_c, 345678)
        self.assertEqual(buffer.read(), DNR)
        self.assertEqual(state.current_tag, SectionEnum.END)

    def test_write_default(self):
        buffer = io.BytesIO()
        self.TestAttributeGroup().write_to(buffer)
        # expected: only _permanent_members and _default_filter fields are written.
        self.assertEqual(read_buffer(buffer),
                         b'!\x00\x07field-a\x00\x04\x00\x00\x00\x01!\x00\x07field-b\x00\x04\x00\x00\x00\x02')

    def test_write_all(self):
        buffer = io.BytesIO()
        self.TestAttributeGroup().write_to(buffer, requested_attrs=['all'])
        # expected: all fields written.
        self.assertEqual(read_buffer(buffer),
                         b'!\x00\x07field-a\x00\x04\x00\x00\x00\x01!\x00\x07field-b\x00\x04\x00\x00\x00\x02'
                         b'!\x00\x07field-c\x00\x04\x00\x00\x00\x03')

    def test_write_filter(self):
        buffer = io.BytesIO()
        self.TestAttributeGroup().write_to(buffer, requested_attrs=['field-c'])
        # expected: only _permanent_members and field_c are written.
        self.assertEqual(read_buffer(buffer),
                         b'!\x00\x07field-a\x00\x04\x00\x00\x00\x01!\x00\x07field-c\x00\x04\x00\x00\x00\x03')

    def test_write_group_filter(self):
        buffer = io.BytesIO()
        self.TestAttributeGroup().write_to(buffer, requested_attrs=['test-filter'])
        # expected: all fields written.
        self.assertEqual(read_buffer(buffer),
                         b'!\x00\x07field-a\x00\x04\x00\x00\x00\x01!\x00\x07field-b\x00\x04\x00\x00\x00\x02'
                         b'!\x00\x07field-c\x00\x04\x00\x00\x00\x03')

    def test_write_empty_filter(self):
        buffer = io.BytesIO()
        self.TestAttributeGroup().write_to(buffer, requested_attrs=[])
        # expected: only _permanent_members are written.
        self.assertEqual(read_buffer(buffer), b'!\x00\x07field-a\x00\x04\x00\x00\x00\x01')

    def test_get_tag(self):
        self.assertEqual(self.TestAttributeGroup.get_tag(), SectionEnum.operation)


# noinspection PyUnresolvedReferences
class MergedGroupTests(TestCase):
    class TestAttributeGroupA(AttributeGroup):
        _filter = 'test-filter-a'
        _permanent_members = 'field_a'
        _default_filter = 'field-b'
        _tag = SectionEnum.operation

        field_a = IntegerField(default=1)
        field_b = IntegerField(default=2)
        field_c = IntegerField()

    class TestAttributeGroupB(AttributeGroup):
        _filter = 'test-filter-b'
        _permanent_members = 'field_d'
        _default_filter = 'field-e'
        _tag = SectionEnum.printer

        field_d = IntegerField(default=4)
        field_e = IntegerField(default=5)
        field_f = IntegerField()

    def _get_merged(self, default_filter=None):
        class TestMergedGroup(MergedGroup):
            merged_groups = [self.TestAttributeGroupA, self.TestAttributeGroupB]
            _tag = SectionEnum.job
            _default_filter = default_filter

        return TestMergedGroup

    def test_merged(self):
        merged_clazz = self._get_merged()
        group = merged_clazz(field_b=20, field_e=50)
        # Expected: all fields present and set correctly.
        self.assertEqual(group.field_a, 1)
        self.assertEqual(group.field_b, 20)
        self.assertEqual(group.field_c, None)
        self.assertEqual(group.field_d, 4)
        self.assertEqual(group.field_e, 50)
        self.assertEqual(group.field_f, None)
        self.assertEqual(group.get_tag(), SectionEnum.job)

    def test_filter_all(self):
        merged_clazz = self._get_merged()
        val = merged_clazz._filter_fields(['all']).keys()
        self.assertListEqual(list(val), ['field_a', 'field_b', 'field_c', 'field_d', 'field_e', 'field_f'])

    def test_filter_delegate_default(self):
        merged_clazz = self._get_merged(default_filter=None)
        val = merged_clazz._filter_fields(None).keys()
        self.assertListEqual(list(val), ['field_a', 'field_b', 'field_d', 'field_e'])

    def test_filter_set_default(self):
        merged_clazz = self._get_merged(default_filter=['field-e'])
        val = merged_clazz._filter_fields(None).keys()
        self.assertListEqual(list(val), ['field_a', 'field_d', 'field_e'])

    def test_filter_set_filter(self):
        merged_clazz = self._get_merged(default_filter=['all'])
        val = merged_clazz._filter_fields(['field-e']).keys()
        self.assertListEqual(list(val), ['field_a', 'field_d', 'field_e'])


class BaseOperationGroupTests(TestCase):
    def test_validation(self):
        fields = OrderedDict()
        fields['attributes_charset'] = 'utf-8'
        fields['attributes_natural_language'] = 'en'
        BaseOperationGroup._validate(fields)

    def test_validation_error(self):
        fields = OrderedDict()
        fields['attributes_charset'] = 'ascii'
        fields['attributes_natural_language'] = 'en'
        with self.assertRaises(InvalidCharsetError):
            BaseOperationGroup._validate(fields)


class IppRequestTests(TestCase):
    def test_validate_ok(self):
        buffer = io.BytesIO()
        request = IppRequest(buffer, (1, 0), StatusCodeEnum.ok, 1)
        request.validate()

    def test_validate_bad_version(self):
        buffer = io.BytesIO()
        request = IppRequest(buffer, (2, 1), StatusCodeEnum.ok, 1)
        with self.assertRaises(UnsupportedIppVersionError):
            request.validate()

    def test_validate_bad_id(self):
        buffer = io.BytesIO()
        request = IppRequest(buffer, (1, 0), StatusCodeEnum.ok, -1)
        with self.assertRaises(BadRequestIDError):
            request.validate()

    def test_parser_state_next(self):
        buffer = io.BytesIO()
        request = IppRequest(buffer, (1, 0), StatusCodeEnum.ok, 1)
        self.assertEqual(request.next_group_tag(), SectionEnum.END)

    def test_parser_state_has_next(self):
        buffer = io.BytesIO()
        request = IppRequest(buffer, (1, 0), StatusCodeEnum.ok, 1)
        self.assertFalse(request.has_next())

    class TestAttributeGroupA(AttributeGroup):
        _tag = SectionEnum.operation
        field_a = IntegerField(default=1)

    class TestAttributeGroupB(AttributeGroup):
        _tag = SectionEnum.printer
        field_b = IntegerField(default=4)

    TEST_HEADER = struct.pack('>bbhi', 2, 0, OperationEnum.get_jobs, 1)

    TEST_REQUEST = (
        TEST_HEADER,

        TAG_STRUCT.pack(SectionEnum.operation),

        TAG_STRUCT.pack(TagEnum.integer),
        len_tag(7),
        b'field-a',
        len_tag(4),
        struct.pack('>i', 123456),

        TAG_STRUCT.pack(SectionEnum.printer),

        TAG_STRUCT.pack(TagEnum.integer),
        len_tag(7),
        b'field-b',
        len_tag(4),
        struct.pack('>i', 234567),
    )

    def test_from_http_request_header(self):
        request = IppRequest.from_http_request(as_terminated_buffer(self.TEST_HEADER))
        self.assertEqual(request.version, (2, 0))
        self.assertEqual(request.opid_or_status, OperationEnum.get_jobs)
        self.assertEqual(request.request_id, 1)
        self.assertEqual(request.http_request.read(), DNR)
        self.assertEqual(request.next_group_tag(), SectionEnum.END)
        self.assertFalse(request.has_next())

    def test_from_http_request_bad_header(self):
        with self.assertRaises(BadRequestError):
            IppRequest.from_http_request(io.BytesIO(b'1234'))

    def test_from_http_request(self):
        request = IppRequest.from_http_request(as_terminated_buffer(*self.TEST_REQUEST))
        self.assertEqual(request.version, (2, 0))
        self.assertEqual(request.opid_or_status, OperationEnum.get_jobs)
        self.assertEqual(request.request_id, 1)

        self.assertEqual(request.next_group_tag(), SectionEnum.operation)
        self.assertTrue(request.has_next())
        group_a = request.read_group(self.TestAttributeGroupA)
        self.assertEqual(group_a.field_a, 123456)

        self.assertEqual(request.next_group_tag(), SectionEnum.printer)
        self.assertTrue(request.has_next())
        group_b = request.read_group(self.TestAttributeGroupB)
        self.assertEqual(group_b.field_b, 234567)

        self.assertEqual(request.http_request.read(), DNR)
        self.assertEqual(request.next_group_tag(), SectionEnum.END)
        self.assertFalse(request.has_next())

    def test_from_http_request_invalid_group(self):
        request = IppRequest.from_http_request(as_terminated_buffer(*self.TEST_REQUEST))
        with self.assertRaises(InvalidGroupError):
            request.read_group(self.TestAttributeGroupB)


class IppResponseTests(TestCase):
    def test_write_header(self):
        buffer = io.BytesIO()
        IppResponse((2, 0), StatusCodeEnum.ok, 1).write_to(buffer)
        self.assertEqual(read_buffer(buffer), b'\x02\x00\x00\x00\x00\x00\x00\x01\x03')

    class TestAttributeGroup(AttributeGroup):
        _tag = SectionEnum.operation
        field_a = IntegerField(default=1)
        field_b = IntegerField(default=2)

    def test_write(self):
        buffer = io.BytesIO()
        response = IppResponse((2, 0), StatusCodeEnum.ok, 1)
        response.add_attribute_group(self.TestAttributeGroup())
        response.write_to(buffer)
        self.assertEqual(read_buffer(buffer),
                         b'\x02\x00\x00\x00\x00\x00\x00\x01\x01!\x00\x07field-a\x00\x04\x00\x00\x00\x01!\x00\x07field-b'
                         b'\x00\x04\x00\x00\x00\x02\x03')

    def test_write_requested(self):
        buffer = io.BytesIO()
        response = IppResponse((2, 0), StatusCodeEnum.ok, 1, requested_attrs=['field-a'])
        response.add_attribute_group(self.TestAttributeGroup())
        response.write_to(buffer)
        self.assertEqual(read_buffer(buffer),
                         b'\x02\x00\x00\x00\x00\x00\x00\x01\x01!\x00\x07field-a\x00\x04\x00\x00\x00\x01\x03')
