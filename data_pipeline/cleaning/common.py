"""
Common cleaning utilities for the data pipeline.
Reusable functions for text normalization, missing value handling,
numeric parsing, deduplication, and ID generation.
"""

import re
import html
import json
import hashlib
from typing import Any, Optional, Dict, List, Set, Tuple
from datetime import datetime
from copy import deepcopy


# Patterns for missing value detection
MISSING_VALUE_PATTERNS = {
    "", "N/A", "NA", "Not Available", "-", "null", "NULL", "Null", "none", "None", "NONE"
}

# Degree normalization mappings
DEGREE_NORMALIZATION = {
    r"^B\.?\s*Tech\.?$": "B.Tech",
    r"^B\.?\s*E\.?$": "B.E.",
    r"^Bachelor of Technology$": "B.Tech",
    r"^Bachelor of Engineering$": "B.E.",
    r"^M\.?\s*Tech\.?$": "M.Tech",
    r"^M\.?\s*E\.?$": "M.E.",
    r"^Master of Technology$": "M.Tech",
    r"^Master of Engineering$": "M.E.",
    r"^B\.?\s*Sc\.?$": "B.Sc",
    r"^Bachelor of Science$": "B.Sc",
    r"^M\.?\s*Sc\.?$": "M.Sc",
    r"^Master of Science$": "M.Sc",
    r"^B\.?\s*Com\.?$": "B.Com",
    r"^Bachelor of Commerce$": "B.Com",
    r"^M\.?\s*Com\.?$": "M.Com",
    r"^Master of Commerce$": "M.Com",
    r"^B\.?\s*A\.?$": "B.A.",
    r"^Bachelor of Arts$": "B.A.",
    r"^M\.?\s*A\.?$": "M.A.",
    r"^Master of Arts$": "M.A.",
    r"^B\.?\s*B\.?\s*A\.?$": "BBA",
    r"^Bachelor of Business Administration$": "BBA",
    r"^M\.?\s*B\.?\s*A\.?$": "MBA",
    r"^Master of Business Administration$": "MBA",
    r"^B\.?\s*Ed\.?$": "B.Ed",
    r"^Bachelor of Education$": "B.Ed",
    r"^M\.?\s*Ed\.?$": "M.Ed",
    r"^Master of Education$": "M.Ed",
    r"^LL\.?\s*B\.?$": "LLB",
    r"^Bachelor of Laws?$": "LLB",
    r"^LL\.?\s*M\.?$": "LLM",
    r"^Master of Laws?$": "LLM",
    r"^B\.?\s*A\.?\s*LL\.?\s*B\.?$": "BA LLB",
    r"^B\.?\s*A\.?\s*L\.?\s*L\.?\s*B\.?$": "BA LLB",
    r"^Ph\.?\s*D\.?$": "Ph.D",
    r"^Doctor of Philosophy$": "Ph.D",
    r"^M\.?\s*Phil\.?$": "M.Phil",
}

# Field of study normalization
FIELD_NORMALIZATION = {
    r"^ML$|^Machine Learning \(ML\)$|^Machine Learning$": "Machine Learning",
    r"^AI$|^Artificial Intelligence \(AI\)$|^Artificial Intelligence$": "Artificial Intelligence",
    r"^Python Programming$|^Python Language$|^Python$": "Python",
    r"^Data Science$|^Data Analytics$": "Data Science",
    r"^Computer Science$|^Computer Science Engineering$|^CSE$": "Computer Science",
    r"^Electronics and Communication$|^ECE$|^Electronics & Communication$": "Electronics and Communication Engineering",
    r"^Electrical and Electronics$|^EEE$|^Electrical & Electronics$": "Electrical and Electronics Engineering",
    r"^Mechanical Engineering$|^Mechanical$": "Mechanical Engineering",
    r"^Civil Engineering$|^Civil$": "Civil Engineering",
    r"^Information Technology$|^IT$": "Information Technology",
    r"^Cyber Security$|^Cybersecurity$": "Cyber Security",
    r"^Artificial Intelligence and Data Science$|^AI and DS$|^AI & DS$": "Artificial Intelligence and Data Science",
    r"^VLSI$|^VLSI Design$|^VLSI Design and Technology$": "VLSI Design and Technology",
}

# Location normalization for Indian cities/states
LOCATION_NORMALIZATION = {
    r"^Bangalore$|^Bengaluru$": "Bengaluru, Karnataka",
    r"^Bombay$|^Mumbai$": "Mumbai, Maharashtra",
    r"^Madras$|^Chennai$": "Chennai, Tamil Nadu",
    r"^Calcutta$|^Kolkata$": "Kolkata, West Bengal",
    r"^Delhi$|^New Delhi$": "New Delhi, Delhi",
    r"^Hyderabad$": "Hyderabad, Telangana",
    r"^Pune$": "Pune, Maharashtra",
    r"^Ahmedabad$": "Ahmedabad, Gujarat",
    r"^Surat$": "Surat, Gujarat",
    r"^Jaipur$": "Jaipur, Rajasthan",
    r"^Lucknow$": "Lucknow, Uttar Pradesh",
    r"^Kanpur$": "Kanpur, Uttar Pradesh",
    r"^Nagpur$": "Nagpur, Maharashtra",
    r"^Indore$": "Indore, Madhya Pradesh",
    r"^Thane$": "Thane, Maharashtra",
    r"^Bhopal$": "Bhopal, Madhya Pradesh",
    r"^Visakhapatnam$|^Vizag$": "Visakhapatnam, Andhra Pradesh",
    r"^Pimpri-Chinchwad$": "Pimpri-Chinchwad, Maharashtra",
    r"^Patna$": "Patna, Bihar",
    r"^Vadodara$": "Vadodara, Gujarat",
    r"^Ghaziabad$": "Ghaziabad, Uttar Pradesh",
    r"^Ludhiana$": "Ludhiana, Punjab",
    r"^Agra$": "Agra, Uttar Pradesh",
    r"^Nashik$": "Nashik, Maharashtra",
    r"^Faridabad$": "Faridabad, Haryana",
    r"^Meerut$": "Meerut, Uttar Pradesh",
    r"^Rajkot$": "Rajkot, Gujarat",
    r"^Kalyan-Dombivli$": "Kalyan-Dombivli, Maharashtra",
    r"^Vasai-Virar$": "Vasai-Virar, Maharashtra",
    r"^Varanasi$": "Varanasi, Uttar Pradesh",
    r"^Srinagar$": "Srinagar, Jammu and Kashmir",
    r"^Aurangabad$": "Aurangabad, Maharashtra",
    r"^Dhanbad$": "Dhanbad, Jharkhand",
    r"^Amritsar$": "Amritsar, Punjab",
    r"^Navi Mumbai$": "Navi Mumbai, Maharashtra",
    r"^Allahabad$|^Prayagraj$": "Prayagraj, Uttar Pradesh",
    r"^Howrah$": "Howrah, West Bengal",
    r"^Gwalior$": "Gwalior, Madhya Pradesh",
    r"^Jabalpur$": "Jabalpur, Madhya Pradesh",
    r"^Coimbatore$": "Coimbatore, Tamil Nadu",
    r"^Vijayawada$": "Vijayawada, Andhra Pradesh",
    r"^Jodhpur$": "Jodhpur, Rajasthan",
    r"^Madurai$": "Madurai, Tamil Nadu",
    r"^Raipur$": "Raipur, Chhattisgarh",
    r"^Kota$": "Kota, Rajasthan",
    r"^Guwahati$": "Guwahati, Assam",
    r"^Chandigarh$": "Chandigarh, Chandigarh",
    r"^Solapur$": "Solapur, Maharashtra",
    r"^Hubli-Dharwad$": "Hubli-Dharwad, Karnataka",
    r"^Mysore$|^Mysuru$": "Mysuru, Karnataka",
    r"^Tiruchirappalli$|^Trichy$": "Tiruchirappalli, Tamil Nadu",
    r"^Bareilly$": "Bareilly, Uttar Pradesh",
    r"^Moradabad$": "Moradabad, Uttar Pradesh",
    r"^Aligarh$": "Aligarh, Uttar Pradesh",
    r"^Tiruppur$": "Tiruppur, Tamil Nadu",
    r"^Gurgaon$|^Gurugram$": "Gurugram, Haryana",
    r"^Multiple locations$|^Multiple Locations$|^Multiple$": "Multiple Locations, India",
}


def clean_text(text: Optional[str]) -> Optional[str]:
    """
    Clean and normalize text:
    - Strip leading/trailing whitespace
    - Normalize repeated spaces, newlines, tabs
    - Decode HTML entities
    - Preserve proper names and capitalization
    """
    if text is None:
        return None
    
    # Convert to string if not already
    if not isinstance(text, str):
        text = str(text)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Replace various whitespace with single space
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    
    # Strip leading/trailing
    text = text.strip()
    
    # Return None if empty after cleaning
    return text if text else None


def normalize_missing(value: Any) -> Any:
    """
    Convert missing value indicators to None.
    Handles strings, lists, and dicts recursively.
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        stripped = value.strip()
        if stripped in MISSING_VALUE_PATTERNS:
            return None
        return stripped
    
    if isinstance(value, list):
        cleaned = [normalize_missing(v) for v in value]
        # Remove None values from lists
        return [v for v in cleaned if v is not None] or None
    
    if isinstance(value, dict):
        cleaned = {k: normalize_missing(v) for k, v in value.items()}
        # Remove keys with None values
        return {k: v for k, v in cleaned.items() if v is not None} or None
    
    return value


def normalize_degree(degree: Optional[str]) -> Optional[str]:
    """Normalize degree names to standard forms."""
    if not degree:
        return None
    
    cleaned = clean_text(degree)
    if not cleaned:
        return None
    
    for pattern, normalized in DEGREE_NORMALIZATION.items():
        if re.match(pattern, cleaned, re.IGNORECASE):
            return normalized
    
    return cleaned


def normalize_field(field: Optional[str]) -> Optional[str]:
    """Normalize field of study names."""
    if not field:
        return None
    
    cleaned = clean_text(field)
    if not cleaned:
        return None
    
    for pattern, normalized in FIELD_NORMALIZATION.items():
        if re.match(pattern, cleaned, re.IGNORECASE):
            return normalized
    
    return cleaned


def normalize_location(location: Optional[str]) -> Optional[str]:
    """Normalize location strings."""
    if not location:
        return None
    
    cleaned = clean_text(location)
    if not cleaned:
        return None
    
    # Try exact pattern matches first
    for pattern, normalized in LOCATION_NORMALIZATION.items():
        if re.match(f"^{pattern}$", cleaned, re.IGNORECASE):
            return normalized
    
    # If already contains comma (city, state), ensure proper formatting
    if ',' in cleaned:
        parts = [p.strip() for p in cleaned.split(',')]
        if len(parts) == 2:
            city, state = parts
            # Title case for city and state
            city = city.title()
            state = state.title()
            return f"{city}, {state}"
    
    return cleaned


def parse_indian_currency(value: Optional[str]) -> Optional[int]:
    """
    Parse Indian currency formats to integer INR.
    Handles: ₹2.5 Lakhs, Rs. 2,50,000, 250000, 2.5L, etc.
    Returns value in base INR (not lakhs/crores).
    """
    if not value:
        return None
    
    cleaned = clean_text(value)
    if not cleaned:
        return None
    
    # Remove currency symbols and commas (but NOT decimal points)
    cleaned = re.sub(r'(?:₹|Rs\.?)', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace(',', '').strip()
    
    # Handle Lakh/Lakhs (including abbreviated L)
    lakh_match = re.match(r'^([\d.]+)\s*(?:[Ll]akh|[Ll](?![a-zA-Z]))', cleaned)
    if lakh_match:
        return int(float(lakh_match.group(1)) * 100000)
    
    # Handle Crore/Crores (including abbreviated Cr)
    crore_match = re.match(r'^([\d.]+)\s*(?:[Cc]rore|[Cc]r(?![a-zA-Z]))', cleaned)
    if crore_match:
        return int(float(crore_match.group(1)) * 10000000)
    
    # Handle K/Thousand - use word boundary to avoid matching partial numbers
    k_match = re.match(r'^([\d.]+)\s*[Kk](?![a-zA-Z])', cleaned)
    if k_match:
        return int(float(k_match.group(1)) * 1000)
    
    # Plain number
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def parse_duration_years(value: Optional[str]) -> Optional[float]:
    """
    Parse duration strings to years (float).
    Handles: "4 Years", "2 Years", "6 Months", "1 Year 6 Months", etc.
    """
    if not value:
        return None
    
    cleaned = clean_text(value)
    if not cleaned:
        return None
    
    total_months = 0
    
    # Years
    year_match = re.search(r'(\d+(?:\.\d+)?)\s*[Yy]ear', cleaned)
    if year_match:
        total_months += float(year_match.group(1)) * 12
    
    # Months
    month_match = re.search(r'(\d+(?:\.\d+)?)\s*[Mm]onth', cleaned)
    if month_match:
        total_months += float(month_match.group(1))
    
    # Weeks (approximate)
    week_match = re.search(r'(\d+(?:\.\d+)?)\s*[Ww]eek', cleaned)
    if week_match:
        total_months += float(week_match.group(1)) / 4.33
    
    if total_months > 0:
        return round(total_months / 12, 2)
    
    # Try plain number as years
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_rating(value: Optional[str]) -> Optional[float]:
    """Parse rating values (0-5 or 0-10 scale)."""
    if not value:
        return None
    
    cleaned = clean_text(value)
    if not cleaned:
        return None
    
    # Extract first number
    match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
    if match:
        rating = float(match.group(1))
        # Assume 0-10 scale if > 5, normalize to 0-5
        if rating > 5:
            rating = rating / 2
        return round(rating, 1)
    
    return None


def parse_percentage(value: Optional[str]) -> Optional[float]:
    """Parse percentage strings to float (0-100)."""
    if not value:
        return None
    
    cleaned = clean_text(value)
    if not cleaned:
        return None
    
    # Remove % sign
    cleaned = cleaned.replace('%', '').strip()
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_ranking(value: Optional[str]) -> Optional[int]:
    """Parse ranking values to integer."""
    if not value:
        return None
    
    cleaned = clean_text(value)
    if not cleaned:
        return None
    
    # Extract number from strings like "#1", "Rank 5", "1st", etc.
    match = re.search(r'(\d+)', cleaned)
    if match:
        return int(match.group(1))
    
    return None


def generate_record_id(record: Dict, key_fields: List[str]) -> str:
    """
    Generate a deterministic ID from key fields.
    Uses SHA256 hash of concatenated key field values.
    """
    parts = []
    for field in key_fields:
        value = record.get(field)
        if value is not None:
            if isinstance(value, (dict, list)):
                parts.append(json.dumps(value, sort_keys=True))
            else:
                parts.append(str(value))
    
    combined = "|".join(parts)
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()[:16]


def deduplicate_records(
    records: List[Dict],
    id_field: str = "source_url",
    key_fields: Optional[List[str]] = None
) -> Tuple[List[Dict], List[Dict], List[Tuple[Dict, Dict]]]:
    """
    Remove exact duplicates and identify possible duplicates.
    
    Returns:
        - unique_records: List of deduplicated records
        - exact_duplicates: List of removed duplicate records
        - possible_duplicates: List of (record1, record2) pairs that might be duplicates
    """
    seen_ids: Set[str] = set()
    seen_keys: Dict[str, Dict] = {}
    unique_records = []
    exact_duplicates = []
    possible_duplicates = []
    
    for record in records:
        # Check exact duplicate by ID field
        record_id = record.get(id_field)
        if record_id and record_id in seen_ids:
            exact_duplicates.append(record)
            continue
        
        # Check exact duplicate by key fields
        if key_fields:
            key = generate_record_id(record, key_fields)
            if key in seen_keys:
                exact_duplicates.append(record)
                continue
            seen_keys[key] = record
        
        if record_id:
            seen_ids.add(record_id)
        
        unique_records.append(record)
    
    # Find possible duplicates (similar names) - only for records with name/title fields
    name_fields = ["name", "course_name", "Standard_College_Name", "college_name", "institute"]
    for i, rec1 in enumerate(unique_records):
        name1 = None
        for f in name_fields:
            if rec1.get(f):
                name1 = clean_text(rec1.get(f))
                break
        
        if not name1:
            continue
        
        for j, rec2 in enumerate(unique_records[i+1:], i+1):
            name2 = None
            for f in name_fields:
                if rec2.get(f):
                    name2 = clean_text(rec2.get(f))
                    break
            
            if not name2:
                continue
            
            # Simple similarity check
            if name1.lower() == name2.lower():
                possible_duplicates.append((rec1, rec2))
            elif len(name1) > 10 and len(name2) > 10:
                # Check if one contains the other (for partial matches)
                if name1.lower() in name2.lower() or name2.lower() in name1.lower():
                    possible_duplicates.append((rec1, rec2))
    
    return unique_records, exact_duplicates, possible_duplicates


def add_metadata(record: Dict, source: str, source_url: Optional[str], 
                 scraped_at: Optional[str], data_type: str) -> Dict:
    """Add standard metadata fields to a record."""
    record = deepcopy(record)
    # Update existing metadata or create new
    if "metadata" in record:
        record["metadata"].update({
            "source": source,
            "source_url": source_url,
            "scraped_at": scraped_at,
            "data_type": data_type,
            "cleaned_at": datetime.utcnow().isoformat() + "Z"
        })
    else:
        record["metadata"] = {
            "source": source,
            "source_url": source_url,
            "scraped_at": scraped_at,
            "data_type": data_type,
            "cleaned_at": datetime.utcnow().isoformat() + "Z"
        }
    return record


def save_json(data: Any, filepath: str) -> None:
    """Save data as JSON with UTF-8 encoding."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> Any:
    """Load JSON from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


class CleaningReport:
    """Track cleaning statistics for reporting."""
    
    def __init__(self, dataset_name: str):
        self.dataset_name = dataset_name
        self.input_records = 0
        self.valid_records = 0
        self.invalid_records = 0
        self.exact_duplicates_removed = 0
        self.possible_duplicates = 0
        self.missing_important_fields: Dict[str, int] = {}
        self.normalized_fields: Dict[str, int] = {}
        self.errors: List[Dict] = []
    
    def to_dict(self) -> Dict:
        return {
            "dataset_name": self.dataset_name,
            "input_records": self.input_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "exact_duplicates_removed": self.exact_duplicates_removed,
            "possible_duplicates": self.possible_duplicates,
            "missing_important_fields": self.missing_important_fields,
            "normalized_fields": self.normalized_fields,
            "errors": self.errors
        }


def clean_html_artifacts(text: Optional[str]) -> Optional[str]:
    """Remove common HTML artifacts from scraped text."""
    if not text:
        return None
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Common HTML entities
    text = html.unescape(text)
    
    # Remove zero-width spaces and other invisible chars
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    
    # Fix common encoding issues
    text = text.replace('', "'").replace('', "'")
    text = text.replace('', '"').replace('', '"')
    text = text.replace('', '—').replace('', '–')
    text = text.replace('', '•')
    
    return clean_text(text)


def extract_emails(text: Optional[str]) -> List[str]:
    """Extract email addresses from text."""
    if not text:
        return []
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)


def extract_phone_numbers(text: Optional[str]) -> List[str]:
    """Extract Indian phone numbers from text."""
    if not text:
        return []
    # Indian mobile: +91-XXXXXXXXXX, 91XXXXXXXXXX, 0XXXXXXXXXX, XXXXXXXXXX
    # Landline: STD code + number
    pattern = r'(?:\+91[- ]?)?(?:91[- ]?)?(?:[6-9]\d{9}|0\d{10,11})'
    return re.findall(pattern, text)