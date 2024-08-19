import pandas as pd


import numpy as np

import datetime

from Locators.Settings import Settings as st
from Extract.Write_Error import WriteErrors as we
from Load.Load_Future_Ind import LoadFutureInd as lf

import logging

logging.basicConfig(filename=st.LOG_PATH + '/{}_{}.log'
                    .format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y')),
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w')

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

class LoadNonValidationData:

    #Non Validation Data
    #This is data that is determined to be an error via SQL and NOT during our Datbase Evaluation Process
    #Here Errors are added after the Database Evaluation has concludied

    def __init__(self):

        #Empty Dataframe to hold errors that are found during validation
        #Error List used in this Class ONLY
        self.errors = pd.DataFrame(
            columns=['Company ID', 'Company', 'Pay Group ID', 'Pay Period', 'Status', 'Error ID', 'Notes'], dtype=str)

    def getOEDatesMatch(self):

            #Method will read in file that has PRE-DETERMINED via SQL IF a clients OE Run Date is equal
            #to or greater than their first pay period run date.

            #If Client is found on the file, t will simply add an error to the global error list

            logging.info('----- Load Data From OE Match Query')
            logging.info('{}'.format('{}'.format(st.OE_MATCH_FILE_DATA)))

            error_message_id = 10

            data = pd.read_csv(st.OE_MATCH_FILE_DATA)

            if data.empty != True:

                for index, row in data.iterrows():

                    self.errors.loc[len(self.errors.index)] = [row.COMPANY_ID, row.NAME
                        , row.PAY_GROUP_ID, 1,'Error' ,error_message_id, st.AVAL_ERRORS.loc[error_message_id
                        , 'Error Message']]

            #Return Method Error List
            return self.errors
