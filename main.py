from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime
import pandas as pd
import mysql.connector

# use pip install webdriver-manager also which is needed

# Setup MYSQL connection
# utilize your preferred database
''''''
con = mysql.connector.connect(
    host="localhost",
    user="root",
    password="expert789",
    database="redbus"
)

cursor = con.cursor()
query = """CREATE TABLE if not exists bus_details ( id INT AUTO_INCREMENT PRIMARY KEY, from_destination TEXT, 
to_destination TEXT, waiting_time Float, CarType TEXT, departing_time DATETIME, duration TEXT, 
reaching_time DATETIME, price DECIMAL(10, 2), )"""
cursor.execute(query)


# Truncate Table
#query = "TRUNCATE TABLE bus_routes"
#cursor.execute(query)


# Function to scroll to end of page to get all buses
def scroll():
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:

        # Scroll down to the bottom in order to load all the buses

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for page to load

        time.sleep(.2)

        # Calculate new scroll height and compare with last scroll height

        new_height = driver.execute_script("return document.body.scrollHeight")

        # If it is the same height then it is at the end of the page
        if new_height == last_height:
            break

        last_height = new_height

'''
# Function to get bus details
def get_bus_details_for_route(url):
    driver.get(url)
    route_info = (driver.find_element(By.CLASS_NAME, 'D136_h1').text).replace(' Bus', '')

    dayelem = driver.find_element(By.XPATH, '//*[@id="searchDat"]')
    dayvar = (dayelem.get_attribute('value')) + " 2024"

    # waiting for page to load
    time.sleep(4)

    # Expanding all the buses section if it has 'view buses' button
    # Adding an exception block if it is unable to click view buses button
    try:
        tourismBusesAgency = driver.find_elements(By.CLASS_NAME, 'gmeta-data.clearfix')

        for agency in tourismBusesAgency:
            btn_var = agency.find_element(By.CLASS_NAME, "button")
            btn_var.click()
    except ElementClickInterceptedException:
        print(url, 'view-buses in this url not clickable')

    # Scrolling so all the bus data gets loaded
    scroll()

    # Creating empty list to store the details of the buses
    buses_list = []

    # Getting all the buses group so that we can get all the bus details for each of them i.e. states and private buses
    busesgroup = driver.find_elements(By.CLASS_NAME, 'bus-items')

    for buses in busesgroup:
        buseslist = buses.find_elements(By.CLASS_NAME, 'clearfix.bus-item')

        #print("buses number:", len(buseslist))

        # Gets all the required bus details in the selected group

        for bus in buseslist:
            busname = bus.find_element(By.CLASS_NAME, 'travels.lh-24.f-bold.d-color').text
            # print(busname)
            bustype = bus.find_element(By.CLASS_NAME, 'bus-type.f-12.m-top-16.l-color.evBus').text
            departing_time = dayvar + " " + bus.find_element(By.CLASS_NAME, 'dp-time.f-19.d-color.f-bold').text + ":00"
            duration = bus.find_element(By.CLASS_NAME, 'dur.l-color.lh-24').text

            # Some buses have reaching date as the next day, so we are using try and exception to get these values
            try:
                bus.find_element(By.CLASS_NAME, 'next-day-dp-lbl.m-top-16') != 0
                new_date = ((bus.find_element(By.CLASS_NAME, 'next-day-dp-lbl.m-top-16').text).replace("-",
                                                                                                       " ")) + " 2024"
                reaching_time = new_date + " " + bus.find_element(By.CLASS_NAME,
                                                                  'bp-time.f-19.d-color.disp-Inline').text + ":00"

            except NoSuchElementException:
                reaching_time = dayvar + " " + bus.find_element(By.CLASS_NAME,
                                                                'bp-time.f-19.d-color.disp-Inline').text + ":00"

            star_rating = (((bus.find_element(By.CLASS_NAME, 'column-six.p-right-10.w-10.fl').text).replace("New",
                                                                                                            "0")).replace(
                " ", "0"))[0:3]
            price = (bus.find_element(By.CLASS_NAME, 'fare.d-block').text).replace("INR ", "")
            seats_available = (bus.find_element(By.CLASS_NAME, 'column-eight.w-15.fl').text)[0:2]

            # print(bus_name, bus_type, departing_time, duration, reaching_time, star_rating, price, seats_available)

            bus_item = {
                'route_name': route_info,
                'route_link': url,
                'busname': busname,
                'bustype': bustype,
                'departing_time': datetime.strptime(departing_time, "%d %b %Y %H:%M:%S"),
                'duration': duration,
                'reaching_time': datetime.strptime(reaching_time, "%d %b %Y %H:%M:%S"),
                'star_rating': float(star_rating),
                'price': float(price),
                'seats_available': float(seats_available[0:2])

            }

            buses_list.append(bus_item)

    # Once all details of the buses are got for a route, we convert it to a dataframe so that we can write it to the db
    df = pd.DataFrame(buses_list)
    return (df)

'''

# Function to write the scrapped data into database
def write_into_db(df):
    query = """insert into uber_details (route_name,route_link,busname,bustype,departing_time,duration,reaching_time,star_rating,price,seats_available) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
             """
    result = []

    for index in df.index:
        row_data = list(df.loc[index].values)
        result.append(row_data)
    cursor.executemany(query,
                       result)  # execute many and storing data in list as it connects to the db once it finishes
    # getting input rather than each time
    con.commit()


# A list to store all the route urls for each state transportation
routes_urls = []

# Function to get all the routes url for the selected state transportation
def get_details(url):
    driver.get(url)
    time.sleep(2)

    uber_go_block = driver.find_elements(By.CLASS_NAME,'_css-zSrrc')

    #routes_list_to_get_urls = driver.find_elements(By.CLASS_NAME, 'route_link')
    # This line used for checking no.of routes fetched from the page --> print(len(routes_list_to_get_urls))
    # Gets all routes for page 1
    #for elem in uber_go_block:
    uber_go_block_price = uber_go_block.find_element(By.CLASS_NAME, '_css-fAzKU').text
    print(uber_go_block_price)

    #    url_to_extract = routes.find_element(By.TAG_NAME, 'a')
     #   url_extracted = url_to_extract.get_attribute('href')
        #print(url_extracted)
     #   routes_urls.append(url_extracted)

    # To handle pagination
    #uber_go_block_1 = uber_go_block.find_element(By.CLASS_NAME, 'DC_117_pageTabs')
'''
    for page in page_elements:
        try:
            page.click()
            print(page.text)
            time.sleep(.2)
            routes_list_to_get_urls = driver.find_elements(By.CLASS_NAME, 'route_link')
            # This line used for checking no.of routes fetched from the page --> print(len(routes_list_to_get_urls))
            # Gets all routes for page 2 to end
            for routes in routes_list_to_get_urls:
                url_to_extract = routes.find_element(By.TAG_NAME, 'a')
                url_extracted = url_to_extract.get_attribute('href')
                #print(url_extracted)
                routes_urls.append(url_extracted)
        # Usually the page 1 is not clickable since it is active, so we need to catch the exception
        except ElementClickInterceptedException:
            print('the page is not not clickable')
'''

list_of_routes_url = ['https://m.uber.com/go/product-selection?_gl=1%2A12fgt4e%2A_ga%2AMTAxNTgxNTUzMy4xNzI1NzA3MTIw%2A_ga_XTGQLY6KPT%2AMTcyNTcwNzEyMC4xLjEuMTcyNTcwNzEyMC4wLjAuMA..&drop%5B0%5D=%7B%22addressLine1%22%3A%22Express%20Avenue%20Mall%22%2C%22addressLine2%22%3A%22Whites%20Rd%2C%20Express%20Estate%2C%20Royapettah%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJgaOxaT1mUjoR_q0IaoVAKvE%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0581879%2C%22longitude%22%3A80.26407119999999%2C%22provider%22%3A%22google_places%22%7D&effect=&marketing_vistor_id=9ef3e8c6-15a1-4dd1-b1e6-2e4f58b3f0dd&pickup=%7B%22addressLine1%22%3A%22Marina%20Beach%22%2C%22addressLine2%22%3A%22Triplicane%2C%20Chennai%2C%20Tamil%20Nadu%22%2C%22id%22%3A%22ChIJUXrunptoUjoR1q79EILYOlo%22%2C%22source%22%3A%22SEARCH%22%2C%22latitude%22%3A13.0555796%2C%22longitude%22%3A80.28369959999999%2C%22provider%22%3A%22google_places%22%7D&uclick_id=8e9d0f00-6007-4012-b85d-1ce7c147ccb4&vehicle=20013279']

    #'https://www.uber.com/in/en/']


# Collecting all the urls for routes from the state tourism urls
for url in list_of_routes_url:
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    get_details(url)

# Collects all the bus details data from each route url we collected and writes to db
#for url in routes_urls:
#    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
#    df = get_bus_details_for_route(url)
#    write_into_db(df)

con.close()