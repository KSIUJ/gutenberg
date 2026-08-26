"""Work out the page limits that apply to a user."""

from dataclasses import dataclass
from typing import Optional

from common.models import User
from control.models import UserQuotaOverride


@dataclass(frozen=True)
class EffectiveQuota:
    """Page limits for a user. ``None`` means unlimited."""

    daily_limit: Optional[int]
    weekly_limit: Optional[int]
    monthly_limit: Optional[int]


def _inherited_limit(user: User, field_name: str) -> Optional[int]:
    """Get the highest limit from the user's groups for one period."""

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
    """Get the limits for a user.

    Group limits are benefits, so the highest value wins. A value set on the
    user always takes precedence. Zero means unlimited in both places.
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
