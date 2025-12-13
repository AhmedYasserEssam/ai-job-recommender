"""
Smart CV Section Extractor
==========================
Extracts structured information from CVs by identifying sections:
- Skills (from Skills/Technical Skills section)
- Years of Experience
- Summary/About section
"""

import re
import fitz  # PyMuPDF for PDF
from docx import Document  # python-docx for DOCX
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple


# ============================================================================
# SECTION HEADER PATTERNS (Common CV section names)
# ============================================================================

SECTION_PATTERNS = {
    "skills": [
        r"(?i)^[\s]*(?:technical\s+)?skills[\s]*:?[\s]*$",
        r"(?i)^[\s]*core\s+(?:competencies|skills)[\s]*:?[\s]*$",
        r"(?i)^[\s]*(?:key\s+)?technologies[\s]*:?[\s]*$",
        r"(?i)^[\s]*technical\s+(?:proficiency|expertise)[\s]*:?[\s]*$",
        r"(?i)^[\s]*areas\s+of\s+expertise[\s]*:?[\s]*$",
        r"(?i)^[\s]*tools?\s*(?:&|and)?\s*technologies[\s]*:?[\s]*$",
        r"(?i)^[\s]*programming\s+(?:languages|skills)[\s]*:?[\s]*$",
    ],
    "summary": [
        r"(?i)^[\s]*(?:professional\s+)?summary[\s]*:?[\s]*$",
        r"(?i)^[\s]*(?:career\s+)?objective[\s]*:?[\s]*$",
        r"(?i)^[\s]*about\s*(?:me)?[\s]*:?[\s]*$",
        r"(?i)^[\s]*profile[\s]*:?[\s]*$",
        r"(?i)^[\s]*(?:executive\s+)?overview[\s]*:?[\s]*$",
        r"(?i)^[\s]*personal\s+statement[\s]*:?[\s]*$",
        r"(?i)^[\s]*introduction[\s]*:?[\s]*$",
    ],
    "experience": [
        r"(?i)^[\s]*(?:work\s+)?experience[\s]*:?[\s]*$",
        r"(?i)^[\s]*(?:professional\s+)?experience[\s]*:?[\s]*$",
        r"(?i)^[\s]*employment\s+(?:history|record)[\s]*:?[\s]*$",
        r"(?i)^[\s]*work\s+history[\s]*:?[\s]*$",
        r"(?i)^[\s]*career\s+history[\s]*:?[\s]*$",
    ],
    "education": [
        r"(?i)^[\s]*education[\s]*:?[\s]*$",
        r"(?i)^[\s]*academic\s+(?:background|qualifications)[\s]*:?[\s]*$",
        r"(?i)^[\s]*qualifications[\s]*:?[\s]*$",
    ],
    "projects": [
        r"(?i)^[\s]*projects?[\s]*:?[\s]*$",
        r"(?i)^[\s]*(?:key\s+)?projects?[\s]*:?[\s]*$",
        r"(?i)^[\s]*personal\s+projects?[\s]*:?[\s]*$",
    ],
    "certifications": [
        r"(?i)^[\s]*certifications?[\s]*:?[\s]*$",
        r"(?i)^[\s]*licenses?\s*(?:&|and)?\s*certifications?[\s]*:?[\s]*$",
        r"(?i)^[\s]*professional\s+certifications?[\s]*:?[\s]*$",
    ],
}

# All section keywords for boundary detection
ALL_SECTION_KEYWORDS = [
    "skills", "technical skills", "core competencies", "technologies",
    "summary", "objective", "about", "profile", "overview",
    "experience", "work experience", "professional experience", "employment",
    "education", "academic", "qualifications",
    "projects", "personal projects",
    "certifications", "licenses",
    "achievements", "awards", "honors",
    "languages", "interests", "hobbies",
    "references", "publications", "courses"
]


@dataclass
class CVData:
    """Structured CV data container."""
    raw_text: str
    skills: List[str]
    skills_raw: str  # Raw skills section text
    summary: str
    total_experience_years: float  # 0 if not determined
    experience_details: List[Dict]
    sections_found: List[str]


# ============================================================================
# TEXT EXTRACTION
# ============================================================================

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF with layout preservation."""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            # Use "text" extraction with preserved layout
            text += page.get_text("text") + "\n"
        doc.close()
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error extracting PDF: {e}")


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        doc = Document(file_path)
        text_parts = []
        
        # Extract from paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        # Extract from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    if cell.text.strip():
                        row_text.append(cell.text.strip())
                if row_text:
                    text_parts.append(" | ".join(row_text))
        
        return "\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Error extracting DOCX: {e}")


def extract_text(file_path: str) -> str:
    """Extract text from CV file (PDF or DOCX)."""
    file_path_lower = file_path.lower()
    
    if file_path_lower.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path_lower.endswith('.docx'):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported format. Only .pdf and .docx are supported.")


# ============================================================================
# SECTION DETECTION & EXTRACTION
# ============================================================================

def find_section_boundaries(text: str) -> List[Tuple[str, int, int]]:
    """
    Find all section headers and their positions in the text.
    Returns list of (section_type, start_pos, end_pos).
    """
    lines = text.split('\n')
    sections = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # Check each section type
        for section_type, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, line_stripped):
                    # Calculate character position
                    char_pos = sum(len(l) + 1 for l in lines[:i])
                    sections.append((section_type, i, char_pos))
                    break
    
    return sections


def extract_section_content(text: str, section_type: str) -> str:
    """
    Extract content of a specific section from CV text.
    Finds the section header and extracts until the next section.
    """
    lines = text.split('\n')
    
    # Find where our target section starts
    section_start = None
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        for pattern in SECTION_PATTERNS.get(section_type, []):
            if re.match(pattern, line_stripped):
                section_start = i + 1  # Content starts after header
                break
        if section_start:
            break
    
    if section_start is None:
        return ""
    
    # Find where the next section starts (end of our section)
    section_end = len(lines)
    for i in range(section_start, len(lines)):
        line_stripped = lines[i].strip()
        if not line_stripped:
            continue
            
        # Check if this line is a section header
        is_header = False
        for patterns in SECTION_PATTERNS.values():
            for pattern in patterns:
                if re.match(pattern, line_stripped):
                    is_header = True
                    break
            if is_header:
                break
        
        # Also check for common section-like headers by format
        # (All caps, ends with colon, short line that looks like a header)
        if not is_header:
            if (line_stripped.isupper() and len(line_stripped) < 50 and 
                any(kw in line_stripped.lower() for kw in ALL_SECTION_KEYWORDS)):
                is_header = True
        
        if is_header:
            section_end = i
            break
    
    # Extract and clean the content
    content_lines = lines[section_start:section_end]
    content = '\n'.join(line for line in content_lines if line.strip())
    
    return content.strip()


# ============================================================================
# SKILLS EXTRACTION
# ============================================================================

def parse_skills_from_section(skills_text: str) -> List[str]:
    """
    Parse individual skills from the skills section text.
    Handles various formats: comma-separated, bullet points, pipes, etc.
    """
    if not skills_text:
        return []
    
    skills = []
    
    # Common delimiters in skills sections
    # Split by common separators
    delimiters = r'[,;|•·▪▸►➤✓✔★●○◦\n\t]|\s{2,}|(?<=[a-z])(?=[A-Z])'
    
    # First, try to handle category-based skills (e.g., "Languages: Python, Java")
    category_pattern = r'([A-Za-z\s&/]+):\s*(.+?)(?=(?:[A-Za-z\s&/]+:|$))'
    category_matches = re.findall(category_pattern, skills_text, re.DOTALL)
    
    if category_matches:
        # Has categories like "Programming: Python, Java"
        for category, skill_list in category_matches:
            parts = re.split(r'[,;|•·\n]+', skill_list)
            for part in parts:
                cleaned = part.strip()
                if cleaned and len(cleaned) > 1 and len(cleaned) < 50:
                    skills.append(cleaned)
    else:
        # Simple list of skills
        parts = re.split(delimiters, skills_text)
        for part in parts:
            cleaned = part.strip().strip('-').strip('•').strip()
            # Filter out noise
            if cleaned and len(cleaned) > 1 and len(cleaned) < 50:
                # Skip if it looks like a sentence (has too many spaces)
                if cleaned.count(' ') < 5:
                    skills.append(cleaned)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_skills = []
    for skill in skills:
        skill_lower = skill.lower()
        if skill_lower not in seen:
            seen.add(skill_lower)
            unique_skills.append(skill)
    
    return unique_skills


# ============================================================================
# EXPERIENCE EXTRACTION
# ============================================================================

def extract_experience_from_summary(summary_text: str) -> Tuple[Optional[float], List[Dict]]:
    """
    Extract years of experience from summary/about section only.
    Returns (years, details) if found explicitly in summary, else (None, []).
    """
    if not summary_text:
        return None, []
    
    experience_details = []
    summary_lower = summary_text.lower()
    
    # Patterns for explicit year mentions in summary
    patterns = [
        # "5+ years of experience" / "5 years experience"
        r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)',
        
        # "experience of 5 years"
        r'(?:experience|exp)(?:\s+of)?\s+(\d+)\+?\s*(?:years?|yrs?)',
        
        # "worked for 5 years"
        r'worked\s+(?:for\s+)?(\d+)\+?\s*(?:years?|yrs?)',
        
        # "5 years as a developer"
        r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:as\s+)?(?:a\s+)?[a-zA-Z\s]+(?:developer|engineer|analyst|scientist|manager)',
        
        # "over 5 years"
        r'over\s+(\d+)\s*(?:years?|yrs?)',
    ]
    
    total_years = 0
    for pattern in patterns:
        matches = re.findall(pattern, summary_lower, re.IGNORECASE)
        for match in matches:
            years = int(match) if isinstance(match, str) else int(match[0])
            experience_details.append({
                "type": "explicit_mention_summary",
                "years": years,
                "context": match
            })
            total_years = max(total_years, years)
    
    return (total_years, experience_details) if total_years > 0 else (None, [])


def extract_experience_from_dates(experience_text: str) -> Tuple[Optional[float], List[Dict]]:
    """
    Extract years of experience from experience section date ranges.
    - If "present" found: present_date - min_start_date
    - Otherwise: max_end_date - min_start_date
    """
    if not experience_text:
        return None, []
    
    experience_details = []
    text_lower = experience_text.lower()
    
    # Date range pattern: "Jan 2019 - Present" or "2019 - 2023"
    date_pattern = r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?\.?\s*(\d{4})\s*[-–—to]+\s*((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?\.?\s*(\d{4})|present|current|now)'
    
    date_matches = re.findall(date_pattern, text_lower, re.IGNORECASE)
    
    if not date_matches:
        return None, []
    
    current_year = 2025  # Update as needed
    start_years = []
    end_years = []
    has_present = False
    
    for match in date_matches:
        start_year = int(match[0])
        end_part = match[1].strip()
        
        # Check if end date is "present", "current", or "now"
        if any(word in end_part.lower() for word in ['present', 'current', 'now']):
            has_present = True
            end_year = current_year
        else:
            # Extract the year from the end part
            year_match = re.search(r'(\d{4})', end_part)
            if year_match:
                end_year = int(year_match.group(1))
            else:
                continue  # Skip if no valid end year
        
        # Sanity check
        if 1950 < start_year <= current_year and 1950 < end_year <= current_year:
            start_years.append(start_year)
            end_years.append(end_year)
            experience_details.append({
                "type": "date_range",
                "start": start_year,
                "end": end_year if not has_present else "present",
                "years": end_year - start_year
            })
    
    if not start_years:
        return None, []
    
    min_start = min(start_years)
    
    # Calculate total experience
    if has_present:
        # present_date - min_start_date
        total_years = current_year - min_start
    else:
        # max_end_date - min_start_date
        max_end = max(end_years)
        total_years = max_end - min_start
    
    return total_years if total_years > 0 else None, experience_details


def extract_years_of_experience(summary_text: str, experience_text: str) -> Tuple[float, List[Dict]]:
    """
    Extract years of experience using the two-part strategy:
    1. If experience is mentioned in summary, use that only
    2. Otherwise, calculate from experience section dates:
       - If "present" found: present_date - min_date
       - Otherwise: max_date - min_date
    
    If experience cannot be determined, returns 0.
    
    Args:
        summary_text: Content of the summary/about section
        experience_text: Content of the experience section
    
    Returns:
        Tuple of (total_years, experience_details)
    """
    # Part 1: Check summary for explicit experience mention
    summary_years, summary_details = extract_experience_from_summary(summary_text)
    
    if summary_years is not None:
        return summary_years, summary_details
    
    # Part 2: Calculate from experience section dates
    exp_years, exp_details = extract_experience_from_dates(experience_text)
    
    # Return 0 if experience could not be determined
    return (exp_years if exp_years is not None else 0), exp_details


# ============================================================================
# MAIN EXTRACTION FUNCTION
# ============================================================================

def extract_cv_data(file_path: str) -> CVData:
    """
    Main function to extract structured data from a CV.
    
    Args:
        file_path: Path to the CV file (.pdf or .docx)
    
    Returns:
        CVData object with extracted information
    """
    # Extract raw text
    raw_text = extract_text(file_path)
    print(raw_text[:2000])  # Print first 2000 chars to see the structure
    # Find which sections exist
    section_boundaries = find_section_boundaries(raw_text)
    sections_found = list(set(s[0] for s in section_boundaries))
    
    # Extract Skills Section
    skills_raw = extract_section_content(raw_text, "skills")
    skills = parse_skills_from_section(skills_raw)
    
    # Extract Summary/About Section
    summary = extract_section_content(raw_text, "summary")
    
    # Extract Experience Section
    experience_section = extract_section_content(raw_text, "experience")
    
    # Extract Experience using two-part strategy:
    # 1. Check summary first, 2. Calculate from experience dates
    total_exp, exp_details = extract_years_of_experience(summary, experience_section)
    
    return CVData(
        raw_text=raw_text,
        skills=skills,
        skills_raw=skills_raw,
        summary=summary,
        total_experience_years=total_exp,
        experience_details=exp_details,
        sections_found=sections_found
    )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_cv_data(cv_data: CVData):
    """Pretty print extracted CV data."""
    print("=" * 60)
    print("CV EXTRACTION RESULTS")
    print("=" * 60)
    
    print(f"\n📋 SECTIONS FOUND: {', '.join(cv_data.sections_found) if cv_data.sections_found else 'None detected'}")
    
    print(f"\n📝 SUMMARY/ABOUT:")
    print("-" * 40)
    if cv_data.summary:
        print(cv_data.summary[:500] + "..." if len(cv_data.summary) > 500 else cv_data.summary)
    else:
        print("No summary section found")
    
    print(f"\n💼 SKILLS ({len(cv_data.skills)} found):")
    print("-" * 40)
    if cv_data.skills:
        # Print in columns
        for i, skill in enumerate(cv_data.skills):
            print(f"  • {skill}")
    else:
        print("No skills section found")
    
    print(f"\n⏱️ EXPERIENCE:")
    print("-" * 40)
    print(f"  Total Years: {cv_data.total_experience_years}")
    
    if cv_data.experience_details:
        print("\n  Details found:")
        for detail in cv_data.experience_details[:5]:  # Show first 5
            if detail["type"] == "date_range":
                print(f"    • {detail['start']} - {detail['end']} ({detail['years']} years)")
            else:
                print(f"    • {detail['years']} years mentioned")
    
    print("\n" + "=" * 60)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Test with your CV
    cv_path = r"C:\Work\Ai Project\Ahmed_Emad_DataScientist.pdf"
    
    try:
        cv_data = extract_cv_data(cv_path)
        print_cv_data(cv_data)
        
        # Access individual fields
        print("\n\n--- PROGRAMMATIC ACCESS ---")
        print(f"Skills list: {cv_data.skills}")
        print(f"Experience: {cv_data.total_experience_years} years")
        print(f"Summary: {cv_data.summary[:100]}..." if cv_data.summary else "No summary")
        
    except Exception as e:
        print(f"Error: {e}")