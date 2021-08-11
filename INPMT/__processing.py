# -*-coding: utf8 -*
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
from typing import AnyStr, SupportsInt

import geopandas as gpd
import libpysal as lps
import pandas as pd
import numpy as np
from alive_progress import alive_bar
from geopandas import GeoDataFrame
from pandas import DataFrame

try:
    from __utils.raster import (
        density,
        get_pixel_count,
        raster_crop,
        raster_stats,
    )
    from __utils.utils import __get_cfg_val, __read_qml, __strip, format_dataset_output
    from __utils.vector import (
        __read_shp_as_gdf,
        intersect,
        iter_geoseries_as_geodataframe,
        merge_touching,
    )
except ImportError:
    from .__utils.raster import (
        density,
        get_pixel_count,
        raster_crop,
        raster_stats,
    )
    from .__utils.utils import __get_cfg_val, __read_qml, __strip, format_dataset_output
    from .__utils.vector import (
        __read_shp_as_gdf,
        intersect,
        iter_geoseries_as_geodataframe,
        merge_touching,
    )


def set_urban_profile(
    urban_areas: GeoDataFrame,
    path_urban_areas: AnyStr,
    urban_treshold: SupportsInt,
    export: bool = False,
) -> GeoDataFrame:
    """
    # TODO
    """
    merging_result = merge_touching(geodataframe=urban_areas, by="sum")

    result = []
    for poly in merging_result.geometry:
        if poly.area <= urban_treshold:
            result.append("small")
        else:
            result.append("large")
    del poly

    merging_result["Size"] = result
    del result

    if export:
        _, _, output_path = format_dataset_output(
            dataset=path_urban_areas, name="urban_extent"
        )
        merging_result.to_file(output_path)
        return merging_result
    else:
        return merging_result


def get_nearest_park(
    index: SupportsInt, df: DataFrame, villages: GeoDataFrame, parks: GeoDataFrame
) -> DataFrame:
    """
    For each polygon, I check the distance from the point to the boundary of the polygon and compare it to the minimum
    distance found yet (at the start it's 100000 but it is modified in the first occurence).
    Every time a distance is smaller, the minimum distance it's resetted.
    Every time the distance from point to the centroid of the polygon equals 0, it means the polygon of villages is
    inside the polygon of parks. In these cases I set it as a negative value.

    :param index: Row index
    :type: index: SupportsInt
    :param df: A DataFrame of the previous results
    :type: df: DataFrame
    :param villages: A GeoDataFrame of the locations of mosquito counts of Africa
    :type: villages: GeoDataFrame
    :param parks: A GeoDataFrame of the national parks of Africa
    :type: parks: GeoDataFrame
    :return: A DataFrame of the result
    :rtype: DataFrame
    """
    name = None
    loc_np = None
    res_dist = None
    min_dist = int(__get_cfg_val("min_dist"))

    for y in range(len(parks)):
        dist = parks.loc[y, "geometry"].boundary.distance(
            villages.loc[index, "geometry"]
        )
        if dist < min_dist:
            min_dist = dist
            name = parks.loc[y, "NAME"]
            if (
                parks.loc[y, "geometry"].distance(villages.loc[index, "geometry"])
                == 0.0
            ):
                res_dist = -min_dist
                loc_np = "P"
            else:
                res_dist = min_dist
                loc_np = "B"
    _, village_id = __strip(villages.loc[index, "Full_Name"])
    _, np_name = __strip(name)
    df.loc[index, "ID"] = village_id
    df.loc[index, "NP"] = np_name
    df.loc[index, "loc_np"] = loc_np
    df.loc[index, "dist_NP"] = round(res_dist, 3)
    return df


def get_landuse(polygon: AnyStr, dataset: AnyStr) -> tuple[DataFrame, int]:
    """
    Use a shapefile and a raster file to process landuse nature and landuse percentage.
    To do this, I first read the qml (legend file) to get the values and their corresponding labels.
    Then I retrieve a number of pixels by values using the Counter object.
    I process the category area and the landuse percentage using the pixel area and the polygon area

    :param polygon: Path to the shapefile
    :type polygon: AnyStr
    :param dataset: Path to the dataset file
    :type dataset: AnyStr
    :return: A DataFrame updated with the processed values
    :rtype: tuple(DataFrame, SupportsInt)
    """
    __data = []
    __val = None
    __polygon = gpd.read_file(polygon)
    # Retrive the legend file's path
    __data_dir = __get_cfg_val("datasets_storage_path")
    __qml_path = os.path.join(__data_dir, "LANDUSE/ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.qml")
    # Count every pixel from the raster and its value
    dataset, ctr = get_pixel_count(dataset_path=dataset, band=0)
    for c in ctr:
        # Multiply the number of pixels by the resolution of a pixel
        category_area = round(ctr[c] * (dataset.res[0] * dataset.res[1]), 3)
        # Cross product with the geodataframe_aoi's polygon's area to get the percetage of land use of
        # the current category
        percentage = round(((category_area * 100) / __polygon.area[0]), 3)
        __data.append([c, ctr[c], category_area, percentage])
    # Creates a DataFrame from the list processed previously
    df_hab_div = pd.DataFrame(
        __data, columns=["Category", "Nbr of pixels", "Surface (m2)", "Proportion (%)"]
    )
    # Format the .qml file path from the dataset path
    # TODO NBR colonne habitats != Colonnes habitats: deux derières colonnes pas insérées ?
    # TODO val 200 inconnue mais présente de manière normale = la légende ne la répertorie pas ?
    # Snow ice et Nodata ne sont pas insérés: merged avec d'autres colonnes ?
    # TODO Might improve performance by associating the label when searching for the categories
    # Reads the corresponding legend style from the .qml file
    # Associates the category number the label name of the legend values (ridden from a .qml file)
    __style = __read_qml(__qml_path)
    for m, r in df_hab_div.iterrows():
        for n in __style:
            if int(r["Category"]) == int(n[0]):
                __val = n[1]
                break
            else:
                __val = "Unknown"
        df_hab_div.loc[m, "Label"] = __val

    return df_hab_div, len(ctr)


def get_urban_profile(
    villages: AnyStr,
    parks: AnyStr,
    landuse: AnyStr,
    population: AnyStr,
    ndvi: AnyStr,
    swi: AnyStr,
    gws: AnyStr,
    prevalence: AnyStr,
    processing_directory: AnyStr,
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

    :param villages: Path to the shapefile
    :type villages: AnyStr
    :param parks: Path to the shapefile
    :type parks: AnyStr
    :param landuse: Path to the dataset file
    :type landuse: AnyStr
    :param population: Path to the dataset file
    :type population: AnyStr
    :param ndvi: Path to the dataset file
    :type ndvi: AnyStr
    :param swi: Path to the dataset file
    :type swi: AnyStr
    :param gws: Path to the dataset file
    :type gws: AnyStr
    :param prevalence: Path to the dataset file
    :type prevalence: AnyStr
    :param processing_directory: Path to the temporary directory used to store temporary files (then deleted)
    :type processing_directory: AnyStr
    :return: A DataFrame of the processed values
    :rtype: DataFrame
    """
    # Read the shapefiles as GeoDataFrames
    gdf_villages = gpd.read_file(villages)
    gdf_parks = gpd.read_file(parks)
    # Set the projection to 3857 to have distance, etc as meters
    gdf_villages.crs = 3857
    gdf_parks.crs = 3857
    # Retrieves buffesr size for the vilages patches
    buffer_villages = int(__get_cfg_val("buffer_villages"))
    # Create a blank DataFrame to receive the result when iterating below
    cols = [
        "ID",
        "NP",
        "loc_NP",
        "dist_NP",
        "POP",
        "PREVALENCE",
        "ANO_DIV",
        "NDVI_min",
        "NDVI_mean",
        "NDVI_max",
        "SWI_min",
        "SWI_mean",
        "SWI_max",
        "GWS",
        "HAB_DIV",
    ]
    result = pd.DataFrame(columns=cols)

    # Create the progress and the temporary directory used to save some temporary files
    with alive_bar(total=len(gdf_villages)) as pbar:
        for i in range(len(gdf_villages)):
            # Get the minimum distance from the village the park edge border and return the said distance and the
            # park's name
            result = get_nearest_park(index=i, df=result, parks=gdf_parks, villages=gdf_villages)
            result.loc[i, "ANO_DIV"] = gdf_villages.iloc[i].str.count("Y").sum()
            # Transform the GeoSeries as a GeoDataFrame
            p = gpd.GeoDataFrame(gpd.GeoSeries(gdf_villages.iloc[i]["geometry"]))
            p = p.rename(columns={0: "geometry"}).set_geometry("geometry")
            p.crs = 3857
            # Format the path for the temporary file
            p1, pext, _ = format_dataset_output(dataset=villages, name="tmp")
            path_poly = os.path.join(processing_directory, "".join([p1, pext]))

            # Create a buffer of the village centroid
            p.buffer(buffer_villages).to_file(path_poly)
            path_pop_aoi = raster_crop(dataset=population, shapefile=path_poly, processing=processing_directory)
            population_density = density(dataset=path_pop_aoi, area=path_poly, processing=processing_directory)
            result.loc[i, "POP"] = population_density

            # Crop the NDVI data to the buffer extent and process it's min, mean and max value
            path_ndvi_aoi = raster_crop(dataset=ndvi, shapefile=path_poly, processing=processing_directory)
            ndvi_min, ndvi_mean, ndvi_max = raster_stats(path_ndvi_aoi)
            result.loc[i, "NDVI_min"] = ndvi_min
            result.loc[i, "NDVI_mean"] = ndvi_mean
            result.loc[i, "NDVI_max"] = ndvi_max
            # TODO SWI Raster

            path_swi_aoi = raster_crop(dataset=swi, shapefile=path_poly, processing=processing_directory)
            swi_min, swi_mean, swi_max = raster_stats(path_swi_aoi)
            result.loc[i, "SWI_min"] = swi_min
            result.loc[i, "SWI_mean"] = swi_mean
            result.loc[i, "SWI_max"] = swi_max

            with rasterio.open(prevalence) as src:
                x, y = list(gdf_villages.loc[i, 'geometry'].coords)[0]
                # get pixel x+y of the coordinate
                py, px = src.index(x, y)
                # create 1x1px window of the pixel
                window = rasterio.windows.Window(px - 1//2, py - 1//2, 1, 1)
                # read rgb values of the window
                value = src.read(window=window)
            result.loc[i, "PREVALENCE"] = value
            
            path_gws_aoi = raster_crop(dataset=gws, shapefile=path_poly, processing=processing_directory)
            df_gwsd, _ = get_landuse(polygon=path_poly, dataset=path_gws_aoi)

            try:
                df_gwsd = df_gwsd.pivot_table(columns="Label", values="Proportion (%)", aggfunc="sum")
                df_gwsd.rename(index={"Proportion (%)": int(i)}, inplace=True)
                result.loc[i, df_gwsd.columns] = df_gwsd.loc[i, :].values
            except KeyError:
                print("GWS data missing")
                result.loc[i, df_gwsd.columns] = np.nan
                pass

            # Crop the landuse data and make stats out of it, add those stats as new columns for each lines
            path_landuse_aoi = raster_crop(dataset=landuse, shapefile=path_poly, processing=processing_directory)
            df_hd, len_ctr = get_landuse(polygon=path_poly, dataset=path_landuse_aoi)
            result.loc[i, "HAB_DIV"] = len_ctr
            try:
                df_hd = df_hd.pivot_table(
                    columns="Label", values="Proportion (%)", aggfunc="sum"
                )  # noqa
                df_hd.rename(index={"Proportion (%)": int(i)}, inplace=True)
                result.loc[i, df_hd.columns] = df_hd.loc[i, :].values
            except KeyError:
                print("Land use data missing")
                result.loc[i, df_hd.columns] = np.nan
                pass
            pbar()
    return result


def get_countries_profile(
    aoi: AnyStr,
    landuse: AnyStr,
    landuse_polygonized: AnyStr,
    processing_directory: AnyStr,
    population: AnyStr = "",
    anopheles: AnyStr = "",
    distances: bool = False,
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
            - Count the number of species found for each captur sites (sums the number of 'Y' in every rows)

    :param landuse_polygonized:
    :param processing_directory:
    :param aoi: Path to the vector file of the Areas of Interest to process.
    :type aoi: AnyStr
    :param landuse: Raster file path for the land cover of Africa (ESA, 2016), degraded to 300m).
    :type landuse: AnyStr
    :param population: Vector file path for the population of Africa (WorldPop, 2020), Unconstrained, UN adjusted, 100m
    :type population: AnyStr
    :param anopheles: Vector file path of the Anopheles species present in countries in sub-Saharan Africa (Kyalo, 2019)
    :type anopheles: AnyStr
    :param distances: Boolean parameter to know wether or not the distances must be processed.
    :type distances: bool
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
    dist_treshold = __get_cfg_val("dist_treshold")

    # Format datasets outputs with the temporary directory's path
    p1, p1ext, _ = format_dataset_output(dataset=aoi, name="tmp")
    path_poly1 = os.path.join(processing_directory, "".join([p1, p1ext]))
    p2, p2ext, _ = format_dataset_output(dataset=landuse, name="tmp")
    path_poly2 = os.path.join(processing_directory, "".join([p2, p2ext]))

    # Inserts new columns if the data is given or not.
    """
    if population:
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, "SUM_POP", 0)
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, "DENS_POP", 0)
    if distances:
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, "MEAN_DIST", 0)
    """
    if anopheles:
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, "CATCH_SITE", 0)
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, "SPECIE_DIV", 0)

    # Progress bar for the first level
    with alive_bar(total=len(geodataframe_aoi)) as bar_main:
        # Iterates over every polygon and yield its index too
        for i, p in iter_geoseries_as_geodataframe(shapefile=geodataframe_aoi):
            p.to_file(filename=path_poly1)
            # TODO Multithreading to ce qui est en dessous

            bar_main.text("Preparing")  # Pbar 1st level
            # Crops the raster file with the first polygon boundaries then polygonize the result.
            # TODO check if intersecting a polygonized land use of Africa isn't faster than polygonizing small rasters ?
            path_landuse_aoi = raster_crop(dataset=landuse, shapefile=path_poly1, processing=processing_directory)
            gdf_os_pol = intersect(base=landuse_polygonized, overlay=path_poly1, crs=3857)

            # Intersects only if the __data is given at the start.
            """
            if population:
                _, population_aoi = intersect(base=population, overlay=path_poly1, crs=3857, export=True)
            """
            if anopheles:
                _, anopheles_aoi = intersect(base=anopheles, overlay=path_poly1, crs=3857, export=True)

            bar_main.text("Processing")  # Pbar 1st level

            # Progress bar for the second level
            with alive_bar(total=(len(gdf_os_pol) * 5)) as bar_process:
                # Iterates over every polygon and yield its index too
                for o, q in iter_geoseries_as_geodataframe(shapefile=gdf_os_pol):
                    # TODO Multiprocessing tout ce qui est en dessous
                    q.to_file(filename=path_poly2)

                    bar_process.text("Preparing")  # Pbar 2nd level
                    # Extracts the row from geodataframe_aoi corresponding to the entity we're currently iterating over
                    aoi_extract = aoi_extract.append(geodataframe_aoi.loc[[i]], ignore_index=True)

                    # Crops the raster file with the second polygon bounaries
                    path_landuse_aoi_landuse = raster_crop(
                        dataset=path_landuse_aoi,
                        shapefile=path_poly2,
                        processing=processing_directory,
                    )
                    """
                    if population:
                        population_aoi_landuse = intersect(base=population_aoi, overlay=path_poly2, crs=3857)
                    """
                    if anopheles:
                        anopheles_aoi_landuse = intersect(base=anopheles_aoi, overlay=path_poly2, crs=3857)
                        anopheles_aoi_landuse["spnb"] = 0
                    bar_process()  # Pbar 2nd level
                    # TODO performance issue au dessus là
                    # TODO Est-ce que je le calcule pas plusieurs fois vu que j'itère plusieurs fois dessus ici ?
                    bar_process.text("Habitat")  # Pbar 2nd level
                    df_hd, _ = get_landuse(polygon=path_poly2, dataset=path_landuse_aoi_landuse)
                    aoi_extract.loc[i, "HAB"] = df_hd.loc[0, "Label"]
                    aoi_extract.loc[i, "HAB_PROP"] = df_hd.loc[0, "Proportion (%)"]

                    # Count every pixel from the raster and its value
                    __data = []
                    dataset, ctr = get_pixel_count(dataset_path=path_landuse_aoi_landuse, band=0)
                    for c in ctr:
                        # Multiply the number of pixels by the resolution of a pixel
                        category_area = round(ctr[c] * (dataset.res[0] * dataset.res[1]), 3)
                        # Cross product with the geodataframe_aoi's polygon's area to get the percetage of land use of
                        # the current category
                        percentage = ((category_area * 100) / p.area[0])
                        __data.append([c, ctr[c], category_area, percentage])
                    # Creates a DataFrame from the list processed previously
                    df_hab_div = pd.DataFrame(__data,
                                              columns=['Category', 'Nbr of pixels', 'Surface (m2)', 'Proportion (%)'])
                    # Format the .qml file path from the dataset path
                    # TODO NBR colonne habitats != Colonnes habitats: deux derières colonnes pas insérées ?
                    # TODO val 200 inconnue mais présente de manièrre normale = la légende ne la répertorie pas ?
                    # Snow ice et Nodata ne sont pas insérés: merged avec d'autres colonnes ?
                    # TODO export style files from cropped raster so it can be read flawlessly here. Right now i have to
                    #  load it into qgis export it into a qml file by hand.
                    # TODO Might improve performance by associating the label when searching for the categories
                    __dataset_name, _, __qml_path = format_dataset_output(dataset=path_landuse_aoi, ext='.qml')
                    # Reads the corresponding legend style from the .qml file
                    __style = __read_qml(__qml_path)
                    # Associates the category number the label name of the legend values (ridden from a .qml file)
                    for m, r in df_hab_div.iterrows():
                        for n in __style:
                            if r['Category'] == n[0]:
                                __val = n[1]
                            else:
                                __val = 'Unknown'
                        df_hab_div.loc[m, 'Label'] = __val
                    # Checks the __data has been given to process only what is available
                    # TODO Est-ce que ça fait pas bugger par rapport à l'itération de mettre method =='append' ?
                    """
                    if method == 'append:':
                        aoi_extract.loc[o, 'HAB_DIV'] = len(ctr)
                        df_hab_div = df_hab_div.pivot_table(columns='Label',
                                                            values='Proportion (%)',
                                                            aggfunc='sum')
                        df_hab_div.rename(index={'Proportion (%)': int(o)}, inplace=True)
                        aoi_extract.loc[o, df_hab_div.columns] = df_hab_div.loc[o, :].values
                    elif method == 'duplicate':
                        aoi_extract.loc[o, 'HAB'] = df_hab_div.loc[0, 'Label']
                        aoi_extract.loc[o, 'HAB_PROP'] = round(df_hab_div.loc[0, 'Proportion (%)'], 3)
                    """
                    aoi_extract.loc[o, 'HAB'] = df_hab_div.loc[0, 'Label']
                    aoi_extract.loc[o, 'HAB_PROP'] = round(df_hab_div.loc[0, 'Proportion (%)'], 3)
                    bar_process()  # Pbar 2nd level
                    """
                    bar_process.text("Population")  # Pbar 2nd level
                    if population:  # Population and urban patches
                        aoi_extract.loc[o, "SUM_POP"] = int(population_aoi_landuse["DN"].sum())
                        aoi_extract.loc[o, "DENS_POP"] = int(population_aoi_landuse["DN"].sum() / p.area[0])
                    bar_process()  # Pbar 2nd level
                    
                    bar_process.text("Distances")  # Pbar 2nd level
                    if distances:  # Distances and urban fragmentation
                        # No need to intersect it again
                        # https://splot.readthedocs.io/en/stable/users/tutorials/weights.html#weights-from-other-python-objects
                        dbc = lps.weights.DistanceBand.from_dataframe(
                            population_aoi_landuse,
                            threshold=dist_treshold,
                            p=2,
                            binary=False,
                            build_sp=True,
                            silent=True,
                        )
                        aoi_extract.loc[o, "MEAN_DIST"] = round(dbc.mean_neighbors, 4)
                    bar_process()  # Pbar 2nd level
                    """

                    bar_process.text("Anopheles")  # Pbar 2nd level
                    if anopheles:  # Anopheles diversity and catching sites
                        for x in range(0, len(anopheles_aoi_landuse)):
                            anopheles_aoi_landuse.loc[x, "spnb"] = (anopheles_aoi_landuse.iloc[x].str.count("Y").sum())
                        aoi_extract.loc[o, "CATCH_SITE"] = int(len(anopheles_aoi_landuse))
                        aoi_extract.loc[o, "SPECIE_DIV"] = anopheles_aoi_landuse["spnb"].max()
                    bar_process()  # Pbar 2nd level

            bar_main.text("Append")  # Pbar 1st level
            result = result.append(aoi_extract, ignore_index=True)

            bar_main.text("Done")  # Progress bar for the first level
            print("[{}/{}]".format(i + 1, len(geodataframe_aoi)))
            bar_main()  # Progress bar for the first level

        # End
        return result, aoi
