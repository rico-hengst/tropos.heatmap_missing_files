#!/usr/bin/env python
# coding: utf-8

# # Read data
# # Plot Heatmap

# # Author: Rico Hengst @tropos.de



"""
    PlotHeatmap

    The module processes data and generates a heatmap, exported as png file

    Parameters
    ----------
    myDict : Python dictionary
        myDict['data_import_type']  : REQUIRED arg, string keywords Test|DataFrame|CSV
        myDict['csv_filename']      : REQUIRED if myDict['data_import_type'] = CSV
        myDict['picture_filename']  : REQUIRED string
        myDict['_optional_info']    : NICE2HAVE Dict of infos
        

    Returns
    -------
    Heatmap
        as png file
        as html file

    """


import sys


import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import platform
import os.path

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors

try:
    from jinja2 import Template
except ImportError:
    print('\nThere was no such module installed: jinja2')
    exit()

import logging
logging.basicConfig(level=logging.INFO)

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
    date_rng = pd.date_range(start='4/1/2019', end='9/5/2019', freq='24H')

    # create DataFrame
    df = pd.DataFrame(date_rng, columns=['date']) # dtype: datetime64[ns]

    df['missing_files_intern'] = np.random.randint(0,2,size=(len(date_rng)))
    

    # add a data element
    ts = pd.to_datetime("2019-09-08 18:47:05.487", format="%Y-%m-%d %H:%M:%S.%f")
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
def create_matrix_from_grouped_filled_dataframe( df_filled, myDict ):
    
    '''
    Returns a matrix and a time axis

        Input: df_filled
        
    '''
    
    myDict['datetime_first_selected']  = df_filled['date'].iloc[0].strftime("%Y-%m-%d")
    myDict['datetime_last_selected']   = df_filled['date'].iloc[-1].strftime("%Y-%m-%d")
    

    df_filled_extented = df_filled.copy()
    
    # number of days to fullfill (prepend) to dataframe to start on MONDAY
    prepend_number = int(df_filled['dayofweek'][0]);
    

    # number of days to fullfill (append) to dataframe to end on SUNDAY
    append_number = 6 - int( df_filled['dayofweek'][  len(df_filled.index) - 1 ] );
    

    # prepend rows to start on prevoius MONDAY
    for i in range(0, prepend_number):
        # get date in loop
        d = df_filled['date'][0] - timedelta(days=i+1)
        
        new_row = {'date':d, 'commit':np.nan, 'dayofweek':d.weekday(), 'info':'prepend'} # use weeekday instead dayofweek, cause its a panda timestamp
        df_filled_extented = df_filled_extented.append(new_row, ignore_index=True)
        
    # append rows to end on next SUNDAY
    for i in range(0, append_number):
        # get date in loop
        d = df_filled['date'][ len(df_filled.index) - 1 ] + timedelta(days=i+1)
        
        new_row = {'date':d, 'commit':np.nan, 'dayofweek':d.weekday(), 'info':'append'} # use weeekday instead dayofweek, cause its a panda timestamp
        df_filled_extented = df_filled_extented.append(new_row, ignore_index=True)

    
    # Sort by data
    df_filled_extented.sort_values('date',ascending = True, inplace=True)
    
    # Drop former default index, automatic add new default index
    df_filled_extented.reset_index(drop=True,inplace=True)

    
    # delta timestamp duration
    # delta = df_filled_extented['date'][len(df_filled_extented.index)-1] - df_filled_extented['date'][0]
    delta = df_filled_extented['date'].iloc[-1] - df_filled_extented['date'].iloc[0]
    


    height = 7
    width = int(delta.days/height+1)
    
    # transform DataFrame gf to an matrix 
    logging.info('The filled DataFrame will be transformed to a matrix (height=days, width=number of week in DataFrame) ' + str(height) + ' x ' + str(width) )
    
    # generate a nan numpy matrix
    npmatrix = np.full([height, width], np.nan)

    # add vector for label xaxis
    timeaxis = []

    # set first timeaxis element to monday
    timeaxis.append( df_filled_extented['date'].iloc[0] - timedelta( days = df_filled_extented['dayofweek'].iloc[0]  )  )

    

    # loop to create array a from dataframe gf
    ii = None
    for iweek in range( width ):

        # add eleement to timeaxis each week add a "monday" 
        if ( ii != None and ii < len(df_filled_extented.date)-1 ):
            # last valid ii -> = Sunday, so add + 1
            timeaxis.append(df_filled_extented.date[ii+1])

        # weekday iterating
        for iweekday in range( height ):

            # start ii index
            if ( ii == None ):
                if ( iweekday == df_filled_extented['dayofweek'].iloc[0] ):
                    ii = -1

            # add gf value to array    
            if ( ii != None and ii < len(df_filled_extented.index)-1 ):
                ii = ii + 1
                npmatrix[iweekday,iweek] = df_filled_extented['commit'].iloc[ii]
              
                
    # add metadata
    myDict['elements_gt0']            = np.count_nonzero( npmatrix[~np.isnan(npmatrix)] > 0 )
    myDict['elements_eq0']            = np.count_nonzero( npmatrix[~np.isnan(npmatrix)] == 0 )
    myDict['total_number_elements']   = str(np.size(npmatrix))
    myDict['datetime_now']            = datetime.now().strftime("%Y-%m-%d")
    myDict['datetime_first_extented']   = df_filled_extented['date'].iloc[0].strftime("%Y-%m-%d")
    myDict['datetime_last_extented'] = df_filled_extented['date'].iloc[-1].strftime("%Y-%m-%d")
    myDict['datetime_first_timeaxis']  = timeaxis[0].strftime("%Y-%m-%d")
    myDict['datetime_last_timeaxist']   = timeaxis[-1].strftime("%Y-%m-%d")
    
    # logging
    logging.info('The selected timespan is: ' + myDict['datetime_first_selected'] + ' - ' + myDict['datetime_last_selected'] )
    logging.info('The extented timespan is: ' + myDict['datetime_first_extented'] + ' - ' + myDict['datetime_last_extented'] )
    logging.info('TOTAL' + myDict['total_number_elements'])
    return npmatrix, timeaxis, df_filled_extented, myDict



# ## Plot

def plot_highchart(df_filled_extented, timeaxis, myDict ):
    # get path
    script_path = os.path.dirname( os.path.realpath(__file__) )
    
    template = Template(open(script_path + '/template_jinja2.tt').read())
    
    output = template.render(df=df_filled_extented.replace(np.nan, '', regex=True),date=datetime.now(), myDict=myDict )
    
    with open(myDict['picture_filename'] + '.html', 'w') as f:
        f.write(output)


def plot_matrix( npmatrix, timeaxis, org_header, myDict ):
    
    logging.info('Plot the data')
    
    picture_filename = myDict['picture_filename'] + '.png'

    # https://matplotlib.org/gallery/images_contours_and_fields/pcolor_demo.html#sphx-glr-gallery-images-contours-and-fields-pcolor-demo-py
    # https://stackoverflow.com/questions/52626103/custom-colormap


    # create new colormap
    norm = matplotlib.colors.Normalize(-1,1)


    # LinearSegmentedColormap
    # https://stackoverflow.com/questions/52626103/custom-colormap
    mycolors = [[norm(-1.0), "limegreen"],
              [norm( -0.95), "yellow"],
               [norm(0.8), "hotpink"],
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

    #fig, ax0 = plt.subplots(1, 1)
    
    
    # start with a rectangular Figure
    fig = plt.figure(figsize=(12, 4.5))
    ax0 = plt.axes([0.07, 0.2, 0.99, 0.8])
    
    
    fontsize_default = 9
    
    
    
    
    # Add text
    """Add figure creating timestamp"""
    """https://riptutorial.com/matplotlib/example/16030/coordinate-systems-and-text"""
    
    my_txt_legend_1 = ["Key","Description","Figure generated", "Number of days without missing data", "Number of days, where data are missed"]
    my_txt_legend_2 = [myDict.get('_optional_info', {}).get('keyword', ''), myDict.get('_optional_info', {}).get('description', ''), str(myDict['datetime_now']), str( myDict['elements_eq0'] ) + ' of ' + str(myDict['total_number_elements']), str( myDict['elements_gt0'] ) + ' of ' + str(myDict['total_number_elements']) ]
    
    for index, item in enumerate(my_txt_legend_1):
        yy = 0.15 - (index+1)/50
        plt.text(0.01, yy, my_txt_legend_1[index], fontsize=fontsize_default-3, ha='left', va='baseline', transform=fig.transFigure)
        plt.text(0.2, yy, my_txt_legend_2[index], fontsize=fontsize_default-3, ha='left', va='baseline', transform=fig.transFigure)
    

    

    # plot npmatrix data
    c = ax0.pcolor(npmatrix,cmap=cmap11, edgecolors='w', linewidths=2)
    
    # set limits of colorbar
    c.set_clim(vmin=0, vmax=1)
    
    # set yticks
    ax0.set_yticks([1.5, 3.5, 5.5])
    ax0.set_yticklabels(['Tue', 'Thu', 'Sat'])

    ax0.set_yticks([0.5, 2.5, 4.5, 6.5])
    ax0.set_yticklabels(['Mon', 'Wed', 'Fri', 'Sun'])

    # stepsize of dates on xaxis in unit WEEK
    stepsize=4
    
    # set xticks and labels 
    # in a eqidistant way
    # xlabeltxt = 'Time [date of first weekday'
    #xticks = np.arange(0+0.5, len(timeaxis)+0.5, stepsize).tolist()
    #xticklabels = [date_obj.strftime('%Y-%m-%d') for date_obj in timeaxis[0:len(timeaxis):stepsize]]
    
    
    # set xticks and labels 
    # based on 15.th of month
    xlabeltxt = 'Time [week]'
    xticks = []
    xticklabels = []
    for kk in range( len(timeaxis) ):
        for nn in range(7):
            currentdate = timeaxis[kk] + timedelta(days=nn)

            if ( currentdate.day == 15 ):
                xticks.append( 0.5 + kk )
                if ( len(xticklabels) == 0 ): # print also year if first tick
                    xticklabels.append( currentdate.strftime('%b') + '\n' + str(currentdate.year) )
            
                elif ( currentdate.month == 1 ): # print year always on January
                    xticklabels.append( currentdate.strftime('%b') + '\n' + str(currentdate.year) )
              
                else:
                    xticklabels.append( currentdate.strftime('%b') )


    # set it
    ax0.set_xticks( xticks )
    ax0.set_xticklabels( xticklabels )

    # adapt fontsize at labels
    plt.xticks(rotation=0, fontsize=fontsize_default)
    plt.yticks(fontsize=fontsize_default)
    #plt.set_cmap('gray')


    # set aspect ratio
    plt.gca().set_aspect('equal', adjustable='box')

    # set title and labels
    title1 = org_header[1].title() # makes string camel case
    #ax0.set_title(label='Data availability', weight='bold')
    #ax0.set_title(label=title1, weight='bold')
    ax0.set_ylabel('Weekday')
    ax0.set_xlabel(xlabeltxt)

    # orientation colorbar
    # https://stackoverflow.com/questions/13310594/positioning-the-colorbar

    #cbar = fig.colorbar(c, ticks=[0, 1], ax=ax0, orientation="horizontal", pad=0.3)
    #cbar = fig.colorbar(c, ticks=[np.nanmin(npmatrix), np.nanmax(npmatrix)], ax=ax0, shrink=0.4)
    cbar = fig.colorbar(c, ticks=[0, 0.45, 0.9], ax=ax0, shrink=0.4)


    #cbar.ax.set_yticklabels(['less', 'more'], fontsize=fontsize_default-1)  # vertically oriented colorbar
    cbar.ax.set_yticklabels(['complete', 'partly', 'less'], fontsize=fontsize_default-1)  # vertically oriented colorbar
    #cbar.set_label(label='Temperature', fontsize=8, weight='bold')
    cbar.set_label(label=title1, labelpad=-75, y=0.5, rotation=90, fontsize=fontsize_default, weight='bold')

    # save figure
    #plt.savefig(facecolor="none",dpi=200,fname=picture_filename)
    plt.savefig(dpi=200,fname=picture_filename)
    
    # close figure
    plt.close(fig)




def main( myDict ):
    logging.info('Start script')
    
    # get data from a source
    if ( myDict['data_import_type'] == 'DataFrame' ):
        df, org_header = rename_external_df_columns( myDict['DataFrame'] )
        
    elif ( myDict['data_import_type'] == 'CSV' ):
        df, org_header = read_csv_file( myDict['csv_filename'] )

    elif ( myDict['data_import_type'] == 'Test' ):
        df, org_header = generate_test_data()
        df, org_header = rename_external_df_columns( df )
    else:
        logging.warning('data_imoprt value is wrong: ' + myDict['data_import_type'] ) 
        exit()
    
    # check if DataFrame
    if not isinstance(df, pd.DataFrame):
        logging.warning('Provided or generated variable is not a DataFrame ') 
        exit()
        
    # add columns
    df = add_df_columns( df )
    
    # generate filled dataframe
    df_filled = group_fill_data( df )
    
    npmatrix, timeaxis, df_filled_extented, myDict = create_matrix_from_grouped_filled_dataframe( df_filled, myDict )
    
    plot_matrix( npmatrix, timeaxis, org_header, myDict )
    
    plot_highchart( df_filled_extented, timeaxis, myDict )


if __name__ == '__main__':
    main( { 
        'data_import_type' : 'Test', # Test|DataFrame|CSV
        'picture_filename' : 'df.png',
        'csv_filename' : 'd2.csv'
    } )



