import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SANDBOX_PATH = os.path.join(BASE_DIR, 'sandbox.sh')
TASK_TIMEOUT_S = 15 * 60
PRINTING_TIMEOUT_S = 10 * 60


class JobCanceledException(ValueError):
    pass
