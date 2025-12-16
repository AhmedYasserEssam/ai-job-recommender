import requests
from bs4 import BeautifulSoup
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import time
from typing import List

from job import Job, parse_experience, parse_salary, parse_list


def create_chrome_driver(timeout: int = 30) -> webdriver.Chrome:
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
        raise RuntimeError(
            "Failed to start Chrome WebDriver."
        ) from e


def scrape_job_listings(job_name: str, page_limit: int = 1) -> List[Job]:
    jobs = []

    if page_limit <= 0:
        return jobs

    for page in range(0, page_limit):
        parsed_job = urllib.parse.quote(job_name)
        url = f'https://wuzzuf.net/search/jobs/?a=navbg%7Cspbg&filters%5Bcountry%5D%5B0%5D=Egypt&q={parsed_job}&start={page}'

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
                    job.country = loc_parts[-1].strip() if len(loc_parts) > 0 else "N/A"
                    job.city = loc_parts[0].strip() if len(loc_parts) > 0 else "N/A"
                    job.area = loc_parts[1].strip() if len(loc_parts) > 1 else "N/A"

                link_elem = card.find("a", class_="css-o171kl")
                job.link = link_elem.get('href') if link_elem else "N/A"

                type_elem = card.find("span", class_="css-uc9rga eoyjyou0")
                job.job_type = type_elem.text.strip() if type_elem else "N/A"

                workplace_elem = card.select_one("span[class*='css-uofntu eoyjyou0']")
                job.work_place = workplace_elem.get_text(strip=True) if workplace_elem else "N/A"

                jobs.append(job)
            except Exception as e:
                print(f"Error processing job card: {e}")
                continue

    return jobs


def scrape_job_details(jobs: List[Job]) -> List[Job]:
    with open("src/utils/job_details_extractor.js", "r", encoding="utf-8") as f:
        extract_script = f.read() + "\nreturn extractJobDetails();"

    if not jobs:
        return jobs

    driver = None
    created_driver = False

    try:
        try:
            driver = create_chrome_driver()
            created_driver = True
        except RuntimeError as e:
            raise RuntimeError("Chrome WebDriver error while creating driver.") from e

        for job in jobs:
            if not job.link or job.link == 'N/A':
                continue

            try:
                driver.get(job.link)
                time.sleep(2)

                data = driver.execute_script(extract_script)

                if not isinstance(data, dict):
                    print(f"Unexpected data format for {job.link}")
                    continue

                job.experience_needed = parse_experience(data.get('experience', 'N/A'))
                job.career_level = data.get('careerLevel', 'N/A')
                job.education_level = data.get('education', 'N/A')
                job.salary = parse_salary(data.get('salary', 'N/A'))
                job.categories = parse_list(data.get('categories', 'N/A'))
                job.skills = parse_list(data.get('skills', 'N/A'))
                job.requirements = data.get('requirements', 'N/A')
            except Exception as e:
                print(f"Error extracting details for {job.link}: {e}")
                continue

        return jobs
    finally:
        if created_driver and driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


def scrape_jobs(job_name: str, page_limit: int = 1) -> List[Job]:
    try:
        jobs = scrape_job_listings(job_name.strip(), page_limit)
    except Exception as e:
        raise RuntimeError(f"Failed to scrape listings for '{job_name}'.") from e

    try:
        jobs = scrape_job_details(jobs)
    except Exception as e:
        raise RuntimeError(f"Failed to scrape job details for listings of '{job_name}'.") from e

    return jobs