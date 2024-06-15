import re
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pyppeteer import launch
from pyppeteer.errors import TimeoutError

LOGINURL = 'https://erp.cisin.com/login.asp'
COMPTIMESHEETURL = 'https://erp.cisin.com/timesheetnew.asp'

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit", response_class=HTMLResponse)
async def submit_form(request: Request, email: str = Form(...), password: str = Form(...)):
    result = await run_pyppeteer(email, password)
    if result: 
        return templates.TemplateResponse("result.html", {"request": request, "result": result})
    return templates.TemplateResponse("result.html", {"request": request, "result": "Invalid Credentials"})

async def run_pyppeteer(email, password):
    browser = await launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-extensions", "--disable-gpu"])
    page = await browser.newPage()

    try:
        await page.goto(LOGINURL)
        await page.type('input[name=uname]', email)
        await page.type('input[name=pass]', password)
        await page.click('input.submit-login')
        await page.waitForSelector('body', timeout=10000)

        await page.goto(COMPTIMESHEETURL)
        await page.waitForSelector('table#product-table', timeout=10000)
        tables = await page.querySelectorAll('table#product-table')

        if tables:
            total_extra_minutes = 0
            rows = await tables[0].querySelectorAll('tr')

            for row in rows:
                cells = await row.querySelectorAll('td')
                for cell in cells:
                    text = (await page.evaluate('(element) => element.textContent', cell)).strip()
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

    except TimeoutError as e:
            return False
    except Exception as e:
            return False
    finally:
        await browser.close()

def extract_hours_and_minutes(text):
    regex = re.compile(r'(\d+)\s*hrs,\s*(\d+)\s*min')
    match = regex.search(text)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None
