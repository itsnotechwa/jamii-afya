from apps.contributions.models import Contribution


def check_eligibility(user, group) -> tuple[bool, str]:
    """
    Rules-based eligibility check before an emergency request is accepted.

    Returns (True, '') if eligible, or (False, reason) if not.
    """
    confirmed_count = Contribution.objects.filter(
        member=user,
        group=group,
        status='confirmed',
    ).count()

    if confirmed_count < group.min_contributions_to_qualify:
        return False, (
            f"You need at least {group.min_contributions_to_qualify} confirmed contributions "
            f"to qualify. You currently have {confirmed_count}."
        )

    # Check for an open (pending/approved) request in the same group
    from apps.emergencies.models import EmergencyRequest
    open_request = EmergencyRequest.objects.filter(
        claimant=user,
        group=group,
        status__in=['pending', 'approved'],
    ).exists()

    if open_request:
        return False, "You already have an open emergency request in this group."

    return True, ''
