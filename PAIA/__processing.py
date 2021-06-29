# -*-coding: utf8 -*
"""
PAIA
A tool to process data to learn more about Protected Areas Impact on Malaria Transmission

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
import math
import pandas as pd
import libpysal as lps
from alive_progress import alive_bar
from pandas import DataFrame
from geopandas import GeoDataFrame
from typing import AnyStr, SupportsInt
from timeit import default_timer

try:
    from __utils.vector import merge_touching, to_wkt, iter_geoseries_as_geodataframe, intersect
    from __utils.raster import raster_crop, get_pixel_count, polygonize
    from __utils.utils import format_dataset_output, __getConfigValue, __read_qml
except ImportError:
    from .__utils.vector import merge_touching, to_wkt, iter_geoseries_as_geodataframe, intersect
    from .__utils.raster import raster_crop, get_pixel_count, polygonize
    from .__utils.utils import format_dataset_output, __getConfigValue, __read_qml


def set_urban_profile(
        urban_areas: GeoDataFrame,
        path_urban_areas: AnyStr,
        urban_treshold: SupportsInt,
        export: bool = False
) -> GeoDataFrame:
    """
    # TODO
    """
    merging_result = merge_touching(geodataframe=urban_areas)

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
        _, _, output_path = format_dataset_output(dataset=path_urban_areas, name='urban_extent')
        merging_result.to_file(output_path)
        return merging_result
    else:
        return merging_result


def get_distances(pas: GeoDataFrame,
                  urban_areas: GeoDataFrame,
                  path_urban_areas: AnyStr,
                  export: bool = False
                  ) -> DataFrame:
    """
    # TODO
    """
    urban_treshold = __getConfigValue('urban_area_treshold')
    ug = set_urban_profile(urban_areas=urban_areas,
                           path_urban_areas=path_urban_areas,
                           urban_treshold=urban_treshold)

    centros = []
    for r in zip(ug.fid, ug.DN, ug.Size, ug.geometry):
        if r[2] == 'small':
            centros.append([r[0], str(r[3].centroid)])
        else:
            centros.append([r[0]])
            pass
    del r
    df = pd.DataFrame(centros, columns=['fid', 'centro'])
    del centros
    df = to_wkt(df=df, column='centro')
    ug = ug.merge(df, on='fid')
    del df

    result = []
    weighted_dist = None
    for u in ug.values:
        min_dist = __getConfigValue('min_dist')
        name = None
        for p in pas.values:
            dist = p[3].distance(u[3])
            if dist < min_dist:
                min_dist = dist
                try:
                    weighted_dist = u[1]/(min_dist*math.sqrt(p[3].area))
                except ZeroDivisionError:
                    weighted_dist = u[1]
                name = p[1]
        result.append([u[0], u[1], u[2], u[3], name, min_dist, weighted_dist])
    del dist, min_dist, name, p, u

    cols = ug.keys().values.tolist()
    cols.append('distance')
    df = pd.DataFrame(result, columns=cols)
    del result

    if export:
        _, _, output_path = format_dataset_output(dataset=path_urban_areas, name='distances', ext='.xlsx')
        df.to_excel(output_path, index=False)
        return df
    else:
        return df


def get_profile(
        geodataframe_aoi: GeoDataFrame,
        aoi: AnyStr,
        landuse: AnyStr,
        population: AnyStr = '',
        anopheles: AnyStr = '',
        method: AnyStr = 'duplicate',
        distances: bool = False,
        export: bool = False
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

    :param method:
    :param geodataframe_aoi: GeoDatFrame of the Areas of Interest to process.
    :type geodataframe_aoi: GeoDataFrame
    :param aoi: Path to the vector file of the Areas of Interest to process.
    :type aoi: AnyStr
    :param landuse: Raster file path for the land cover of Africa (ESA, 2016), degraded to 300m).
    :type landuse: AnyStr
    :param method: The __data is produced as a duplicate for each habitat (default) or groupped by countries
    :type method: AnyStr
    :param population: Vector file path for the population of Africa (WorldPop, 2020), Unconstrained, UN adjusted, 100m
    :type population: AnyStr
    :param anopheles: Vector file path of the Anopheles species present in countries in sub-Saharan Africa (Kyalo, 2019)
    :type anopheles: AnyStr
    :param distances: Boolean parameter to know wether or not the distances must be processed.
    :type distances: bool
    :param export: Same file as input but with additional columns corresponding to the results of the calculations
    :type export: bool
    :return: Same file as input but with additional columns corresponding to the results of the calculations
    :rtype: tuple[GeoDataFrame, AnyStr]
    """

    # Creates empty GeoDataFrames used later to store the results
    result = GeoDataFrame()
    aoi_extract = GeoDataFrame()
    geodataframe_aoi.index.name = 'id'
    dist_treshold = __getConfigValue('dist_treshold')

    # Format datasets outputs
    _, _, path_poly1 = format_dataset_output(dataset=aoi, name='tmp')
    _, _, path_poly2 = format_dataset_output(dataset=landuse, name='tmp')

    # Inserts new columns if the __data is given or not.
    if method == 'append':
        try:
            geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'HAB_DIV', 0)
        except ValueError:
            geodataframe_aoi.insert(0, 'HAB_DIV', 0)
    elif method == 'duplicate':
        try:
            aoi_extract.insert(aoi_extract.shape[1] - 1, 'HAB', 0)
            aoi_extract.insert(aoi_extract.shape[1] - 1, 'HAB_PROP', 0)
        except ValueError:
            aoi_extract.insert(0, 'HAB', 0)
            aoi_extract.insert(0, 'HAB_PROP', 0)

    if population:
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'SUM_POP', 0)
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'DENS_POP', 0)
    if distances:
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'MEAN_DIST', 0)
    if anopheles:
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'CATCH_SITE', 0)
        geodataframe_aoi.insert(geodataframe_aoi.shape[1] - 1, 'SPECIE_DIV', 0)

    print('OK')

    # Progress bar for the first level
    with alive_bar(total=(len(geodataframe_aoi))) as bar_main:
        # Iterates over every polygon and yield its index too
        for i, p in iter_geoseries_as_geodataframe(shapefile=geodataframe_aoi):
            p.to_file(filename=path_poly1)
            # TODO Multithreading to ce qui est en dessous
            print(geodataframe_aoi.loc[i, 'NAME'])
            start_time = default_timer()
            bar_main.text('Preparing')  # Pbar 1st level
            # Crops the raster file with the first polygon boundaries then polygonize the result.
            # TODO check if intersecting a polygonized land use of Africa isn't faster than polygonizing small rasters ?
            path_landuse_aoi = raster_crop(dataset=landuse, shapefile=path_poly1)
            print('raster_crop: ', round(default_timer() - start_time), 3)
            gdf_os_pol = polygonize(dataset=path_landuse_aoi)
            print('polygonize: ', round(default_timer() - start_time), 3)
            # Intersects only if the __data is given at the start.
            if population:
                _, population_aoi = intersect(base=population, overlay=path_poly1, crs=3857, export=True)
                print('population intersects: ', round(default_timer() - start_time), 3)
            if anopheles:
                _, anopheles_aoi = intersect(base=anopheles, overlay=path_poly1, crs=3857, export=True)
                print('anopheles inetersects: ', round(default_timer() - start_time), 3)

            bar_main.text('Processing')  # Pbar 1st level

            # Progress bar for the second level
            with alive_bar(total=(len(gdf_os_pol)*5)) as bar_process:
                # Iterates over every polygon and yield its index too
                for o, q in iter_geoseries_as_geodataframe(shapefile=gdf_os_pol):
                    # TODO Multiprocessing tout ce qui est en dessous
                    q.to_file(filename=path_poly2)

                    bar_process.text('Preparing')  # Pbar 2nd level
                    # Set vars to default states
                    __data = []
                    __val = None
                    # Extracts the row from geodataframe_aoi corresponding to the entity we're currently iterating over
                    aoi_extract = aoi_extract.append(geodataframe_aoi.loc[[i]], ignore_index=True)

                    # Crops the raster file with the second polygon bounaries
                    path_landuse_aoi_landuse = raster_crop(dataset=path_landuse_aoi, shapefile=path_poly2)
                    if population:
                        population_aoi_landuse = intersect(base=population_aoi, overlay=path_poly2, crs=3857)
                    if anopheles:
                        anopheles_aoi_landuse = intersect(base=anopheles_aoi, overlay=path_poly2, crs=3857)
                        anopheles_aoi_landuse['spnb'] = 0
                    bar_process()  # Pbar 2nd level
                    # TODO performance issue au dessus là
                    # TODO Est-ce que je le calcule pas plusieurs fois vu que j'itère plusieurs fois dessus ici ?
                    bar_process.text('Habitat')  # Pbar 2nd level
                    # Count every pixel from the raster and its value
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
                    bar_process()  # Pbar 2nd level

                    bar_process.text('Population')  # Pbar 2nd level
                    if population:  # Population and urban patches
                        aoi_extract.loc[o, 'SUM_POP'] = int(population_aoi_landuse['DN'].sum())
                        aoi_extract.loc[o, 'DENS_POP'] = int(population_aoi_landuse['DN'].sum() / p.area[0])
                    bar_process()  # Pbar 2nd level

                    bar_process.text('Distances')  # Pbar 2nd level
                    if distances:  # Distances and urban fragmentation
                        # No need to intersect it again
                        # https://splot.readthedocs.io/en/stable/users/tutorials/weights.html#weights-from-other-python-objects
                        dbc = lps.weights.DistanceBand.from_dataframe(population_aoi_landuse,
                                                                      threshold=dist_treshold,
                                                                      p=2,
                                                                      binary=False,
                                                                      build_sp=True,
                                                                      silent=True)
                        aoi_extract.loc[o, 'MEAN_DIST'] = round(dbc.mean_neighbors, 4)
                    bar_process()  # Pbar 2nd level

                    bar_process.text('Anopheles')  # Pbar 2nd level
                    if anopheles:  # Anopheles diversity and catching sites
                        for x in range(0, len(anopheles_aoi_landuse)):
                            anopheles_aoi_landuse.loc[x, 'spnb'] = anopheles_aoi_landuse.iloc[x].str.count('Y').sum()
                        aoi_extract.loc[o, 'CATCH_SITE'] = int(len(anopheles_aoi_landuse))
                        aoi_extract.loc[o, 'SPECIE_DIV'] = anopheles_aoi_landuse['spnb'].max()
                    bar_process()  # Pbar 2nd level

            bar_main.text('Append')  # Pbar 1st level
            result = result.append(aoi_extract, ignore_index=True)

            bar_main.text('Done')  # Progress bar for the first level
            print('[{}/{}]'.format(i+1, len(geodataframe_aoi)))
            bar_main()  # Progress bar for the first level

        # End

    if export:
        _, _, path_poly1 = format_dataset_output(dataset=aoi, name='profiles', ext='.xlsx')
        result.to_excel(path_poly1, index=False)
        return result, aoi
    else:
        return result, aoi
