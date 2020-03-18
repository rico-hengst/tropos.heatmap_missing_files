#!/usr/bin/env python
# coding: utf-8

# # Read csv data

# In[1]:


"""
This is the "example" module.

The example module supplies one function, factorial().  For example,

"""

import getopt
import sys


import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import platform
import os.path

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors

import logging
logging.basicConfig(level=logging.WARNING)

"""Check python version"""
python_version = platform.python_version().split(".")
if int(python_version[0]) < 3:
    logging.error("Your python version is: " + platform.python_version() )
    logging.error("Script will be terminated cause python version < 3 is required !")
    exit()


# ## Generate Testdata

# In[2]:


def generate_test_data():
    '''
    Returns testdata as DataFrame
    '''
    
    
    # create panda date range: dtype: datetime64[ns]
    date_rng = pd.date_range(start='4/4/2019', end='8/28/2019', freq='12H')

    # create DataFrame
    df = pd.DataFrame(date_rng, columns=['date']) # dtype: datetime64[ns]

    df['missing_files_intern'] = np.random.randint(0,3,size=(len(date_rng)))
    

    # add a data element
    ts = pd.to_datetime("2019-09-09 18:47:05.487", format="%Y-%m-%d %H:%M:%S.%f")
    df =df.append({'date' : ts , 'missing_files_intern' : 1},ignore_index=True)

    # get header name
    org_header = list(df.columns.values)
    
    return df, org_header



# ## Rename DataFrame columns
def rename_external_df_columns( df ):
    
    if not isinstance(df, pd.DataFrame):
        logging.warning('Provided or generated variable is not a DataFrame ') 
        exit()
    
    # get header name
    org_header = list(df.columns.values)

    if( len(org_header) != 2):
        logging.warning('A DataFrame with two columns is expected!!!' + str(org_header) )
        exit()

    # rename columns
    df = df.rename(columns={org_header[0]: "date", org_header[1]: "commit"})
    
    return df, org_header



# ## Add columns to df
def add_df_columns( df ):
    
    # sort data
    df = df.sort_index(ascending=1)


    df['week'] = df['date'].dt.week
    df['dayofweek'] = df['date'].dt.dayofweek;
  
    # https://strftime.org/
    df['week_in_year'] = df['date'].dt.strftime('%Y-%W');
    
    return df

# ## Read data from File


def read_csv_file(csv_filename):
    '''
    Returns a DataFrame

            Read file, filenam must be provided
            Several operation are made
    '''
    
    # check file
    # csv_filename = 'd2.csv'
    if ( not os.path.isfile( csv_filename) ):
        logging.warning('File not exists: ' + csv_filename) 
        exit()
    else:
        logging.info('Read csv file: ' + csv_filename)

    # read file
    df = None
    df = pd.read_csv( csv_filename )

    # get header name
    org_header = list(df.columns.values)

    if( len(org_header) != 2):
        logging.warning('A csv-file with two columns is expected!!!') 
        exit()

    # rename columns
    df = df.rename(columns={org_header[0]: "date", org_header[1]: "commit"})

    # transform column date to datetime
    df['date'] =  pd.to_datetime(df['date'])


    # sort data
    df = df.sort_values(by='date', ascending=1)
    
    return df, org_header


# ## Group data and fill values

# In[4]:


def group_fill_data( df ):
    
    '''
    Returns a new DataFrame, data are grouped by date and data gaps are NaN filled
    '''

    logging.info('Original data will be grouped by dates')

    # group data to a new datatframe
    df_grouped = df.groupby( df['date'].dt.strftime('%Y-%m-%d') ).agg({ 'commit':['sum', 'mean', 'max'], 'week':'first', 'dayofweek':'first', 'week_in_year':'first' })

    # set datetime again
    df_grouped.index = pd.to_datetime(df_grouped.index)
    
    # fill value
    logging.info('The grouped data will be filled by NAN if necessary')

    # add new DatFrame with nan values
    # data_range of the whole timespan in 1 day step
    # this make sure, that the whole timespan will be shown
    date_rng_new = pd.date_range( start = df_grouped.index[0], end = df_grouped.index[-1], freq = '1D')

    # add full dataframe
    df_filled = pd.DataFrame(date_rng_new, columns=['date']) # dtype: datetime64[ns]

    # add nan values
    df_filled['commit'] = np.nan
    
    
    # add values from DataFrame df2 to gf
    # loop over gf
    # put df2 mean value if timestamps matched
    jj=0
    for ii in range( len(df_filled.index) ):

        # set dayofweek
        df_filled.at[ii, 'dayofweek'] = df_filled['date'][ii].dayofweek

        #delta = gf.date[ii+1] - gf.date[ii]
        if ( df_filled.date[ii] == df_grouped.index[jj] ):
            #print('times mated: ' + str(gf.date[ii]) + '    ' + str(df2.index[jj]) + '   ' + str(df2['commit']['mean'][jj])  )
            df_filled.at[ii, 'commit'] = df_grouped['commit']['mean'][jj]
            jj=jj+1
    
    
    return df_filled


# ## Sort DataFrame to matrix

# In[5]:


def create_matrix_from_grouped_filled_dataframe( df_filled ):
    
    '''
    Returns a matrix and a time axis

        Input: df_filled
    '''
    
    logging.info('The filled DataFrame will be transformed to a matrix(height=7days, width=number of week in DataFrame')

    # transform DataFrame gf to an matrix 

    # generate a nan numpy matrix
    delta = df_filled['date'][len(df_filled.index)-1] - df_filled['date'][0]

    height = 7
    width = int(delta.days/7 + 2)
    npmatrix = np.full([height, width], np.nan)

    # add vector for label xaxis
    timeaxis = []

    # set first timeaxis element to monday
    timeaxis.append( df_filled['date'][0] - timedelta( days = df_filled['dayofweek'][0]  )  )

    # loop to create array a from dataframe gf
    ii = None
    for iweek in range( width ):

        # add eleement to timeaxis each week add a "monday" 
        if ( ii != None and ii < len(df_filled.date)-1 ):
            # last valid ii -> = Sunday, so add + 1
            timeaxis.append(df_filled.date[ii+1])
            #print(timeaxis[-1].strftime( "%A     --- %c"))

        # weekday iterating
        for iweekday in range( height ):

            # start ii index
            if ( ii == None ):
                if ( iweekday == df_filled['dayofweek'][0] ):
                    ii = -1

            # add gf value to array    
            if ( ii != None and ii < len(df_filled.index)-1 ):
                ii = ii + 1
                npmatrix[iweekday,iweek] = df_filled['commit'][ii]
                
    return npmatrix, timeaxis


# ## Plot

# In[6]:


def plot_matrix( npmatrix, timeaxis, org_header, picture_filename ):
    
    logging.info('Plot the data')
    
    picture_filename = picture_filename + '.png'

    # https://matplotlib.org/gallery/images_contours_and_fields/pcolor_demo.html#sphx-glr-gallery-images-contours-and-fields-pcolor-demo-py
    # https://stackoverflow.com/questions/52626103/custom-colormap


    # create new colormap
    norm = matplotlib.colors.Normalize(-1,1)


    # LinearSegmentedColormap
    # https://stackoverflow.com/questions/52626103/custom-colormap
    mycolors = [[norm(-1.0), "lightgrey"],
              [norm( 0.4), "yellow"],
              [norm( 1.0), "red"]]

    cmap11 = matplotlib.colors.LinearSegmentedColormap.from_list("", mycolors)
    


    # Discrete colormap
    # https://matplotlib.org/3.1.3/tutorials/colors/colorbar_only.html
    # cmap11 = mpl.colors.ListedColormap(['lightgrey', 'orange', 'red'])


    # discrete via pre-defined cmaps
    # cmap11 = matplotlib.cm.get_cmap("Reds", 4)

    # discrete colormaps
    # https://gist.github.com/jakevdp/91077b0cae40f8f8244a


    # plot in jupyter notbook
    #get_ipython().run_line_magic('matplotlib', 'notebook')

    fig, ax0 = plt.subplots(1, 1)
    
    fontsize_default = 9
    
    # Add text
    """Add figure creating timestamp"""
    """https://riptutorial.com/matplotlib/example/16030/coordinate-systems-and-text"""
    plt.text(  # position text relative to Figure
        0.0, 0.02, 
        'Figure generated: ' + str(datetime.now().strftime("%Y-%m-%d %H:%M")) + 
        '\nFilename:       ' + picture_filename, fontsize=fontsize_default-3,
        ha='left', va='baseline',
        transform=fig.transFigure
    )
    

    

    # plot npmatrix data
    c = ax0.pcolor(npmatrix,cmap=cmap11, edgecolors='w', linewidths=2)

    # set yticks
    ax0.set_yticks([1.5, 3.5, 5.5])
    ax0.set_yticklabels(['Tue', 'Thu', 'Sat'])

    ax0.set_yticks([0.5, 2.5, 4.5, 6.5])
    ax0.set_yticklabels(['Mon', 'Wed', 'Fri', 'Sun'])

    # stepsize of dates on xaxis in unit WEEK
    stepsize=4

    # set xticks and labels
    xticks = np.arange(0+0.5, len(timeaxis)+0.5, stepsize).tolist()
    xticklabels = [date_obj.strftime('%Y-%m-%d') for date_obj in timeaxis[0:len(timeaxis):stepsize]]

    # set it
    ax0.set_xticks( xticks )
    ax0.set_xticklabels( xticklabels )

    # adapt fontsize at labels
    plt.xticks(rotation=55, fontsize=fontsize_default)
    plt.yticks(fontsize=fontsize_default)
    #plt.set_cmap('gray')


    # set aspect ratio
    plt.gca().set_aspect('equal', adjustable='box')

    # set title and labels
    title1 = org_header[1].title() # makes string camel case
    #ax0.set_title(label='Data availability', weight='bold')
    #ax0.set_title(label=title1, weight='bold')
    ax0.set_ylabel('Weekday')
    ax0.set_xlabel('Time [date of first weekday]')

    # orientation colorbar
    # https://stackoverflow.com/questions/13310594/positioning-the-colorbar

    #cbar = fig.colorbar(c, ticks=[0, 1], ax=ax0, orientation="horizontal", pad=0.3)
    cbar = fig.colorbar(c, ticks=[np.nanmin(npmatrix), np.nanmax(npmatrix)], ax=ax0, shrink=0.4)

    cbar.ax.set_yticklabels(['less', 'more'], fontsize=fontsize_default-1)  # vertically oriented colorbar
    #cbar.set_label(label='Temperature', fontsize=8, weight='bold')
    cbar.set_label(label=title1, labelpad=-20, y=0.5, rotation=90, fontsize=fontsize_default, weight='bold')

    # save figure
    plt.savefig(facecolor="none",dpi=200,fname=picture_filename)





# In[7]:


def main( myDict ):
    logging.info('Start script')
    
    # get data from a source
    if ( myDict['data_import'] == 'DataFrame' ):
        df, org_header = rename_external_df_columns( myDict['DataFrame'] )
        
    elif ( myDict['data_import'] == 'CSV' ):
        df, org_header = read_csv_file( myDict['csv_filename'] )

    elif ( myDict['data_import'] == 'Test' ):
        df, org_header = generate_test_data()
        df, org_header = rename_external_df_columns( df )
    else:
        logging.warning('data_imoprt value is wrong: ' + myDict['data_import'] ) 
        exit()
    
    # check if DataFrame
    if not isinstance(df, pd.DataFrame):
        logging.warning('Provided or generated variable is not a DataFrame ') 
        exit()
        
    # add columns
    df = add_df_columns( df )
    
    # generate filled dataframe
    df_filled = group_fill_data( df )
    
    npmatrix, timeaxis = create_matrix_from_grouped_filled_dataframe( df_filled )
    
    plot_matrix( npmatrix, timeaxis, org_header, myDict['picture_filename'] )


if __name__ == '__main__':
    main( { 
        'data_import' : 'Test', # Test|DataFrame|CSV
        'picture_filename' : 'df.png',
        'csv_filename' : 'd2.csv'
    } )


# In[ ]:





# In[ ]:




