import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime as dt
from Locators.Settings import Settings as st

import logging

logging.basicConfig(filename=st.LOG_PATH + '/{}_{}.log'
                    .format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y')),
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w')

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

class CalendarCompare:

    def __init__(self,current_cal):

        #Copy Original Calendar Data
        self.current_cal = current_cal

        self.current_cal_columns = list(self.current_cal.columns)

        #Dummy Data Set to hold Dates that have changed
        #We will use this generate a report
        self.changed = pd.DataFrame(columns=['COMPANY_ID','NAME','PAY_GROUP_ID','Pay Period','Date Column'
                                         ,'Changed From','Changed To'])

        #Copy Calendar
        self.copyCalendar()

        #Compare Previous Calendar To Latest
        self.compareCalendars()

    def compareCalendars(self):

        logging.info('----- Comparing Current Calendar Data versus the Last Dump')

        #Get The List of Latest Modified Files
        list_of_files = glob.glob(st.CAL_HIST_PATH +'/*')

        #Files that have been found to been generated i nthe current enviroment
        #i.e. If we are in Delivery, finds all the Dumps w/ Delivery in the name
        files_that_match_environment = [match for match in list_of_files if match.find(st.TEST_CAL) > 0]

        #Extract Date From Files
        #Then Sort and Reverse Files in Desc Order

        file_dates = [pd.to_datetime(date.split('_')[1], format='%m%d%Y', errors='coerce').date() for date in files_that_match_environment ]
        file_dates.sort(reverse=True)
        logging.info('Searching for Dump Files w/ {}'.format(st.TEST_CAL))
        logging.info('Last 3 Dates Found {}'.format(file_dates[:3]))

        logging.info('Searching for changes to calendars')

        for date in file_dates:

            #If the File is of Todays Date, we dont want to compare
            #We are looking for the latest, and some times we run this multple times a day
            #Keep in Mind, we're assuming the folder is already sorted by Modified.

            if date == dt.today().date():
                pass
            else:
                file = st.CAL_HIST_PATH+'{}_{}_CALENDAR_DUMP.csv'.format(st.TEST_CAL,date.strftime('%m%d%Y'))
                previous_cal_data = pd.read_csv(file)
                logging.info('Latest File Before Today: {}'.format(file))
                break

        diff_df = pd.merge(previous_cal_data, self.current_cal, how='outer',indicator=True)

        diff_date_dropped = diff_df.loc[diff_df['_merge'] == 'left_only']
        diff_date_added = diff_df.loc[diff_df['_merge'] == 'right_only']

        diff_date_dropped = diff_date_dropped.drop(['_merge'], axis=1)
        diff_date_added = diff_date_added.drop(['_merge'], axis=1)

        if (diff_date_dropped.empty) and (diff_date_added.empty):
            logging.info('No changes to calendars have been found')

        #Were going to find the rows that CHANGED w/ a manual process
        #First were going to look to see if the latest rows have a previous row
        #and then Vice Versa, if old rows have a new row.

        #Compare The Current Rows Versus the Previous

        #Cycle Through Rows that are found on the Current Cal and NOT the Previous
        #This is tricky because it will include any changes
        #Here we're going to look at what was added and what has changed
        for index, row in diff_date_added.iterrows():

            logging.info('Changes to calendars have been found')

            curr_row_list = list(row)

            #Look for the current row in the last dump
            prev_row = diff_date_dropped.loc[(diff_date_dropped['COMPANY_ID'] == row['COMPANY_ID'])
                                            &(diff_date_dropped['PAY_GROUP_ID'] == row['PAY_GROUP_ID'])
                                            &(diff_date_dropped['Pay Period'] == row['Pay Period'])]

            #If the current row has been found in the last dump
            #we will consider this a "Change"
            if len(prev_row.index) > 0:

                prev_row_list = list(prev_row.values[0])

                #Cycle Through each element of the current/latest row
                #and compare that value to what was in the previous dump
                #This is to find WHICH Date has Changed
                i=0
                for element in curr_row_list:

                    #If they are the same, pass
                    if element == prev_row_list[i]:
                        pass

                    #Else if they are different, we'll consider this a change and add it
                    #to the global change report
                    else:

                        self.changed.loc[len(self.changed.index)] = [curr_row_list[0],curr_row_list[1], curr_row_list[2],
                                            curr_row_list[3],self.current_cal_columns[i],element,prev_row_list[i]]

                        logging.error('{}: Pay Period {} {} has changed'.format(curr_row_list[2]
                                                                                ,curr_row_list[3]
                                                                                ,self.current_cal_columns[i]))
                    i+=1

            #If a Previous Row is not found, we'll consider this an "Add"
            #As the row was not present previously
            else:

                self.changed.loc[len(self.changed.index)] = [curr_row_list[0], curr_row_list[1], curr_row_list[2],
                                                   curr_row_list[3], 'Entire Row', 'Missing', 'Added']

                logging.error('{}: Pay Period {} row has been added'.format(curr_row_list[2],curr_row_list[3]))

        #Compare The Previous Rows Versus the Current
        #Here we are not looking or a "Change" at all
        #If a Future Row is NOT FOUND, then we'll assume this row is missing in the Current Cal Data

        #Cycle through Data that was in the latest Dump BUT NOT the Current Cal Data
        for index, row in diff_date_dropped.iterrows():

            #Look for that row in the Current Cal Data
            future_row = diff_date_added.loc[(diff_date_added['COMPANY_ID'] == row['COMPANY_ID'])
                                            &(diff_date_added['PAY_GROUP_ID'] == row['PAY_GROUP_ID'])
                                            &(diff_date_added['Pay Period'] == row['Pay Period'])]

            #If 0, then NO future data was found
            #We're going to assume it is missing from the current data
            #thus its been removed.
            if len(future_row.index) == 0:

                prev_row_list = list(row)

                self.changed.loc[len(self.changed.index)] = [prev_row_list[0], prev_row_list[1], prev_row_list[2],
                                                   prev_row_list[3], 'Entire Row', 'Present', 'Missing']

                logging.error('{}: Pay Period {} has been removed'.format(prev_row_list[2],prev_row_list[3]))

            #We are not looking for any changes because we've already that
            else:
                pass

    def getCompareResults(self):
        self.changed.rename(columns={'COMPANY_ID': 'Company ID', 'PAY_GROUP_ID': 'Pay Group ID',
                                     'NAME': 'Company Name'}, inplace=True)
        return self.changed

    def copyCalendar(self):

        #Copy the Calendar Data that was validated, and dump as a new file
        #This is for historical reference

        logging.info('----- Dumping Calendars')

        cal_dump_file_name = st.CAL_HIST_PATH + '{}_{}_CALENDAR_DUMP.csv'.format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y'))
        logging.info('{}'.format(cal_dump_file_name))

        self.current_cal.to_csv(cal_dump_file_name, index=None)
