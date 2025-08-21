import io

from ipp.constants import SectionEnum
from ipp.fields import TAG_STRUCT, LENGTH_STRUCT

DNR = b'DO_NOT_READ'
END = TAG_STRUCT.pack(SectionEnum.END)


def as_buffer(*data: bytes):
    return io.BytesIO(b''.join(data))


def as_terminated_buffer(*data: bytes):
    return as_buffer(*data, END, DNR)


def read_buffer(buff: io.BytesIO):
    buff.seek(0)
    return buff.read()


def len_tag(length: int):
    return LENGTH_STRUCT.pack(length)
