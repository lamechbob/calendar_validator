import os
import pandas as pd


class Settings:

    BASE_DIR = os.getcwd()

    #Paths
    LOG_PATH = 'Data/Logs'
    REPORT_PATH = 'Data/Reports/'
    CAL_HIST_PATH = 'Data/Pay Calendars History/'
    PAY_CAL_PATH = 'Data/Pay Calendars/'

    #Plan Year
    DESIRED_PLAY_YEAR = 2024

    #Used to determine which enviroment to test
    #Variable must be set by the user
    #0 = AUTHORING
    #1 = SIMULATION
    #2 = DELIVERY
    #3 = TEST

    TEST_ENVIROMENT = 3

    #Using a switcher to determine which enviroment calendar will be evaluated
    TEST_CAL_SWITCHER = {0: 'AUTHORING',1: 'SIMULATION',2: 'DELIVERY',3: 'TEST'}
    TEST_CAL = TEST_CAL_SWITCHER.get(TEST_ENVIROMENT,'DELIVERY')

    #DATABASE_CAL is the Final Calendar Data that will be evaluated
    #If TEST_ENVIROMENT is Null or has not been defined, it will default to the Delivery Calendar

    DATABASE_CAL = 'Data/Pay Calendars/{}_{}_CALENDAR.csv'.format(DESIRED_PLAY_YEAR,TEST_CAL)

    DATABASE_CAL_FILENAME = os.path.basename(DATABASE_CAL).split(".")[0]

    #Future Indicators File
    #File contains Plan Year Start and Stop, and the Future Date Indicator Flag

    FUTURE_IND_FILE = 'Data/Pay Calendars/{}_{}_FUTURE_INDICATORS.csv'.format(DESIRED_PLAY_YEAR,TEST_CAL)

    #OE Match Data
    OE_MATCH_FILE_DATA = 'Data/Pay Calendars/{}_OE_MATCH_{}.csv'.format(DESIRED_PLAY_YEAR,TEST_CAL)

    # Accpeted Coulmn List
    # Anything outside of these values will be removed

    PAYROLL_FILE_COLUMNS = ['Pay Period', 'Pay Period Begin Date', 'Pay Period End Date',
                            'Deduction Cutoff Date', 'File Run Date','EXC_STANDARD','SUPP_CYCLE_NO']

    PAYROLL_FILE_DATES_ONLY_COLUMNS = ['Pay Period', 'Pay Period Begin Date', 'Pay Period End Date',
                            'Deduction Cutoff Date', 'File Run Date']

    #List of Email Addresses To Notify of Resuts
    NOTIFICATION_FILE = 'Data/Helpers/notification_list.csv'

    #Availabe Errors Used In Repoorting
    AVAL_ERRORS = pd.read_csv('Data/Helpers/Available_Errors.csv')
    AVAL_ERRORS.set_index('Error ID', inplace=True)

    #Errors to be excused
    ERROR_EXCEPT_DATA = pd.read_csv('Data/Helpers/Error_Exceptions_List.csv')

    #Colleague Data
    COLLEAGUE_TEAM_DATA = pd.read_csv('Data/Helpers/Active client teams.csv')

    #Date Error Added Data
    #DATE_ERROR_ADDED_FILE_NAME = r'C:\Users\Lamech-Bob-Manuel\PycharmProjects\calendarValidator\Data\Pay Calendars\{}_{}_DATE_ADDED.csv'.format(DESIRED_PLAY_YEAR,TEST_CAL)
    #DATE_ERROR_ADDED = pd.read_csv(DATE_ERROR_ADDED_FILE_NAME)