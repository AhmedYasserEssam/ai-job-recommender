from dataclasses import dataclass, field
from typing import List, Union
import re


@dataclass
class Job:
    job_search: str = "N/A"
    title: str = "N/A"
    company: str = "N/A"
    country: str = "N/A"
    city: str = "N/A"
    area: str = "N/A"
    link: str = "N/A"
    job_type: str = "N/A"
    work_place: str = "N/A"
    salary: Union[int, str] = "N/A"
    experience_needed: int = 0
    career_level: str = "N/A"
    education_level: str = "N/A"
    categories: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    requirements: str = "N/A"

    
def parse_experience(exp_str: str) -> int:
    if not exp_str or exp_str == "N/A":
        return 0
    
    match = re.search(r'(\d+)', exp_str)
    if match:
        return int(match.group(1))
    return 0


def parse_salary(salary_str: str) -> Union[int, str]:
    if not salary_str or salary_str == "N/A":
        return "N/A"
    
    cleaned = salary_str.replace(",", "").replace(" ", "")
    match = re.search(r'(\d+)', cleaned)
    if match:
        return int(match.group(1))
    return salary_str


def parse_list(value_str: str, delimiter: str = " | ") -> List[str]:
    if not value_str or value_str == "N/A":
        return []
    
    return [item.strip() for item in value_str.split(delimiter) if item.strip()]