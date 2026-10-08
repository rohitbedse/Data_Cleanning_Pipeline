"""
Upskilling courses cleaner for swayam.json.
Transforms raw SWAYAM course data into validated, normalized records.
"""

import re
from typing import Dict, List, Any, Optional
from copy import deepcopy

from .common import (
    clean_text, normalize_missing, normalize_field, normalize_location,
    parse_duration_years, generate_record_id, deduplicate_records,
    add_metadata, CleaningReport, clean_html_artifacts, load_json, save_json
)
from .validators import (
    UpskillingCourses, UpskillingCourse, CourseInstructor, validate_records, validate_single
)


def parse_course_duration_weeks(duration: Optional[str]) -> Optional[float]:
    """
    Parse course duration to weeks.
    Handles: "4 Weeks", "12 Weeks", "6 Months", "1 Year", "-1 Week", etc.
    """
    if not duration:
        return None
    
    cleaned = clean_text(duration)
    if not cleaned:
        return None
    
    # Handle negative/invalid durations
    if cleaned.startswith('-'):
        return None
    
    total_weeks = 0.0
    
    # Years
    year_match = re.search(r'(\d+(?:\.\d+)?)\s*[Yy]ear', cleaned)
    if year_match:
        total_weeks += float(year_match.group(1)) * 52
    
    # Months
    month_match = re.search(r'(\d+(?:\.\d+)?)\s*[Mm]onth', cleaned)
    if month_match:
        total_weeks += float(month_match.group(1)) * 4.33
    
    # Weeks
    week_match = re.search(r'(\d+(?:\.\d+)?)\s*[Ww]eek', cleaned)
    if week_match:
        total_weeks += float(week_match.group(1))
    
    # Days
    day_match = re.search(r'(\d+(?:\.\d+)?)\s*[Dd]ay', cleaned)
    if day_match:
        total_weeks += float(day_match.group(1)) / 7
    
    if total_weeks > 0:
        return round(total_weeks, 1)
    
    # Try plain number as weeks
    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_instructor(instructor_raw: Any) -> Optional[CourseInstructor]:
    """Clean instructor information."""
    if not instructor_raw:
        return None
    
    if isinstance(instructor_raw, dict):
        name = normalize_missing(instructor_raw.get("name"))
        bio = normalize_missing(instructor_raw.get("bio"))
        if name:
            return CourseInstructor(name=clean_text(name), bio=clean_html_artifacts(bio))
        return None
    
    if isinstance(instructor_raw, str):
        # Parse "Name | Title, Institute" or "Name\nTitle\nInstitute" format
        cleaned = clean_text(instructor_raw)
        if not cleaned:
            return None
        
        # Try splitting by common delimiters
        parts = re.split(r'\s*\|\s*|\n+', cleaned)
        name = parts[0].strip() if parts else cleaned
        bio = " | ".join(parts[1:]).strip() if len(parts) > 1 else None
        
        return CourseInstructor(name=name, bio=clean_html_artifacts(bio) if bio else None)
    
    return None


def clean_course(course: Dict, report: CleaningReport) -> Optional[UpskillingCourse]:
    """Clean a single course record."""
    course = normalize_missing(course)
    
    # Required fields
    course_name = clean_text(course.get("course_name"))
    url = clean_text(course.get("url"))
    
    if not course_name or not url:
        return None
    
    # Track missing important fields
    important_fields = ["source", "institute", "description", "subject_area", 
                        "course_duration", "academic_level", "language"]
    for field in important_fields:
        if not course.get(field):
            report.missing_important_fields[field] = report.missing_important_fields.get(field, 0) + 1
    
    cleaned = {
        "course_name": course_name,
        "url": url
    }
    
    # Source (AICTE, IGNOU, NPTEL, etc.)
    source = clean_text(course.get("source"))
    if source:
        cleaned["source"] = source
    
    # Institute
    institute = normalize_missing(course.get("institute"))
    if institute:
        cleaned["institute"] = clean_html_artifacts(institute)
    
    # Description
    description = normalize_missing(course.get("description"))
    if description:
        cleaned["description"] = clean_html_artifacts(description)
    
    # Subject area
    subject_area = normalize_missing(course.get("subject_area"))
    if subject_area:
        cleaned["subject_area"] = clean_html_artifacts(subject_area)
    
    # Course type
    course_type = normalize_missing(course.get("course_type"))
    if course_type:
        cleaned["course_type"] = clean_text(course_type)
    
    # Course format
    course_format = normalize_missing(course.get("course_format"))
    if course_format:
        cleaned["course_format"] = clean_text(course_format)
    
    # Difficulty level
    difficulty = normalize_missing(course.get("difficulty_level"))
    if difficulty:
        cleaned["difficulty_level"] = clean_text(difficulty)
    
    # Academic level
    academic_level = normalize_missing(course.get("academic_level"))
    if academic_level:
        cleaned["academic_level"] = clean_text(academic_level)
    
    # Duration
    duration = normalize_missing(course.get("course_duration"))
    if duration and duration != "-":
        cleaned["course_duration"] = duration
        weeks = parse_course_duration_weeks(duration)
        if weeks:
            cleaned["course_duration_weeks"] = weeks
    
    # Skills learned
    skills = normalize_missing(course.get("skills_learned"))
    if skills:
        cleaned["skills_learned"] = clean_html_artifacts(skills)
    
    # Intended audience
    audience = normalize_missing(course.get("intended_audience"))
    if audience:
        cleaned["intended_audience"] = clean_html_artifacts(audience)
    
    # Prerequisites
    prereqs = normalize_missing(course.get("prerequisites"))
    if prereqs:
        cleaned["prerequisites"] = clean_html_artifacts(prereqs)
    
    # Language
    language = normalize_missing(course.get("language"))
    if language:
        cleaned["language"] = clean_text(language)
    
    # Instructor
    instructor_raw = course.get("instructor")
    if instructor_raw:
        instructor = clean_instructor(instructor_raw)
        if instructor:
            cleaned["instructor"] = instructor
    
    # Live status (from parent dataset, added during processing)
    # Will be set in main function
    
    # Track normalizations
    if duration and duration != course.get("course_duration"):
        report.normalized_fields["course_duration"] = report.normalized_fields.get("course_duration", 0) + 1
    if institute and institute != course.get("institute"):
        report.normalized_fields["institute"] = report.normalized_fields.get("institute", 0) + 1
    
    try:
        return UpskillingCourse(**cleaned)
    except Exception as e:
        report.errors.append({
            "course_name": course_name,
            "error": str(e)
        })
        return None


def clean_upskilling_courses(input_path: str, output_path: str, errors_path: str, report: CleaningReport) -> Dict:
    """
    Main cleaning function for upskilling courses data.
    """
    raw_data = load_json(input_path)
    
    job_id = raw_data.get("job_id")
    source = raw_data.get("source", "swayam")
    scraped_at = raw_data.get("scraped_at")
    total_items = raw_data.get("total_items", 0)
    live_status_count = raw_data.get("live_status_count", {})
    
    report.input_records = total_items
    
    # Clean each course
    courses_raw = raw_data.get("items", [])
    cleaned_courses = []
    
    for course_raw in courses_raw:
        cleaned_course = clean_course(course_raw, report)
        if cleaned_course:
            # Add live status from parent if available
            # (not in individual course records)
            cleaned_courses.append(cleaned_course)
    
    # Deduplicate by URL
    unique_courses, exact_duplicates, possible_duplicates = deduplicate_records(
        [c.model_dump(exclude_none=True) for c in cleaned_courses],
        id_field="url",
        key_fields=["course_name", "institute"]
    )
    
    report.exact_duplicates_removed = len(exact_duplicates)
    report.possible_duplicates = len(possible_duplicates)
    
    # Re-validate deduplicated courses
    valid_courses = []
    invalid_records = []
    
    for course_dict in unique_courses:
        try:
            validated = UpskillingCourse(**course_dict)
            valid_courses.append(validated.model_dump(exclude_none=True))
        except Exception as e:
            invalid_records.append({"record": course_dict, "error": str(e)})
    
    report.valid_records = len(valid_courses)
    report.invalid_records = len(invalid_records) + len(exact_duplicates)
    
    for inv in invalid_records:
        report.errors.append({
            "course_name": inv["record"].get("course_name", "unknown"),
            "error": inv["error"]
        })
    
    # Build final dataset
    cleaned_dataset = {
        "job_id": job_id,
        "source": source,
        "scraped_at": scraped_at,
        "total_items": len(valid_courses),
        "items": valid_courses,
        "live_status_count": live_status_count
    }
    
    # Add metadata (includes cleaned_at timestamp)
    cleaned_dataset = add_metadata(cleaned_dataset, source, None, scraped_at, "upskilling_course")
    cleaned_dataset["metadata"]["job_id"] = job_id
    cleaned_dataset["metadata"]["total_items"] = len(valid_courses)
    
    # Validate full dataset
    valid_dataset, dataset_error = validate_single(cleaned_dataset, UpskillingCourses)
    
    if not valid_dataset:
        report.errors.append({"dataset_error": dataset_error})
    
    # Save outputs
    save_json(valid_dataset if valid_dataset else cleaned_dataset, output_path)
    save_json({
        "exact_duplicates": exact_duplicates,
        "possible_duplicates": [
            {"course1": c1.get("course_name"), "course2": c2.get("course_name")}
            for c1, c2 in possible_duplicates
        ],
        "validation_errors": invalid_records
    }, errors_path)
    
    return valid_dataset if valid_dataset else cleaned_dataset


if __name__ == "__main__":
    report = CleaningReport("upskilling_courses")
    clean_upskilling_courses(
        "D:/Data_Cleanning_Pipeline/data/raw/swayam.json",
        "D:/Data_Cleanning_Pipeline/data/cleaned/upskilling_courses.json",
        "D:/Data_Cleanning_Pipeline/data/errors/upskilling_courses_errors.json",
        report
    )
    print(report.to_dict())