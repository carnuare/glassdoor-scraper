import time
import pandas as pd
import logging
import os
import sys
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import tkinter as tk
from tkinter import filedialog


# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s")

def get_user_input():
    # # Create a simple GUI for input using tkinter
    # root = tk.Tk()
    # root.withdraw()  # Hide the root window

    # job_title = tk.simpledialog.askstring("Input", "Enter the job title:")
    # country = tk.simpledialog.askstring("Input", "Enter the country:")
    # output_directory = filedialog.askdirectory(title="Select Output Directory")

    job_title = "Software Engineer"
    country = "Spain"
    output_directory = "./output"

    return job_title, country, output_directory

def scrape_glassdoor(job_title, country, output_directory, output, debug):
    # Log info
    logging.info(f"Scraping Glassdoor for {job_title} salaries in {country}")
    logging.info(f"Output will be saved to {output_directory}")

    # Initialize WebDriver
    logging.info("Initializing WebDriver")
    options = webdriver.ChromeOptions()
    options.page_load_strategy = 'eager'
    options.add_argument("--start-maximized")
    options.add_argument("--disable-search-engine-choice-screen")
    driver = webdriver.Chrome(options=options)  # Update path to your chromedriver

    driver.get("https://www.glassdoor.es/Sueldos/index.htm")

    # Input the job title
    logging.info(f"     Step 1: Inputting job title ({job_title}) and country ({country})")
    try:
        job_title_input = driver.find_element(By.ID, "job-title-autocomplete")
        job_title_input.send_keys(job_title)
        job_title_input.send_keys(Keys.RETURN)
    except Exception as e:
        logging.error(f"Error inputting job title: {e}")
        sys.exit(1)

    # Input the country
    try:
        country_input = driver.find_element(By.ID, "location-autocomplete")
        country_input.send_keys(country)
        country_input.send_keys(Keys.RETURN)
    except Exception as e:
        logging.error(f"Error inputting country: {e}")
        sys.exit(1)

    # Click the search button
    try:
        search_button = driver.find_element(By.CSS_SELECTOR, "#SrchHero > div.HeroSearch_staticHphHeroSrch__c9lfL > div > div > div > form > div > button")
        search_button.click()
    except Exception as e:
        logging.error(f"Error clicking search button: {e}")
        sys.exit(1)

    # Wait for results to load
    time.sleep(5)

    companies_data = []

    page_count = 1

    def scrape_page():
        output.write(f"Scraping page {page_count}\n")
        logging.info(f"     Step 2: Scraping page {page_count}. Clicking to sort by salary...")
        logging.debug("Clicking to sort by salary...")
        # Click to sort by salary
        try:
            sort_button = driver.find_element(By.CSS_SELECTOR, "#popular-companies-list > div.SalariesList_SalariesList__66Jhm > section.SalariesSubHeader_HeaderSection__qXYAy > div")
            sort_button.click()
            time.sleep(2)  # Wait for sorting
            sorted_by_salary_button = driver.find_element(By.CSS_SELECTOR, "#radix-0 > section > ul > li:nth-child(3) > button")
            sorted_by_salary_button.click()
            time.sleep(3)  # Wait for sorting
        except Exception as e:
            logging.error(f"Error selecting to sort by salary: {e}")
            output.write(f"[E] Error selecting to sort by salary: {e}\n")
            sys.exit(1)

        

        logging.debug("Extracting company details...")
        # Extract company details
        companies = driver.find_elements(By.CSS_SELECTOR, "#popular-companies-list > div.SalariesList_SalariesList__66Jhm > section.SalariesList_SalariesList__66Jhm > div")
        logging.info("      Step 3: Extracting company details...")
        for company in companies:
            try:
                name = company.find_element(By.CSS_SELECTOR, "div:nth-child(2) > a > p").text
                output.write(f"     Company Name: {name}\n")
                logging.debug(f"    Company Name: {name}")
                rating = company.find_element(By.CSS_SELECTOR, "div:nth-child(2) > a > div > p").text
                output.write(f"         Rating: {rating}\n")
                salary = company.find_element(By.CSS_SELECTOR, "section.salary-card_TotalPaySection__5YLU2.salary-card_FontNormal__lx1CR.salary-card_SectionPadding__sHlg6 > div.salary-card_TotalPay__tVZF_").text
                output.write(f"         Salary: {salary}\n")
                companies_data.append({"Company Name": name, "Rating": rating, "Salary": salary})
            except Exception as e:
                logging.error(f"Error extracting company details: {e}")
                output.write(f"[E] Error extracting company details: {e}\n")
                sys.exit(1)

    # Scrape the first 50 entries
    while len(companies_data) < 50:
        scrape_page()
        logging.info("      Step 4: Clicking to go to the next page...")
        # Click to go to the next page
        try:
            page_count += 1
            next_page_button = driver.find_element(By.CSS_SELECTOR, "#popular-companies-list > div.SalariesList_SalariesList__66Jhm > nav > ol > li:nth-child(3) > a")
            next_page_button.click()
            time.sleep(5)  # Wait for the next page to load
        except:
            logging.info("No more pages or unable to find the next page button.")
            print("No more pages or unable to find the next page button.")
            break

    # Create a DataFrame and save to CSV
    df = pd.DataFrame(companies_data)
    output_path = f"{output_directory}/top_50_companies.csv"
    df.to_csv(output_path, index=False)
    print(f"Data saved to {output_path}")

    driver.quit()

if __name__ == "__main__":
    job_title, country, output_directory = get_user_input()

    debug = True

    output = open(os.path.join(output_directory, "scrapper-log.txt"), "w")
    # Add utils/header.txt to the log file
    with open("utils/header.txt", "r") as header:
        output.write(header.read())

    # Write the job title, country and output directory to the log file
    output.write(f"Job Title: {job_title}\n")
    output.write(f"Country: {country}\n")
    output.write(f"Output Directory: {output_directory}\n")

    scrape_glassdoor(job_title, country, output_directory, output, debug)
