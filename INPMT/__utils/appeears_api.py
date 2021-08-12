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
import cgi
import json
import os
from tempfile import TemporaryDirectory

import geopandas as gpd
import requests

try:
    from utils import format_dataset_output
except ImportError:
    from .utils import format_dataset_output


class APPEEARSapi:
    """
    Made using APPEEARS's api
    https://lpdaacsvc.cr.usgs.gov/appeears/api/?language=Python%203
    """

    def __init__(self):
        self.task_id = None
        self.file_id = None

    def __enter__(self):
        # Login
        self.response = requests.post(
            "https://lpdaacsvc.cr.usgs.gov/appeears/api/login",
            auth=(
                "pierre.manchon",
                "u7-VYcL3BWv_BFnN#dpy4GGhf#4Sz^2@kqwa%Be$ddGZA?fAb4@jLj*bVS$QkRM4dV?XX4xdVkjD@u@xT+X3AMNpHy!$m!gmgnr2WQ5m+%QT2A&TV99X*nDLcWswYQ2x",
            ),
        )
        self.token_response = self.response.json()
        self.token = self.token_response["token"]
        return self.token

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Logout
        self.response = requests.post(
            "https://lpdaacsvc.cr.usgs.gov/appeears/api/logout",
            headers={"Authorization": "Bearer {0}".format(self.token)},
        )

    def __to_geojson(self, area):
        with TemporaryDirectory() as tmp_directory:
            area_shapefile = gpd.read_file(area)
            *_, geojson_path = format_dataset_output(
                dataset=tmp_directory, name="area", ext=".geojson"
            )
            area_shapefile.to_file(geojson_path, driver="GeoJSON")
        geojson_file = open(geojson_path)
        j = json.load(geojson_file)
        return j["features"]

    def send_request(self, area, startDate, endDate, layer, product, projection):
        # create the task request
        task = {
            "task_type": "area",
            "task_name": "{}".format(area),
            "params": {
                "dates": [
                    {
                        "startDate": "{}".format(startDate),
                        "endDate": "{}".format(endDate),
                    }
                ],
                "layers": [
                    {"layer": "{}".format(layer), "product": "{}".format(product)}
                ],
                "output": {
                    "format": {"type": "geotiff"},
                    "projection": "{}".format(projection),
                },
                "geo": {
                    "type": "FeatureCollection",
                    "fileName": "User-Drawn-Polygon",
                    "features": self.__to_geojson(area=area),
                },
            },
        }

        # submit the task request
        response = requests.post(
            "https://lpdaacsvc.cr.usgs.gov/appeears/api/task",
            json=task,
            headers={"Authorization": "Bearer {0}".format(self.token)},
        )
        self.task_id = response.json()
        return self.task_id

    def get_request_state(self):
        response = requests.get(
            "https://lpdaacsvc.cr.usgs.gov/appeears/api/status/{0}".format(
                self.task_id
            ),
            headers={"Authorization": "Bearer {0}".format(self.token)},
        )
        status_response = response.json()
        print(status_response)

    def get_file_credentials(self):
        response = requests.get(
            "https://lpdaacsvc.cr.usgs.gov/appeears/api/bundle/{0}".format(self.task_id)
        )
        bundle_response = response.json()
        print(bundle_response)
        for x in bundle_response["files"]:
            if x["file_name"] == "MOD13A1-006-Statistics.csv":
                print("found {}, {}".format(x["file_name"], x["file_id"]))
                self.file_id = x["file_id"]
        return self.file_id

    def download_product(self):
        response = requests.get("https://lpdaacsvc.cr.usgs.gov/appeears/api/bundle/{0}/{1}".format(
            self.task_id,
            self.file_id), stream=True)

        # parse the filename from the Content-Disposition header
        content_disposition = cgi.parse_header(response.headers["Content-Disposition"])[1]
        filename = os.path.basename(content_disposition["filename"])

        # create a destination directory to store the file in
        dest_dir = r"H:\Cours\M2\Cours\HGADU03 - Mémoire\Projet Impact PN Anophèles\datasets\test NDVI/"
        filepath = os.path.join(dest_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # write the file to the destination directory
        with open(filepath, "wb") as f:
            for data in response.iter_content(chunk_size=8192):
                f.write(data)
