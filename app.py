import re
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pyppeteer import launch
from pyppeteer_stealth import stealth
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
        return templates.TemplateResponse("result.html",
                                          {"request": request,
                                           "over": result[0],
                                           "short": result[1]}
                                          )
    return templates.TemplateResponse("result.html",
                                      {"request": request,
                                       "result": "Invalid Credentials"}
                                      )


async def run_pyppeteer(email, password):
    browser = await launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-extensions", "--disable-gpu"])
    page = await browser.newPage()
    await stealth(page)  # Apply stealth plugin

    try:
        await page.goto(LOGINURL)
        await page.type('input[name=uname]', email)
        await page.type('input[name=pass]', password)
        await page.click('input.submit-login')
        await page.waitForSelector('body', timeout=10000)

        await page.goto(COMPTIMESHEETURL)
        await page.waitForFunction('document.querySelectorAll("table#product-table").length > 0', timeout=10000)
        tables = await page.querySelectorAllEval('table#product-table', 'tables => tables.map(table => table.innerHTML)')

        if tables:
            first_table_content = tables[0]

            rows = await page.evaluate('''(firstTableContent) => {
                const table = document.createElement('table');
                table.innerHTML = firstTableContent;
                return Array.from(table.querySelectorAll('tr')).map(row => {
                    return Array.from(row.querySelectorAll('td')).map(cell => cell.textContent.trim());
                });
            }''', first_table_content)

            log = []

            row = rows[14][1:]

            for cell in row:
                time = extract_hours_and_minutes(cell)
                if time:
                    log.append(time)

            return calc_time(log)
        else:
            return 'No data found'
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


def calc_time(log):
    std_minutes = 8 * 60  # 8 hours in minutes
    total_minutes = 0

    for day in log:
        hrs, mins = day
        total_minutes += hrs * 60 + mins

    total_required_minutes = len(log) * std_minutes
    overtime = 0
    shortfall = 0

    if total_minutes > total_required_minutes:
        overtime = total_minutes - total_required_minutes
    elif total_minutes < total_required_minutes:
        shortfall = total_required_minutes - total_minutes

    ot_hours, ot_minutes = divmod(overtime, 60)
    sf_hours, sf_minutes = divmod(shortfall, 60)
    return (f"Over Time: {ot_hours} hrs, {ot_minutes} min",
            f"Short Time: {sf_hours} hrs, {sf_minutes} min")
