import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

job_names = []  # Will be set by user input

# create needed lists
# these ones for the data within the jobs search page
job_title = []
company_name = []
country = []
city = []
area = []
links = []
date = []
job_type = []
work_place = []
job_searched = []

# these ones for each job's link (detailed info)
Salary = []
Experience_Needed = []
Career_Level = []
Education_Level = []
Job_Categories = []
Skills = []
Job_Requirements = []

jobs_df = None



def scrape_job_listings():
    """Scrape basic job info from search results pages"""
    for job_name in job_names:
        print(f"\n--- Scraping listings for: {job_name} ---")
        for page in range(0, 1):
            parsed_job = urllib.parse.quote(job_name)
            url = f'https://wuzzuf.net/search/jobs/?a=navbg%7Cspbg&filters%5Bcountry%5D%5B0%5D=Egypt&q={parsed_job}&start={page}'
            
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                job_cards = soup.find_all('div', class_='css-ghe2tq e1v1l3u10')
                
                if not job_cards:
                    print(f"No more jobs found on page {page}")
                    break
                
                for card in job_cards:
                    # Job Title
                    title_elem = card.find("h2", class_="css-193uk2c")
                    job_title.append(title_elem.text.strip() if title_elem else "N/A")
                    
                    # Company Name
                    company_elem = card.find("a", class_="css-ipsyv7")
                    company_name.append(company_elem.text.strip() if company_elem else "N/A")
                    
                    # Location
                    location_elem = card.find("span", class_="css-16x61xq")
                    if location_elem:
                        loc_parts = location_elem.text.split(',')
                        country.append(loc_parts[-1].strip() if len(loc_parts) > 0 else "N/A")
                        city.append(loc_parts[0].strip() if len(loc_parts) > 0 else "N/A")
                        area.append(loc_parts[1].strip() if len(loc_parts) > 1 else "N/A")
                    else:
                        country.append("N/A")
                        city.append("N/A")
                        area.append("N/A")
                    
                    # Publish Date
                    publish_elem = card.select_one("div[class*='css-eg55jf']")
                    date.append(publish_elem.get_text(strip=True) if publish_elem else "N/A")
                    
                    # Job Link
                    link_elem = card.find("a", class_="css-o171kl")
                    links.append(link_elem.get('href') if link_elem else "N/A")
                    
                    # Job Type
                    type_elem = card.find("span", class_="css-uc9rga eoyjyou0")
                    job_type.append(type_elem.text.strip() if type_elem else "N/A")
                    
                    # Work Place
                    workplace_elem = card.select_one("span[class*='css-uofntu eoyjyou0']")
                    work_place.append(workplace_elem.get_text(strip=True) if workplace_elem else "N/A")
                    
                    # Track which job search this came from
                    job_searched.append(job_name)
                
                print(f"Page {page + 1}: Found {len(job_cards)} jobs")
                
            except Exception as e:
                print(f"Error on page {page}: {e}")
                continue
    
    print(f"\nTotal jobs found: {len(job_title)}")


def scrape_job_details():
    """Scrape detailed info from each job's individual page using Selenium with JavaScript"""
    print("\n--- Scraping detailed job information ---")
    
    # JavaScript to extract all job details reliably
    extract_script = """
    const result = {
        experience: 'N/A',
        careerLevel: 'N/A',
        education: 'N/A',
        salary: 'N/A',
        categories: 'N/A',
        skills: 'N/A',
        requirements: 'N/A'
    };
    
    // Get Job Details section
    const jobDetailsH2 = Array.from(document.querySelectorAll('h2')).find(h => h.textContent.includes('Job Details'));
    if (jobDetailsH2) {
        const section = jobDetailsH2.parentElement;
        const allDivs = section.querySelectorAll('div');
        
        for (const div of allDivs) {
            const text = div.textContent.trim();
            
            if (text.startsWith('Experience Needed:')) {
                const children = div.querySelectorAll('*');
                for (const child of children) {
                    const childText = child.textContent.trim();
                    if (childText && !childText.includes(':') && childText !== text) {
                        result.experience = childText;
                        break;
                    }
                }
            }
            
            if (text.startsWith('Career Level:')) {
                const children = div.querySelectorAll('*');
                for (const child of children) {
                    const childText = child.textContent.trim();
                    if (childText && !childText.includes(':') && childText !== text) {
                        result.careerLevel = childText;
                        break;
                    }
                }
            }
            
            if (text.startsWith('Education Level:')) {
                const children = div.querySelectorAll('*');
                for (const child of children) {
                    const childText = child.textContent.trim();
                    if (childText && !childText.includes(':') && childText !== text) {
                        result.education = childText;
                        break;
                    }
                }
            }
            
            if (text.startsWith('Salary:')) {
                const children = div.querySelectorAll('*');
                for (const child of children) {
                    const childText = child.textContent.trim();
                    if (childText && !childText.includes(':') && childText !== text) {
                        result.salary = childText;
                        break;
                    }
                }
            }
        }
        
        // Job Categories
        const catLabel = Array.from(section.querySelectorAll('*')).find(el => 
            el.childNodes.length === 1 && el.textContent.trim() === 'Job Categories:'
        );
        if (catLabel) {
            const list = catLabel.nextElementSibling;
            if (list) {
                const cats = Array.from(list.querySelectorAll('a')).map(a => a.textContent.trim());
                result.categories = cats.length > 0 ? cats.join(' | ') : 'N/A';
            }
        }
    }
    
    // Skills And Tools
    const skillsHeading = Array.from(document.querySelectorAll('h4')).find(h => h.textContent.includes('Skills'));
    if (skillsHeading) {
        const container = skillsHeading.nextElementSibling;
        if (container) {
            const allSkills = Array.from(container.querySelectorAll('a')).map(a => a.textContent.trim());
            const uniqueSkills = [...new Set(allSkills)];
            result.skills = uniqueSkills.length > 0 ? uniqueSkills.join(' | ') : 'N/A';
        }
    }
    
    // Job Requirements
    const reqHeading = Array.from(document.querySelectorAll('h2')).find(h => h.textContent.includes('Job Requirements'));
    if (reqHeading) {
        const reqSection = reqHeading.nextElementSibling;
        if (reqSection) {
            result.requirements = reqSection.textContent.trim().substring(0, 500) || 'N/A';
        }
    }
    
    return result;
    """
    
    # Initialize Chrome driver
    driver = webdriver.Chrome()
    driver.set_page_load_timeout(30)
    
    for i, link in enumerate(links):
        if link == "N/A":
            # Append N/A for all detail fields
            Salary.append("N/A")
            Experience_Needed.append("N/A")
            Career_Level.append("N/A")
            Education_Level.append("N/A")
            Job_Categories.append("N/A")
            Skills.append("N/A")
            Job_Requirements.append("N/A")
            continue
            
        try:
            driver.get(link)
            time.sleep(2)  # Wait for page to load
            
            # Execute JavaScript to extract all data
            data = driver.execute_script(extract_script)
            
            Experience_Needed.append(data.get('experience', 'N/A'))
            Career_Level.append(data.get('careerLevel', 'N/A'))
            Education_Level.append(data.get('education', 'N/A'))
            Salary.append(data.get('salary', 'N/A'))
            Job_Categories.append(data.get('categories', 'N/A'))
            Skills.append(data.get('skills', 'N/A'))
            Job_Requirements.append(data.get('requirements', 'N/A'))
            
            print(f"Scraped job {i + 1}/{len(links)}: {job_title[i][:30]}...")
            
        except Exception as e:
            print(f"Job {i + 1} page error: {e}")
            Experience_Needed.append("N/A")
            Career_Level.append("N/A")
            Education_Level.append("N/A")
            Salary.append("N/A")
            Job_Categories.append("N/A")
            Skills.append("N/A")
            Job_Requirements.append("N/A")
    
    driver.quit()
    print("Detailed scraping complete!")


def save_to_csv():
    """Save all scraped data to CSV"""
    df = pd.DataFrame({
        'Job Search': job_searched,
        'Job Title': job_title,
        'Company': company_name,
        'Country': country,
        'City': city,
        'Area': area,
        'Publish Date': date,
        'Job Link': links,
        'Job Type': job_type,
        'Work Place': work_place,
        'Salary': Salary,
        'Experience Needed': Experience_Needed,
        'Career Level': Career_Level,
        'Education Level': Education_Level,
        'Job Categories': Job_Categories,
        'Skills': Skills,
        'Job Requirements': Job_Requirements
    })
    
    file_path = "wuzzuf_jobs_data.csv"
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"\nData saved to {file_path}")
    print(f"Total records: {len(df)}")
    return df


def initializeJobData():
    user_input = input("Enter job title(s): ").strip()
    
    if not user_input:
        print("No job titles entered. Exiting.")
        exit()
    
    # Parse user input - split by comma and clean up
    job_names = [job.strip() for job in user_input.split(",") if job.strip()]
    
    # Step 1: Scrape job listings from search pages
    scrape_job_listings()
    
    # Step 2: Scrape detailed info from each job page
    scrape_job_details()
    
    # Step 3: Save to CSV
    jobs_df = save_to_csv()

def getJobsDF():
    return jobs_df
