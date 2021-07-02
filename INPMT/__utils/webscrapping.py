"""
INPMT
A tool to process data to learn more about Impact of National Parks on Malaria Transmission

Copyright (C) <2021>  <Manchon Pierre>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = Options()
options.page_load_strategy = 'normal'
# options.headless = True
path_driver = 'C:\Program Files (x86)/chromedriver.exe'
website = 'https://lpdaacsvc.cr.usgs.gov/appeears/task/area'
username = "pierre.manchon@pm.me"
password = "sike  "

browser = webdriver.Chrome(path_driver, options=options)
browser.get(website)

# Wait until the page is loaded to fill in the login credentials and hit the login button
login_wait = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "button-with-notes")))
username_placeholder = browser.find_element_by_id("username")
username_placeholder.clear()
username_placeholder.send_keys(username)
password_placeholder = browser.find_element_by_name("password")
password_placeholder.clear()
password_placeholder.send_keys(password)
browser.find_element_by_name("commit").click()

# Wait until the page is loaded to the "Extract Area Sample" page
app_wait = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "well")))
browser.find_element_by_class_name('thumbnail').click()

# Fill the Area name placholder with the string  'AREA NAME'
area_sample_name = 'AREA NAME'
area_sample_name_placeholder = browser.find_element_by_id("taskName")
area_sample_name_placeholder.clear()
area_sample_name_placeholder.send_keys(area_sample_name)

# Assign the starting date to 06012021
startDate = '06012021'
startDate_placeholder = browser.find_element_by_id("startDate")
startDate_placeholder.clear()
startDate_placeholder.click()
startDate_placeholder.send_keys(startDate)

# Assign the ending date to 07012021
endDate = '07012021'
endDate_placeholder = browser.find_element_by_id("endDate")
endDate_placeholder.clear()
endDate_placeholder.click()
endDate_placeholder.send_keys(endDate)

# Search satellites that produce NDVI data and pick:
# Terra MODIS Vegetation Indices (NDVI & EVI)
# MOD13A1.006, 500m, 16day, (2000-02-18 to Present)
NDVI_layers = browser.find_element_by_id("product")
NDVI_layers.click()
NDVI_layers.send_keys('NDVI')
NDVI_product_list = browser.find_element_by_id("typeahead-667-7605-option-0")
NDVI_product_list.click()
# Pick the actual NDVI layers from the available data
NDVI_product = browser.find_element_by_link_text('layer-name word-break')
values = browser.find_elements(By.XPATH, '//div[@class="list-group-item layers layers-available"]/div/table/tbody/tr/td[@class="layer-name word-break"]')
add = browser.find_elements(By.XPATH, '//div[@class="list-group-item layers layers-available"]/div/table/tbody/tr/td[@class="layer-add"]')
for x, y in zip(values, add):
    if 'NDVI' in x.text:
        y.click()

# Pick the native projection
projection = browser.find_element_by_id("projection")
projection.click()
native_projection = browser.find_element_by_id("typeahead-669-5008-option-0")
native_projection.click()

# Submit the request
submit = browser.find_elements(By.XPATH, '//div[@class="col-md-12 text-right button-group"]/button[@class="btn btn-text btn-primary"]')
submit[0].click()

# Quit the browser
browser.quit()
