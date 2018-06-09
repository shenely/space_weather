space_weather
=========
It's gon' rain

Installation
---------------------

Go to the space_weather directory and create a source distribution:
```bash
python setup.py sdist
```
The distribution will be packaged as a *.tar.gz by default.

Go to the dist/ directory and use pip to install the package:
```bash
cd ./dist/
pip install space_weather-#.#.tar.gz
```
Prompts may appear to install dependencies. The version number will be in the filename in place of #.#.

For starters, run the space_weather module in Python from the top-level directory of this project (i.e. the top-most space_weather directory):
```bash
python -m space_weather
```
The configuration file is expected to be in the directory where the above command was run.
An example configuration file may be found in the top-level directory of this project (i.e. planet.conf).
All plots generated are saved to the directory the above command was run from.

**Note**: The configuration file must contain information for a valid mail server for the program to run properly. Otherwise, the program will (gracefully) exit.

For (slightly) more information, see the help documetation in the main script:
```bash
python -m space_weather --help
```

Test cases may be run from the top-level project directory with the following command:
```bash
python -m test_space_weather
```

