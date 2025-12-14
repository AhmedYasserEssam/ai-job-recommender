import requests
from bs4 import BeautifulSoup
import pandas as pd
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time


def scrape_job_listings(job_name: str) -> pd.DataFrame:
    """
    Scrape basic job info from search results pages.
    
    Args:
        job_name: The job title to search for
        
    Returns:
        DataFrame containing scraped job listings
    """
    rows = []
    
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
                row = {'Job Search': job_name}
                
                # Job Title
                title_elem = card.find("h2", class_="css-193uk2c")
                row['Job Title'] = title_elem.text.strip() if title_elem else "N/A"
                
                # Company Name
                company_elem = card.find("a", class_="css-ipsyv7")
                row['Company'] = company_elem.text.strip() if company_elem else "N/A"
                
                # Location
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
                
                # Publish Date
                publish_elem = card.select_one("div[class*='css-eg55jf']")
                row['Publish Date'] = publish_elem.get_text(strip=True) if publish_elem else "N/A"
                
                # Job Link
                link_elem = card.find("a", class_="css-o171kl")
                row['Job Link'] = link_elem.get('href') if link_elem else "N/A"
                
                # Job Type
                type_elem = card.find("span", class_="css-uc9rga eoyjyou0")
                row['Job Type'] = type_elem.text.strip() if type_elem else "N/A"
                
                # Work Place
                workplace_elem = card.select_one("span[class*='css-uofntu eoyjyou0']")
                row['Work Place'] = workplace_elem.get_text(strip=True) if workplace_elem else "N/A"
                
                rows.append(row)
            
            print(f"Page {page + 1}: Found {len(job_cards)} jobs")
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            continue
    
    df = pd.DataFrame(rows)
    print(f"\nTotal jobs found: {len(df)}")
    return df


def scrape_job_details(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scrape detailed info from each job's individual page using Selenium.
    Adds detail columns directly to the DataFrame.
    
    Args:
        df: DataFrame with job listings (must have 'Job Link' and 'Job Title' columns)
        
    Returns:
        DataFrame with added detail columns
    """
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
    
    # Initialize new columns with N/A
    df['Salary'] = "N/A"
    df['Experience Needed'] = "N/A"
    df['Career Level'] = "N/A"
    df['Education Level'] = "N/A"
    df['Job Categories'] = "N/A"
    df['Skills'] = "N/A"
    df['Job Requirements'] = "N/A"
    
    # Initialize Chrome driver in headless mode (no browser window)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    
    for i, row in df.iterrows():
        link = row['Job Link']
        
        if link == "N/A":
            continue
            
        try:
            driver.get(link)
            time.sleep(2)  # Wait for page to load
            
            # Execute JavaScript to extract all data
            data = driver.execute_script(extract_script)
            
            # Update DataFrame directly
            df.at[i, 'Experience Needed'] = data.get('experience', 'N/A')
            df.at[i, 'Career Level'] = data.get('careerLevel', 'N/A')
            df.at[i, 'Education Level'] = data.get('education', 'N/A')
            df.at[i, 'Salary'] = data.get('salary', 'N/A')
            df.at[i, 'Job Categories'] = data.get('categories', 'N/A')
            df.at[i, 'Skills'] = data.get('skills', 'N/A')
            df.at[i, 'Job Requirements'] = data.get('requirements', 'N/A')
            
            print(f"Scraped job {i + 1}/{len(df)}: {row['Job Title'][:30]}...")
            
        except Exception as e:
            print(f"Job {i + 1} page error: {e}")
    
    driver.quit()
    print("Detailed scraping complete!")
    return df


def save_to_csv(df: pd.DataFrame, file_path: str = "wuzzuf_jobs_data.csv") -> str:
    """
    Save DataFrame to CSV file.
    
    Args:
        df: The DataFrame to save
        file_path: Output file path (default: wuzzuf_jobs_data.csv)
        
    Returns:
        The file path where data was saved
    """
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"\nData saved to {file_path}")
    print(f"Total records: {len(df)}")
    return file_path


def scrape_jobs(job_name: str, save_csv: bool = True) -> pd.DataFrame:
    """
    Main function to scrape jobs for a given job title.
    
    Args:
        job_name: The job title to search for
        save_csv: Whether to save results to CSV (default: True)
        
    Returns:
        pandas DataFrame with all scraped job data
    """
    if not job_name or not job_name.strip():
        raise ValueError("Job name cannot be empty")
    
    job_name = job_name.strip()
    
    # Step 1: Scrape job listings from search pages (returns DataFrame)
    df = scrape_job_listings(job_name)
    
    # Step 2: Scrape detailed info and add to DataFrame
    df = scrape_job_details(df)
    
    # Step 3: Optionally save to CSV
    if save_csv:
        save_to_csv(df)
    
    return df


def getJobsDF(job_name: str) -> pd.DataFrame:
    """
    Get jobs DataFrame for a given job title.
    Alias for scrape_jobs() for backward compatibility.
    
    Args:
        job_name: The job title to search for
        
    Returns:
        pandas DataFrame with all scraped job data
    """
    return scrape_jobs(job_name, save_csv=False)


# Allow running as standalone script
if __name__ == "__main__":
    user_input = input("Enter job title: ").strip()
    
    if not user_input:
        print("No job title entered. Exiting.")
        exit()
    
    df = scrape_jobs(user_input)
    print(df.head())
