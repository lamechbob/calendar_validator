import pandas as pd
from datetime import datetime
from Locators.Settings import Settings as st

import logging

logging.basicConfig(filename=st.LOG_PATH + '/{}_{}.log'
                    .format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y')),
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w')

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

class LoadCalendar:

    def __init__(self, file_name, skip_row_count, tab, data_flag):
        self.file_name = file_name
        self.skip_row_count = skip_row_count
        self.tab = tab
        self.data_flag = data_flag
        self.excel_data = pd.DataFrame()
        self.header_values = []

        self.load_file()

    def load_file(self):

        try:
            wb = load_workbook(self.file_name, data_only=self.data_flag)
        except:
            print('{} file is not found'.format(self.file_name))

        source = wb[self.tab]

        header_row = self.skip_row_count + 1
        current_row = header_row + 1

        # Get Header Row
        for head in source[header_row]:
            self.header_values.append(head.value)

        row = []

        while True:
            temp_list = []

            for cell in source[current_row]:
                temp_list.append(cell.value)

            if temp_list[0] != None:
                row.append(temp_list)
            else:
                break;

            current_row += 1

        self.excel_data = pd.DataFrame(row, columns=self.header_values)

    def get_excel_data(self):

        return self.excel_data

    def get_headers(self):
        return self.header_values