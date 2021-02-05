import io
import logging
from typing import Any, List, Optional, Tuple
from unittest import TestCase
from unittest.mock import Mock

from ipp.constants import StatusCodeEnum, JobStateEnum
from ipp.exceptions import BadRequestError, UnsupportedIppVersionError, DocumentFormatError
from ipp.proto import IppResponse, IppRequest, minimal_valid_response, AttributeGroup
from ipp.proto_operations import JobObjectAttributeGroupFull, JobObjectAttributeGroup, \
    GetPrinterAttributesRequestOperationGroup, PrintJobRequestOperationGroup, JobTemplateAttributeGroup, \
    SendDocumentRequestOperationGroup, GetJobsRequestOperationGroup, GetJobAttributesRequestOperationGroup, \
    CancelJobRequestOperationGroup, CloseJobRequestOperationGroup, IdentifyPrinterRequestOperationGroup
from ipp.service import BaseIppService, BaseIppEverywhereService


def _get_mocked_request_factory(return_value):
    request_class = IppRequest
    request_class.from_http_request = Mock(return_value=return_value)
    return request_class


class BaseIppServiceTests(TestCase):
    class TestIppServiceWrapper(BaseIppService):
        def __init__(self, request_factory=IppRequest) -> None:
            super().__init__('test_user', request_factory)
            self.last_response = None
            self.last_code = None

        # Implement abstract methods.
        def _http_response(self, ipp_response: IppResponse, http_code=200):
            self.last_response = ipp_response
            self.last_code = http_code

        def raise_ipp_error(self, request):
            raise BadRequestError()

        def raise_internal_error(self, request):
            raise Exception()

        def return_ok(self, request):
            return minimal_valid_response(request)

        SUPPORTED_OPERATIONS = {
            1: raise_ipp_error,
            2: raise_internal_error,
            3: return_ok,
        }

    def _assert_response(self, service, status_code, request_id=100):
        self.assertEqual(service.last_code, 200)
        self.assertEqual(service.last_response.opid_or_status, status_code)
        self.assertEqual(service.last_response.request_id, request_id)

    def test_unparsable_request(self):
        buffer = io.BytesIO()
        request_class = IppRequest
        request_class.from_http_request = Mock(side_effect=BadRequestError())
        service = self.TestIppServiceWrapper(request_factory=request_class)
        service.handle_request(buffer, 'print')
        self._assert_response(service, StatusCodeEnum.client_error_bad_request, 0)

    def test_invalid_request(self):
        buffer = io.BytesIO()
        request = IppRequest(buffer, request_id=100)
        request.validate = Mock(side_effect=UnsupportedIppVersionError())
        request_class = _get_mocked_request_factory(request)
        service = self.TestIppServiceWrapper(request_factory=request_class)
        service.handle_request(buffer, 'print')
        self._assert_response(service, StatusCodeEnum.server_error_version_not_supported)

    def test_parsing_unhandled_exception(self):
        logging.disable(logging.CRITICAL)
        buffer = io.BytesIO()
        request = IppRequest(buffer, request_id=100)
        request.validate = Mock(side_effect=Exception())
        request_class = _get_mocked_request_factory(request)
        service = self.TestIppServiceWrapper(request_factory=request_class)
        service.handle_request(buffer, 'print')
        self._assert_response(service, StatusCodeEnum.server_error_internal_error)

    def test_operation_error(self):
        buffer = io.BytesIO()
        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        request_class = _get_mocked_request_factory(request)
        service = self.TestIppServiceWrapper(request_factory=request_class)
        service.handle_request(buffer, 'print')
        self._assert_response(service, StatusCodeEnum.client_error_bad_request)

    def test_operation_unhandled_exception(self):
        logging.disable(logging.CRITICAL)
        buffer = io.BytesIO()
        request = IppRequest(buffer, request_id=100, opid_or_status=2)
        request_class = _get_mocked_request_factory(request)
        service = self.TestIppServiceWrapper(request_factory=request_class)
        service.handle_request(buffer, 'print')
        self._assert_response(service, StatusCodeEnum.server_error_internal_error)

    def test_operation_not_implemented(self):
        buffer = io.BytesIO()
        request = IppRequest(buffer, request_id=100, opid_or_status=999)
        request_class = _get_mocked_request_factory(request)
        service = self.TestIppServiceWrapper(request_factory=request_class)
        service.handle_request(buffer, 'print')
        self._assert_response(service, StatusCodeEnum.server_error_operation_not_supported)

    def test_operation_ok(self):
        buffer = io.BytesIO()
        request = IppRequest(buffer, request_id=100, opid_or_status=3)
        request_class = _get_mocked_request_factory(request)
        service = self.TestIppServiceWrapper(request_factory=request_class)
        service.handle_request(buffer, 'print')
        self._assert_response(service, StatusCodeEnum.ok)


class BaseIppEverywhereServiceTests(TestCase):
    class TestIppServiceWrapper(BaseIppEverywhereService):
        def __init__(self, mock, request_factory=IppRequest, job_submitted=True) -> None:
            super().__init__(actor_name='test_user', request_factory=request_factory,
                             printer_name='test-printer',
                             printer_uri='ipps://test',
                             printer_tls=True,
                             printer_basic_auth=True,
                             printer_color=True,
                             printer_duplex=True,
                             printer_icon='https://test/icon',
                             supported_ipp_formats=['application/pdf'],
                             default_ipp_format='application/pdf',
                             webpage_uri='https://test')

            self.last_response = None
            self.last_code = None
            self.mock = mock
            self.job_submitted = job_submitted

        # Implement abstract methods.

        def _create_job(self, *args, **kwargs) -> int:
            self.mock(*args, **kwargs)
            return 1234

        def _submit_job(self, *args, **kwargs) -> int:
            self.mock(*args, **kwargs)
            return 4321

        def _get_job_uri(self, job_id) -> str:
            self.mock(job_id)
            return "ipps://test/job/{}".format(job_id)

        def _get_job(self, job_id) -> Optional[Tuple[int, JobStateEnum, bool, Any]]:
            self.mock(job_id)
            return 1, JobStateEnum.pending, self.job_submitted, None

        def _get_jobs(self, *args, **kwargs) -> List[Any]:
            self.mock(*args, **kwargs)
            return [None]

        def _build_job_proto(self, *args, full_job_proto=True, **kwargs) -> AttributeGroup:
            self.mock(full_job_proto, *args, **kwargs)
            clazz = JobObjectAttributeGroupFull if full_job_proto else JobObjectAttributeGroup
            return clazz(
                job_uri='ipps://test/job/1',
                job_id=1,
                job_state=JobStateEnum.pending,
                job_printer_uri=self.printer_uri,
                job_name='test-job',
                job_originating_user_name='test-user',
                time_at_creation=1234,
                time_at_processing=12345,
                time_at_completed=123456,
                job_printer_up_time=1234567,
            )

        def _cancel_job(self, job: Any) -> None:
            self.mock(job)

        def _http_response(self, ipp_response: IppResponse, http_code=200):
            self.last_response = ipp_response
            self.last_code = http_code

    def test_get_printer_attrs(self):
        buffer = io.BytesIO()
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = GetPrinterAttributesRequestOperationGroup(
            printer_uri='unused',
            document_format='application/pdf'
        )
        request.read_group = Mock(return_value=operation)

        service = self.TestIppServiceWrapper(argument_captor)
        response = service.get_printer_attrs(request)
        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].printer_name, 'Gutenberg-test-printer')
        self.assertIn('ipps://test', response._attribute_groups[1].printer_uri_supported)

    def test_get_printer_attrs_unsupported_format(self):
        buffer = io.BytesIO()
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = GetPrinterAttributesRequestOperationGroup(
            printer_uri='unused',
            document_format='application/octet-stream'
        )
        request.read_group = Mock(return_value=operation)

        service = self.TestIppServiceWrapper(argument_captor)
        with self.assertRaises(DocumentFormatError):
            service.get_printer_attrs(request)

    def test_print_job(self):
        buffer = io.BytesIO()
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = PrintJobRequestOperationGroup(
            printer_uri='unused',
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor)
        response = service.print_job(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].job_id, 4321)
        self.assertEqual(argument_captor.call_count, 3)
        call_create_job = argument_captor.call_args_list[0].args
        self.assertEqual(call_create_job[0], operation)
        self.assertEqual(call_create_job[1], JobTemplateAttributeGroup())
        call_submit_job = argument_captor.call_args_list[1].args
        self.assertEqual(call_submit_job[0].http_request, buffer)
        self.assertEqual(call_submit_job[1], operation)
        self.assertEqual(call_submit_job[2], 1234)
        self.assertEqual(argument_captor.call_args_list[2].args[0], 4321)

    def test_print_job_with_template(self):
        buffer = io.BytesIO()
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = PrintJobRequestOperationGroup(
            printer_uri='unused'
        )
        template = JobTemplateAttributeGroup(
            copies=10
        )
        request.read_group = Mock(side_effect=[operation, template])
        request.has_next = Mock(side_effect=[True, False])
        service = self.TestIppServiceWrapper(argument_captor)
        response = service.print_job(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].job_id, 4321)
        self.assertEqual(argument_captor.call_count, 3)
        call_create_job = argument_captor.call_args_list[0].args
        self.assertEqual(call_create_job[0], operation)
        self.assertEqual(call_create_job[1], template)
        call_submit_job = argument_captor.call_args_list[1].args
        self.assertEqual(call_submit_job[0].http_request, buffer)
        self.assertEqual(call_submit_job[1], operation)
        self.assertEqual(call_submit_job[2], 1234)
        self.assertEqual(argument_captor.call_args_list[2].args[0], 4321)

    def test_validate_job(self):
        buffer = io.BytesIO()
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = PrintJobRequestOperationGroup(
            printer_uri='unused',
            document_format='application/pdf'
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor)
        response = service.validate_job(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)

    def test_validate_job_unsupported_format(self):
        buffer = io.BytesIO()
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = PrintJobRequestOperationGroup(
            printer_uri='unused',
            document_format='application/octet-stream'
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor)
        with self.assertRaises(DocumentFormatError):
            service.validate_job(request)

    def test_create_job(self):
        buffer = io.BytesIO()
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = PrintJobRequestOperationGroup(
            printer_uri='unused',
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor)
        response = service.create_job(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].job_id, 1234)
        self.assertEqual(argument_captor.call_count, 2)
        call_create_job = argument_captor.call_args_list[0].args
        self.assertEqual(call_create_job[0], operation)
        self.assertEqual(call_create_job[1], JobTemplateAttributeGroup())
        self.assertEqual(argument_captor.call_args_list[1].args[0], 1234)

    def test_create_job_with_template(self):
        buffer = io.BytesIO()
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = PrintJobRequestOperationGroup(
            printer_uri='unused'
        )
        template = JobTemplateAttributeGroup(
            copies=10
        )
        request.read_group = Mock(side_effect=[operation, template])
        request.has_next = Mock(side_effect=[True, False])
        service = self.TestIppServiceWrapper(argument_captor)
        response = service.create_job(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].job_id, 1234)
        self.assertEqual(argument_captor.call_count, 2)
        call_create_job = argument_captor.call_args_list[0].args
        self.assertEqual(call_create_job[0], operation)
        self.assertEqual(call_create_job[1], template)
        self.assertEqual(argument_captor.call_args_list[1].args[0], 1234)

    def test_send_document(self):
        buffer = io.BytesIO()
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = SendDocumentRequestOperationGroup(
            printer_uri='unused',
            last_document=True,
            job_id=1,
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor, job_submitted=False)
        response = service.send_document(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].job_id, 1)
        self.assertEqual(argument_captor.call_count, 3)
        call_get_job = argument_captor.call_args_list[0].args
        self.assertEqual(call_get_job[0], 1)
        call_submit_job = argument_captor.call_args_list[1].args
        self.assertEqual(call_submit_job[0].http_request, buffer)
        self.assertEqual(call_submit_job[1], operation)
        self.assertEqual(call_submit_job[2], 1)
        self.assertEqual(argument_captor.call_args_list[2].args[0], 1)

    def test_send_document_again_last_empty(self):
        buffer = io.BytesIO()
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = SendDocumentRequestOperationGroup(
            printer_uri='unused',
            last_document=True,
            job_id=1,
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor, job_submitted=True)
        response = service.send_document(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].job_id, 1)
        self.assertEqual(argument_captor.call_count, 2)
        call_get_job = argument_captor.call_args_list[0].args
        self.assertEqual(call_get_job[0], 1)
        self.assertEqual(argument_captor.call_args_list[1].args[0], 1)

    def test_send_document_again_not_last(self):
        buffer = io.BytesIO(b'12345678901234567890')
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = SendDocumentRequestOperationGroup(
            printer_uri='unused',
            last_document=False,
            job_id=1,
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor, job_submitted=True)
        response = service.send_document(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.server_error_multiple_document_jobs_not_supported)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(argument_captor.call_count, 1)
        call_get_job = argument_captor.call_args_list[0].args
        self.assertEqual(call_get_job[0], 1)

    def test_send_document_again_last_nonempty(self):
        buffer = io.BytesIO(b'\0' * 200)
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = SendDocumentRequestOperationGroup(
            printer_uri='unused',
            last_document=True,
            job_id=1,
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor, job_submitted=True)
        response = service.send_document(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.server_error_multiple_document_jobs_not_supported)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(argument_captor.call_count, 1)
        call_get_job = argument_captor.call_args_list[0].args
        self.assertEqual(call_get_job[0], 1)

    def test_get_jobs_all(self):
        buffer = io.BytesIO(b'\0' * 200)
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = GetJobsRequestOperationGroup(
            printer_uri='unused',
            which_jobs='all'
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor, job_submitted=True)
        response = service.get_jobs(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].job_id, 1)
        self.assertEqual(argument_captor.call_count, 2)
        call_get_jobs = argument_captor.call_args_list[0].kwargs
        self.assertDictEqual(call_get_jobs,
                             {'first_index': 0, 'limit': 10000, 'all_jobs': True, 'exclude_completed': True})
        self.assertListEqual(list(argument_captor.call_args_list[1].args), [False, None])

    def test_get_jobs_completed(self):
        buffer = io.BytesIO(b'\0' * 200)
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = GetJobsRequestOperationGroup(
            printer_uri='unused',
            which_jobs='completed'
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor, job_submitted=True)
        response = service.get_jobs(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].job_id, 1)
        self.assertEqual(argument_captor.call_count, 2)
        call_get_jobs = argument_captor.call_args_list[0].kwargs
        self.assertDictEqual(call_get_jobs,
                             {'first_index': 0, 'limit': 10000, 'all_jobs': False, 'exclude_completed': False})
        self.assertListEqual(list(argument_captor.call_args_list[1].args), [False, None])

    def test_get_job_attrs(self):
        buffer = io.BytesIO(b'\0' * 200)
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = GetJobAttributesRequestOperationGroup(
            printer_uri='unused',
            job_uri='ipps://test/job/1'
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor, job_submitted=True)
        response = service.get_job_attrs(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].job_id, 1)
        self.assertEqual(argument_captor.call_count, 2)
        self.assertEqual(argument_captor.call_args_list[0].args[0], 1)
        self.assertListEqual(list(argument_captor.call_args_list[1].args), [True, None])

    def test_cancel_job(self):
        buffer = io.BytesIO(b'\0' * 200)
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = CancelJobRequestOperationGroup(
            printer_uri='unused',
            job_uri='ipps://test/job/1'
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor)
        response = service.cancel_job(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(argument_captor.call_count, 2)
        self.assertEqual(argument_captor.call_args_list[0].args[0], 1)
        self.assertListEqual(list(argument_captor.call_args_list[1].args), [None])

    def test_close_job(self):
        buffer = io.BytesIO(b'\0' * 200)
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = CloseJobRequestOperationGroup(
            printer_uri='unused',
            job_uri='ipps://test/job/1'
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor)
        response = service.close_job(request)

        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
        self.assertEqual(response._attribute_groups[1].job_id, 1)
        self.assertEqual(argument_captor.call_count, 2)
        self.assertEqual(argument_captor.call_args_list[0].args[0], 1)
        self.assertListEqual(list(argument_captor.call_args_list[1].args), [1])

    def test_identify_printer(self):
        buffer = io.BytesIO(b'\0' * 200)
        argument_captor = Mock()

        request = IppRequest(buffer, request_id=100, opid_or_status=1)
        operation = IdentifyPrinterRequestOperationGroup(
            printer_uri='unused',
        )
        request.read_group = Mock(return_value=operation)
        service = self.TestIppServiceWrapper(argument_captor)
        response = service.identify_printer(request)

        # No-op, just test the header.
        self.assertEqual(response.opid_or_status, StatusCodeEnum.ok)
        self.assertEqual(response.request_id, 100)
