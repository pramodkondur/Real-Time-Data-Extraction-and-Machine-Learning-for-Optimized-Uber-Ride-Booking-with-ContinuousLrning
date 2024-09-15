import time
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from csv import DictReader
import json
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement  # Import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import config as cf
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import mysql.connector
import schedule
from datetime import datetime, timedelta, date
import re





con = mysql.connector.connect(
    host="localhost",
    user="root",
    password="expert789",
    database="uber"
)

cursor = con.cursor()


# Query to Create Table
query = """CREATE TABLE if not exists uber_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    route_from TEXT,
    route_to TEXT,
    ride_type TEXT,
    ride_max_persons FLOAT,
    ride_request_time TEXT,
    ride_waiting_time FLOAT,
    ride_request_date TEXT,
    ride_reaching_time TEXT,
    ride_time TEXT,
    ride_price DECIMAL(10, 2)
    )"""
cursor.execute(query)

#chrome_options = Options()

#chrome_options.add_argument("--disable-notifications")

#try from video
options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={cf.local['userDataDir']}")

options.add_argument("--headless")  # Ensure GUI is off
options.add_argument("--no-sandbox")  # Required if running as root
options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

#service = ChromeService(executable_path=r"/Users/pramodkondur/Downloads/chromedriver-mac-arm642/chromedriver")

service = ChromeService(ChromeDriverManager().install())


def get_details(route,url):

    driver = webdriver.Chrome(service=service, options=options)


    # Set the page load timeout
    driver.set_page_load_timeout(6)  # Timeout after 10 seconds

    # Creating empty list to store the details of the routes
    routes_list = []

    try:
        driver.get(url)
        print('Route loaded')

    except Exception as e:
        print('Page load timed out or encountered an error:', str(e))
        # Find all parent elements with the class name
        time.sleep(1)
        elements = []
        elements = driver.find_elements(By.CSS_SELECTOR, "div._css-zSrrc")
        print('elements loaded')
        print(elements)

        time.sleep(1)

        # Loop through each element and extract details
        for element in elements:
            ride_type_person = element.find_element(By.CSS_SELECTOR, "p._css-gmxjOK").text
            ride_time = element.find_element(By.CSS_SELECTOR, "p._css-bNXHBf").text
            ride_price = element.find_element(By.CSS_SELECTOR, "p._css-iQlrzm").text
            print("  ride_type_person:", ride_type_person)
            print("  ride_time:", ride_time)
            print("  ride_price:", ride_price)
            print('  route:', route)

            if ride_type_person[-1] == 'L':
                # Extract ride type and person
                ride_type = ride_type_person
                ride_person = 6
            else:
                ride_type = ride_type_person[:-1]  # remove last character
                ride_person = float(ride_type_person[-1])  # convert last character to int

            # Extract ride waiting time
            ride_waiting_time = float(ride_time.split(" ")[0])

            # Extract ride reaching time and convert to 24-hour format
            ride_reaching_time_str = re.search(r'\d{1,2}:\d{2} (AM|PM)', ride_time).group()
            ride_reaching_time = datetime.strptime(ride_reaching_time_str, "%I:%M %p")
            ride_reaching_time = ride_reaching_time.strftime("%H:%M:%S")

            # Get current time and date
            current_time = datetime.now()
            ride_request_time = current_time.strftime("%H:%M:%S")
            ride_request_date = current_time.strftime("%Y-%m-%d")

            # Calculate ride time
            ride_request_time_obj = datetime.strptime(ride_request_time, "%H:%M:%S")
            ride_reaching_time_obj = datetime.strptime(ride_reaching_time, "%H:%M:%S")
            ride_waiting_time_obj = timedelta(minutes=ride_waiting_time)
            ride_time_obj = ride_reaching_time_obj - (ride_request_time_obj + ride_waiting_time_obj)
            ride_time = str(ride_time_obj)

            # Transform ride price
            ride_price = float(ride_price.replace("₹", ""))

            # Transform route
            route_parts = route.split(" to ")
            route_from = route_parts[0]
            route_to = route_parts[1]

            route_item = {
                'route_from': route_from,
                'route_to': route_to,
                'ride_type': ride_type,
                'ride_max_persons': ride_person,
                'ride_request_time': ride_request_time,
                'ride_waiting_time': ride_waiting_time,
                'ride_request_date': ride_request_date,
                'ride_reaching_time': ride_reaching_time,
                'ride_time': ride_time,
                'ride_price': ride_price
            }

            routes_list.append(route_item)
            print(routes_list)
            # Once all details are got for a route, we convert it to a dataframe so that we can write it to the db
        df = pd.DataFrame(routes_list)
        return (df)

    finally:
        # Ensure that the browser is closed
        driver.quit()


def write_into_db(df):
    query = """INSERT INTO uber_details (
        route_from,
        route_to,
        ride_type,
        ride_max_persons,
        ride_request_time,
        ride_waiting_time,
        ride_request_date,
        ride_reaching_time,
        ride_time,
        ride_price
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    result = []

    if df is not None:
        for index in df.index:
            row_data = list(df.loc[index].values)
            result.append(row_data)
        cursor.executemany(query,
                           result)  # execute many and storing data in list as it connects to the db once it finishes
        # getting input rather than each time
        con.commit()

    else:
        print("DataFrame is None, cannot process.")






route_urls = {
'Chennai Lighthouse to Chennai Citi Centre' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Dr%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Citi Centre to Chennai Lighthouse':'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Dr%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Express Avenue Mall to Chennai Lighthouse' :'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Rd%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Lighthouse to Express Avenue Mall' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Road%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Lighthouse to PVR Ampa SkyOne':'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22PVR%20Ampa%20SkyOne%2C%20Aminjikarai%22%2C%22addressLine2%22%3A%221%2C%20Nelson%20Manickam%20Rd%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJyzSdtIRmUjoRqkjefEktGWk%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0739961%2C%22longitude%22%3A80.2214138%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'PVR Ampa SkyOne to Chennai Lighthouse': 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22PVR%20Ampa%20SkyOne%2C%20Aminjikarai%22%2C%22addressLine2%22%3A%221%2C%20Nelson%20Manickam%20Rd%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJyzSdtIRmUjoRqkjefEktGWk%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0739961%2C%22longitude%22%3A80.2214138%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Marina Beach to Chennai Lighthouse': 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Lighthouse to Marina Beach': 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Lighthouse to Semmozhi Poonga' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Semmozhi Poonga to Chennai Lighthouse' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Sai Baba Temple Mylapore to Chennai Lighthouse' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%2227M7%2B4VF%2C%20Venkatesa%20Agraharam%20Rd%2C%20Kabali%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Lighthouse to Sai Baba Temple Mylapore' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%22Venkatesa%20Agraharam%20Road%2C%20Kapaleeswarar%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Chennai%20Lighthouse%22%2C%22addressLine2%22%3A%22Marina%20Beach%20Road%2C%20Marina%20Beach%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ5dptVYBoUjoRCQL97Hq9F1w%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0397427%2C%22longitude%22%3A80.2792303%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Citi Centre to Express Avenue Mall': 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Rd%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Dr%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Express Avenue Mall to CitiCenter' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Doctor%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Rd%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'PVR Ampa SkyOne to Chennai Citi Centre': 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Doctor%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Ampa%20Skyone%22%2C%22addressLine2%22%3A%221%2C%20Nelson%20Manickam%20Rd%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJZ7WProRmUjoRRAt0jFusLw8%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0734943%2C%22longitude%22%3A80.22136259999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Citi Centre to PVR Ampa SkyOne' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Ampa%20Skyone%22%2C%22addressLine2%22%3A%22Nelson%20Manickam%20Road%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJZ7WProRmUjoRRAt0jFusLw8%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0734943%2C%22longitude%22%3A80.22136259999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Dr%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Citi Centre to Marina Beach' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Dr%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Marina Beach to Chennai Citi Centre' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Doctor%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Semmozhi Poonga to Chennai Citi Centre':'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Doctor%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Citi Centre to Semmozhi Poonga' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Doctor%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Chennai Citi Centre to Sai Baba Temple Mylapore' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%22Venkatesa%20Agraharam%20Road%2C%20Kapaleeswarar%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Doctor%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Sai Baba Temple Mylapore to Chennai Citi Centre' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22CHENNAI%20CITI%20CENTRE%22%2C%22addressLine2%22%3A%22Doctor%20Radha%20Krishnan%20Salai%2C%20Loganathan%20Colony%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJ8X9W6P9nUjoR1PQDf-g24qg%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0429549%2C%22longitude%22%3A80.2737891%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%2227M7%2B4VF%2C%20Venkatesa%20Agraharam%20Rd%2C%20Kabali%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Express Avenue Mall to PVR Ampa SkyOne' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Ampa%20Skyone%22%2C%22addressLine2%22%3A%22Nelson%20Manickam%20Road%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJZ7WProRmUjoRRAt0jFusLw8%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0734943%2C%22longitude%22%3A80.22136259999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Road%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'PVR Ampa SkyOne to Express Avenue Mall' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Road%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22PVR%20Ampa%20SkyOne%2C%20Aminjikarai%22%2C%22addressLine2%22%3A%221%2C%20Nelson%20Manickam%20Rd%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJyzSdtIRmUjoRqkjefEktGWk%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0739961%2C%22longitude%22%3A80.2214138%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Express Avenue Mall to Marina Beach' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Rd%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Marina Beach to Express Avenue Mall' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Road%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Semmozhi Poonga to Express Avenue Mall' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Rd%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Express Avenue Mall to Semmozhi Poonga' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Rd%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Sai Baba Temple Mylapore to Express Avenue Mall' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Rd%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%22Venkatesa%20Agraharam%20Road%2C%20Kapaleeswarar%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Express Avenue Mall to Sai Baba Temple Mylapore' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%22Venkatesa%20Agraharam%20Road%2C%20Kapaleeswarar%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Road%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'PVR Ampa SkyOne to Marina Beach' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22PVR%20Ampa%20SkyOne%2C%20Aminjikarai%22%2C%22addressLine2%22%3A%22Nelson%20Manickam%20Road%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJyzSdtIRmUjoRqkjefEktGWk%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0739961%2C%22longitude%22%3A80.2214138%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Marina Beach to PVR Ampa SkyOne' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22PVR%20Ampa%20SkyOne%2C%20Aminjikarai%22%2C%22addressLine2%22%3A%22Nelson%20Manickam%20Road%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJyzSdtIRmUjoRqkjefEktGWk%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0739961%2C%22longitude%22%3A80.2214138%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Semmozhi Poonga to PVR Ampa SkyOne' :'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22PVR%20Ampa%20SkyOne%2C%20Aminjikarai%22%2C%22addressLine2%22%3A%22Nelson%20Manickam%20Road%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJyzSdtIRmUjoRqkjefEktGWk%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0739961%2C%22longitude%22%3A80.2214138%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'PVR Ampa SkyOne to Semmozhi Poonga' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22PVR%20Ampa%20SkyOne%2C%20Aminjikarai%22%2C%22addressLine2%22%3A%221%2C%20Nelson%20Manickam%20Rd%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJyzSdtIRmUjoRqkjefEktGWk%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0739961%2C%22longitude%22%3A80.2214138%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'PVR Ampa SkyOne to Sai Baba Temple Mylapore': 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%22Venkatesa%20Agraharam%20Road%2C%20Kapaleeswarar%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22PVR%20Ampa%20SkyOne%2C%20Aminjikarai%22%2C%22addressLine2%22%3A%221%2C%20Nelson%20Manickam%20Rd%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJyzSdtIRmUjoRqkjefEktGWk%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0739961%2C%22longitude%22%3A80.2214138%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Sai Baba Temple Mylapore to PVR Ampa SkyOne': 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22PVR%20Ampa%20SkyOne%2C%20Aminjikarai%22%2C%22addressLine2%22%3A%22Nelson%20Manickam%20Road%2C%20Aminjikarai%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJyzSdtIRmUjoRqkjefEktGWk%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0739961%2C%22longitude%22%3A80.2214138%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%2227M7%2B4VF%2C%20Venkatesa%20Agraharam%20Rd%2C%20Kabali%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Sai Baba Temple Mylapore to Marina Beach' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%2227M7%2B4VF%2C%20Venkatesa%20Agraharam%20Rd%2C%20Kabali%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Marina Beach to Sai Baba Temple Mylapore' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%22Venkatesa%20Agraharam%20Road%2C%20Kapaleeswarar%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Semmozhi Poonga to Sai Baba Temple Mylapore' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%22Venkatesa%20Agraharam%20Road%2C%20Kapaleeswarar%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Sai Baba Temple Mylapore to Semmozhi Poonga' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Sai%20Baba%20Temple%20Mylapore%22%2C%22addressLine2%22%3A%2227M7%2B4VF%2C%20Venkatesa%20Agraharam%20Rd%2C%20Kabali%20Nagar%2C%20Venkatesa%20Agraharam%2C%20Mylapore%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJFwDbhM1nUjoR9lMVvvVD89o%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0328131%2C%22longitude%22%3A80.26467889999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Marina Beach to Semmozhi Poonga' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279',
'Semmozhi Poonga to Marina Beach' : 'https://m.uber.com/go/product-selection?_gl=1%2Anu74i5%2A_gcl_au%2ANTEyODIxMTIyLjE3MjU4NjExNzg.%2A_ga%2ANTU1NzI2MzIuMTcyNTcxNTczNw..%2A_ga_XTGQLY6KPT%2AMTcyNTkzODkwMS4xMS4xLjE3MjU5NDAxOTguMC4wLjA.&drop%5B0%5D=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Tamil%20Nadu%22%2C%22id%22%3A%22ChIJuzIBtptoUjoRCrZi347PSQU%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0499526%2C%22longitude%22%3A80.2824026%2C%22provider%22%3A%22google_places%22%7D&marketing_vistor_id=95dd8594-7619-4d77-b0e1-c3ca5ff6776f&pickup=%7B%22addressLine1%22%3A%22Semmozhi%20Poonga%22%2C%22addressLine2%22%3A%22Cathedral%20Road%2C%20opposite%20American%20Consulate%2C%20Ellaiamman%20Colony%2C%20Teynampet%2C%20Chennai%2C%20Tamil%20Nadu%2C%20India%22%2C%22id%22%3A%22ChIJcVcO_UZmUjoR21emTXt0U4k%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0505371%2C%22longitude%22%3A80.2514128%2C%22provider%22%3A%22google_places%22%7D&uclick_id=e6e110fb-7ff2-4d6b-bebd-37dce42603ef&vehicle=20013279'

}

def fetch_and_write_details():
    current_time = datetime.now().strftime("%H:%M")
    print(f"Running fetch_and_write_details function at {current_time}...")
    for key, value in route_urls.items():
        df = get_details(key, value)
        write_into_db(df)

def wait_until_next_interval():
    now = datetime.now()
    current_minute = now.minute

    # Define the stop and start times
    stop_time = now.replace(hour=23, minute=0, second=0, microsecond=0)
    start_time = now.replace(hour=7, minute=0, second=0, microsecond=0)

    # Determine if we should stop for the night
    if now > stop_time:
        # If it's past 11:00 PM, calculate the wait time until 7:00 AM next day
        next_start = start_time + timedelta(days=1)
        wait_time = (next_start - now).total_seconds()
        print(f"Waiting for {wait_time} seconds until {next_start}")
        time.sleep(wait_time)
        return

    # Calculate the next hour mark
    next_interval = now.replace(minute=0, second=0, microsecond=0)
    if now.minute >= 0:
        next_interval += timedelta(hours=1)

    # If next_interval is after 11:00 PM, wait until 7:00 AM the next day
    if next_interval > stop_time:
        next_start = start_time + timedelta(days=1)
        wait_time = (next_start - now).total_seconds()
        print(f"Waiting for {wait_time} seconds until {next_start}")
        time.sleep(wait_time)
        return

    wait_time = (next_interval - now).total_seconds()
    print(f"Waiting for {wait_time} seconds until {next_interval}")
    time.sleep(wait_time)

while True:
    fetch_and_write_details()  # Perform the task
    wait_until_next_interval()  # Wait until the next top-of-hour mark


"""
def get_cookies_values(file):
    with open(file, encoding='utf-8-sig') as f:
        dict_reader = DictReader(f)
        list_of_dicts = list(dict_reader)
    return list_of_dicts

def save_cookies(driver, filename):
    cookies = driver.get_cookies()
    with open(filename, 'w') as file:
        json.dump(cookies, file)

def load_cookies(driver, filename):
    with open(filename, 'r') as file:
        cookies = json.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)

cookies = get_cookies_values("uber_cookies.csv")

for i in cookies:
    driver.add_cookie(i)
time.sleep(1)
driver.refresh()

time.sleep(2) # 2 seconds timeout

print("Cookies Got")


save_cookies(driver, 'cookies.json')
time.sleep(.1)
print("Cookies Saved")


load_cookies(driver, 'cookies.json')
print("Cookies loaded")
driver.refresh()
"""
