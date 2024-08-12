import pandas as pd
from Locators.Settings import Settings as st

import logging

logging.basicConfig(filename=st.LOG_PATH + '\{}_{}.log'
                    .format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y')),
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w')

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

class LoadFutureInd:

    def __init__(self):

        pass

    def get_future_ind(self):

        logging.info('----- Loading Future Indicators File')
        logging.info('{}'.format(st.FUTURE_IND_FILE))

        return pd.read_csv(st.FUTURE_IND_FILE)
