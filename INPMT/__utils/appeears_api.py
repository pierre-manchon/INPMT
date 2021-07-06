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
# https://lpdaacsvc.cr.usgs.gov/appeears/api/
import requests
import geopandas as gpd
from tempfile import TemporaryDirectory

try:
    from utils import format_dataset_output
except ImportError:
    from .utils import format_dataset_output

"""
import os
import geopandas as gpd
from typing import AnyStr
from tempfile import TemporaryDirectory
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from utils import format_dataset_output
except ImportError:
    from .utils import format_dataset_output


def send_NDVI_request(area: AnyStr) -> None:
    # https://medium.com/@sdoshi579/to-read-emails-and-download-attachments-in-python-6d7d6b60269
    # Various options to make the webscraper work
    options = Options()
    options.page_load_strategy = 'normal'
    # options.headless = True
    path_driver = os.path.join(os.getcwd(), 'dependencies/chromedriver.exe')
    website = 'https://lpdaacsvc.cr.usgs.gov/appeears/task/area'

    # Create the browser driver and access the website
    browser = webdriver.Chrome(executable_path=path_driver, options=options)
    browser.get(website)

    # Wait until the page is loaded to fill in the login credentials and hit the login button
    _ = WebDriverWait(browser, 3).until(EC.presence_of_element_located((By.CLASS_NAME, "button-with-notes")))
    username_placeholder = browser.find_element_by_id("username")
    username_placeholder.clear()
    username_placeholder.send_keys("pierre.manchon@pm.me")
    password_placeholder = browser.find_element_by_name("password")
    password_placeholder.clear()
    password_placeholder.send_keys("u7-VYcL3BWv_BFnN#dpy4GGhf#4Sz^2@kqwa%Be$ddGZA?fAb4@jLj*bVS$QkRM4dV?XX4xdVkjD@u@xT+X3AMNpHy!$m!gmgnr2WQ5m+%QT2A&TV99X*nDLcWswYQ2x")
    browser.find_element_by_name("commit").click()

    # Wait until the page is loaded to the "Extract Area Sample" page
    _ = WebDriverWait(browser, 500).until(EC.presence_of_element_located((By.CLASS_NAME, "well")))
    browser.find_element_by_class_name('thumbnail').click()

    # Fill the Area name placholder with the string  'AREA NAME'
    area_sample_name = 'AREA NAME'
    taskName = browser.find_element_by_id("taskName")
    taskName.clear()
    taskName.send_keys(area_sample_name)

    # Gives the shapefile of the desired area
    with TemporaryDirectory() as tmp_directory:
        area_shapefile = gpd.read_file(area)
        *_, geojson_path = format_dataset_output(dataset=tmp_directory, name='area', ext=".geojson")
        area_shapefile.to_file(geojson_path, driver='GeoJSON')
        shapeFileUpload = browser.find_elements_by_id('shapeFileUpload')
        shapeFileUpload[0].send_keys(geojson_path)

    # Assign the starting date to 06012021
    date_debut = '06012021'
    startDate = browser.find_element_by_id("startDate")
    startDate.clear()
    startDate.click()
    startDate.send_keys(date_debut)

    # Assign the ending date to 07012021
    date_fin = '07012021'
    endDate = browser.find_element_by_id("endDate")
    endDate.clear()
    endDate.click()
    endDate.send_keys(date_fin)

    # Search satellites that produce NDVI data and pick:
    # Terra MODIS Vegetation Indices (NDVI & EVI)
    # MOD13A1.006, 500m, 16day, (2000-02-18 to Present)
    product = browser.find_element_by_id("product")
    product.click()
    product.send_keys('NDVI')
    product_title = browser.find_elements(By.XPATH, '//ul[@class="dropdown-menu"]/li/a/div[@class="product-description word-break"]')
    product_desc = browser.find_elements(By.XPATH, '//ul[@class="dropdown-menu"]/li/a/div[@class="product-details word-break"]')
    for x, y in zip(product_title, product_desc):
        if 'Terra' in x.text and 'NDVI' in x.text and '500m' in y.text:
            x.click()

    # Pick the actual NDVI layers from the available data
    values = browser.find_elements(By.XPATH, '//div[@class="list-group-item layers layers-available"]/div/table/tbody/tr/td[@class="layer-name word-break"]')
    add = browser.find_elements(By.XPATH, '//div[@class="list-group-item layers layers-available"]/div/table/tbody/tr/td[@class="layer-add"]')
    for i, o in zip(values, add):
        if 'NDVI' in i.text:
            i.click()

    # Pick the native projection
    projection = browser.find_element_by_id("projection")
    projection.click()
    native_projection = browser.find_element_by_id('typeahead-670-8079-option-0')
    native_projection.click()

    # Submit the request
    submit = browser.find_elements(By.XPATH, '//div[@class="col-md-12 text-right button-group"]/button[@class="btn btn-text btn-primary"]')
    submit[0].click()

    browser.quit()
"""


class APPEEARSapi:
    """
    AA
    """
    def __init__(self):
        pass

    def __enter__(self):
        # Login
        self.response = requests.post('https://lpdaacsvc.cr.usgs.gov/appeears/api/login', auth=('pierre.manchon', ''))
        self.token_response = self.response.json()
        self.token = self.token_response['token']
        return self.token

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Logout
        self.response = requests.post(
            'https://lpdaacsvc.cr.usgs.gov/appeears/api/logout',
            headers={'Authorization': 'Bearer {0}'.format(self.token)})

    def __to_geojson(self, area):
        with TemporaryDirectory() as tmp_directory:
            area_shapefile = gpd.read_file(area)
            *_, geojson_path = format_dataset_output(dataset=tmp_directory, name='area', ext=".geojson")
            area_shapefile.to_file(geojson_path, driver='GeoJSON')
            return geojson_path

    def send_request(self, area, startDate, endDate, layer, product, projection):
        # create the task request
        task = {
          "task_type": "area",
          "task_name": "{}".format(area),
          "params":
          {
            "dates": [
            {
              "startDate": "{}".format(startDate),
              "endDate": "02-14-2018".format(endDate)
            }],
            "layers": [
            {
              "layer": "{}".format(layer),
              "product": "{}".format(product)
            }],
            "output":
            {
              "format":
              {
                "type": "geotiff"
              },
              "projection": "{}".format(projection)
            },
            "geo":
            {
              "type": "FeatureCollection",
              "fileName": "User-Drawn-Polygon",
              "features": [
              {
                "type": "Feature",
                "properties":
                {},
                "geometry":
                {
                  "type": "Polygon",
                  "coordinates": [
                    [
                      [-104.29394567012787, 43.375488325953484],
                      [-104.29394567012787, 44.562011763453484],
                      [-103.17334020137787, 44.562011763453484],
                      [-103.17334020137787, 43.375488325953484],
                      [-104.29394567012787, 43.375488325953484]
                    ]
                  ]
                }
              }]
            }
          }
        }

        # submit the task request
        response = requests.post(
            'https://lpdaacsvc.cr.usgs.gov/appeears/api/task',
            json=task,
            headers={'Authorization': 'Bearer {0}'.format(self.token)})
        task_response = response.json()
        print(task_response)
        # TODO recuperer le token de la task

    def get_request_state(self):
        task_id = 'd6c36957-7337-4ceb-ac38-36e58038a9fb'
        response = requests.get(
            'https://lpdaacsvc.cr.usgs.gov/appeears/api/status/{0}'.format(task_id),
            headers={'Authorization': 'Bearer {0}'.format(self.token)})
        status_response = response.json()
        print(status_response)

    def download_product(self):
        pass
