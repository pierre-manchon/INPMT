# -*-coding: utf8 -*
import rasterio
import rasterio.mask
import pandas as pd
from numpy import ndarray
from pandas import DataFrame, Series
from geopandas import GeoDataFrame
from typing import AnyStr, SupportsInt, Counter, Any
from PAIA.utils.decorators import timer
from PAIA.utils.utils import __count_values, __gather, format_dataset_output, get_config_value, read_qml
from PAIA.utils.vector import merge_touching, to_wkt, iter_poly, intersect
from PAIA.utils.raster import read_pixels, raster_crop


def get_urban_extent(
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


def get_pixel_count(dataset_path: AnyStr, band: SupportsInt) -> tuple[Any, Counter]:
    __pixel_value = 0
    __val = None
    __dataset = None
    __output_path = None

    with rasterio.open(dataset_path) as __dataset:
        __band = __dataset.read()[band]
        __pixel_value = read_pixels(dataset=__dataset, band=__band)
        __pixel_array = __gather(pixel_values=__pixel_value)
        __ctr = __count_values(pixel_array=__pixel_array)
    return __dataset, __ctr


@timer
def get_categories(dataset_path: AnyStr, band: SupportsInt, export: bool = False) -> DataFrame:
    """
    As an input, i take the dataset path and the band number i want to categorize.
    Then i export the counted values (from the __count_values() function).
    To do so, i retrieve the path where the dataset is stored then join it to nameofthedataset_report.txt.
    That way, i can save the report at the same place where the dataset is stored.
    After that, i create the file and populate it with the field names then the values with formatted strings:
        - Number of the category
        - Number of pixels found
        - Surface (based on the pixels surface (h*w) and the number of pixels)

    :param shapefile_area:
    :type shapefile_area:
    :param dataset:
    :type dataset:
    :param band: Specific band from a raster file
    :type band: ndarray
    :return: Export the counter to a text file row by row
    :rtype: None
    """
    __dataset, __ctr = get_pixel_count(dataset_path=dataset_path, band=band)

    data = []
    for c in __ctr:
        category_area = round(__ctr[c] * (__dataset.res[0] * __dataset.res[1]), 3)
        raster_area = sum(__ctr.values())
        percentage = ((__ctr[c] * 100) / raster_area)
        data.append([c, __ctr[c], category_area, percentage])

    df = pd.DataFrame(data, columns=['Category', 'Nbr of pixels', 'Surface (m2)', 'Proportion (%)'])

    # TODO export style files from cropped raster so it can be read flawlessly here. Right now i have to load it into
    #  qgis export it into a qml file by hand.
    _, _, __qml_path = format_dataset_output(dataset=dataset_path, ext='.qml')
    __style = read_qml(__qml_path)
    __val = None
    for i, row in df.iterrows():
        for j in __style:
            if row['Category'] == j['value']:
                __val = j['label']
        df.at[i, 'Label'] = __val

    # Retrieves the directory the dataset is in and joins it the output filename
    _, _, __output_path = format_dataset_output(dataset=dataset_path, name='report', ext='.xlsx')

    if export:
        df.to_excel(__output_path, index=False)
        return df
    else:
        return df


@timer
def get_distances(pas: GeoDataFrame,
                  urban_areas: GeoDataFrame,
                  path_urban_areas: AnyStr,
                  export: bool = False
                  ) -> DataFrame:
    """
    # TODO
    """
    urban_treshold = get_config_value('urban_area_treshold')
    ug = get_urban_extent(urban_areas=urban_areas,
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
    for u in ug.values:
        min_dist = get_config_value('min_dist')
        name = None
        for p in pas.values:
            dist = p[3].distance(u[3])
            if dist < min_dist:
                min_dist = dist
                name = p[1]
        result.append([u[0], u[1], u[2], u[3], name, min_dist])
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


@timer
def get_pas_profiles(
        geodataframe_aoi: GeoDataFrame,
        aoi: AnyStr,
        occsol: AnyStr,
        population: AnyStr,
        export: bool = False
) -> tuple[GeoDataFrame, AnyStr]:
    # Crop the raster and the vector for every polygon of the pas layer
    # Might want use a mask otherwise
    # Then process and associate result to each polygon
    _, _, output_path = format_dataset_output(dataset=aoi, name='tmp')

    for i, row, p in iter_poly(shapefile=geodataframe_aoi):
        p.to_file(filename=output_path)
        path_occsol_cropped = raster_crop(occsol, output_path)
        _, ctr = get_pixel_count(path_occsol_cropped, 0)
        geodataframe_aoi.at[i, 'HABITAT_DIVERSITY'] = len(ctr)
        gdf_pop_cropped, path_pop_cropped = intersect(population, output_path)
        geodataframe_aoi.at[i, 'SUMPOP'] = gdf_pop_cropped['DN'].sum()
        for o, tpx, q in iter_poly(shapefile=gdf_pop_cropped):
            dist = None
            for p, yqc, s in iter_poly(shapefile=gdf_pop_cropped):
                dist = q.distance(s)
                dist.append(Series(dist))
            gdf_pop_cropped.at[o, 'mean_distance'] = dist.mean()
        geodataframe_aoi.at[i, 'mean_distance'] = gdf_pop_cropped['mean_distance'].mean()

    if export:
        _, _, output_path = format_dataset_output(dataset=aoi, name='profiles', ext='.xlsx')
        geodataframe_aoi.to_excel(output_path, index=False)
        return geodataframe_aoi, aoi
    else:
        return geodataframe_aoi, aoi
