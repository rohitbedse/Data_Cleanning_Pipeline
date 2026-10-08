import json

# Show college before/after
with open('D:/Data_Cleanning_Pipeline/data/raw/career360.json', encoding='utf-8') as f:
    raw = json.load(f)
with open('D:/Data_Cleanning_Pipeline/data/cleaned/colleges.json', encoding='utf-8') as f:
    cleaned = json.load(f)

print('=== COLLEGE BEFORE/AFTER ===')
print()
print('RAW (first college):')
raw_college = raw[0]
print(f'  Standard_College_Name: {raw_college["Standard_College_Name"]}')
print(f'  Standard_University_Name: {raw_college["Standard_University_Name"]}')
print(f'  College_Category: {raw_college["College_Category"]}')
print(f'  Location: {raw_college["Location"]}')
print(f'  Fees (first UG course): "{raw_college["Degree_Level"]["UG"][0]["Fees"]}"')
print(f'  NIRF_Ranking: "{raw_college["Ranking_Category"]["NIRF_Ranking"]}"')
print()
print('CLEANED (first college):')
c = cleaned[0]
print(f'  college_name: {c["college_name"]}')
print(f'  university_name: {c["university_name"]}')
print(f'  college_category: {c["college_category"]}')
print(f'  location: {c["location"]}')
print(f'  city: {c["city"]}')
print(f'  state: {c["state"]}')
print(f'  degree_level.ug[0].course_name: {c["degree_level"]["ug"][0]["course_name"]}')
print(f'  degree_level.ug[0].course_duration_years: {c["degree_level"]["ug"][0]["course_duration_years"]}')
print(f'  degree_level.ug[0].fees_inr: {c["degree_level"]["ug"][0].get("fees_inr", "null (empty in source)")}')
print(f'  ranking.nirf_ranking: {c["ranking"].get("nirf_ranking")}')
print(f'  metadata: {c["metadata"]}')
print()

# Show career pathway before/after
with open('D:/Data_Cleanning_Pipeline/data/raw/mindler.json', encoding='utf-8') as f:
    raw_career = json.load(f)
with open('D:/Data_Cleanning_Pipeline/data/cleaned/career_pathway.json', encoding='utf-8') as f:
    cleaned_career = json.load(f)

print('=== CAREER PATHWAY BEFORE/AFTER ===')
print()
print('RAW (first subcareer):')
raw_sub = raw_career["items"][0]["subcareers"][0]
print(f'  id: {raw_sub["id"]}')
print(f'  name: {raw_sub["name"]}')
print(f'  keywords: {raw_sub["keywords"][:80]}...')
print(f'  location (first college): {raw_sub["colleges_india"][0]["location"]}')
print(f'  after_graduation: "{raw_sub["career_paths"][2]["after_graduation"]}"')
print()
print('CLEANED (first subcareer):')
cleaned_sub = cleaned_career["items"][0]["subcareers"][0]
print(f'  id: {cleaned_sub["id"]}')
print(f'  name: {cleaned_sub["name"]}')
print(f'  keywords: {cleaned_sub["keywords"][:80]}...')
print(f'  location (first college): {cleaned_sub["colleges_india"][0]["location"]}')
print(f'  after_graduation: {cleaned_sub["career_paths"][2]["after_graduation"]}')
print(f'  entrance_exams count: {len(cleaned_sub["entrance_exams"])}')
print()

# Show upskilling courses before/after
with open('D:/Data_Cleanning_Pipeline/data/raw/swayam.json', encoding='utf-8') as f:
    raw_up = json.load(f)
with open('D:/Data_Cleanning_Pipeline/data/cleaned/upskilling_courses.json', encoding='utf-8') as f:
    cleaned_up = json.load(f)

print('=== UPSKILLING COURSE BEFORE/AFTER ===')
print()
print('RAW (first course):')
raw_course = raw_up["items"][0]
print(f'  course_name: {raw_course["course_name"]}')
print(f'  url: {raw_course["url"]}')
print(f'  source: {raw_course["source"]}')
print(f'  institute: {raw_course["institute"]}')
print(f'  course_duration: {raw_course["course_duration"]}')
print(f'  difficulty_level: {raw_course["difficulty_level"]}')
print(f'  academic_level: {raw_course["academic_level"]}')
print(f'  language: {raw_course["language"]}')
print()
print('CLEANED (first course):')
c = cleaned_up["items"][0]
print(f'  course_name: {c["course_name"]}')
print(f'  url: {c["url"]}')
print(f'  source: {c["source"]}')
print(f'  institute: {c["institute"]}')
print(f'  course_duration: {c["course_duration"]}')
print(f'  course_duration_weeks: {c["course_duration_weeks"]}')
print(f'  difficulty_level: {c["difficulty_level"]}')
print(f'  academic_level: {c["academic_level"]}')
print(f'  language: {c["language"]}')
print(f'  metadata: {c.get("metadata", "N/A")}')