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
import os
import warnings
from typing import Any, AnyStr

import geopandas as gpd
import pandas as pd
import xarray as xr
from alive_progress import alive_bar
from geopandas import GeoDataFrame
from pandas import DataFrame

try:
    from utils.raster import (
        get_pixel_count,
        raster_crop,
    )
    from utils.utils import (
        __read_qml,
        __strip,
        format_dataset_output,
        get_cfg_val,
    )
    from utils.vector import (
        __read_shp_as_gdf,
        intersect,
        iter_geoseries_as_geodataframe,
    )
except ImportError:
    from INPMT.utils.raster import (
        get_pixel_count,
        raster_crop,
    )
    from INPMT.utils.utils import (
        __read_qml,
        __strip,
        format_dataset_output,
        get_cfg_val,
    )
    from INPMT.utils.vector import (
        __read_shp_as_gdf,
        intersect,
        iter_geoseries_as_geodataframe,
    )

warnings.filterwarnings("ignore")


def get_nearest_park(
        parks: GeoDataFrame,
        geom_villages: GeoDataFrame
) -> tuple[Any | None, str | None, str]:
    """
    For each polygon, I check the distance from the point to the boundary of the polygon and compare it to the minimum
    distance found yet (at the start it's 100000 but it is modified in the first occurrence).
    Every time a distance is smaller, the minimum distance it's reset.
    Every time the distance from point to the centroid of the polygon equals 0, it means the polygon of villages is
    inside the polygon of parks. In these cases I set it as a negative value.
    :param geom_villages: A GeoDataFrame of the locations of mosquito counts of Africa
    :type: geom_villages: GeoDataFrame
    :param parks: A GeoDataFrame of the national parks of Africa
    :type: parks: GeoDataFrame
    :return: A DataFrame of the result
    :rtype: DataFrame
    """
    name = None
    loc_np = None
    res_dist = None
    min_dist = 1000000000000000
    for i in range(len(parks)):
        dist = parks.loc[i, "geometry"].boundary.distance(geom_villages.centroid)
        if dist < min_dist:
            min_dist = dist
            name = parks.loc[i, "NAME"]
            if parks.loc[i, "geometry"].contains(geom_villages):
                res_dist = -min_dist
                loc_np = "P"
            else:
                res_dist = min_dist
                loc_np = "B"
    return res_dist, loc_np, name


def get_landuse(
    polygon: AnyStr,
    dataset: AnyStr,
    legend_filename: AnyStr,
    processing: AnyStr,
    item_type: AnyStr,
) -> tuple[DataFrame, int]:
    """
    Use a shapefile and a raster file to process landuse nature and landuse percentage.
    To do this, I first read the qml (legend file) to get the values and their corresponding labels.
    Then I retrieve a number of pixels by values using the Counter object.
    I process the category area and the landuse percentage using the pixel area and the polygon area

    :param processing:
    :type processing:
    :param legend_filename:
    :param polygon: Path to the shapefile
    :type polygon: AnyStr
    :param dataset: Path to the dataset file
    :type dataset: AnyStr
    :param item_type: Type of the item containing labels, values and colors for the legend.
    :type item_type: AnyStr
    :return: A DataFrame updated with the processed values
    :rtype: tuple(DataFrame, SupportsInt)
    """
    __val = None
    __polygon = gpd.read_file(polygon, encoding="windows-1252")
    # Retrieve the legend file's path
    __data_dir = get_cfg_val("datasets_storage_path")
    __qml_path = os.path.join(__data_dir, legend_filename)
    # Count every pixel from the raster and its value
    # TODO here i retrieve the area by multiplying the width and height resolutions
    #  => need to get the pixels area for each pixel here
    df_hab_div = get_pixel_count(dataset_path=dataset, processing=processing)
    # Format the .qml file path from the dataset path
    __style = __read_qml(path_qml=__qml_path, item_type=item_type)
    for m, r in df_hab_div.iterrows():
        for n in __style:
            # https://stackoverflow.com/a/8948303/12258568
            if int(float(r["Category"])) == int(n[0]):
                __val = n[1]
                break
            else:
                __val = "Unknown"
        df_hab_div.loc[m, "Label"] = __val
    return df_hab_div, len(df_hab_div)


def get_urban_profile(
    villages: AnyStr,
    parks: AnyStr,
    population: xr.Dataset,
    landuse: xr.Dataset,
    ndvi: xr.Dataset,
    swi: xr.Dataset,
    gws: xr.Dataset,
    prevalence: xr.Dataset,
    loc: bool = True,
) -> DataFrame:
    """
    I use 4 different data, 2 vectors that I read in a GeoDataFrame at the beginning of the script and 2 raster.
    Then, I iterate on the GeoDataFrame of the villages.
    This allows me to make calculations for each entity and not for the whole layer.

    For each iteration:
    - I first calculate which is the nearest park with the ***get_nearest_park*** function. In addition, if the village
        is in the park, I transform the value into a negative value),
    - I count the number of mosquito species in the village,
    - I transform the GeoSeries in GeoDataFrame: The result that we obtain when we iterate on each line of a
        GeoDataFrame, is an object of type GeoSeries. I transform it in GeoDataFrame because these two objects have
        different properties (in particular to calculate a buffer or especially to cut a raster),
    - I calculate a buffer of 500m,
    - I cut my raster of NDVI values with the ***raster_crop*** function. This function has the particularity to produce
        a new raster file that I have to save and then reopen. Indeed, the rasterio package does not allow to overwrite
        files as it can be done with geopandas,
    - I read the raster that I have cut and then calculate statistical values like the minimum, the average and the
        maximum thanks to the ***raster_stats*** function,
    - I cut my raster of NDVI values with the ***raster_crop*** function. This function has the particularity to produce
        a new raster file that I have to save and then reopen. Indeed, the rasterio package does not allow to overwrite
        files as it can be done with geopandas (which I just use above),
    - I read the raster that I cut out then I calculate the percentages of land use and I associate them to the nature
        of these land uses with the ***get_landuse*** function

    :param loc: In or out of the national parks buffers
    :type loc: bool
    :param villages: Path to the shapefile
    :type villages: AnyStr
    :param parks: Path to the shapefile
    :type parks: AnyStr
    :param population: A Dataset with every type of data in it
    :type population: xr.Dataset
    :param population: A Dataset with every type of data in it
    :type population: xr.Dataset
    :param landuse: A Dataset with every type of data in it
    :type landuse: xr.Dataset
    :param ndvi: A Dataset with every type of data in it
    :type ndvi: xr.Dataset
    :param swi: A Dataset with every type of data in it
    :type swi: xr.Dataset
    :param gws: A Dataset with every type of data in it
    :type gws: xr.Dataset
    :param prevalence: A Dataset with every type of data in it
    :type prevalence: xr.Dataset
    :return: A DataFrame of the processed values
    :rtype: DataFrame
    """
    buffer_500 = 500
    buffer_2000 = 2000
    # Read the shapefiles as GeoDataFrames
    gdf_villages = gpd.read_file(villages)
    gdf_parks = gpd.read_file(parks)
    # Set the projection to 3857 to have distance, etc as meters
    # Retrieves buffer size for the villages patches
    # Create a blank DataFrame to receive the result when iterating below
    cols = [
        "ID",
        "x",
        "y",
        "NP",
        "loc_NP",
        "dist_NP",
        "POP",
        "PREVALENCE",
        "ANO_DIV",
        "SWI_500",
        "NDVI_min_500",
        "NDVI_mean_500",
        "NDVI_max_500",
        "HAB_DIV_500",
        "POP_2000",
        "PREVALENCE_2000",
        "ANO_DIV_2000",
        "SWI_2000",
        "NDVI_min_2000",
        "NDVI_mean_2000",
        "NDVI_max_2000",
        "HAB_DIV_2000",
    ]
    result = pd.DataFrame(columns=cols)
    # Create the progress and the temporary directory used to save some temporary files
    with alive_bar(total=len(gdf_villages)) as pbar:
        for i in range(len(gdf_villages[:50])):
            _, village_id = __strip(gdf_villages.loc[i, "Full_Name"])
            result.loc[i, "ID"] = village_id
            result.loc[i, "ANO_DIV"] = gdf_villages.iloc[i].str.count("Y").sum()

            # Geometry
            geom = gdf_villages.loc[i, "geometry"]
            geom_500 = geom.buffer(buffer_500)
            geom_2000 = geom.buffer(buffer_2000)
            xmin500, ymin500, xmax500, ymax500 = geom_500.bounds
            xmin2000, ymin2000, xmax2000, ymax2000 = geom_2000.bounds

            # Get the minimum distance from the village the park edge border and return the said distance and the
            # park's name
            if loc:
                res_dist, loc_np, np_name = get_nearest_park(parks=gdf_parks, geom_villages=geom_2000)
                result.loc[i, "NP"] = np_name
                result.loc[i, "loc_NP"] = loc_np
                result.loc[i, "dist_NP"] = round(res_dist, 3)

            # Coordinates
            result.loc[i, "x"] = geom_500.centroid.x
            result.loc[i, "y"] = geom_500.centroid.y

            print(village_id, np_name, loc_np, res_dist, [xmin500, ymin500, xmax500, ymax500], [xmin2000, ymin2000, xmax2000, ymax2000])
            """
            # RESOLUTION IS 100 METERS SO A BUFFER
            # For 500 meters
            datasets_sliced_500 = [population.sel(x=slice(xmin500, xmax500), y=slice(ymin500, ymax500)).chunk(),
                                   landuse.sel(x=slice(xmin500, xmax500), y=slice(ymin500, ymax500)).chunk(),
                                   ndvi.sel(x=slice(xmin500, xmax500), y=slice(ymin500, ymax500)).chunk(),
                                   swi.sel(x=slice(xmin500, xmax500), y=slice(ymin500, ymax500)).chunk(),
                                   gws.sel(x=slice(xmin500, xmax500), y=slice(ymin500, ymax500)).chunk(),
                                   prevalence.sel(x=slice(xmin500, xmax500), y=slice(ymin500, ymax500)).chunk()]
            dataset_500 = xr.merge(datasets_sliced_500)
            # For 2000 meters
            datasets_sliced_2000 = [population.sel(x=slice(xmin2000, xmax2000), y=slice(ymin2000, ymax2000)).chunk(),
                                   landuse.sel(x=slice(xmin2000, xmax2000), y=slice(ymin2000, ymax2000)).chunk(),
                                   ndvi.sel(x=slice(xmin2000, xmax2000), y=slice(ymin2000, ymax2000)).chunk(),
                                   swi.sel(x=slice(xmin2000, xmax2000), y=slice(ymin2000, ymax2000)).chunk(),
                                   gws.sel(x=slice(xmin2000, xmax2000), y=slice(ymin2000, ymax2000)).chunk(),
                                   prevalence.sel(x=slice(xmin2000, xmax2000), y=slice(ymin2000, ymax2000)).chunk()]
            dataset_2000 = xr.merge(datasets_sliced_2000)

            result.loc[i, "POP_500"] = dataset_500['population'].sum(skipna=True).values
            result.loc[i, "POP_2000"] = dataset_2000['population'].sum(skipna=True).values

            # I divide by 10 000 because Normalized Difference Vegetation
            # Index is usually between -1 and 1.
            # For 500 meters
            result.loc[i, "NDVI_min_500"] = dataset_500['ndvi'].min(skipna=True) / 10000
            result.loc[i, "NDVI_mean_500"] = dataset_500['ndvi'].mean(skipna=True) / 10000
            result.loc[i, "NDVI_max_500"] = dataset_500['ndvi'].max(skipna=True) / 10000
            # For 2000 meters
            result.loc[i, "NDVI_min_2000"] = dataset_2000['ndvi'].min(skipna=True) / 10000
            result.loc[i, "NDVI_mean_2000"] = dataset_2000['ndvi'].mean(skipna=True) / 10000
            result.loc[i, "NDVI_max_2000"] = dataset_2000['ndvi'].max(skipna=True) / 10000

            # https://land.copernicus.eu/global/products/SWI I divide by a 2
            # because SWI data must be between 0 and 100.
            result.loc[i, "SWI_500"] = dataset_500['swi'].sum(skipna=True) / 2
            result.loc[i, "SWI_2000"] = dataset_2000['swi'].sum(skipna=True) / 2

            # https://malariaatlas.org/explorer/#/ I multiply by 100 because PREVALENCE is a percentage between 0
            # and 100.
            result.loc[i, "PREVALENCE_500"] = dataset_500['prevalence'].sum(skipna=True) * 100
            result.loc[i, "PREVALENCE_2000"] = dataset_2000['prevalence'].sum(skipna=True) * 100
            result.loc[i, gws.columns] = gws.loc[i, :].values
            result.loc[i, "HAB_DIV"] = len_ctr
            result.loc[i, hd.columns] = hd.loc[i, :].values
            """
            pbar()
    return result


def get_countries_profile(
    aoi: AnyStr,
    landuse: AnyStr,
    landuse_polygonized: AnyStr,
    processing_directory: AnyStr,
    anopheles: AnyStr = "",
) -> tuple[GeoDataFrame, AnyStr]:
    """
    Takes a Geodataframe as an input and iterate over every of its polygons, each as a new GeoDataFrame.

    For every of those polygons, this function does two types of things:
        - Crop/Intersect the __data
        - Process the __data

    There is four kind of __data to be processed:
        - Land use
            - Read and count pixel values to see the diversity of these values
            - Read and associate the labels with the pixel values to get the land use categories and the proportionality
        - Population
            - Read every vectorized pixel and sums their value to get the total population.
            - Does the same thing but divide by the area to get the density.
        - Distances
            - Calculate the mean distance for every polygons of urban settlement to get the fragmentation index
        - Anopheles species (mosquitoes)
            - Count every point in the polygon to get the number of sites where anopheles (mosquitoes) where captured
            - Count the number of species found for each capture sites (sums the number of 'Y' in every rows)

    :param landuse_polygonized:
    :param processing_directory:
    :param aoi: Path to the vector file of the Areas of Interest to process.
    :type aoi: AnyStr
    :param landuse: Raster file path for the land cover of Africa (ESA, 2016), degraded to 300m).
    :type landuse: AnyStr
    :param anopheles: Vector file path of the Anopheles species present in countries in sub-Saharan Africa (Kyalo, 2019)
    :type anopheles: AnyStr
    :return: Same file as input but with additional columns corresponding to the results of the calculations
    :rtype: tuple[GeoDataFrame, AnyStr]
    """

    # Creates empty GeoDataFrames used later to store the results
    result = GeoDataFrame()
    aoi_extract = GeoDataFrame()
    try:
        aoi_extract.insert(aoi_extract.shape[1] - 1, "HAB", 0)
        aoi_extract.insert(aoi_extract.shape[1] - 1, "HAB_PROP", 0)
    except ValueError:
        aoi_extract.insert(0, "HAB", 0)
        aoi_extract.insert(0, "HAB_PROP", 0)
    geodataframe_aoi = __read_shp_as_gdf(shapefile=aoi)
    geodataframe_aoi.index.name = "id"

    # Format datasets outputs with the temporary directory's path
    p1, p1ext, _ = format_dataset_output(dataset=aoi, name="tmp")
    path_poly1 = os.path.join(processing_directory, "".join([p1, p1ext]))
    p2, p2ext, _ = format_dataset_output(dataset=landuse, name="tmp")
    path_poly2 = os.path.join(processing_directory, "".join([p2, p2ext]))

    # Inserts new columns if the data is given or not.
    if anopheles:
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, "CATCH_SITE", 0)
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, "SPECIE_DIV", 0)

    # Progress bar for the first level
    with alive_bar(total=len(geodataframe_aoi)) as bar_main:
        # Iterates over every polygon and yield its index too
        for i, p in iter_geoseries_as_geodataframe(shapefile=geodataframe_aoi):
            p.to_file(filename=path_poly1)
            # TODO Multithreading everything below

            bar_main.text("Preparing")  # Pbar 1st level
            # Crops the raster file with the first polygon boundaries then polygonize the result.
            # TODO check if intersecting a polygonized land use of Africa isn't faster than polygonizing small rasters ?
            path_landuse_aoi = raster_crop(
                dataset=landuse, shapefile=path_poly1, processing=processing_directory
            )
            gdf_os_pol = intersect(
                base=landuse_polygonized, overlay=path_poly1, crs=3857
            )

            # Intersects only if the __data is given at the start.
            if anopheles:
                _, anopheles_aoi = intersect(
                    base=anopheles, overlay=path_poly1, crs=3857, export=True
                )

            bar_main.text("Processing")  # Pbar 1st level

            # Progress bar for the second level
            with alive_bar(total=(len(gdf_os_pol) * 5)) as bar_process:
                # Iterates over every polygon and yield its index too
                for o, q in iter_geoseries_as_geodataframe(shapefile=gdf_os_pol):
                    # TODO Multiprocessing everything below
                    q.to_file(filename=path_poly2)

                    bar_process.text("Preparing")  # Pbar 2nd level
                    # Extracts the row from geodataframe_aoi corresponding to the entity we're currently iterating over
                    aoi_extract = aoi_extract.append(
                        geodataframe_aoi.loc[[i]], ignore_index=True
                    )

                    # Crops the raster file with the second polygon boundaries
                    path_landuse_aoi_landuse = raster_crop(
                        dataset=path_landuse_aoi,
                        shapefile=path_poly2,
                        processing=processing_directory,
                    )
                    if anopheles:
                        anopheles_aoi_landuse = intersect(
                            base=anopheles_aoi, overlay=path_poly2, crs=3857
                        )
                        anopheles_aoi_landuse["spnb"] = 0
                    bar_process()  # Pbar 2nd level
                    # TODO performance issue above there
                    # TODO Am I not calculating it several times as I iterate on it several times here?
                    bar_process.text("Habitat")  # Pbar 2nd level
                    df_hd, _ = get_landuse(
                        polygon=path_poly2,
                        dataset=path_landuse_aoi_landuse,
                        legend_filename="LANDUSE/ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.qml",
                        item_type="item",
                        processing=anopheles,
                    )
                    aoi_extract.loc[i, "HAB"] = df_hd.loc[0, "Label"]
                    aoi_extract.loc[i, "HAB_PROP"] = df_hd.loc[0, "Proportion (%)"]

                    # Count every pixel from the raster and its value
                    __data = []
                    dataset, ctr = get_pixel_count(
                        dataset_path=path_landuse_aoi_landuse, processing=anopheles
                    )
                    for c in ctr:
                        # Multiply the number of pixels by the resolution of a pixel
                        category_area = round(
                            ctr[c] * (dataset.res[0] * dataset.res[1]), 3
                        )
                        # Cross product with the geodataframe_aoi's polygon's area to get the percentage of land use of
                        # the current category
                        percentage = (category_area * 100) / p.area[0]
                        __data.append([c, ctr[c], category_area, percentage])
                    # Creates a DataFrame from the list processed previously
                    df_hab_div = pd.DataFrame(
                        __data,
                        columns=[
                            "Category",
                            "Nbr of pixels",
                            "Surface (m2)",
                            "Proportion (%)",
                        ],
                    )

                    __dataset_name, _, __qml_path = format_dataset_output(
                        dataset=path_landuse_aoi, ext=".qml"
                    )
                    # Reads the corresponding legend style from the .qml file
                    __style = __read_qml(path_qml=__qml_path, item_type="item")
                    # Associates the category number the label name of the legend values (ridden from a .qml file)
                    for m, r in df_hab_div.iterrows():
                        for n in __style:
                            if r["Category"] == n[0]:
                                __val = n[1]
                            else:
                                __val = "Unknown"
                        df_hab_div.loc[m, "Label"] = __val
                    # Checks the __data has been given to process only what is available
                    aoi_extract.loc[o, "HAB"] = df_hab_div.loc[0, "Label"]
                    aoi_extract.loc[o, "HAB_PROP"] = round(
                        df_hab_div.loc[0, "Proportion (%)"], 3
                    )
                    bar_process()  # Pbar 2nd level

                    bar_process.text("Anopheles")  # Pbar 2nd level
                    if anopheles:  # Anopheles diversity and catching sites
                        for x in range(0, len(anopheles_aoi_landuse)):
                            anopheles_aoi_landuse.loc[x, "spnb"] = (
                                anopheles_aoi_landuse.iloc[x].str.count("Y").sum()
                            )
                        aoi_extract.loc[o, "CATCH_SITE"] = int(
                            len(anopheles_aoi_landuse)
                        )
                        aoi_extract.loc[o, "SPECIE_DIV"] = anopheles_aoi_landuse[
                            "spnb"
                        ].max()
                    bar_process()  # Pbar 2nd level

            bar_main.text("Append")  # Pbar 1st level
            result = result.append(aoi_extract, ignore_index=True)
            bar_main.text("Done")  # Progress bar for the first level
            print(f"[{i + 1}/{len(geodataframe_aoi)}]")
            bar_main()  # Progress bar for the first level
        # End
        return result, aoi
