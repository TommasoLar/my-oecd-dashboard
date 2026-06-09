import re

REGIONAL_PATTERNS = [
    r'regional', r'unspecified', r'bilateral', r'multilateral', r'\bglobal\b',
    r'states ex\.', r'far east asia', r'south & central', r'sub-saharan',
    r'middle east', r'north & central', r'southern africa', r'west africa',
    r'east africa', r'north africa', r'caribbean', r'oceania', r'central asia',
    r'central america', r'developing countr', r'south of sahara',
    r'middle africa', r'north of sahara', r'micronesia',
    r'europe, regional',
]

REGIONAL_RE = re.compile("|".join(REGIONAL_PATTERNS), re.IGNORECASE)


def is_multi_country(name: str) -> bool:
    return ";" in str(name or "")


def is_regional(name: str) -> bool:
    n = str(name or "")
    return is_multi_country(n) or bool(REGIONAL_RE.search(n))


def is_valid_country_point(name: str) -> bool:
    """ONLY for mapping layers"""
    return not is_regional(name)