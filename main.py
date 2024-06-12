import os
import asyncio
from playwright.async_api import async_playwright
import getpass

LOGINURL = os.getenv('LOGINURL')
TIMESHEETURL = os.getenv('TIMESHEETURL')
COMPTIMESHEETURL = os.getenv('COMPTIMESHEETURL')

async def main():
    email = input('Enter your email: ')
    password = getpass.getpass('Enter your password: ')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(LOGINURL, wait_until='networkidle')
            print('Navigated to login page.')

            await page.fill('input[name="uname"]', email)
            await page.fill('input[name="pass"]', password)
            print('Entered login credentials.')

            await page.click('input.submit-login')
            await page.wait_for_load_state('networkidle')
            print('Logged in successfully.')

            await page.goto(TIMESHEETURL, wait_until='networkidle')

            ul_selector = 'ul.shadetabs'
            await page.wait_for_selector(ul_selector, timeout=60000)

            link_text = 'Monthly'
            monthly_link_exists = await page.evaluate(r'''(text) => {
                const link = Array.from(document.querySelectorAll('ul.shadetabs li a')).find(el => el.textContent.includes(text));
                return !!link;
            }''', link_text)

            if monthly_link_exists:
                await page.evaluate(r'''(text) => {
                    const link = Array.from(document.querySelectorAll('ul.shadetabs li a')).find(el => el.textContent.includes(text));
                    if (link) {
                        link.click();
                    }
                }''', link_text)
            else:
                print('Monthly link not found.')
                await browser.close()
                return

            await asyncio.sleep(2)

            await page.goto(COMPTIMESHEETURL, wait_until='networkidle')

            await page.wait_for_function(r'''() => {
                const tables = document.querySelectorAll('table#product-table');
                return tables.length > 0;
            }''', timeout=10000)

            table_contents = await page.evaluate(r'''() => {
                const tables = document.querySelectorAll('table#product-table');
                const tableContents = [];
                tables.forEach((table, index) => {
                    tableContents.push({
                        index: index + 1,
                        content: table.innerHTML
                    });
                });
                return tableContents;
            }''')

            if table_contents:
                first_table_content = table_contents[0]['content']

                table_content = await page.evaluate(r'''(first_table_content) => {
                    const table = document.createElement('table');
                    table.innerHTML = first_table_content;

                    const rows = table.querySelectorAll('tr');

                    const extract_hours_and_minutes = (str) => {
                        const regex = /(\d+)\s*hrs,\s*(\d+)\s*min/;
                        const match = str.match(regex);
                        if (match) {
                            const hours = parseInt(match[1]);
                            const minutes = parseInt(match[2]);
                            return { hours, minutes };
                        }
                        return null;
                    };

                    let total_extra_minutes = 0;

                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        cells.forEach(cell => {
                            const text = cell.textContent.trim();
                            const time = extract_hours_and_minutes(text);
                            if (time) {
                                if (time.hours > 8) {
                                    total_extra_minutes += ((time.hours - 8) * 60) + time.minutes;
                                } else if (time.hours < 8) {
                                    total_extra_minutes -= ((8 - time.hours) * 60) - time.minutes;
                                } else {
                                    total_extra_minutes += time.minutes;
                                }
                            }
                        });
                    });

                    let total_hours = Math.floor(total_extra_minutes / 60);
                    let remaining_minutes = total_extra_minutes % 60;

                    if (total_hours < 0) {
                        total_hours += 1;
                    }
                    return { total_hours, total_minutes: remaining_minutes };
                }''', first_table_content)

                if table_content['total_hours'] < 0:
                    print(f'Lagged By: {table_content["total_hours"]} Hours, {table_content["total_minutes"]} Minutes')
                else:
                    print(f'Ahead By: {table_content["total_hours"]} Hours, {table_content["total_minutes"]} Minutes')
            else:
                print('No table found with id="product-table"')

        except Exception as e:
            print('Error:', e)
        finally:
            await browser.close()

asyncio.run(main())
