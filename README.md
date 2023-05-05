# INPMT [![RELEASE (latest by date)](https://img.shields.io/github/v/release/pierre-manchon/INPMT)](https://github.com/pierre-manchon/INPMT/releases/latest) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5269134.svg)](https://doi.org/10.5281/zenodo.5269134) [![LICENSE](https://img.shields.io/github/license/pierre-manchon/INPMT)](https://www.gnu.org/licenses/gpl-3.0.en.html)
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![Maintainability](https://api.codeclimate.com/v1/badges/f1888eb8938e688ad438/maintainability)](https://codeclimate.com/github/pierre-manchon/INPMT/maintainability)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)

Impact of National Parks on Malaria Transmission

 You can [mail me](mailto:pierre.manchon@pm.me) to get the download link or use data of your own which is trickier (You should provide tour own .qml and make sure the data has the right CRS).

### Run
````python
import INPMT
df = INPMT.run('path/to/your/datasets')
````

### Code
Github repo is organized as follow:

    INPMT/
    ├──conda/: specific conda installation files
    ├──docs/: graphs and xml files from drawio
    ├──INPMT/: Python script developped to process and analyse the data
    │   └──utils/: Python functions developped to ease the readability and processing
