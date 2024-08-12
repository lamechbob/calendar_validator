import pandas as pd
from datetime import datetime
from Locators.Settings import Settings as st

import logging

logging.basicConfig(filename=st.LOG_PATH + '\{}_{}.log'
                    .format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y')),
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w')

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

class LoadCalendarDatabase:

    def __init__(self):

        logging.info('----- Loading Calendar Data')
        logging.info('{}'.format(st.DATABASE_CAL))

        self.calenders = pd.read_csv(st.DATABASE_CAL)
        self.calender_ids = list(self.calenders['PAY_GROUP_ID'].unique())

    def get_database_calendar(self):
        return self.calenders

    def get_list_of_calendars(self):
        return self.calender_ids