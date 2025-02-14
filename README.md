# sverify
Code to utilize emissions from CEMS and measurements of SO2 from ground stations for ATDM model evaluation.

Dependencies

* monetio
* monet
* geopandas
* timezonefinder

Scripts are in the top level directory and include the following files

* getdata.py
* setupruns.py
* mkscripts.py

Each script reads a configuration file. An example configuration file is in the top level directory.
This file also contains information about how to use the scripts.

* CONFIG.S

## Disclaimer
"This repository is a scientific product and is not official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project code is provided on an 'as is' basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government."
