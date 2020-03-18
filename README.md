# README
[![License: CC BY-SA 4.0](https://licensebuttons.net/l/by-sa/4.0/80x15.png)](https://creativecommons.org/licenses/by-sa/4.0/)

The repo contains a python3 module to visualize subjects (e.g. missing files) - hereafter refered as data - in a heatmap with daily resolution.

## Description and objective
The repo contains a python3 module to visualize data in a heatmap with daily resolution.

The software package is written to visualize data similar to the 
[github contribution chart](https://help.github.com/en/github/setting-up-and-managing-your-github-profile/viewing-contributions-on-your-profile).


## Assumption
This package is **not prepared for collecting** the data.
This package is **prepared for visualization** only.

## Requirements

* Python version 3.x

## Usage
The data can be provided 
* as two column comma separated csv-file, with a single line header with the names of the columns
    * the data row1 should be consists of a date or a datetime
    * the data row2 should be a float or a integer value
    * e.g.:
```
date,missing files
2020-01-18 00:00:00, 1
2020-01-18 10:00:00, 1
2020-01-20 00:00:00, 0
2020-01-21, 1
2019-12-18 01:00:00, 0
2020-01-21 10:00:00, 0
2020-01-21 10:00:00, 0
2020-01-25 10:00:00, 1
2020-01-30 10:00:00, 0.5
```
* as DataFrame
    * the values in the column 'data' should be a dtype: datetime64[ns]
    * the values in the second column shouls be float or integer


In general 
* the data can contain gaps and 
* the data can be provided unsorted.