# INPMT [![GitHub release (latest by date)](https://img.shields.io/github/v/release/pierre-manchon/INPMT)](https://github.com/pierre-manchon/INPMT/releases/latest) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4972214.svg)](https://doi.org/10.5281/zenodo.4972214) [![GitHub](https://img.shields.io/github/license/pierre-manchon/INPMT)](https://www.gnu.org/licenses/gpl-3.0.en.html) 
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![CircleCI](https://circleci.com/gh/pierre-manchon/INPMT/tree/main.svg?style=svg)](https://circleci.com/gh/pierre-manchon/INPMT/tree/main) 

Impact of National Parks on Malaria Transmission

<!--
jenkins: needs java (https://www.jenkins.io/)
travis ci: ci/cd not reliable on the long term (https://www.travis-ci.com/)
non
circleci: ci/cd (https://app.circleci.com/pipelines/github/pierre-manchon)
appveyor: ci/cd (https://ci.appveyor.com/login)
tox: differnt versions and interpreters (https://github.com/tox-dev/tox)
voir si je peux test les builds sur plusieurs plateformes à partir de circle ci directement
requires.io: dependencies security (http://requires.io/)
safety: venv and packages security issues (https://pyup.io/safety/)
voir si j'utilises requires ou plutôt safety
bandit: security issue (https://github.com/PyCQA/bandit)
black: syntax formatting (https://github.com/psf/black)
ok
twine: 
flit:
which is better to publish package to pypi

tox => formatting: black
       security: bandit + safety (local) + requires.io (local+remote)
       build and test the wheel: sdist + twine
       publish: twine
-->
