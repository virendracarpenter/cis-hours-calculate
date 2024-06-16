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
            std_minutes = 8 * 60
            rows = await tables[0].querySelectorAll('tr')
            for row in rows:
                cells = await row.querySelectorAll('td')
                for cell in cells:
                    text = (await page.evaluate('(element) => element.textContent', cell)).strip()
                    time_data = extract_hours_and_minutes(text)
                    if time_data:
                        hrs, mins = time_data
                        total_mins = hrs * 60 + mins
                        if total_mins > std_minutes:
                            overtime += total_mins - std_minutes
                        elif total_mins < std_minutes:
                            shortfall += std_minutes - total_mins
                        ot_hours, ot_minutes = divmod(overtime, 60)
                        sf_hours, sf_minutes = divmod(shortfall, 60)
                return {
                    "Over Time": (ot_hours, ot_minutes),
                    "Short Time": (sf_hours, sf_minutes)
                }
        else:
            return 'No data found'
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
