import os
import subprocess
from abc import ABC, abstractmethod
from collections import deque, defaultdict
from typing import List, Type, Set, Union

import magic

from control.models import PrintJob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Converter(ABC):
    supported_types = []
    output_type = None

    def __init__(self, work_dir):
        self.work_dir = work_dir

    @abstractmethod
    def convert(self, input_file: str) -> str:
        pass


class SandboxConverter(Converter, ABC):
    SANDBOX_PATH = os.path.join(BASE_DIR, 'sandbox.sh')

    def run_in_sandbox(self, command: List[str]):
        subprocess.check_call(
            [SandboxConverter.SANDBOX_PATH, self.work_dir] + command)


class ImageConverter(SandboxConverter):
    supported_types = ['image/png', 'image/jpeg']
    output_type = 'application/pdf'

    CONVERT_OPTIONS = [
        '-resize', '2365x3335', '-gravity', 'center', '-background', 'white',
        '-extent', '2490x3510', '-units', 'PixelsPerInch', '-density', '300x300'
    ]

    def convert(self, input_file: str) -> str:
        out = os.path.join(self.work_dir, 'out.pdf')
        self.run_in_sandbox(['convert', input_file] + self.CONVERT_OPTIONS + [out])
        return out


class PDFConverter(SandboxConverter):
    supported_types = ['application/pdf']
    output_type = 'gutenberg/pdf'

    def convert(self, input_file: str) -> str:
        out = os.path.join(self.work_dir, 'final.pdf')
        self.run_in_sandbox(['gs', '-sDEVICE=pdfwrite', '-dNOPAUSE',
                             '-dBATCH', '-dSAFER', '-dCompatibilityLevel=1.4',
                             '-sOutputFile=' + out, input_file])
        return out


class DocConverter(SandboxConverter):
    supported_types = ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessing',
                       'application/rtf', 'application/vnd.oasis.opendocument.text']
    output_type = 'application/pdf'

    def convert(self, input_file: str) -> str:
        out = os.path.join(self.work_dir, 'out.pdf')
        self.run_in_sandbox(['unoconv', '-o', out, input_file])
        return out


CONVERTERS = [ImageConverter, DocConverter, PDFConverter]


class NoConverterAvailableError(ValueError):
    pass


def get_converter_chain(input_type: str, output_types: Set[str]) -> List[Type[Converter]]:
    converters_for_type = defaultdict(list)
    reverse = {}
    for conv in CONVERTERS:
        for mime in conv.supported_types:
            converters_for_type[mime].append(conv)

    def bfs():
        queue = deque([input_type])
        while len(queue) > 0:
            v = queue.pop()
            for conv in converters_for_type[v]:
                u = conv.output_type
                if u not in reverse:
                    reverse[u] = v, conv
                    queue.append(u)
                if u in output_types:
                    return

    bfs()
    intersect = output_types & reverse.keys()
    if not intersect:
        raise NoConverterAvailableError(
            "Unable to convert {} to {} - no converter available".format(input_type, output_types))
    pipeline = deque()
    v = next(iter(intersect))
    while v != input_type:
        v, conv = reverse[v]
        pipeline.appendleft(conv)
    return list(pipeline)


def auto_convert(input_file: str, out_types: Union[str, List[str]], work_dir: str) -> str:
    if isinstance(out_types, str):
        out_types = [out_types]
    out_types = set(out_types)
    mime_detector = magic.Magic(mime=True)
    input_type = mime_detector.from_file(input_file)
    if input_type in out_types:
        return input_type
    pipeline = get_converter_chain(input_type, out_types)
    file = input_file
    for conv_class in pipeline:
        conv = conv_class(work_dir)
        file = conv.convert(file)
    return file
