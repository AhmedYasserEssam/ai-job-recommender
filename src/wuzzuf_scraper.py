import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import time


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


def scrape_job_listings(job_name: str, page_limit: int = 1) -> pd.DataFrame:
    rows = []

    if page_limit <= 0:
        return pd.DataFrame(rows)

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
                row = {'Job Search': job_name}

                title_elem = card.find("h2", class_="css-193uk2c")
                row['Job Title'] = title_elem.text.strip() if title_elem else "N/A"

                company_elem = card.find("a", class_="css-ipsyv7")
                row['Company'] = company_elem.text.strip() if company_elem else "N/A"

                location_elem = card.find("span", class_="css-16x61xq")
                if location_elem:
                    loc_parts = location_elem.text.split(',')
                    row['Country'] = loc_parts[-1].strip() if len(loc_parts) > 0 else "N/A"
                    row['City'] = loc_parts[0].strip() if len(loc_parts) > 0 else "N/A"
                    row['Area'] = loc_parts[1].strip() if len(loc_parts) > 1 else "N/A"
                else:
                    row['Country'] = "N/A"
                    row['City'] = "N/A"
                    row['Area'] = "N/A"

                publish_elem = card.select_one("div[class*='css-eg55jf']")
                row['Publish Date'] = publish_elem.get_text(strip=True) if publish_elem else "N/A"

                link_elem = card.find("a", class_="css-o171kl")
                row['Job Link'] = link_elem.get('href') if link_elem else "N/A"

                type_elem = card.find("span", class_="css-uc9rga eoyjyou0")
                row['Job Type'] = type_elem.text.strip() if type_elem else "N/A"

                workplace_elem = card.select_one("span[class*='css-uofntu eoyjyou0']")
                row['Work Place'] = workplace_elem.get_text(strip=True) if workplace_elem else "N/A"

                rows.append(row)
            except Exception as e:
                print(f"Error processing job card for {row.get('Job Link', '[Link not available]')}: {e}")
                continue

    df = pd.DataFrame(rows)
    return df


def scrape_job_details(df: pd.DataFrame) -> pd.DataFrame:
    with open("src/utils/job_details_extractor.js", "r", encoding="utf-8") as f:
        extract_script = f.read() + "\nreturn extractJobDetails();"

    if df.empty:
        return df

    df['Salary'] = "N/A"
    df['Experience Needed'] = "N/A"
    df['Career Level'] = "N/A"
    df['Education Level'] = "N/A"
    df['Job Categories'] = "N/A"
    df['Skills'] = "N/A"
    df['Job Requirements'] = "N/A"

    driver = None
    created_driver = False

    try:
        try:
            driver = create_chrome_driver()
            created_driver = True
        except RuntimeError as e:
            raise RuntimeError("Chrome WebDriver error while creating driver.") from e

        for i, row in df.iterrows():
            link = row.get('Job Link', 'N/A')

            if not link or link == 'N/A':
                continue

            try:
                driver.get(link)
                time.sleep(2)

                data = driver.execute_script(extract_script)

                if not isinstance(data, dict):
                    print(f"Unexpected data format for {link}")
                    continue

                df.at[i, 'Experience Needed'] = data.get('experience', 'N/A')
                df.at[i, 'Career Level'] = data.get('careerLevel', 'N/A')
                df.at[i, 'Education Level'] = data.get('education', 'N/A')
                df.at[i, 'Salary'] = data.get('salary', 'N/A')
                df.at[i, 'Job Categories'] = data.get('categories', 'N/A')
                df.at[i, 'Skills'] = data.get('skills', 'N/A')
                df.at[i, 'Job Requirements'] = data.get('requirements', 'N/A')
            except Exception as e:
                print(f"Error extracting details for {link}: {e}")
                continue

        return df
    finally:
        if created_driver and driver is not None:
            try:
                driver.quit()
            except Exception as e:
                pass


def scrape_jobs(job_name: str, page_limit: int = 1, save_csv: bool = True) -> pd.DataFrame:   
    try:
        df = scrape_job_listings(job_name.strip(), page_limit)
    except Exception as e:
        raise RuntimeError(f"Failed to scrape listings for '{job_name}'.") from e

    try:
        df = scrape_job_details(df)
    except Exception as e:
        raise RuntimeError(f"Failed to scrape job details for listings of '{job_name}'.") from e

    if save_csv:
        try:
            df.to_csv("scraped_jobs.csv", index=False, encoding='utf-8-sig')
        except Exception as e:
            raise RuntimeError("Failed to save scraped jobs to CSV.") from e

    return df