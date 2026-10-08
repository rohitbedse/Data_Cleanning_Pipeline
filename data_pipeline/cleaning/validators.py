"""
Pydantic validators for cleaned datasets.
Defines schemas for colleges, career pathways, and upskilling courses.
"""

from typing import Optional, List, Dict, Any, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime


# ============================================================
# College Validators (from career360.json)
# ============================================================

class CollegeCourse(BaseModel):
    """Individual course offered by a college."""
    course_name: str = Field(..., min_length=1)
    domain: Optional[str] = None
    eligibility: Optional[str] = None
    course_details: Optional[str] = None
    course_duration: Optional[str] = None
    course_duration_years: Optional[float] = None
    fees: Optional[str] = None
    fees_inr: Optional[int] = None
    entrance_exams_accepted: List[str] = Field(default_factory=list)
    research_areas: Optional[str] = None
    course_intake: Optional[str] = None
    admission_process: Optional[str] = None
    
    @field_validator('course_name', 'domain', 'eligibility', 'course_details', 
                     'research_areas', 'course_intake', 'admission_process', mode='before')
    @classmethod
    def clean_strings(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v
    
    @field_validator('entrance_exams_accepted', mode='before')
    @classmethod
    def clean_exam_list(cls, v):
        if not v:
            return []
        if isinstance(v, list):
            return [e.strip() for e in v if e and e.strip()]
        return []


class CollegeDegreeLevel(BaseModel):
    """Courses grouped by degree level."""
    ug: List[CollegeCourse] = Field(default_factory=list, alias="UG")
    pg: List[CollegeCourse] = Field(default_factory=list, alias="PG")
    phd: List[CollegeCourse] = Field(default_factory=list, alias="PhD")
    
    class Config:
        populate_by_name = True


class CollegeRanking(BaseModel):
    """College ranking information."""
    nirf_ranking: Optional[int] = None
    qs_world_ranking: Optional[int] = None
    times_higher_education_ranking: Optional[int] = None


class CollegeMetadata(BaseModel):
    """Metadata for provenance tracking."""
    source: str
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None
    data_type: str = "college"
    cleaned_at: str


class College(BaseModel):
    """Cleaned college record."""
    college_name: str = Field(..., min_length=1)
    university_name: Optional[str] = None
    college_category: Optional[str] = None  # Private, Government, etc.
    description: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    study_destination: Optional[str] = None
    degree_level: CollegeDegreeLevel = Field(default_factory=CollegeDegreeLevel)
    ranking: CollegeRanking = Field(default_factory=CollegeRanking)
    metadata: CollegeMetadata
    
    @field_validator('college_name', 'university_name', 'college_category', 
                     'description', 'location', 'city', 'state', 'study_destination', mode='before')
    @classmethod
    def clean_strings(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v


# ============================================================
# Career Pathway Validators (from mindler.json)
# ============================================================

class EntranceExam(BaseModel):
    """Entrance exam information."""
    name: str
    key_elements: Optional[str] = None
    tentative_date: Optional[str] = None
    level: Optional[str] = None  # UG, PG
    website: Optional[str] = None


class CollegeInfo(BaseModel):
    """College information for a career."""
    name: str
    location: Optional[str] = None
    course: Optional[str] = None
    website: Optional[str] = None


class CareerPath(BaseModel):
    """Career path step."""
    path_group: str
    path_name: str  # stream, graduation, After_Graduation, After_Post_Graduation
    path_title: Optional[str] = None
    stream: Optional[str] = None
    graduation: Optional[str] = None
    after_graduation: Optional[str] = None
    after_post_graduation: Optional[str] = None
    description: Optional[str] = None


class ProsCons(BaseModel):
    """Pros and cons for a career."""
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)


class CareerOpportunity(BaseModel):
    """Career opportunity."""
    title: str
    description: Optional[str] = None


class SubCareer(BaseModel):
    """A specific sub-career within a domain."""
    id: Optional[str] = None
    career_id: Optional[str] = None
    career_domain_id: Optional[str] = None
    career_broad_id: Optional[str] = None
    name: str = Field(..., min_length=1)
    keywords: Optional[str] = None
    notes: Optional[str] = None
    eligibility_status: Optional[str] = None
    entrance_exams: List[EntranceExam] = Field(default_factory=list)
    colleges_india: List[CollegeInfo] = Field(default_factory=list)
    colleges_abroad: List[CollegeInfo] = Field(default_factory=list)
    career_paths: List[CareerPath] = Field(default_factory=list)
    pros_cons: ProsCons = Field(default_factory=ProsCons)
    career_opportunities: List[CareerOpportunity] = Field(default_factory=list)
    work_description: List[str] = Field(default_factory=list)


class CareerDomain(BaseModel):
    """A career domain (e.g., Engineering)."""
    subject_id: str
    subject_title: str
    description: Optional[str] = None
    image: Optional[str] = None
    subcareers: List[SubCareer] = Field(default_factory=list)


class CareerPathwayMetadata(BaseModel):
    """Metadata for career pathway."""
    source: str
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None
    data_type: str = "career_pathway"
    cleaned_at: str
    job_id: Optional[str] = None


class CareerPathway(BaseModel):
    """Cleaned career pathway record (wrapper for the whole dataset)."""
    job_id: Optional[str] = None
    source: str
    scraped_at: Optional[str] = None
    total_items: int = 0
    total_subcareers: int = 0
    items: List[CareerDomain] = Field(default_factory=list)
    metadata: CareerPathwayMetadata


# ============================================================
# Upskilling Courses Validators (from swayam.json)
# ============================================================

class CourseInstructor(BaseModel):
    """Course instructor information."""
    name: str
    bio: Optional[str] = None


class UpskillingCourse(BaseModel):
    """Cleaned upskilling course record."""
    course_name: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    source: str  # AICTE, IGNOU, NPTEL, etc.
    institute: Optional[str] = None
    description: Optional[str] = None
    subject_area: Optional[str] = None
    course_type: Optional[str] = None  # Core, Elective, Not Applicable
    course_format: Optional[str] = None
    difficulty_level: Optional[str] = None  # Beginner, Intermediate, Advanced
    academic_level: Optional[str] = None  # UG, PG, Certificate, etc.
    course_duration: Optional[str] = None
    course_duration_weeks: Optional[float] = None
    skills_learned: Optional[str] = None
    intended_audience: Optional[str] = None
    prerequisites: Optional[str] = None
    language: Optional[str] = None
    instructor: Optional[CourseInstructor] = None
    live_status: Optional[str] = None
    
    @field_validator('course_name', 'url', 'source', 'institute', 'description',
                     'subject_area', 'course_type', 'course_format', 'difficulty_level',
                     'academic_level', 'course_duration', 'skills_learned', 
                     'intended_audience', 'prerequisites', 'language', 'live_status', mode='before')
    @classmethod
    def clean_strings(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v
    
    @field_validator('instructor', mode='before')
    @classmethod
    def parse_instructor(cls, v):
        if not v:
            return None
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            # Parse "Name | Title, Institute" format
            parts = v.split('|')
            name = parts[0].strip() if parts else v.strip()
            bio = parts[1].strip() if len(parts) > 1 else None
            return {"name": name, "bio": bio}
        return None


class UpskillingCoursesMetadata(BaseModel):
    """Metadata for upskilling courses dataset."""
    source: str
    scraped_at: Optional[str] = None
    data_type: str = "upskilling_course"
    cleaned_at: str
    job_id: Optional[str] = None
    total_items: int = 0


class UpskillingCourses(BaseModel):
    """Cleaned upskilling courses dataset."""
    job_id: Optional[str] = None
    source: str
    scraped_at: Optional[str] = None
    total_items: int = 0
    items: List[UpskillingCourse] = Field(default_factory=list)
    metadata: UpskillingCoursesMetadata
    live_status_count: Dict[str, int] = Field(default_factory=dict)


# ============================================================
# Validation Helpers
# ============================================================

def validate_records(records: List[Dict], model_class: type) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate a list of records against a Pydantic model.
    Returns (valid_records, invalid_records_with_errors).
    """
    valid = []
    invalid = []
    
    for i, record in enumerate(records):
        try:
            validated = model_class(**record)
            valid.append(validated.model_dump(exclude_none=True))
        except Exception as e:
            invalid.append({
                "record_index": i,
                "record": record,
                "error": str(e)
            })
    
    return valid, invalid


def validate_single(record: Dict, model_class: type) -> tuple[Optional[Dict], Optional[str]]:
    """Validate a single record. Returns (validated_dict, error_message)."""
    try:
        validated = model_class(**record)
        return validated.model_dump(exclude_none=True), None
    except Exception as e:
        return None, str(e)