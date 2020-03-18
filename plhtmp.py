#!/usr/bin/env python
# coding: utf-8


import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import PlotHeatmap

PlotHeatmap.main(
{ 
    'data_import' : 'CSV', # Test|DataFrame|CSV
    'picture_filename' : 'test/mypic_testfile_csv',
    'csv_filename' : 'test/test_missing_files.csv'
}
)

PlotHeatmap.main(
{ 
    'data_import' : 'Test', # Test|DataFrame|CSV
    'picture_filename' : 'test/mypic_local_dataframe',
    #'csv_filename' : 'test_missing_files.csv'
}
)



# create panda date range: dtype: datetime64[ns]
date_rng = pd.date_range(start='3/19/2019', end='8/28/2019', freq='12H')

# create DataFrame
df = pd.DataFrame(date_rng, columns=['date']) # dtype: datetime64[ns]

df['missing files'] = np.random.randint(0,3,size=(len(date_rng)))


# add a data element
ts = pd.to_datetime("2019-03-07 18:47:05.487", format="%Y-%m-%d %H:%M:%S.%f")
df =df.append({'date' : ts , 'missing files' : 2},ignore_index=True)

# sort data
df = df.sort_index(ascending=1)


PlotHeatmap.main(
{ 
    'data_import' : 'DataFrame', # Test|DataFrame|CSV
    'picture_filename' : 'test/mypic_external_dataframe',
    #'csv_filename' : 'test_missing_files.csv',
    'DataFrame' : df
}
)