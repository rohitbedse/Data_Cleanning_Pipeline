"""
Career pathway cleaner for mindler.json.
Transforms raw Mindler career data into validated, normalized records.
"""

import re
from typing import Dict, List, Any, Optional
from copy import deepcopy

from .common import (
    clean_text, normalize_missing, normalize_field, normalize_location,
    generate_record_id, deduplicate_records, add_metadata,
    CleaningReport, clean_html_artifacts, load_json, save_json
)
from .validators import (
    CareerPathway, CareerDomain, SubCareer, EntranceExam, CollegeInfo,
    CareerPath, ProsCons, CareerOpportunity, validate_records
)


def clean_entrance_exam(exam: Dict) -> EntranceExam:
    """Clean a single entrance exam record."""
    cleaned = {}
    
    name = normalize_missing(exam.get("name"))
    if name:
        cleaned["name"] = clean_html_artifacts(name)
    
    key_elements = normalize_missing(exam.get("key_elements"))
    if key_elements:
        cleaned["key_elements"] = clean_html_artifacts(key_elements)
    
    tentative_date = normalize_missing(exam.get("tentative_date"))
    if tentative_date:
        cleaned["tentative_date"] = clean_text(tentative_date)
    
    level = normalize_missing(exam.get("level"))
    if level:
        cleaned["level"] = clean_text(level)
    
    website = normalize_missing(exam.get("website"))
    if website:
        cleaned["website"] = clean_text(website)
    
    return EntranceExam(**cleaned)


def clean_college_info(college: Dict) -> CollegeInfo:
    """Clean a single college info record."""
    cleaned = {}
    
    name = normalize_missing(college.get("name"))
    if name:
        cleaned["name"] = clean_html_artifacts(name)
    
    location = normalize_missing(college.get("location"))
    if location:
        cleaned["location"] = normalize_location(location)
    
    course = normalize_missing(college.get("course"))
    if course:
        cleaned["course"] = clean_html_artifacts(course)
    
    website = normalize_missing(college.get("website"))
    if website:
        cleaned["website"] = clean_text(website)
    
    return CollegeInfo(**cleaned)


def clean_career_path(path: Dict) -> CareerPath:
    """Clean a single career path step."""
    cleaned = {}
    
    path_group = normalize_missing(path.get("path_group"))
    if path_group:
        cleaned["path_group"] = clean_text(path_group)
    
    path_name = normalize_missing(path.get("path_name"))
    if path_name:
        cleaned["path_name"] = clean_text(path_name)
    
    path_title = normalize_missing(path.get("path_title"))
    if path_title:
        cleaned["path_title"] = clean_text(path_title)
    
    for field in ["stream", "graduation", "after_graduation", 
                  "after_post_graduation", "description"]:
        value = normalize_missing(path.get(field))
        if value and value != "-":
            cleaned[field] = clean_html_artifacts(value)
    
    return CareerPath(**cleaned)


def clean_pros_cons(pros_cons: Dict) -> ProsCons:
    """Clean pros and cons."""
    pros = pros_cons.get("Pros", [])
    cons = pros_cons.get("Cons", [])
    
    cleaned_pros = []
    for p in pros:
        p_clean = normalize_missing(p)
        if p_clean:
            cleaned_pros.append(clean_html_artifacts(p_clean))
    
    cleaned_cons = []
    for c in cons:
        c_clean = normalize_missing(c)
        if c_clean:
            cleaned_cons.append(clean_html_artifacts(c_clean))
    
    return ProsCons(pros=cleaned_pros, cons=cleaned_cons)


def clean_career_opportunity(opp: Dict) -> CareerOpportunity:
    """Clean a career opportunity."""
    cleaned = {}
    
    title = normalize_missing(opp.get("title"))
    if title:
        cleaned["title"] = clean_html_artifacts(title)
    
    description = normalize_missing(opp.get("description"))
    if description:
        cleaned["description"] = clean_html_artifacts(description)
    
    return CareerOpportunity(**cleaned)


def clean_subcareer(subcareer: Dict, report: CleaningReport) -> Optional[SubCareer]:
    """Clean a single subcareer record."""
    # Normalize missing values
    subcareer = normalize_missing(subcareer)
    
    # Required field: name
    name = clean_text(subcareer.get("name"))
    if not name:
        return None
    
    # Track missing important fields
    important_fields = ["id", "entrance_exams", "colleges_india", "career_paths"]
    for field in important_fields:
        if not subcareer.get(field):
            report.missing_important_fields[field] = report.missing_important_fields.get(field, 0) + 1
    
    # Build cleaned record
    cleaned = {"name": name}
    
    # ID fields
    for field in ["id", "career_id", "career_domain_id", "career_broad_id"]:
        value = normalize_missing(subcareer.get(field))
        if value is not None:
            cleaned[field] = clean_text(str(value))
    
    # Keywords
    keywords = normalize_missing(subcareer.get("keywords"))
    if keywords:
        cleaned["keywords"] = clean_html_artifacts(keywords)
    
    # Notes
    notes = normalize_missing(subcareer.get("notes"))
    if notes:
        cleaned["notes"] = clean_html_artifacts(notes)
    
    # Eligibility status
    eligibility = normalize_missing(subcareer.get("eligibility_status"))
    if eligibility:
        cleaned["eligibility_status"] = clean_text(eligibility)
    
    # Entrance exams
    exams_raw = subcareer.get("entrance_exams", [])
    if exams_raw:
        cleaned_exams = []
        for exam in exams_raw:
            try:
                cleaned_exams.append(clean_entrance_exam(exam))
            except Exception:
                pass
        if cleaned_exams:
            cleaned["entrance_exams"] = cleaned_exams
    
    # Colleges India
    colleges_india_raw = subcareer.get("colleges_india", [])
    if colleges_india_raw:
        cleaned_colleges = []
        for college in colleges_india_raw:
            try:
                cleaned_colleges.append(clean_college_info(college))
            except Exception:
                pass
        if cleaned_colleges:
            cleaned["colleges_india"] = cleaned_colleges
    
    # Colleges Abroad
    colleges_abroad_raw = subcareer.get("colleges_abroad", [])
    if colleges_abroad_raw:
        cleaned_colleges = []
        for college in colleges_abroad_raw:
            try:
                cleaned_colleges.append(clean_college_info(college))
            except Exception:
                pass
        if cleaned_colleges:
            cleaned["colleges_abroad"] = cleaned_colleges
    
    # Career paths
    paths_raw = subcareer.get("career_paths", [])
    if paths_raw:
        cleaned_paths = []
        for path in paths_raw:
            try:
                cleaned_paths.append(clean_career_path(path))
            except Exception:
                pass
        if cleaned_paths:
            cleaned["career_paths"] = cleaned_paths
    
    # Pros and cons
    pros_cons_raw = subcareer.get("pros_cons")
    if pros_cons_raw:
        cleaned["pros_cons"] = clean_pros_cons(pros_cons_raw)
    
    # Career opportunities
    opps_raw = subcareer.get("career_opportunities", [])
    if opps_raw:
        cleaned_opps = []
        for opp in opps_raw:
            try:
                cleaned_opps.append(clean_career_opportunity(opp))
            except Exception:
                pass
        if cleaned_opps:
            cleaned["career_opportunities"] = cleaned_opps
    
    # Work description
    work_desc_raw = subcareer.get("work_description", [])
    if work_desc_raw:
        cleaned_work = []
        for desc in work_desc_raw:
            desc_clean = normalize_missing(desc)
            if desc_clean:
                cleaned_work.append(clean_html_artifacts(desc_clean))
        if cleaned_work:
            cleaned["work_description"] = cleaned_work
    
    # Track normalizations
    if name != subcareer.get("name"):
        report.normalized_fields["subcareer_name"] = report.normalized_fields.get("subcareer_name", 0) + 1
    
    try:
        return SubCareer(**cleaned)
    except Exception as e:
        report.errors.append({
            "subcareer_name": name,
            "error": str(e)
        })
        return None


def clean_career_domain(domain: Dict, report: CleaningReport) -> Optional[CareerDomain]:
    """Clean a single career domain (subject)."""
    domain = normalize_missing(domain)
    
    subject_id = clean_text(domain.get("subject_id"))
    subject_title = clean_text(domain.get("subject_title"))
    
    if not subject_id or not subject_title:
        return None
    
    cleaned = {
        "subject_id": subject_id,
        "subject_title": subject_title
    }
    
    description = normalize_missing(domain.get("description"))
    if description:
        cleaned["description"] = clean_html_artifacts(description)
    
    image = normalize_missing(domain.get("image"))
    if image:
        cleaned["image"] = clean_text(image)
    
    # Clean subcareers
    subcareers_raw = domain.get("subcareers", [])
    cleaned_subcareers = []
    for sub in subcareers_raw:
        cleaned_sub = clean_subcareer(sub, report)
        if cleaned_sub:
            cleaned_subcareers.append(cleaned_sub)
    
    if cleaned_subcareers:
        cleaned["subcareers"] = cleaned_subcareers
    
    # Track normalizations
    if description and description != domain.get("description"):
        report.normalized_fields["domain_description"] = report.normalized_fields.get("domain_description", 0) + 1
    
    return CareerDomain(**cleaned)


def clean_career_pathway(input_path: str, output_path: str, errors_path: str, report: CleaningReport) -> Dict:
    """
    Main cleaning function for career pathway data.
    """
    raw_data = load_json(input_path)
    
    # The mindler.json has a wrapper structure
    report.input_records = raw_data.get("total_subcareers", 0)
    
    job_id = raw_data.get("job_id")
    source = raw_data.get("source", "mindler")
    scraped_at = raw_data.get("scraped_at")
    total_items = raw_data.get("total_items", 0)
    
    # Clean each domain
    cleaned_domains = []
    domains_raw = raw_data.get("items", [])
    
    for domain_raw in domains_raw:
        cleaned_domain = clean_career_domain(domain_raw, report)
        if cleaned_domain:
            cleaned_domains.append(cleaned_domain)
    
    # Build the cleaned pathway structure
    cleaned_pathway = {
        "job_id": job_id,
        "source": source,
        "scraped_at": scraped_at,
        "total_items": total_items,
        "total_subcareers": sum(len(d.subcareers) for d in cleaned_domains),
        "items": [d.model_dump(exclude_none=True) for d in cleaned_domains]
    }
    
    # Add metadata
    cleaned_pathway = add_metadata(
        cleaned_pathway,
        source,
        None,  # No single URL for this dataset
        scraped_at,
        "career_pathway"
    )
    
    # Validate with Pydantic
    valid_pathway, invalid_errors = validate_single(cleaned_pathway, CareerPathway)
    
    if valid_pathway:
        report.valid_records = 1
    else:
        report.valid_records = 0
        report.invalid_records = 1
        report.errors.append({"error": invalid_errors})
    
    # Save outputs
    save_json(valid_pathway if valid_pathway else cleaned_pathway, output_path)
    save_json({
        "validation_errors": invalid_errors if invalid_errors else None,
        "domain_errors": report.errors
    }, errors_path)
    
    return valid_pathway if valid_pathway else cleaned_pathway


def validate_single(record: Dict, model_class) -> tuple:
    """Validate a single record against a model."""
    try:
        validated = model_class(**record)
        return validated.model_dump(exclude_none=True), None
    except Exception as e:
        return None, str(e)


if __name__ == "__main__":
    report = CleaningReport("career_pathway")
    clean_career_pathway(
        "D:/Data_Cleanning_Pipeline/data/raw/mindler.json",
        "D:/Data_Cleanning_Pipeline/data/cleaned/career_pathway.json",
        "D:/Data_Cleanning_Pipeline/data/errors/career_pathway_errors.json",
        report
    )
    print(report.to_dict())