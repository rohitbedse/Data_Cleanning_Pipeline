"""
College data cleaner for career360.json.
Transforms raw Careers360 college data into validated, normalized records.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from copy import deepcopy

from .common import (
    clean_text, normalize_missing, normalize_degree, normalize_field,
    normalize_location, parse_indian_currency, parse_duration_years,
    parse_ranking, generate_record_id, deduplicate_records,
    add_metadata, CleaningReport, clean_html_artifacts
)
from .validators import College, CollegeCourse, CollegeDegreeLevel, validate_records


def clean_course(course: Dict) -> CollegeCourse:
    """Clean and normalize a single course record."""
    cleaned = {}
    
    # Course name - normalize degree
    course_name = normalize_missing(course.get("Course_Name"))
    if course_name:
        cleaned["course_name"] = normalize_degree(course_name)
    
    # Domain - normalize field
    domain = normalize_missing(course.get("Domain"))
    if domain:
        cleaned["domain"] = normalize_field(domain)
    
    # Text fields
    for field in ["Eligibility", "Course_Details", "Research_Areas", 
                  "Course_Intake", "Admission_Process"]:
        value = normalize_missing(course.get(field))
        if value:
            cleaned[field.lower()] = clean_html_artifacts(value)
    
    # Duration
    duration = normalize_missing(course.get("Course_Duration"))
    if duration:
        cleaned["course_duration"] = duration
        cleaned["course_duration_years"] = parse_duration_years(duration)
    
    # Fees
    fees = normalize_missing(course.get("Fees"))
    if fees:
        cleaned["fees"] = fees
        cleaned["fees_inr"] = parse_indian_currency(fees)
    
    # Entrance exams
    exams = course.get("Entrance_Exams_Accepted", [])
    if exams:
        cleaned["entrance_exams_accepted"] = [
            clean_text(e) for e in exams if clean_text(e)
        ]
    
    return CollegeCourse(**cleaned)


def clean_degree_level(degree_level: Dict) -> CollegeDegreeLevel:
    """Clean all courses within a degree level."""
    result = {}
    
    for level_key in ["UG", "PG", "PhD"]:
        courses = degree_level.get(level_key, [])
        if courses:
            cleaned_courses = []
            for course in courses:
                try:
                    cleaned_courses.append(clean_course(course))
                except Exception:
                    # Skip invalid courses but continue
                    pass
            if cleaned_courses:
                result[level_key.lower()] = cleaned_courses
    
    return CollegeDegreeLevel(**result)


def clean_ranking(ranking: Dict) -> Dict:
    """Clean ranking information."""
    cleaned = {}
    for field in ["NIRF_Ranking", "QS_World_Ranking", "Times_Higher_Education_Ranking"]:
        value = normalize_missing(ranking.get(field))
        if value:
            parsed = parse_ranking(value)
            if parsed:
                cleaned[field.lower()] = parsed
    return cleaned


def parse_location(location: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse location string into (full_location, city, state).
    Returns normalized values.
    """
    if not location:
        return None, None, None
    
    normalized = normalize_location(location)
    if not normalized:
        return None, None, None
    
    city = None
    state = None
    if ',' in normalized:
        parts = [p.strip() for p in normalized.split(',')]
        if len(parts) >= 2:
            city = parts[0]
            state = parts[1]
    
    return normalized, city, state


def clean_college_record(raw: Dict, report: CleaningReport) -> Optional[Dict]:
    """Clean a single college record from career360.json."""
    # Normalize missing values first
    raw = normalize_missing(raw)
    
    # Track missing important fields
    important_fields = [
        "Standard_College_Name", "Standard_University_Name", "Location",
        "College_Category", "URL"
    ]
    for field in important_fields:
        if not raw.get(field):
            report.missing_important_fields[field] = report.missing_important_fields.get(field, 0) + 1
    
    # College name (required)
    college_name = clean_text(raw.get("Standard_College_Name"))
    if not college_name:
        return None
    
    # University name
    university_name = clean_text(raw.get("Standard_University_Name"))
    
    # Category
    college_category = clean_text(raw.get("College_Category"))
    
    # Description
    description = clean_html_artifacts(raw.get("Description"))
    
    # Location
    location_raw = clean_text(raw.get("Location"))
    location, city, state = parse_location(location_raw)
    
    # Study destination
    study_destination = clean_text(raw.get("Study_Destination"))
    
    # Degree level with courses
    degree_level_raw = raw.get("Degree_Level", {})
    degree_level = clean_degree_level(degree_level_raw)
    
    # Ranking
    ranking_raw = raw.get("Ranking_Category", {})
    ranking_dict = clean_ranking(ranking_raw)
    ranking_obj = type('obj', (object,), ranking_dict)()  # Simple object for validation
    
    # Metadata
    source = clean_text(raw.get("Source")) or "Careers360"
    source_url = clean_text(raw.get("URL"))
    scraped_at = None  # Not available in career360.json
    
    metadata = {
        "source": source,
        "source_url": source_url,
        "scraped_at": scraped_at,
        "data_type": "college",
        "cleaned_at": None  # Will be set by add_metadata
    }
    
    # Build cleaned record
    cleaned = {
        "college_name": college_name,
        "university_name": university_name,
        "college_category": college_category,
        "description": description,
        "location": location,
        "city": city,
        "state": state,
        "study_destination": study_destination,
        "degree_level": degree_level.model_dump(exclude_none=True),
        "ranking": ranking_dict,
        "metadata": metadata
    }
    
    # Track normalizations
    if college_name != raw.get("Standard_College_Name"):
        report.normalized_fields["college_name"] = report.normalized_fields.get("college_name", 0) + 1
    if university_name and university_name != raw.get("Standard_University_Name"):
        report.normalized_fields["university_name"] = report.normalized_fields.get("university_name", 0) + 1
    if location and location != location_raw:
        report.normalized_fields["location"] = report.normalized_fields.get("location", 0) + 1
    if degree_level_raw:
        report.normalized_fields["courses"] = report.normalized_fields.get("courses", 0) + 1
    
    return cleaned


def clean_colleges(input_path: str, output_path: str, errors_path: str, report: CleaningReport) -> List[Dict]:
    """
    Main cleaning function for colleges data.
    Reads from input_path, writes cleaned data to output_path,
    errors to errors_path, updates report.
    """
    # Load raw data
    raw_data = load_json(input_path)
    report.input_records = len(raw_data)
    
    cleaned_records = []
    
    for raw_record in raw_data:
        try:
            cleaned = clean_college_record(raw_record, report)
            if cleaned:
                # Add metadata with cleaned_at timestamp
                cleaned = add_metadata(
                    cleaned, 
                    cleaned["metadata"]["source"],
                    cleaned["metadata"]["source_url"],
                    cleaned["metadata"]["scraped_at"],
                    "college"
                )
                cleaned_records.append(cleaned)
        except Exception as e:
            report.errors.append({
                "record": raw_record.get("Standard_College_Name", "unknown"),
                "error": str(e)
            })
    
    # Deduplicate
    unique_records, exact_duplicates, possible_duplicates = deduplicate_records(
        cleaned_records,
        id_field="metadata.source_url",
        key_fields=["college_name", "location"]
    )
    
    report.exact_duplicates_removed = len(exact_duplicates)
    report.possible_duplicates = len(possible_duplicates)
    
    # Validate with Pydantic
    valid_records, invalid_records = validate_records(unique_records, College)
    
    report.valid_records = len(valid_records)
    report.invalid_records = len(invalid_records) + len(exact_duplicates)
    
    # Add invalid records to errors
    for inv in invalid_records:
        report.errors.append({
            "record_index": inv["record_index"],
            "college_name": inv["record"].get("college_name", "unknown"),
            "error": inv["error"]
        })
    
    # Save outputs
    save_json(valid_records, output_path)
    save_json({
        "exact_duplicates": exact_duplicates,
        "possible_duplicates": [
            {"record1": r1.get("college_name"), "record2": r2.get("college_name")}
            for r1, r2 in possible_duplicates
        ],
        "validation_errors": invalid_records
    }, errors_path)
    
    return valid_records


# Import here to avoid circular dependency
from .common import load_json, save_json


if __name__ == "__main__":
    # Test run
    report = CleaningReport("colleges")
    clean_colleges(
        "D:/Data_Cleanning_Pipeline/data/raw/career360.json",
        "D:/Data_Cleanning_Pipeline/data/cleaned/colleges.json",
        "D:/Data_Cleanning_Pipeline/data/errors/colleges_errors.json",
        report
    )
    print(report.to_dict())