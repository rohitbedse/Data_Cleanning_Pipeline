# Data Cleaning Pipeline

Production-quality Python pipeline for cleaning and normalizing raw scraped JSON data for RAG applications.

## Structure

```
data_pipeline/
├── cleaning/
│   ├── common.py              # Shared utilities (text cleaning, normalization, deduplication)
│   ├── validators.py          # Pydantic models for schema validation
│   ├── colleges.py            # Cleaner for career360.json (college data)
│   ├── career_pathway.py      # Cleaner for mindler.json (career pathway data)
│   └── upskilling_courses.py  # Cleaner for swayam.json (course data)
├── run_cleaning.py            # Main pipeline runner
└── README.md                  # This file
```

## Data Flow

```
data/raw/
├── career360.json      →  data/cleaned/colleges.json
├── mindler.json        →  data/cleaned/career_pathway.json
└── swayam.json         →  data/cleaned/upskilling_courses.json

data/errors/
├── colleges_errors.json
├── career_pathway_errors.json
└── upskilling_courses_errors.json

data/reports/
└── cleaning_report.json
```

## Features

- **Raw data preservation**: Never modifies files in `data/raw/`
- **Text cleaning**: Whitespace normalization, HTML entity decoding, artifact removal
- **Missing value normalization**: Converts `""`, `"N/A"`, `"NA"`, `"Not Available"`, `"-"`, `"null"` → `null`
- **Entity normalization**: Degrees (`BTech`→`B.Tech`), fields (`ML`→`Machine Learning`), locations
- **Numeric parsing**: Indian currency (`₹2.5 Lakhs`→`250000`), durations, ratings, rankings, percentages
- **Deduplication**: Exact duplicates removed by `source_url` or deterministic ID; possible duplicates reported
- **Schema validation**: Pydantic models with invalid records saved separately
- **Metadata preservation**: Source, URL, scrape time, data type, cleaning timestamp
- **Comprehensive reporting**: Input/valid/invalid counts, duplicates, missing fields, normalizations, errors

## Usage

```bash
# Run full pipeline
cd data_pipeline
python run_cleaning.py

# Run individual cleaners (for testing)
python -m cleaning.colleges
python -m cleaning.career_pathway
python -m cleaning.upskilling_courses
```

## Requirements

- Python 3.10+
- pydantic >= 2.0

```bash
pip install pydantic
```

## Output Schema Examples

### College Record
```json
{
  "college_name": "AAA College of Engineering and Technology, Sivakasi",
  "university_name": "Anna University, Chennai",
  "college_category": "Private",
  "description": "...",
  "location": "Virudhunagar, Tamil Nadu",
  "city": "Virudhunagar",
  "state": "Tamil Nadu",
  "study_destination": "India",
  "degree_level": {
    "ug": [...],
    "pg": [...],
    "phd": [...]
  },
  "ranking": {
    "nirf_ranking": null,
    "qs_world_ranking": null,
    "times_higher_education_ranking": null
  },
  "metadata": {
    "source": "Careers360",
    "source_url": "https://...",
    "scraped_at": null,
    "data_type": "college",
    "cleaned_at": "2026-10-08T..."
  }
}
```

### Career Pathway Record
```json
{
  "job_id": "...",
  "source": "mindler",
  "scraped_at": "2026-10-08T...",
  "total_items": 44,
  "total_subcareers": 237,
  "items": [
    {
      "subject_id": "engineering",
      "subject_title": "Engineering",
      "description": "...",
      "image": "...",
      "subcareers": [...]
    }
  ],
  "metadata": {...}
}
```

### Upskilling Course Record
```json
{
  "course_name": "Advanced C++",
  "url": "https://onlinecourses.swayam2.ac.in/...",
  "source": "AICTE",
  "institute": "Indian Institute of Technology Bombay",
  "description": "...",
  "subject_area": "Multidisciplinary",
  "course_type": "Elective",
  "course_format": "Video / Self-paced",
  "difficulty_level": "Advanced",
  "academic_level": "UG, PG",
  "course_duration": "12 Weeks",
  "course_duration_weeks": 12.0,
  "skills_learned": "...",
  "language": "English",
  "instructor": {
    "name": "...",
    "bio": "..."
  },
  "live_status": "Upcoming"
}
```

## Normalization Rules

### Degrees
| Input | Normalized |
|-------|------------|
| BTech, B. Tech, Bachelor of Technology | B.Tech |
| BE, B.E., Bachelor of Engineering | B.E. |
| MTech, M. Tech, Master of Technology | M.Tech |
| BSc, B.Sc, Bachelor of Science | B.Sc |
| MBA, M.B.A., Master of Business Administration | MBA |

### Fields
| Input | Normalized |
|-------|------------|
| ML, Machine Learning (ML) | Machine Learning |
| AI, Artificial Intelligence (AI) | Artificial Intelligence |
| Python Programming, Python Language | Python |
| CSE, Computer Science Engineering | Computer Science |

### Locations
| Input | Normalized |
|-------|------------|
| Bangalore, Bengaluru | Bengaluru, Karnataka |
| Mumbai, Bombay | Mumbai, Maharashtra |
| Delhi, New Delhi | New Delhi, Delhi |
| Multiple locations | Multiple Locations, India |

### Currency
| Input | Normalized (INR) |
|-------|------------------|
| ₹2.5 Lakhs | 250000 |
| Rs. 2,50,000 | 250000 |
| 250000 | 250000 |
| 1.5 Crore | 15000000 |

## Error Handling

Invalid records are **not silently dropped**. They are saved to `data/errors/` with:
- Original record
- Validation error message
- Record index for traceability

Possible duplicates (similar names) are reported separately for manual review.

## Deterministic & Rerunnable

- All ID generation uses SHA256 hashes of key fields
- Cleaning operations are pure functions
- Pipeline can be run multiple times with identical results
- Timestamps only added to metadata (`cleaned_at`)

## Logging

Key transformations and errors are tracked in `cleaning_report.json`:
- Input/valid/invalid record counts per dataset
- Exact duplicates removed
- Possible duplicates flagged
- Missing important fields (with counts)
- Normalized fields/entities (with counts)
- Validation errors with context