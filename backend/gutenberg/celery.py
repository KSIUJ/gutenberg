import os

from celery import Celery, signals

from gutenberg.worker_capabilities import update_supported_document_formats

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gutenberg.settings.local_settings")

app = Celery('gutenberg')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.conf.beat_schedule = {
        'cleanup_print_jobs': {
            'task': 'printing.printing.cleanup_print_jobs',
            'schedule': 60. * 60 * 24,
        }
    }
    sender.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


@signals.worker_ready.connect
def on_connect(sender: Celery, **kwargs):
    # After this worker is ready, query all workers for their supported document formats
    # and update the cache.

    # We add this job to the queue to be able to accept it ourselves
    update_supported_document_formats.delay()
