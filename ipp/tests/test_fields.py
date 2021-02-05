import datetime
import io
import struct
from collections import OrderedDict
from unittest import TestCase
from ipp.constants import SectionEnum, TagEnum, ValueTagsEnum
from ipp.exceptions import InvalidTagError, MissingFieldError, FieldOrderError
from ipp.fields import ParserState, TAG_STRUCT, NullField, UnknownField, BooleanField, IntegerField, \
    TextWLField, DateTimeField, Resolution, ResolutionField, IntRangeField, OneSetField, UnionField, \
    Collection, CollectionField, IntRange, OctetStringField, IppFieldsStruct
from ipp.tests.utils import as_buffer, len_tag, DNR, as_terminated_buffer, read_buffer


class ParserStateTests(TestCase):
    def test_empty(self):
        state = ParserState()
        state.read_field_header(as_buffer(b''))
        self.assertEqual(state.current_tag, SectionEnum.END)
        self.assertFalse(state.is_next_set_attr())

    def test_section_tag(self):
        state = ParserState()
        state.read_field_header(as_buffer(TAG_STRUCT.pack(SectionEnum.operation)))
        self.assertEqual(state.current_tag, SectionEnum.operation)
        self.assertFalse(state.is_next_set_attr())

    def test_field_tag(self):
        state = ParserState()
        buffer = as_buffer(
            TAG_STRUCT.pack(TagEnum.integer),
            len_tag(4),
            b'test',
            DNR
        )
        state.read_field_header(buffer)
        self.assertEqual(state.current_tag, TagEnum.integer)
        self.assertEqual(state.current_name, 'test')
        self.assertFalse(state.is_next_set_attr())
        self.assertEqual(buffer.read(), DNR)

    def test_repeated_field_tag(self):
        state = ParserState()
        buffer = as_buffer(
            TAG_STRUCT.pack(TagEnum.integer),
            len_tag(0),
            DNR
        )
        state.read_field_header(buffer)
        self.assertEqual(state.current_tag, TagEnum.integer)
        self.assertTrue(state.is_next_set_attr())
        self.assertEqual(buffer.read(), DNR)


class ReadFieldsTests(TestCase):
    def _get_state(self, tag):
        state = ParserState()
        state.current_tag = tag
        state.current_name = 'test'
        return state

    def _assert_buffer_safe(self, buffer, state):
        self.assertEqual(buffer.read(), DNR)
        self.assertEqual(state.current_tag, SectionEnum.END)

    def test_invalid_tag(self):
        buffer = as_terminated_buffer(
            len_tag(12),
            b'testtesttest',
        )
        state = self._get_state(1234)
        with self.assertRaises(InvalidTagError):
            _ = UnknownField().read(buffer, state)

    def test_null_field(self):
        buffer = as_terminated_buffer(
            len_tag(12),
            b'testtesttest',
        )
        state = self._get_state(TagEnum.unknown_value)
        _ = NullField().read(buffer, state)
        self._assert_buffer_safe(buffer, state)

    def test_unknown_field(self):
        buffer = as_terminated_buffer(
            len_tag(12),
            b'testtesttest',
        )
        state = self._get_state(ValueTagsEnum.unknown)
        _ = UnknownField().read(buffer, state)
        self._assert_buffer_safe(buffer, state)

    def test_boolean_field(self):
        buffer = as_terminated_buffer(
            len_tag(1),
            b'\01',
        )
        state = self._get_state(TagEnum.boolean)
        val = BooleanField().read(buffer, state)
        self.assertTrue(val)
        self._assert_buffer_safe(buffer, state)

    def test_integer_field(self):
        buffer = as_terminated_buffer(
            len_tag(4),
            struct.pack('>i', 123456789)
        )
        state = self._get_state(TagEnum.integer)
        val = IntegerField().read(buffer, state)
        self.assertEqual(val, 123456789)
        self._assert_buffer_safe(buffer, state)

    def test_octet_field(self):
        buffer = as_terminated_buffer(
            len_tag(8),
            b'test1234'
        )
        state = self._get_state(TagEnum.octet_str)
        val = OctetStringField().read(buffer, state)
        self.assertEqual(val, b'test1234')
        self._assert_buffer_safe(buffer, state)

    def test_text_field(self):
        buffer = as_terminated_buffer(
            len_tag(8),
            b'test1234'
        )
        state = self._get_state(TagEnum.text_without_language)
        val = TextWLField().read(buffer, state)
        self.assertEqual(val, 'test1234')
        self._assert_buffer_safe(buffer, state)

    def test_datetime_field(self):
        buffer = as_terminated_buffer(
            len_tag(11),
            b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x10\x11'
        )
        state = self._get_state(TagEnum.datetime)
        val = DateTimeField().read(buffer, state)
        self.assertEqual(val.timestamp(), -54020054212.2)
        self._assert_buffer_safe(buffer, state)

    def test_resolution_field(self):
        buffer = as_terminated_buffer(
            len_tag(9),
            struct.pack('>iib', 1, 2, Resolution.Units.DOTS_PER_INCH)
        )
        state = self._get_state(TagEnum.resolution)
        val = ResolutionField().read(buffer, state)
        self.assertEqual(val.x, 1)
        self.assertEqual(val.y, 2)
        self.assertEqual(val.unit, Resolution.Units.DOTS_PER_INCH)
        self._assert_buffer_safe(buffer, state)

    def test_range_field(self):
        buffer = as_terminated_buffer(
            len_tag(8),
            struct.pack('>ii', 1, 2)
        )
        state = self._get_state(TagEnum.range_of_integer)
        val = IntRangeField().read(buffer, state)
        self.assertEqual(val.lower, 1)
        self.assertEqual(val.upper, 2)
        self._assert_buffer_safe(buffer, state)

    def test_one_set_field(self):
        buffer = as_terminated_buffer(
            TAG_STRUCT.pack(TagEnum.integer),
            len_tag(4),
            b'test',
            len_tag(4),
            struct.pack('>i', 123456789),

            TAG_STRUCT.pack(TagEnum.text_without_language),
            len_tag(0),
            len_tag(8),
            b'test1234'
        )
        state = ParserState()
        state.read_field_header(buffer)
        val = OneSetField(accepted_fields=[IntegerField(), TextWLField()]).read(buffer, state)
        self.assertListEqual(val, [
            (IntegerField, 123456789),
            (TextWLField, 'test1234')
        ])
        self._assert_buffer_safe(buffer, state)

    def test_one_set_field_invalid_type(self):
        buffer = as_terminated_buffer(
            TAG_STRUCT.pack(TagEnum.integer),
            len_tag(4),
            b'test',
            len_tag(4),
            struct.pack('>i', 123456789),
        )
        state = ParserState()
        state.read_field_header(buffer)
        with self.assertRaises(InvalidTagError):
            _ = OneSetField(accepted_fields=[TextWLField()]).read(buffer, state)

    def test_union_field(self):
        buffer = as_terminated_buffer(
            TAG_STRUCT.pack(TagEnum.integer),
            len_tag(4),
            b'test',
            len_tag(4),
            struct.pack('>i', 123456789),
        )
        state = ParserState()
        state.read_field_header(buffer)
        val = UnionField(accepted_fields=[IntegerField(), TextWLField()]).read(buffer, state)
        self.assertEqual(val, (IntegerField, 123456789))
        self._assert_buffer_safe(buffer, state)

    def test_union_field_invalid_type(self):
        buffer = as_terminated_buffer(
            TAG_STRUCT.pack(TagEnum.integer),
            len_tag(4),
            b'test',
            len_tag(4),
            struct.pack('>i', 123456789),
        )
        state = ParserState()
        state.read_field_header(buffer)
        with self.assertRaises(InvalidTagError):
            _ = UnionField(accepted_fields=[TextWLField()]).read(buffer, state)

    class TestCollection(Collection):
        class TestNestedCollection(Collection):
            field = BooleanField()

        field_a = IntegerField(required=True)
        field_b = TextWLField(required=False)
        field_c = CollectionField(collection_type=TestNestedCollection)

    def test_collection_field(self):
        buffer = as_terminated_buffer(
            # begin collection
            TAG_STRUCT.pack(TagEnum.begin_collection),
            len_tag(4),
            b'test',
            len_tag(0),

            # field_a name
            TAG_STRUCT.pack(TagEnum.member_attr_name),
            len_tag(0),
            len_tag(7),
            b'field-a',

            # field_a value
            TAG_STRUCT.pack(TagEnum.integer),
            len_tag(0),
            len_tag(4),
            struct.pack('>i', 123456789),

            # field_b name
            TAG_STRUCT.pack(TagEnum.member_attr_name),
            len_tag(0),
            len_tag(7),
            b'field-b',

            # field_b value
            TAG_STRUCT.pack(TagEnum.text_without_language),
            len_tag(0),
            len_tag(8),
            b'test1234',

            # field_b name
            TAG_STRUCT.pack(TagEnum.member_attr_name),
            len_tag(0),
            len_tag(7),
            b'field-c',

            # begin nested collection
            TAG_STRUCT.pack(TagEnum.begin_collection),
            len_tag(0),
            len_tag(0),

            # field_a name
            TAG_STRUCT.pack(TagEnum.member_attr_name),
            len_tag(0),
            len_tag(5),
            b'field',

            # field_a value
            TAG_STRUCT.pack(TagEnum.boolean),
            len_tag(0),
            len_tag(1),
            struct.pack('>b', True),

            # end nested collection
            TAG_STRUCT.pack(TagEnum.end_collection),
            len_tag(0),
            len_tag(0),

            # unknown field name (should be ignored)
            TAG_STRUCT.pack(TagEnum.member_attr_name),
            len_tag(0),
            len_tag(7),
            b'field-x',

            # unknown field value (should be ignored)
            TAG_STRUCT.pack(TagEnum.text_without_language),
            len_tag(0),
            len_tag(7),
            b'unknown',

            # end collection
            TAG_STRUCT.pack(TagEnum.end_collection),
            len_tag(0),
            len_tag(0),
        )
        state = ParserState()
        state.read_field_header(buffer)
        val = CollectionField(collection_type=self.TestCollection).read(buffer, state)
        self.assertEqual(val.field_a, 123456789)
        self.assertEqual(val.field_b, 'test1234')
        self.assertEqual(val.field_c.field, True)
        self._assert_buffer_safe(buffer, state)


class WriteFieldTests(TestCase):
    def test_unknown_field(self):
        buffer = io.BytesIO()
        UnknownField().write(buffer, 'test', b'1234')
        self.assertEqual(read_buffer(buffer), b'\x12\x00\x04test\x00\x00')

    def test_boolean_field(self):
        buffer = io.BytesIO()
        BooleanField().write(buffer, 'test', True)
        self.assertEqual(read_buffer(buffer), b'\x22\x00\x04test\x00\x01\x01')

    def test_integer_field(self):
        buffer = io.BytesIO()
        IntegerField().write(buffer, 'test', 123456789)
        self.assertEqual(read_buffer(buffer), b'!\x00\x04test\x00\x04\x07[\xcd\x15')

    def test_text_field(self):
        buffer = io.BytesIO()
        TextWLField().write(buffer, 'test', 'test1234')
        self.assertEqual(read_buffer(buffer), b'A\x00\x04test\x00\x08test1234')

    def test_octet_field(self):
        buffer = io.BytesIO()
        OctetStringField().write(buffer, 'test', b'test1234')
        self.assertEqual(read_buffer(buffer), b'0\x00\x04test\x00\x08test1234')

    def test_datetime_field(self):
        buffer = io.BytesIO()
        dt = datetime.datetime.fromtimestamp(12345678.1234)
        DateTimeField().write(buffer, 'test', dt)
        self.assertEqual(read_buffer(buffer), b'1\x00\x04test\x00\x0b\x07\xb2\x05\x17\x15\x15\x12\x01+\x00\x00')

    def test_resolution_field(self):
        buffer = io.BytesIO()
        ResolutionField().write(buffer, 'test', Resolution(1, 2, Resolution.Units.DOTS_PER_INCH))
        self.assertEqual(read_buffer(buffer), b'2\x00\x04test\x00\t\x00\x00\x00\x01\x00\x00\x00\x02\x03')

    def test_range_field(self):
        buffer = io.BytesIO()
        IntRangeField().write(buffer, 'test', IntRange(1, 2))
        self.assertEqual(read_buffer(buffer), b'3\x00\x04test\x00\x08\x00\x00\x00\x01\x00\x00\x00\x02')

    def test_one_set_field(self):
        buffer = io.BytesIO()
        OneSetField(accepted_fields=[IntegerField(), TextWLField()]).write(buffer, 'test', [
            (IntegerField, 123456789),
            (TextWLField, 'test1234')
        ])
        self.assertEqual(read_buffer(buffer), b'!\x00\x04test\x00\x04\x07[\xcd\x15A\x00\x00\x00\x08test1234')

    def test_one_set_field_short_args(self):
        buffer = io.BytesIO()
        OneSetField(accepted_fields=[TextWLField(), IntegerField()]).write(buffer, 'test', [
            'test1234', '4321test', (IntegerField, 123456789),
        ])
        self.assertEqual(read_buffer(buffer),
                         b'A\x00\x04test\x00\x08test1234A\x00\x00\x00\x084321test!\x00\x00\x00\x04\x07[\xcd\x15')

    def test_union_field(self):
        buffer = io.BytesIO()
        UnionField(accepted_fields=[IntegerField(), TextWLField()]).write(buffer, 'test', (TextWLField, 'test1234'))
        self.assertEqual(read_buffer(buffer), b'A\x00\x04test\x00\x08test1234')

    def test_union_field_short(self):
        buffer = io.BytesIO()
        UnionField(accepted_fields=[TextWLField(), IntegerField()]).write(buffer, 'test', 'test1234')
        self.assertEqual(read_buffer(buffer), b'A\x00\x04test\x00\x08test1234')

    class TestCollection(Collection):
        class TestNestedCollection(Collection):
            field = BooleanField()

        field_a = IntegerField(required=True)
        field_b = TextWLField(required=False)
        field_c = CollectionField(collection_type=TestNestedCollection)

    def test_collection_field(self):
        buffer = io.BytesIO()
        CollectionField(collection_type=self.TestCollection) \
            .write(buffer, 'test', self.TestCollection(field_a=1234,
                                                       field_b='test1235',
                                                       field_c=self.TestCollection.TestNestedCollection(
                                                           field=True)))
        self.assertEqual(read_buffer(buffer),
                         b'4\x00\x04test\x00\x00J\x00\x00\x00\x07field-a!\x00\x00\x00\x04\x00\x00\x04\xd2J\x00\x00\x00'
                         b'\x07field-bA\x00\x00\x00\x08test1235J\x00\x00\x00\x07field-c4\x00\x00\x00\x00J\x00\x00\x00'
                         b'\x05field"\x00\x00\x00\x01\x017\x00\x00\x00\x007\x00\x00\x00\x00')


class IppFieldsStructTests(TestCase):
    class TestStruct(IppFieldsStruct):
        field_a = IntegerField(required=True, default=1, order=1)
        field_b = IntegerField(required=False, default=1, order=2)
        field_c = IntegerField(required=True)
        field_d = IntegerField(required=False)

    def test_get_fields(self):
        self.maxDiff = None
        fields = self.TestStruct._get_proto_fields()
        self.assertDictEqual(fields, {
            'field_a': IntegerField(required=True, default=1, order=1),
            'field_b': IntegerField(required=False, default=1, order=2),
            'field_c': IntegerField(required=True),
            'field_d': IntegerField(required=False),
        })

    def test_create(self):
        val = self.TestStruct(
            field_a=10,
            field_b=20,
            field_c=30,
            field_d=40,
        )
        self.assertEqual(val.field_a, 10)
        self.assertEqual(val.field_b, 20)
        self.assertEqual(val.field_c, 30)
        self.assertEqual(val.field_d, 40)

    def test_create_unexpected_arg(self):
        with self.assertRaises(TypeError):
            self.TestStruct(
                field_a=10,
                field_b=20,
                field_c=30,
                field_d=40,
                field_x=50,
            )

    def test_create_missing_required_arg_no_default(self):
        with self.assertRaises(TypeError):
            self.TestStruct(
                field_a=10,
                field_b=20,
                field_d=40,
            )

    def test_create_missing_required_arg_default(self):
        val = self.TestStruct(
            field_b=20,
            field_c=30,
            field_d=40,
        )
        self.assertEqual(val.field_a, 1)
        self.assertEqual(val.field_b, 20)
        self.assertEqual(val.field_c, 30)
        self.assertEqual(val.field_d, 40)

    def test_create_no_defaults_missing_required(self):
        with self.assertRaises(TypeError):
            self.TestStruct(
                field_b=20,
                field_c=30,
                field_d=40,
                use_defaults=False
            )

    def test_create_no_defaults_missing_not_required(self):
        val = self.TestStruct(
            field_a=10,
            field_c=30,
            use_defaults=False
        )
        self.assertEqual(val.field_a, 10)
        self.assertEqual(val.field_b, None)
        self.assertEqual(val.field_c, 30)
        self.assertEqual(val.field_d, None)

    def test_validate(self):
        fields = OrderedDict()
        fields['field_a'] = 10
        fields['field_b'] = 20
        fields['field_c'] = 30
        fields['field_d'] = 40
        self.TestStruct._validate(fields)

    def test_validate_missing_required(self):
        fields = OrderedDict()
        fields['field_b'] = 20
        fields['field_c'] = 30
        fields['field_d'] = 40
        with self.assertRaises(MissingFieldError):
            self.TestStruct._validate(fields)

    def test_validate_missing_not_required(self):
        fields = OrderedDict()
        fields['field_a'] = 10
        fields['field_c'] = 30
        fields['field_d'] = 40
        self.TestStruct._validate(fields)

    def test_validate_wrong_order(self):
        fields = OrderedDict()
        fields['field_a'] = 10
        fields['field_c'] = 30
        fields['field_b'] = 20
        fields['field_d'] = 40
        with self.assertRaises(FieldOrderError):
            self.TestStruct._validate(fields)
