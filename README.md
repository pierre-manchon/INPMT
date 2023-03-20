# INPMT [![RELEASE (latest by date)](https://img.shields.io/github/v/release/pierre-manchon/INPMT)](https://github.com/pierre-manchon/INPMT/releases/latest) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5269134.svg)](https://doi.org/10.5281/zenodo.5269134) [![LICENSE](https://img.shields.io/github/license/pierre-manchon/INPMT)](https://www.gnu.org/licenses/gpl-3.0.en.html)
[![Pre-commit auto-update](https://github.com/pierre-manchon/INPMT/actions/workflows/pre-commit-autoupdate.yml/badge.svg)](https://github.com/pierre-manchon/INPMT/actions/workflows/pre-commit-autoupdate.yml)
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![Maintainability](https://api.codeclimate.com/v1/badges/f1888eb8938e688ad438/maintainability)](https://codeclimate.com/github/pierre-manchon/INPMT/maintainability)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Impact of National Parks on Malaria Transmission

You need to have every type of data specified [here](#data) downloaded and stored in whatever directory you choose.
Then you'll need to specify the directory link in the config file.

### Installation

With conda:
```shell
conda env create -f environment.yml
```

### Configure
1. CLI in the package directory: `python INPMT`:

   You can use `python INPMT --config` to visualise the config file then `python INPMT --config <variable> <new value>` to set a new value.

2. Package in a python file or console: `import INPMT`:

   You can use `INPMT.get_config()` to visualise the config file then `INPMT.set_config_value(varname=<varname>, value=<value>)` to set a new value.

### Run
You have two ways of executing two commands:

1. CLI in the package directory: `python INPMT`
    1. get_urban_profile `python INPMT --villages --loc`
    2. get_countries `python INPMT --countries`
2. Package in a python file or console: `import INPMT`
    1. get_urban_profile `INPMT.run(method='villages', loc=True)`
    2. get_countries `INPMT.run(method='countries', loc=False)`
3. The corr file to compute correlation matrix from the result file
   1. `from INPMT.__utils import corr`

### Data
You can [mail me](mailto:pierre.manchon@pm.me) to get the download link or use data of your own which is trickier.
Either way you'll need to modify the `<datasets_storage_path>` variable in the config file so the program can find it.
If you choose to use your own data you'll need to provide:
- a .qml (legend file) file along with your raster files,
- data at the scale of the African continent,
- data projected to WGS 84 / Pseudo-Mercator (EPSG:3857)

### Code
Github repo is organized as follow:

    INPMT/
    ├──dependencies/: specific gdal wheel and requirements file
    ├──docs/: graphs and xml files from drawio
    ├──INPMT/: Python script developped to process and analyse the data
    │   └──__utils/: Python functions developped to ease the readability and processing
    ├──test/: test files for gdal + gdal based packages and import
