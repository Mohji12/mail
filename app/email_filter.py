"""Filter invalid, duplicate, suspicious, and near-duplicate emails before sending."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

EMAIL_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$", re.IGNORECASE)

# Leading/trailing junk often typed by mistake (digits, dots, underscores, hyphens)
AFFIX_RE = re.compile(r"^[\d._\-]+|[\d._\-]+$")


@dataclass
class FilterResult:
    valid: list[str] = field(default_factory=list)
    skipped_invalid: list[str] = field(default_factory=list)
    skipped_duplicate: list[str] = field(default_factory=list)
    skipped_similar: list[dict] = field(default_factory=list)
    skipped_suspicious: list[dict] = field(default_factory=list)

    @property
    def skipped_count(self) -> int:
        return (
            len(self.skipped_invalid)
            + len(self.skipped_duplicate)
            + len(self.skipped_similar)
            + len(self.skipped_suspicious)
        )


def normalize_email(raw: str) -> str:
    return (raw or "").strip().lower()


def is_valid_format(email: str) -> bool:
    if not email or "@" not in email:
        return False
    if email.count("@") != 1:
        return False
    local, domain = email.split("@", 1)
    if not local or not domain or "." not in domain:
        return False
    return bool(EMAIL_RE.match(email))


def _split(email: str) -> tuple[str, str]:
    local, domain = email.split("@", 1)
    return local, domain


def is_suspicious_local(local: str) -> tuple[bool, str]:
    """
    Detect likely fake/tampered addresses even when no clean duplicate is in the list.
    Examples: 23mohangola89@gmail.com, 1mohangola47@gmail.com
    """
    if not local:
        return True, "empty_local"

    # Digits glued to start: 23mohangola89, 1mohangola47
    if re.match(r"^\d{1,6}[a-z]", local):
        return True, "leading_digit_prefix"

    # Digits + separator + name: 23_mohangola, 1.mohangola
    if re.match(r"^\d{1,6}[\._\-]+[a-z]", local):
        return True, "leading_digit_prefix"

    # Short digit junk prefix before a longer name-like part
    m = re.match(r"^([\d._\-]{1,6})([a-z][a-z0-9._\-]{3,})$", local)
    if m:
        prefix, rest = m.group(1), m.group(2)
        if prefix and re.search(r"[a-z]{4,}", rest):
            return True, "leading_junk_prefix"

    return False, ""


def _similarity_core(local: str) -> str:
    """Strip common leading/trailing digit/punctuation affixes for comparison."""
    core = AFFIX_RE.sub("", local)
    return core or local


def are_similar_locals(a: str, b: str) -> bool:
    """True when one local-part is the other with only a short prefix/suffix."""
    if a == b:
        return True

    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)

    # Exact containment at start or end: 1mohangola47 vs mohangola47
    if longer.startswith(shorter) or longer.endswith(shorter):
        extra = longer[len(shorter) :] if longer.startswith(shorter) else longer[: -len(shorter)]
        if extra and re.fullmatch(r"[\d._\-]{1,6}", extra):
            return True
        if not extra:
            return True

    # Substring with only digit/punct affixes around it
    idx = longer.find(shorter)
    if idx >= 0:
        prefix = longer[:idx]
        suffix = longer[idx + len(shorter) :]
        if (
            (not prefix or re.fullmatch(r"[\d._\-]{1,6}", prefix))
            and (not suffix or re.fullmatch(r"[\d._\-]{1,6}", suffix))
            and (prefix or suffix)
        ):
            return True

    # Same core after stripping affixes
    if _similarity_core(a) == _similarity_core(b) and _similarity_core(a):
        return True

    return False


def _prefer_email(a: str, b: str) -> str:
    """Prefer the cleaner address when two are similar."""
    a_local, _ = _split(a)
    b_local, _ = _split(b)

    def score(local: str) -> tuple:
        leading_digits = 1 if re.match(r"^\d", local) else 0
        trailing_digits = 1 if re.search(r"\d$", local) else 0
        has_affix = 1 if AFFIX_RE.search(local) else 0
        return (leading_digits, has_affix, len(local), trailing_digits)

    return a if score(a_local) <= score(b_local) else b


def filter_emails(emails: list[str], *, filter_similar: bool = True) -> FilterResult:
    """
    Keep only valid unique emails. When filter_similar is True:
    - drop suspicious fake patterns (e.g. 23mohangola89@gmail.com)
    - drop near-duplicates like 1mohangola47@gmail.com when mohangola47@gmail.com exists
    """
    result = FilterResult()
    seen_exact: set[str] = set()
    kept: list[str] = []

    for raw in emails:
        email = normalize_email(str(raw))
        if not email:
            continue

        if not is_valid_format(email):
            result.skipped_invalid.append(email)
            continue

        local, domain = _split(email)

        if filter_similar:
            suspicious, reason = is_suspicious_local(local)
            if suspicious:
                result.skipped_suspicious.append({"email": email, "reason": reason})
                continue

        if email in seen_exact:
            result.skipped_duplicate.append(email)
            continue
        seen_exact.add(email)

        if not filter_similar:
            kept.append(email)
            continue

        conflict_idx = None
        for i, existing in enumerate(kept):
            ex_local, ex_domain = _split(existing)
            if ex_domain != domain:
                continue
            if are_similar_locals(local, ex_local):
                conflict_idx = i
                break

        if conflict_idx is None:
            kept.append(email)
            continue

        existing = kept[conflict_idx]
        preferred = _prefer_email(existing, email)
        if preferred == existing:
            result.skipped_similar.append(
                {"email": email, "kept": existing, "reason": "similar_prefix_or_suffix"}
            )
        else:
            result.skipped_similar.append(
                {"email": existing, "kept": email, "reason": "similar_prefix_or_suffix"}
            )
            kept[conflict_idx] = email

    result.valid = kept
    return result
