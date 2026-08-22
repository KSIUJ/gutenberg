"""Keep track of pages held for, and charged to, print jobs."""

from dataclasses import dataclass
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from common.models import User
from control.models import (
    GutenbergJob,
    QuotaPeriod,
    QuotaReservation,
    QuotaReservationState,
    QuotaUsage,
)
from control.quotas import effective_quota_for_user


@dataclass(frozen=True)
class QuotaExceeded(Exception):
    period: str
    limit: int
    requested: int
    remaining: int

    def __str__(self):
        return (
            'Print quota exceeded for the {} period: {} pages requested, '
            '{} remaining out of {}.'.format(
                self.period,
                self.requested,
                self.remaining,
                self.limit,
            )
        )


@dataclass(frozen=True)
class QuotaPeriodSummary:
    period: str
    limit_pages: int
    used_pages: int
    remaining_pages: int


def _period_start(period: str, today: date) -> date:
    if period == QuotaPeriod.DAILY:
        return today
    if period == QuotaPeriod.WEEKLY:
        return today - timedelta(days=today.weekday())
    if period == QuotaPeriod.MONTHLY:
        return today.replace(day=1)
    raise ValueError('Unknown quota period: {}'.format(period))


def _limited_periods(user: User):
    quota = effective_quota_for_user(user)
    return (
        (QuotaPeriod.DAILY, quota.daily_limit),
        (QuotaPeriod.WEEKLY, quota.weekly_limit),
        (QuotaPeriod.MONTHLY, quota.monthly_limit),
    )


def quota_summary_for_user(user: User) -> list[QuotaPeriodSummary]:
    """Return what the user has used and has left in each limited period."""

    today = timezone.localdate()
    periods = [
        (period, limit, _period_start(period, today))
        for period, limit in _limited_periods(user)
        if limit is not None
    ]
    usages = {
        (usage.period, usage.period_start): usage
        for usage in QuotaUsage.objects.filter(
            user=user,
            period__in=[period for period, _, _ in periods],
            period_start__in=[period_start for _, _, period_start in periods],
        )
    }
    summaries = []
    for period, limit, period_start in periods:
        usage = usages.get((period, period_start))
        used_pages = 0 if usage is None else (
            usage.reserved_impressions + usage.charged_impressions
        )
        summaries.append(QuotaPeriodSummary(
            period=period,
            limit_pages=limit,
            used_pages=used_pages,
            remaining_pages=max(limit - used_pages, 0),
        ))
    return summaries


def reserve_quota_for_job(job: GutenbergJob) -> bool:
    """Hold enough pages for a job, or raise ``QuotaExceeded``.

    Locking the user stops two jobs from both using the same remaining pages.
    It also makes retrying a task safe.
    """

    if job.pages is None:
        raise ValueError('Cannot reserve quota before final page count is known')

    with transaction.atomic():
        job = GutenbergJob.objects.select_for_update(of=('self',)).select_related('owner').get(pk=job.pk)
        if job.owner_id is None:
            return False

        user = User.objects.select_for_update().get(pk=job.owner_id)
        if QuotaReservation.objects.filter(
            job=job,
            state__in=(QuotaReservationState.RESERVED, QuotaReservationState.CHARGED),
        ).exists():
            return True

        today = timezone.localdate()
        reservations = []
        for period, limit in _limited_periods(user):
            if limit is None:
                continue
            usage, _ = QuotaUsage.objects.select_for_update().get_or_create(
                user=user,
                period=period,
                period_start=_period_start(period, today),
            )
            used = usage.reserved_impressions + usage.charged_impressions
            remaining = max(limit - used, 0)
            if job.pages > remaining:
                raise QuotaExceeded(period, limit, job.pages, remaining)
            reservations.append((usage, job.pages))

        for usage, pages in reservations:
            usage.reserved_impressions += pages
            usage.save(update_fields=['reserved_impressions'])
            QuotaReservation.objects.create(
                job=job,
                usage=usage,
                impressions=pages,
            )
        return bool(reservations)


def _update_reservation_state(job: GutenbergJob, from_state: str, to_state: str) -> bool:
    with transaction.atomic():
        reservations = list(
            QuotaReservation.objects.select_for_update()
            .filter(job=job, state=from_state)
            .order_by('usage_id')
        )
        if not reservations:
            return False

        usage_by_id = QuotaUsage.objects.select_for_update().in_bulk(
            [reservation.usage_id for reservation in reservations],
        )
        for reservation in reservations:
            usage = usage_by_id[reservation.usage_id]
            if from_state == QuotaReservationState.RESERVED:
                usage.reserved_impressions -= reservation.impressions
            if to_state == QuotaReservationState.CHARGED:
                usage.charged_impressions += reservation.impressions
            usage.save(update_fields=['reserved_impressions', 'charged_impressions'])
            reservation.state = to_state
            reservation.save(update_fields=['state', 'updated_at'])
        return True


def charge_quota_for_job(job: GutenbergJob) -> bool:
    """Charge a job after CUPS has accepted it."""

    return _update_reservation_state(
        job,
        QuotaReservationState.RESERVED,
        QuotaReservationState.CHARGED,
    )


def release_quota_for_job(job: GutenbergJob) -> bool:
    """Give held pages back when the job never reached CUPS."""

    return _update_reservation_state(
        job,
        QuotaReservationState.RESERVED,
        QuotaReservationState.RELEASED,
    )
