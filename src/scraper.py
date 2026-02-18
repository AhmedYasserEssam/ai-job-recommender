import logging
import os
import time
import urllib.parse
from typing import List

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

from models import Job, parse_experience, parse_salary, parse_list

log = logging.getLogger(__name__)

_BASE_URL = "https://wuzzuf.net"

_JS_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "utils", "job_details_extractor.js")


def _create_chrome_driver(timeout: int = 30) -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(timeout)
        return driver
    except WebDriverException as e:
        raise RuntimeError("Failed to start Chrome WebDriver.") from e


def _scrape_listings(job_name: str, page_limit: int = 1) -> List[Job]:
    jobs: List[Job] = []

    for page in range(page_limit):
        parsed_job = urllib.parse.quote(job_name)
        url = (
            f"https://wuzzuf.net/search/jobs/"
            f"?a=navbg%7Cspbg&filters%5Bcountry%5D%5B0%5D=Egypt"
            f"&q={parsed_job}&start={page}"
        )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Request error while fetching {url}") from e

        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            job_cards = soup.find_all('div', class_='css-ghe2tq e1v1l3u10')
        except Exception as e:
            raise RuntimeError(f"Parsing error while parsing response from {url}") from e

        if not job_cards:
            break

        for card in job_cards:
            try:
                job = Job(job_search=job_name)

                title_elem = card.find("h2", class_="css-193uk2c")
                job.title = title_elem.text.strip() if title_elem else "N/A"

                company_elem = card.find("a", class_="css-ipsyv7")
                job.company = company_elem.text.strip().rstrip(" -") if company_elem else "N/A"

                location_elem = card.find("span", class_="css-16x61xq")
                if location_elem:
                    loc_parts = location_elem.text.split(',')
                    job.country = loc_parts[-1].strip() if loc_parts else "N/A"
                    job.city = loc_parts[0].strip() if loc_parts else "N/A"
                    job.area = loc_parts[1].strip() if len(loc_parts) > 1 else "N/A"

                link_elem = card.find("a", class_="css-o171kl")
                href = link_elem.get('href', '') if link_elem else ""
                if href and not href.startswith("http"):
                    href = _BASE_URL + href
                job.link = href or "N/A"

                type_elem = card.find("span", class_="css-uc9rga eoyjyou0")
                job.job_type = type_elem.text.strip() if type_elem else "N/A"

                workplace_elem = card.select_one("span[class*='css-uofntu eoyjyou0']")
                job.work_place = workplace_elem.get_text(strip=True) if workplace_elem else "N/A"

                jobs.append(job)
            except Exception as e:
                log.warning("Error processing job card: %s", e)
                continue

    log.info("Scraped %d listings for '%s'", len(jobs), job_name)
    return jobs


def _scrape_details(jobs: List[Job]) -> List[Job]:
    with open(_JS_SCRIPT_PATH, "r", encoding="utf-8") as f:
        extract_script = f.read() + "\nreturn extractJobDetails();"

    if not jobs:
        return jobs

    driver = None
    try:
        driver = _create_chrome_driver()

        for i, job in enumerate(jobs):
            if not job.link or job.link == "N/A":
                continue
            try:
                log.info("Extracting details [%d/%d]: %s", i + 1, len(jobs), job.title)
                driver.get(job.link)
                time.sleep(2)
                data = driver.execute_script(extract_script)

                if not isinstance(data, dict):
                    log.warning("Unexpected data format for %s", job.link)
                    continue

                job.experience_needed = parse_experience(data.get('experience', 'N/A'))
                job.career_level = data.get('careerLevel', 'N/A')
                job.education_level = data.get('education', 'N/A')
                job.salary = parse_salary(data.get('salary', 'N/A'))
                job.categories = parse_list(data.get('categories', 'N/A'))
                job.skills = parse_list(data.get('skills', 'N/A'))
                job.requirements = data.get('requirements', 'N/A')
                log.info("  -> skills=%s, exp=%s", job.skills[:3], job.experience_needed)
            except Exception as e:
                log.warning("Error extracting details for %s: %s", job.link, e)
                continue

        return jobs
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


def scrape_jobs(job_name: str, page_limit: int = 1) -> List[Job]:
    try:
        jobs = _scrape_listings(job_name.strip(), page_limit)
    except Exception as e:
        raise RuntimeError(f"Failed to scrape listings for '{job_name}'.") from e

    try:
        jobs = _scrape_details(jobs)
    except Exception as e:
        raise RuntimeError(f"Failed to scrape job details for '{job_name}'.") from e

    return jobs
