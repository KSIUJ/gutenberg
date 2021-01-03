import os
import re
import subprocess
import sys

from control.models import PrintingProperties
from printing import SANDBOX_PATH


def postprocess_postscript(input_file: str, work_dir: str, properties: PrintingProperties):
    out = os.path.join(work_dir, 'final.pdf')
    subprocess.check_call([SANDBOX_PATH, work_dir, 'gs', '-sDEVICE=pdfwrite', '-dNOPAUSE',
                           '-dBATCH', '-dSAFER', '-dCompatibilityLevel=1.4',
                           '-sOutputFile=' + out, input_file])

    if properties.pages_to_print:
        new_out = os.path.join(work_dir, 'post.pdf')
        pages = properties.pages_to_print.split(',')
        subprocess.check_call([SANDBOX_PATH, work_dir, 'pdftk', out, 'cat', *pages, 'output', new_out])
        out = new_out

    meta = subprocess.check_output([SANDBOX_PATH, work_dir, 'pdftk', out, 'dump_data_annots']).decode('utf-8',
                                                                                                      errors='ignore')
    num_pages = int(re.match(r'^NumberOfPages:\s+(\d+)', meta).group(1))

    return out, num_pages


PWG_PAGE_HEADER = b'PwgRaster\0'
CHUNK_SIZE = 100000


def postprocess_pwg(input_file: str, work_dir: str, properties: PrintingProperties):
    out = os.path.join(work_dir, 'final.pwg')
    if properties.pages_to_print:
        ranges = [range(int(r[0]), int(r[0]) + 1) if len(r) == 1 else range(int(r[0]), int(r[1]) + 1)
                  for r in [x.split('-') for x in properties.pages_to_print.split(',')]]
    else:
        ranges = [range(1, sys.maxsize)]
    page_counter = 0
    saved_pages = -1  # we save the file header first as a page, hence -1.
    last = False
    save_current = True
    # Count and filter pages
    with open(input_file, 'rb') as input_fd, open(out, 'xb') as output_fd:
        buff = bytearray()
        while not last:
            rd = input_fd.read(CHUNK_SIZE)
            last = len(rd) < CHUNK_SIZE
            buff += rd
            while True:
                page_header = buff.find(PWG_PAGE_HEADER, 1)
                if page_header < 0:
                    break
                if save_current:
                    output_fd.write(buff[:page_header])
                    saved_pages += 1
                buff = buff[page_header:]
                page_counter += 1
                save_current = any(page_counter in r for r in ranges)
        if save_current:
            if buff:
                saved_pages += 1
            output_fd.write(buff)
    return out, saved_pages


def auto_postprocess(input_file: str, input_type: str, work_dir: str, properties: PrintingProperties):
    return {
        'application/pdf': postprocess_postscript,
        'application/postscript': postprocess_postscript,
        'image/pwg-raster': postprocess_pwg,
    }[input_type](input_file, work_dir, properties)
