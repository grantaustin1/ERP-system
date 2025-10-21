"""
Normalization utilities for duplicate detection
Includes email, phone, and name normalization
"""
import re
from typing import Optional

# Nickname to canonical name mapping
NICKNAME_MAP = {
    # Common nicknames
    "bob": "robert",
    "rob": "robert",
    "robbie": "robert",
    "bobby": "robert",
    "bill": "william",
    "billy": "william",
    "will": "william",
    "willie": "william",
    "mike": "michael",
    "mikey": "michael",
    "mick": "michael",
    "mickey": "michael",
    "jim": "james",
    "jimmy": "james",
    "jamie": "james",
    "dick": "richard",
    "rick": "richard",
    "ricky": "richard",
    "rich": "richard",
    "tom": "thomas",
    "tommy": "thomas",
    "dave": "david",
    "davey": "david",
    "dan": "daniel",
    "danny": "daniel",
    "joe": "joseph",
    "joey": "joseph",
    "tony": "anthony",
    "chris": "christopher",
    "matt": "matthew",
    "steve": "steven",
    "steve": "stephen",
    "andy": "andrew",
    "alex": "alexander",
    "ben": "benjamin",
    "sam": "samuel",
    "jack": "john",
    "jake": "jacob",
    "josh": "joshua",
    "nick": "nicholas",
    "pat": "patrick",
    "pete": "peter",
    "phil": "philip",
    "drew": "andrew",
    "fred": "frederick",
    "gene": "eugene",
    "greg": "gregory",
    "jeff": "jeffrey",
    "ken": "kenneth",
    "larry": "lawrence",
    "len": "leonard",
    "ron": "ronald",
    "ted": "theodore",
    "tim": "timothy",
    # Female names
    "liz": "elizabeth",
    "beth": "elizabeth",
    "betty": "elizabeth",
    "lizzy": "elizabeth",
    "sue": "susan",
    "susie": "susan",
    "suzy": "susan",
    "jen": "jennifer",
    "jenny": "jennifer",
    "jess": "jessica",
    "jessie": "jessica",
    "kate": "katherine",
    "katie": "katherine",
    "kathy": "katherine",
    "kate": "catherine",
    "cathy": "catherine",
    "maggie": "margaret",
    "meg": "margaret",
    "peggy": "margaret",
    "becky": "rebecca",
    "becca": "rebecca",
    "deb": "deborah",
    "debbie": "deborah",
    "cindy": "cynthia",
    "sandy": "sandra",
    "mandy": "amanda",
    "amy": "amelia",
    "annie": "anna",
    "nan": "nancy",
    "barb": "barbara",
    "chris": "christine",
    "christie": "christine",
    "steph": "stephanie",
    "val": "valerie",
}


def normalize_email(email: str) -> str:
    """
    Normalize email for duplicate detection
    - Lowercase
    - Gmail-style: remove dots and plus addressing
    - Extract base username
    
    Examples:
        john.doe+gym@gmail.com -> johndoe@gmail.com
        John.Doe@Gmail.COM -> johndoe@gmail.com
    """
    if not email:
        return ""
    
    email = email.lower().strip()
    
    # Split into username and domain
    if "@" not in email:
        return email
    
    username, domain = email.split("@", 1)
    
    # Gmail-specific normalization
    if domain in ["gmail.com", "googlemail.com"]:
        # Remove dots (Gmail ignores them)
        username = username.replace(".", "")
        
        # Remove plus addressing (everything after +)
        if "+" in username:
            username = username.split("+")[0]
        
        # Normalize domain to gmail.com
        domain = "gmail.com"
    
    return f"{username}@{domain}"


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number for duplicate detection
    - Extract only digits
    - Remove country code if present (for South African numbers)
    - E.164-lite format
    
    Examples:
        +27 81 234 5678 -> 0812345678
        0812345678 -> 0812345678
        (081) 234-5678 -> 0812345678
    """
    if not phone:
        return ""
    
    # Extract only digits
    digits = re.sub(r'\D', '', phone)
    
    if not digits:
        return ""
    
    # Handle South African numbers (+27)
    if digits.startswith("27") and len(digits) == 11:
        # Convert +27812345678 to 0812345678
        digits = "0" + digits[2:]
    elif digits.startswith("0") and len(digits) == 10:
        # Already in correct format
        pass
    elif len(digits) == 9:
        # Missing leading 0, add it
        digits = "0" + digits
    
    return digits


def normalize_name(name: str) -> str:
    """
    Normalize name for duplicate detection
    - Lowercase
    - Remove extra whitespace
    - Canonicalize nicknames to full names
    
    Examples:
        Bob -> robert
        Mike Smith -> michael smith
        Billy-Bob -> william bob
    """
    if not name:
        return ""
    
    name = name.lower().strip()
    
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name)
    
    # Split into parts (handle hyphenated names)
    parts = re.split(r'[\s\-]+', name)
    
    # Canonicalize each part if it's a known nickname
    normalized_parts = []
    for part in parts:
        canonical = NICKNAME_MAP.get(part, part)
        normalized_parts.append(canonical)
    
    return ' '.join(normalized_parts)


def normalize_full_name(first_name: str, last_name: str) -> tuple[str, str]:
    """
    Normalize both first and last name
    Returns tuple of (normalized_first, normalized_last)
    """
    return (
        normalize_name(first_name),
        normalize_name(last_name)
    )


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Calculate similarity between two names
    Simple implementation using character overlap
    Returns value between 0.0 and 1.0
    """
    if not name1 or not name2:
        return 0.0
    
    name1 = normalize_name(name1)
    name2 = normalize_name(name2)
    
    if name1 == name2:
        return 1.0
    
    # Simple character-based similarity
    set1 = set(name1)
    set2 = set(name2)
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0.0
    
    return intersection / union
