# -*-coding: utf8 -*
from pandas import DataFrame
from shapefile import Reader
from matplotlib import pyplot as plt
from numpy import zeros, mean


def plot_shape(shapefile: Reader, dataframe: DataFrame, name: str):
    com_id = dataframe[dataframe.NAME == name].index[0]

    plt.figure()
    ax = plt.axes()
    ax.set_aspect('equal')

    shape_ex = shapefile.shape(com_id)
    x_lon = zeros((len(shape_ex.points), 1))
    y_lat = zeros((len(shape_ex.points), 1))

    for ip in range(len(shape_ex.points)):
        x_lon[ip] = shape_ex.points[ip][0]
        y_lat[ip] = shape_ex.points[ip][1]

    plt.plot(x_lon, y_lat, color='black')
    x0 = mean(x_lon)
    y0 = mean(y_lat)

    # plt.text(x0, y0, name, fontsize=10) //Name of the polygon in its center
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('{}'.format(name))
    plt.xlim(shape_ex.bbox[0], shape_ex.bbox[2])

    plt.savefig(r'H:\Logiciels\0_Projets\python\PAIA\plots\{}.png'.format(name))
    return x0, y0
