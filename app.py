import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import json

LOGINURL = os.getenv('LOGINURL')
TIMESHEETURL = os.getenv('TIMESHEETURL')
COMPTIMESHEETURL = os.getenv('COMPTIMESHEETURL')

def main():
    email = input('Enter your email: ')
    password = input('Enter your password: ')

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized"); 
    options.add_argument("disable-infobars");
    options.add_argument("--disable-extensions"); 
    options.add_argument("--disable-gpu");
    options.add_argument("--disable-dev-shm-usage");

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(LOGINURL)
        print('Navigated to login page.')

        driver.find_element(By.NAME, 'uname').send_keys(email)
        driver.find_element(By.NAME, 'pass').send_keys(password)
        print('Entered login credentials.')

        driver.find_element(By.CSS_SELECTOR, 'input.submit-login').click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))  # Wait until logged in
        print('Logged in successfully.')

        driver.get(TIMESHEETURL)

        # Check if the "Monthly" link exists
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.shadetabs')))
        links = driver.find_elements(By.CSS_SELECTOR, 'ul.shadetabs li a')
        monthly_link = None

        for link in links:
            if 'Monthly' in link.text:
                monthly_link = link
                break

        if monthly_link:
            monthly_link.click()
        else:
            print('Monthly link not found.')
            driver.quit()
            return

        time.sleep(2)

        driver.get(COMPTIMESHEETURL)

        # Wait for the table to load
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table#product-table')))

        # Extract and log the number of tables and their content
        tables = driver.find_elements(By.CSS_SELECTOR, 'table#product-table')

        if tables:
            first_table_content = tables[0].get_attribute('innerHTML')

            total_extra_minutes = 0

            rows = tables[0].find_elements(By.CSS_SELECTOR, 'tr')

            for row in rows:
                cells = row.find_elements(By.CSS_SELECTOR, 'td')
                for cell in cells:
                    text = cell.text.strip()
                    time_data = extract_hours_and_minutes(text)
                    if time_data:
                        hours, minutes = time_data
                        if hours > 8:
                            total_extra_minutes += ((hours - 8) * 60) + minutes
                        elif hours < 8:
                            total_extra_minutes -= ((8 - hours) * 60) - minutes
                        else:
                            total_extra_minutes += minutes

            total_hours = total_extra_minutes // 60
            remaining_minutes = total_extra_minutes % 60

            if total_hours < 0:
                total_hours += 1

            if total_hours < 0:
                print(f'Lagged By: {total_hours} Hours, {remaining_minutes} Minutes')
            else:
                print(f'Ahead By: {total_hours} Hours, {remaining_minutes} Minutes')

        else:
            print('No table found with id="product-table"')

    except Exception as e:
        print('Error:', e)
    finally:
        driver.quit()

def extract_hours_and_minutes(text):
    import re
    regex = re.compile(r'(\d+)\s*hrs,\s*(\d+)\s*min')
    match = regex.search(text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None

if __name__ == "__main__":
    main()
