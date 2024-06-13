import re
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


LOGINURL = 'https://erp.cisin.com/login.asp'
COMPTIMESHEETURL = 'https://erp.cisin.com/timesheetnew.asp'

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/submit", response_class=HTMLResponse)
async def submit_form(request: Request, email: str = Form(...), password: str = Form(...)):
    result = await run_selenium(email, password)
    return templates.TemplateResponse("result.html", {"request": request, "result": result})


async def run_selenium(email, password):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get(LOGINURL)
        driver.find_element(By.NAME, 'uname').send_keys(email)
        driver.find_element(By.NAME, 'pass').send_keys(password)
        driver.find_element(By.CSS_SELECTOR, 'input.submit-login').click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))

        driver.get(COMPTIMESHEETURL)
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'table#product-table')))
        tables = driver.find_elements(By.CSS_SELECTOR, 'table#product-table')

        if tables:
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
                return f'Lagged By: {total_hours} Hours, {remaining_minutes} Minutes'
            else:
                return f'Ahead By: {total_hours} Hours, {remaining_minutes} Minutes'
        else:
            return 'No table found with id="product-table"'

    except Exception as e:
        return f'Error: {str(e)}'
    finally:
        driver.quit()


def extract_hours_and_minutes(text):
    regex = re.compile(r'(\d+)\s*hrs,\s*(\d+)\s*min')
    match = regex.search(text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None
