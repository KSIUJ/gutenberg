from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
import os

def upload_to_uploads(instance, filename):
    return os.path.join('uploads', str(instance.user_id or 'anon'), filename)

class PrintJob(models.Model):
    PREVIEW_PENDING = 'pending'
    PREVIEW_PROCESSING = 'processing'
    PREVIEW_READY = 'ready'
    PREVIEW_FAILED = 'failed'
    PREVIEW_CHOICES = [
        (PREVIEW_PENDING, 'pending'),
        (PREVIEW_PROCESSING, 'processing'),
        (PREVIEW_READY, 'ready'),
        (PREVIEW_FAILED, 'failed'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_file = models.FileField(upload_to=upload_to_uploads)
    created_at = models.DateTimeField(auto_now_add=True)
    preview_status = models.CharField(max_length=20, choices=PREVIEW_CHOICES, default=PREVIEW_PENDING)
    preview_pages = models.IntegerField(default=0)
    preview_meta = models.JSONField(default=dict, blank=True)  # {'pages': ['page-1.png', ...]}
    settings = models.JSONField(default=dict, blank=True)  # duplex, copies, page_range, color, etc.
    printed_at = models.DateTimeField(null=True, blank=True)
    ipp_job_id = models.CharField(max_length=128, blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def preview_dir(self):
        # filesystem dir inside MEDIA_ROOT where preview files are stored
        return os.path.join('previews', str(self.id))

    def preview_urls(self, request):
        # build list of absolute URLs for preview pages
        pages = self.preview_meta.get('pages', [])
        urls = []
        for p in pages:
            urls.append(request.build_absolute_uri(settings.MEDIA_URL + f"{self.preview_dir()}/{p}"))
        return urls
