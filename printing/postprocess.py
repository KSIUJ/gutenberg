import os
import re
import subprocess

from control.models import PrintingProperties
from printing import SANDBOX_PATH


def postprocess_pdf(input_file: str, work_dir: str, properties: PrintingProperties):
    out = os.path.join(work_dir, 'final.pdf')
    subprocess.check_call([SANDBOX_PATH, work_dir, 'gs', '-sDEVICE=pdfwrite', '-dNOPAUSE',
                           '-dBATCH', '-dSAFER', '-dCompatibilityLevel=1.4',
                           '-sOutputFile=' + out, input_file])

    if properties.pages_to_print:
        new_out = os.path.join(work_dir, 'post.pdf')
        pages = properties.pages_to_print.replace(',', ' ').split()
        subprocess.check_call([SANDBOX_PATH, work_dir, 'pdftk', out, 'cat', *pages, 'output', new_out])
        out = new_out

    meta = subprocess.check_output([SANDBOX_PATH, work_dir, 'pdftk', out, 'dump_data_annots']).decode('utf-8',
                                                                                                      errors='ignore')
    num_pages = int(re.match(r'^NumberOfPages:\s+(\d+)', meta).group(1))

    return out, num_pages
