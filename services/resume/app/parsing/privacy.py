import re
from copy import deepcopy


PHONE_RE = re.compile(r"(?<!\d)(1\d{10})(?!\d)")
EMAIL_RE = re.compile(r"([\w.+-]+)@([\w.-]+)")


def mask_phone(value: str | None) -> str | None:
    if not value:
        return value
    return PHONE_RE.sub(lambda match: f"{match.group(1)[:3]}****{match.group(1)[-4:]}", value)


def mask_email(value: str | None) -> str | None:
    if not value:
        return value

    def replace(match: re.Match[str]) -> str:
        local_part = match.group(1)
        domain = match.group(2)
        if len(local_part) <= 2:
            masked_local = local_part[:1] + "*"
        else:
            masked_local = f"{local_part[:2]}***{local_part[-1:]}"
        return f"{masked_local}@{domain}"

    return EMAIL_RE.sub(replace, value)


def redact_profile(profile: dict) -> dict:
    redacted = deepcopy(profile)
    redacted["phone"] = mask_phone(redacted.get("phone"))
    redacted["email"] = mask_email(redacted.get("email"))
    return redacted
