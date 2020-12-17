import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from collections import deque, defaultdict
from itertools import chain
from typing import List, Type, Set, Tuple

import magic

from printing import SANDBOX_PATH


class Converter(ABC):
    supported_types = []
    supported_extensions = []
    output_type = None

    def __init__(self, work_dir):
        self.work_dir = work_dir

    @abstractmethod
    def convert(self, input_file: str) -> str:
        pass

    @classmethod
    @abstractmethod
    def is_available(cls):
        pass


class SandboxConverter(Converter, ABC):
    def run_in_sandbox(self, command: List[str]):
        subprocess.check_call(
            [SANDBOX_PATH, self.work_dir] + command)

    @staticmethod
    def binary_exists(name: str):
        return shutil.which(name) is not None


class ImageConverter(SandboxConverter):
    supported_types = ['image/png', 'image/jpeg']
    supported_extensions = ['png', 'jpg', 'jpeg']
    output_type = 'application/pdf'

    CONVERT_OPTIONS = [
        '-resize', '2365x3335', '-gravity', 'center', '-background', 'white',
        '-extent', '2490x3510', '-units', 'PixelsPerInch', '-density', '300x300'
    ]

    def convert(self, input_file: str) -> str:
        out = os.path.join(self.work_dir, 'out.pdf')
        self.run_in_sandbox(['convert', input_file] + self.CONVERT_OPTIONS + [out])
        return out

    @classmethod
    def is_available(cls):
        return cls.binary_exists('convert')


class DocConverter(SandboxConverter):
    supported_types = ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessing',
                       'application/rtf', 'application/vnd.oasis.opendocument.text']
    supported_extensions = ['doc', 'docx', 'rtf', 'odt']
    output_type = 'application/pdf'

    def convert(self, input_file: str) -> str:
        out = os.path.join(self.work_dir, 'out.pdf')
        self.run_in_sandbox(['unoconv', '-o', out, input_file])
        return out

    @classmethod
    def is_available(cls):
        return cls.binary_exists('unoconv')


NATIVE_FILE_FORMATS = ['application/pdf', 'image/pwg-raster']
NATIVE_FILE_EXTENSIONS = ['pdf', 'pwg']
CONVERTERS_ALL = [ImageConverter, DocConverter]
CONVERTERS = [conv for conv in CONVERTERS_ALL if conv.is_available()]
SUPPORTED_FILE_FORMATS = NATIVE_FILE_FORMATS + list(chain.from_iterable(conv.supported_types for conv in CONVERTERS))
SUPPORTED_EXTENSIONS = NATIVE_FILE_EXTENSIONS + list(
    chain.from_iterable(conv.supported_extensions for conv in CONVERTERS))


class NoConverterAvailableError(ValueError):
    pass


def get_converter_chain(input_type: str, output_types: Set[str]) -> Tuple[List[Type[Converter]], str]:
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
    final_type = v
    while v != input_type:
        v, conv = reverse[v]
        pipeline.appendleft(conv)
    return list(pipeline), final_type


def detect_file_format(input_file: str):
    mime_detector = magic.Magic(mime=True)
    input_type = mime_detector.from_file(input_file)
    return input_type


def auto_convert(input_file: str, input_type: str, work_dir: str) -> Tuple[str, str]:
    out_types = set(NATIVE_FILE_FORMATS)
    if input_type in out_types:
        return input_file, input_type
    pipeline, out_type = get_converter_chain(input_type, out_types)
    file = input_file
    for conv_class in pipeline:
        conv = conv_class(work_dir)
        file = conv.convert(file)
    return file, out_type
