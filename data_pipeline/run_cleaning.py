#!/usr/bin/env python
"""
Main runner for the data cleaning pipeline.
Executes all cleaning modules and generates a consolidated report.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add the cleaning module to path
sys.path.insert(0, str(Path(__file__).parent))

from cleaning.common import CleaningReport, save_json
from cleaning.colleges import clean_colleges
from cleaning.career_pathway import clean_career_pathway
from cleaning.upskilling_courses import clean_upskilling_courses


def main():
    base_dir = Path(__file__).parent.parent
    raw_dir = base_dir / "data" / "raw"
    cleaned_dir = base_dir / "data" / "cleaned"
    errors_dir = base_dir / "data" / "errors"
    reports_dir = base_dir / "data" / "reports"
    
    # Ensure output directories exist
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    errors_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    all_reports = {}
    
    # ============================================================
    # 1. Clean Colleges (career360.json)
    # ============================================================
    print("\n" + "="*60)
    print("Cleaning Colleges (career360.json)...")
    print("="*60)
    
    colleges_report = CleaningReport("colleges")
    colleges_input = raw_dir / "career360.json"
    colleges_output = cleaned_dir / "colleges.json"
    colleges_errors = errors_dir / "colleges_errors.json"
    
    if colleges_input.exists():
        clean_colleges(str(colleges_input), str(colleges_output), str(colleges_errors), colleges_report)
        all_reports["colleges"] = colleges_report.to_dict()
        print(f"  Input records: {colleges_report.input_records}")
        print(f"  Valid records: {colleges_report.valid_records}")
        print(f"  Invalid records: {colleges_report.invalid_records}")
        print(f"  Duplicates removed: {colleges_report.exact_duplicates_removed}")
        print(f"  Possible duplicates: {colleges_report.possible_duplicates}")
    else:
        print(f"  WARNING: {colleges_input} not found")
        all_reports["colleges"] = {"error": "Input file not found"}
    
    # ============================================================
    # 2. Clean Career Pathways (mindler.json)
    # ============================================================
    print("\n" + "="*60)
    print("Cleaning Career Pathways (mindler.json)...")
    print("="*60)
    
    career_report = CleaningReport("career_pathway")
    career_input = raw_dir / "mindler.json"
    career_output = cleaned_dir / "career_pathway.json"
    career_errors = errors_dir / "career_pathway_errors.json"
    
    if career_input.exists():
        clean_career_pathway(str(career_input), str(career_output), str(career_errors), career_report)
        all_reports["career_pathway"] = career_report.to_dict()
        print(f"  Input subcareers: {career_report.input_records}")
        print(f"  Valid records: {career_report.valid_records}")
        print(f"  Invalid records: {career_report.invalid_records}")
        print(f"  Errors: {len(career_report.errors)}")
    else:
        print(f"  WARNING: {career_input} not found")
        all_reports["career_pathway"] = {"error": "Input file not found"}
    
    # ============================================================
    # 3. Clean Upskilling Courses (swayam.json)
    # ============================================================
    print("\n" + "="*60)
    print("Cleaning Upskilling Courses (swayam.json)...")
    print("="*60)
    
    upskilling_report = CleaningReport("upskilling_courses")
    upskilling_input = raw_dir / "swayam.json"
    upskilling_output = cleaned_dir / "upskilling_courses.json"
    upskilling_errors = errors_dir / "upskilling_courses_errors.json"
    
    if upskilling_input.exists():
        clean_upskilling_courses(str(upskilling_input), str(upskilling_output), str(upskilling_errors), upskilling_report)
        all_reports["upskilling_courses"] = upskilling_report.to_dict()
        print(f"  Input records: {upskilling_report.input_records}")
        print(f"  Valid records: {upskilling_report.valid_records}")
        print(f"  Invalid records: {upskilling_report.invalid_records}")
        print(f"  Duplicates removed: {upskilling_report.exact_duplicates_removed}")
        print(f"  Possible duplicates: {upskilling_report.possible_duplicates}")
    else:
        print(f"  WARNING: {upskilling_input} not found")
        all_reports["upskilling_courses"] = {"error": "Input file not found"}
    
    # ============================================================
    # Generate consolidated report
    # ============================================================
    print("\n" + "="*60)
    print("Generating consolidated report...")
    print("="*60)
    
    consolidated_report = {
        "pipeline_run_at": datetime.utcnow().isoformat() + "Z",
        "datasets": all_reports,
        "summary": {
            "total_input_records": sum(r.get("input_records", 0) for r in all_reports.values() if isinstance(r, dict)),
            "total_valid_records": sum(r.get("valid_records", 0) for r in all_reports.values() if isinstance(r, dict)),
            "total_invalid_records": sum(r.get("invalid_records", 0) for r in all_reports.values() if isinstance(r, dict)),
            "total_duplicates_removed": sum(r.get("exact_duplicates_removed", 0) for r in all_reports.values() if isinstance(r, dict)),
            "total_possible_duplicates": sum(r.get("possible_duplicates", 0) for r in all_reports.values() if isinstance(r, dict)),
        }
    }
    
    report_path = reports_dir / "cleaning_report.json"
    save_json(consolidated_report, str(report_path))
    
    print(f"\nReport saved to: {report_path}")
    print(f"Summary:")
    print(f"  Total input records: {consolidated_report['summary']['total_input_records']}")
    print(f"  Total valid records: {consolidated_report['summary']['total_valid_records']}")
    print(f"  Total invalid records: {consolidated_report['summary']['total_invalid_records']}")
    print(f"  Total duplicates removed: {consolidated_report['summary']['total_duplicates_removed']}")
    print(f"  Total possible duplicates: {consolidated_report['summary']['total_possible_duplicates']}")
    
    # Print file sizes
    print("\n" + "="*60)
    print("Output files:")
    print("="*60)
    for f in [colleges_output, career_output, upskilling_output]:
        if f.exists():
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name}: {size_kb:.1f} KB")
    
    for f in [colleges_errors, career_errors, upskilling_errors]:
        if f.exists():
            size_kb = f.stat().st_size / 1024
            print(f"  {f.name}: {size_kb:.1f} KB")
    
    print(f"\nPipeline completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())