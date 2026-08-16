"""Resolution of per-user print quota configuration.

Quota accounting and enforcement deliberately live elsewhere.  This module
only turns group memberships and an optional user override into the limits
that should be applied to a user.
"""

from dataclasses import dataclass
from typing import Optional

from common.models import User
from control.models import UserQuotaOverride


@dataclass(frozen=True)
class EffectiveQuota:
    """Limits in printed impressions; ``None`` means unlimited."""

    daily_limit: Optional[int]
    weekly_limit: Optional[int]
    monthly_limit: Optional[int]


def _inherited_limit(user: User, field_name: str) -> Optional[int]:
    """Return the most generous explicit group value for one period."""

    values = list(
        user.groups.filter(groupquota__isnull=False)
        .exclude(**{'groupquota__{}__isnull'.format(field_name): True})
        .values_list('groupquota__{}'.format(field_name), flat=True)
    )
    if not values:
        return None
    if 0 in values:
        return None
    return max(values)


def effective_quota_for_user(user: User) -> EffectiveQuota:
    """Resolve effective limits for ``user``.

    Each group quota is an entitlement: the highest non-blank value wins.
    An explicit zero makes the corresponding period unlimited.  A user-level
    non-blank value replaces the inherited value for that period.
    """

    try:
        override = user.userquotaoverride
    except UserQuotaOverride.DoesNotExist:
        override = None

    def resolve(field_name: str) -> Optional[int]:
        if override is not None:
            value = getattr(override, field_name)
            if value is not None:
                return None if value == 0 else value
        return _inherited_limit(user, field_name)

    return EffectiveQuota(
        daily_limit=resolve('daily_limit'),
        weekly_limit=resolve('weekly_limit'),
        monthly_limit=resolve('monthly_limit'),
    )
