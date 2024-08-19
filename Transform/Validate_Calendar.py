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

class ValidateCalendar:

    def __init__(self, cal, cal_id, client_id, future_dates_ind,plan_year_begin_date,plan_year_end_date):

        #Master Calendar
        self.calendar = cal
        self.cal_id = cal_id
        self.company_name = self.calendar['NAME'].unique()[0]
        self.client_id = client_id
        self.future_dates_ind = future_dates_ind
        self.plan_year_begin_date = plan_year_begin_date
        self.plan_year_end_date = plan_year_end_date

        logging.info('----- Evaluating Cal {} {}'.format(cal_id,self.company_name))

        #Empty Dataframe to hold errors that are found during validation
        self.errors = pd.DataFrame(columns = ['Company ID','Company','Pay Group ID','Pay Period','Status','Error ID','Notes'],dtype=str)

        #Convert Dates To Datetime
        self.convertDatesToDateTime()

        #Check Dates Format
        #Method will drop unneeded columns
        self.checkDateFormats()

        #Check for First Pay Period, make sure it is not listed as OE
        self.isFirstPayPeriodOE()

        #Check Number of Pay Periods
        self.checkNumberofPayPeriods()

        #Check All Deduction Cutoff Dates are within the plan year
        self.cutoffDatesInSamePlanYear()

        #Check All Cutoff Dates ARE NOT Less Than Run Dates
        self.cutoffLessThanRunDate()

        #Future Date Indicator should = Y, If Cutoff Date > Run Date
        self.cutoffGreaterThanRunDate()

        #Check if one Pay Periods Cutoff Date is not greater than the Next Pay Period
        self.cutoffNotGreaterThanNextCutoff()

        #Check for Date Gaps In bewteen Pay Periods
        self.checkBeginAndEndDateGaps()

        #Check IF ALL Outside of Desired Plan Year
        self.datesOutsidePlanYear()

        #Check if the last Cutoff Date in the Lats Pay Period is in the Next Plan Year
        self.lastCutoffDateInNextPlanYear()

        #Check If Run Dates Are In Order
        self.areRunDatesInOrder()

        #Check for multiple Pay Periods running on the same day
        self.duplicateRunDates()

        #Check for EXC_STANDARD on PAYROLL_SCHEDULE
        self.doesExcStandardNotEqualN()

        #Check if SUPP_CCLE_NO is NOT 0
        self.doesSuppCycleNoEqualZero()

    def convertDatesToDateTime(self):

        for column in st.PAYROLL_FILE_COLUMNS:

            logging.info('Converting Column: {}'.format(column))

            try:

                if column not in ['Pay Period','EXC_STANDARD','SUPP_CYCLE_NO']:

                    #Convert Date to Datetime
                    #If DateTime CANNOT recgonized value as a Date, it will return 'NaT'
                    self.calendar[column] = pd.to_datetime(self.calendar[column]
                                                             , format='%d-%b-%y',errors ='coerce')

                logging.info('Column Converted: {}'.format(column))

            except:
                self.calendar[column] = pd.NaT
                logging.error('{} Column Not Found; Added with NaT values'.format(column))

                self.errors.loc[len(self.errors.index)] = [0, 'Warning'
                    , 'Column {} was not found and has been added with Null values'.format(column)]


    def checkDateFormats(self):

        logging.info('----- Check Date Formats')

        old_payroll_columns = list(self.calendar.columns)
        old_payroll_columns = [str(i or '') for i in old_payroll_columns]

        logging.info('Columns Found On File: {}'.format(old_payroll_columns))

        error_message_id = 9

        dropped_columns = np.setdiff1d(old_payroll_columns,st.PAYROLL_FILE_COLUMNS)

        if len(dropped_columns) > 0:

            '''
            self.errors.loc[len(self.errors.index)] = [self.company_name, self.cal_id, 0, 'Warning'
                , 'Columns should be removed: {}'.format(list(dropped_columns))]
            '''

            logging.error('Columns should be removed: {}'.format(list(dropped_columns)))
        else:
            logging.info('Dates Format: Passed')

        #Remove unwanted columns from the Master Calendar
        self.calendar = self.calendar[st.PAYROLL_FILE_COLUMNS]

        # Check Formarts of Dates
        # An incorrect format will be listed as 'Nat'
        bool_bad_date_format = self.calendar[st.PAYROLL_FILE_DATES_ONLY_COLUMNS].isnull()
        bool_bad_date_format = bool_bad_date_format[bool_bad_date_format.eq(True).any(axis=1)]

        # Cycle Through rows w/ Bad Formats
        for index, row in bool_bad_date_format.iterrows():

            original_row = self.calendar.iloc[index]

            for column in st.PAYROLL_FILE_DATES_ONLY_COLUMNS:

                if row[column] == True:
                    self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id,
                                        original_row['Pay Period'], 'Error', error_message_id,st.AVAL_ERRORS.loc
                                                               [error_message_id,'Error Message']]


    def isFirstPayPeriodOE(self):

        # Method will check if the First row of the Calendar is listed as the 1st Pay Period
        # Routinely Client will add an "OE" row, essentially saying the OE is the 1st Pay Period

        logging.info('----- Verifying First Pay Period')

        error_message_id = 0

        first_pay_period_cutoff = self.calendar.iloc[0]['Deduction Cutoff Date']

        logging.info('First Pay Period Cutoff: {}'.format(first_pay_period_cutoff))

        if first_pay_period_cutoff < pd.Timestamp('{}-01-02'.format(st.DESIRED_PLAY_YEAR)):
            logging.error('First Pay Period: Fail')
            logging.error('First Pay Period Cutoff Date is prior to 1/2 of the current plan year'
                          .format(first_pay_period_cutoff))

            self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id,1, 'Error'
                , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]


        else:
            logging.info('First Pay Period: Pass')

    def checkNumberofPayPeriods(self):

        # Method will check the number of Pay Periods listed in the calendar ad determine if it equals
        # 12,24,26, or 52 Pay Periods. If a different number of Pay Periods are needed for validation,
        # add it the valid_no_of_pay_periods list.

        logging.info('----- Verifying Number of Pay Periods')

        error_message_id = 1

        no_of_rows_in_cal = len(self.calendar.index)

        logging.info('Listed # of Pay Periods: {}'.format(no_of_rows_in_cal))

        valid_no_of_pay_periods = [12,24,26,52] #Add or Remove Values if needed

        if no_of_rows_in_cal in valid_no_of_pay_periods:
            logging.info('Number of pay periods: Pass')
        else:
            logging.error('Number of pay periods: Fail')

            self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id, 0, 'Error'
                , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]

    def cutoffDatesInSamePlanYear(self):

        # Method will check to see if all Deduction Cutoff Dates are in the Desired Plan Year
        # For Example, if the Desired Plan Year is 2022, and a date is in 2021, that date will be flagged.

        logging.info('----- Checking Cutoff Dates In {} Plan Year'.format(st.DESIRED_PLAY_YEAR))

        error_message_id = 2

        #Finds Dates NOT IN the desired plan year
        #dates_outside_plan_year = self.calendar[self.calendar['Deduction Cutoff Date'].dt.year != st.DESIRED_PLAY_YEAR]

        dates_outside_plan_year = self.calendar[(self.calendar['Deduction Cutoff Date'] < self.plan_year_begin_date)
        | (self.calendar['Deduction Cutoff Date'] > self.plan_year_end_date)]

        logging.info('Cutoff Dates: {}'.format(self.calendar['Deduction Cutoff Date']))
        logging.info('Plan Year Begin Date: {}'.format(self.plan_year_begin_date))
        logging.info('Plan Year End Date: {}'.format(self.plan_year_end_date))

        if len(dates_outside_plan_year.index) > 0:

            logging.error("The following Pay Periods ARE NOT in {}".format(st.DESIRED_PLAY_YEAR))

            for index, row in dates_outside_plan_year.iterrows():

                logging.error('Pay Period: {}'.format(row['Pay Period']))
                logging.error('Deduction Cutoff Date: {}'.format(row['Deduction Cutoff Date']))

                self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id,row['Pay Period'], 'Error'
                    , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]

            logging.error('Dates In Plan Year: Fail')

        else:
            logging.info('Dates In Plan Year: Pass')


    def cutoffLessThanRunDate(self):

        # Method will check if a Pay Periods cutoff Dates are less than the Run Date in the same Pay Period.
        # If Cutoff Date is less than Run Date, a value of "Bad" will display. Else "Good"

        logging.info('----- Cutoff Dates Less Than Run Dates')

        error_message_id = 3

        temp_cal = self.calendar.copy()

        temp_cal['New'] = temp_cal.apply(lambda x: 'Bad' if x['Deduction Cutoff Date'] <
                                                       x['File Run Date'] else 'Good', axis=1)

        cutoff_less_than_run = temp_cal[temp_cal['New'] == 'Bad']

        #If bad dates are found, cycle through each bad date row
        if len(cutoff_less_than_run.index) > 0:

            logging.error('The Following Pay Periods Have Deduction Cutoff Dates Less Than Run Dates')

            for index, row in cutoff_less_than_run.iterrows():

                logging.error('Pay Period: {}'.format(row['Pay Period']))
                logging.error('Deduction Cutoff Date: {}'.format(row['Deduction Cutoff Date']))

                self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id,row['Pay Period'], 'Error'
                    , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]

            logging.error('Cutoff Less Than Run: Fail')

        else:
            logging.info('Cutoff Less Than Run: Pass')

    def cutoffGreaterThanRunDate(self):

        # Method will check if a Pay Periods cutoff Dates are Greater than the Run Date in the same Pay Period.
        # If Cutoff Date is Greater than Run Date, a value of "Bad" will display. Else "Good"
        # This method is too determine if the Client needs payauto_payroll_config.og_future_dated_events_ind = "Y"

        logging.info('----- Cutoff Dates Greater Than Run Dates')

        error_message_id = 4

        temp_cal = self.calendar.copy()

        temp_cal['New'] = temp_cal.apply(lambda x: 'Bad' if x['Deduction Cutoff Date'] >
                                                       x['File Run Date'] else 'Good', axis=1)

        cutoff_greater_than_run = temp_cal[temp_cal['New'] == 'Bad']

        #If bad dates are found, cycle through each bad date row
        if (len(cutoff_greater_than_run.index) > 0) and (self.future_dates_ind != 'Y'):

            logging.error('The Following Pay Periods Have Deduction Greater Dates Less Than Run Dates (Warning Only!)')

            for index, row in cutoff_greater_than_run.iterrows():

                logging.error('Pay Period: {}'.format(row['Pay Period']))
                logging.error('Deduction Cutoff Date: {}'.format(row['Deduction Cutoff Date']))

                self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id,row['Pay Period'], 'Error'
                    , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]

            logging.error('Cutoff Greater Than Run: Error')

        else:
            logging.info('Cutoff Less Than Run: Pass')

    def cutoffNotGreaterThanNextCutoff(self):

        # This Method will check to see if a Deduction Cutoff Date in one period, is greater than
        # the Deduction Cutoff Date in the next Pay Period

        logging.info('----- Cutoff Dates Not Greater Than The Next Cutoff Date')

        error_message_id = 5

        # If Cutoff Dates are in order, no further processing is needed
        if pd.Index([self.calendar['Deduction Cutoff Date']]).is_monotonic_increasing == True:

            logging.info('Deduction Cutoff Greater Than Next: Pass')
        else:

            temp_data = self.calendar[['Pay Period','Deduction Cutoff Date']]

            for index, row in temp_data.iterrows():

                #Cycle trhough each Cutoff Date

                curr_pay_ded_cut = row['Deduction Cutoff Date']

                #If row is not the last row on the calendar, get cut date from the next pay period
                #Last row is assigned its own cut date as next cut date

                if index != (len(temp_data.index) - 1):
                    next_pay_ded_cut = temp_data.iloc[index+1]['Deduction Cutoff Date']
                else:
                    next_pay_ded_cut = curr_pay_ded_cut

                #If current cut date greater than the next, log an error
                if curr_pay_ded_cut > next_pay_ded_cut:
                    logging.error('Pay Period: {} Current Ded Cut Date: {} Next PP Cut Date: {}'
                                 .format(row['Pay Period'],row['Deduction Cutoff Date'],next_pay_ded_cut))

                    self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id,row['Pay Period'], 'Error'
                        , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]
                else:
                    logging.info('Pay Period: {} Current Ded Cut Date: {} Next PP Cut Date: {}'
                                 .format(row['Pay Period'],row['Deduction Cutoff Date'],next_pay_ded_cut))

    def checkBeginAndEndDateGaps(self):

        logging.info('----- Check Gaps Between End Dates and Begin Dates')

        temp_data = self.calendar[['Pay Period','Pay Period Begin Date','Pay Period End Date']]

        for index, row in temp_data.iterrows():

            # Cycle through each Cycle and evaluate the previous cycles end date, and the next cycles begin date
            # For Example, if the loop is on Cycle 3, then it will evaluate the End Date from Cycle 2
            # and the Begin Date from Cycle 4

            #Assumed to be the first Pay Period
            if index == 0:
                next_pay_begin_dt = temp_data.iloc[index + 1]['Pay Period Begin Date']
                prev_pay_end_dt = None

                expected_next_begin_dt = row['Pay Period End Date'] + datetime.timedelta(days=1)
                expected_prev_end_dt = None

            #Assumed to be the last pay period
            elif index == (len(temp_data.index) - 1):
                next_pay_begin_dt = None
                prev_pay_end_dt = temp_data.iloc[index - 1]['Pay Period End Date']

                expected_next_begin_dt = None
                expected_prev_end_dt = row['Pay Period Begin Date'] - datetime.timedelta(days=1)
            else:
                next_pay_begin_dt = temp_data.iloc[index + 1]['Pay Period Begin Date']
                prev_pay_end_dt = temp_data.iloc[index - 1]['Pay Period End Date']

                expected_next_begin_dt = row['Pay Period End Date'] + datetime.timedelta(days=1)
                expected_prev_end_dt = row['Pay Period Begin Date'] - datetime.timedelta(days=1)


            logging.info('Pay Period: {} Begin Date: {} End Date: {}'.format(row['Pay Period'],
                                                                             row['Pay Period Begin Date'],
                                                                             row['Pay Period End Date']))

            logging.info('Prev End Dates | Actual: {} Expected: {}'.format(prev_pay_end_dt,expected_prev_end_dt))

            logging.info('Next Begin Dates | Actual: {} Expected: {}'.format(next_pay_begin_dt,expected_next_begin_dt))

            #If the expected values DO NOT MATCH the actual values
            if next_pay_begin_dt != expected_next_begin_dt:
                logging.error('Expected Next Begin Date Incorrect')

                error_message_id = 6

                self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id,row['Pay Period'], 'Error'
                    , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]

            if prev_pay_end_dt != expected_prev_end_dt:
                logging.error('Expected Prev End Date Incorrect')

                error_message_id = 7

                self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id,row['Pay Period'], 'Error'
                    , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]

    def datesOutsidePlanYear(self):

        # Method will check if there are any Dates outside of plan year

        logging.info('----- Dates Outside Plan Year')

        error_message_id = 8

        dates_outside_plan_year_flag = False

        # Finds Dates NOT IN the desired plan year
        for column in list(self.calendar.columns):

            logging.info('Evaluating {}'.format(column))

            if (isinstance(self.calendar.loc[0, column], datetime.datetime)):

                logging.info('Column is Date Format..')

                #dates_outside_plan_year = self.calendar[self.calendar[column].dt.year != st.DESIRED_PLAY_YEAR]

                dates_outside_plan_year = self.calendar[
                    (self.calendar[column] < self.plan_year_begin_date)
                    | (self.calendar[column] > self.plan_year_end_date)]

                if len(dates_outside_plan_year.index) > 0:
                    dates_outside_plan_year_flag = True

                    logging.error('Date outside plan year: {}'.format(dates_outside_plan_year))

                else:
                    logging.info('No dates outside of plan  year found')
            else:
                logging.info('Column IS NOT Date Format..')

        if dates_outside_plan_year_flag:
            self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name,self.cal_id,0,
                                                       'Warning',error_message_id,
                                                       st.AVAL_ERRORS.loc[error_message_id,'Error Message']]

    def getOEDatesMatch(self):

        # Method will read in file that determines IF a clients OE Run Date is equal to or greater than
        # their first pay period run date.

        logging.info('----- Verifying Number of Pay Periods')

        error_message_id = 1

        no_of_rows_in_cal = len(self.calendar.index)

        logging.info('Listed # of Pay Periods: {}'.format(no_of_rows_in_cal))

        valid_no_of_pay_periods = [12,24,26,52] #Add or Remove Values if needed

        if no_of_rows_in_cal in valid_no_of_pay_periods:
            logging.info('Number of pay periods: Pass')
        else:
            logging.error('Number of pay periods: Fail')

            self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id, 0, 'Error'
                , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]


    def lastCutoffDateInNextPlanYear(self):

        # Method will check if the last pay periods cutoff date, is in the next plan year and
        # not the current

        logging.info('----- Last Cutoff Date In Next Plan Year')

        error_message_id = 11

        # Get Last Row on the Calendar
        last_row = self.calendar.iloc[-1]

        logging.info('Last Pay Period of Calendar: {}'.format(last_row))

        # Get the Year of the Cutoff Date
        last_cutoff_ded_date = last_row['Deduction Cutoff Date']

        logging.info('Last Deduction Cutoff Date: {}'.format(last_cutoff_ded_date))
        logging.info('Plan Year End Date: {}'.format(self.plan_year_end_date))

        #If last cutoff date is r=greater than the desired plan year
        if last_cutoff_ded_date > self.plan_year_end_date:
            logging.error('Last Pay Period Cutoff: Fail')

            self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id
                , last_row['Pay Period'], 'Error'
                , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]
        else:
            logging.info('Last Pay Period Cutoff: Pass')

    def areRunDatesInOrder(self):

        # Method will check if run dates are in sequental order

        logging.info('----- Check if Cutoff/Run Dates Are In Order')

        error_message_id = 12

        #If Run Dates Are In Order
        if self.calendar['File Run Date'].is_monotonic_increasing:
            logging.error('Last Pay Period Cutoff: Pass')
        else:
            logging.info('Last Pay Period Cutoff: Fail')

            self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id
                , 0, 'Error'
                , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]

    def duplicateRunDates(self):

        # Method will check if run dates are in sequental order

        logging.info('----- Check if there are Duplicate Run Dates')

        error_message_id = 13

        #If Run Dates Are In Order
        if self.calendar.duplicated(subset=['File Run Date']).any():

            logging.error('Duplicate Run Dates: Fail')

            self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id
                , 0, 'Error'
                , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]
        else:
            logging.info('Duplicate Run Dates: Pass')

    def doesExcStandardNotEqualN(self):

        # Method will check if Exc Standard is set to N
        # According to Louis, there will be an error with HSA/FSA if not

        logging.info('----- Check if Exc Standard NOT set to N')

        error_message_id = 14

        #If Any Value is NOT N, report error
        exc_standard_values = self.calendar['EXC_STANDARD'].unique()
        if (all(x == 'N' for x in exc_standard_values)):

            logging.info('EXC_STANDARD = N: Pass')

        else:

            logging.error('EXC_STANDARD = N: Fail')

            self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id
                , 0, 'Error'
                , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]

    def doesSuppCycleNoEqualZero(self):

        # Method will check if Supp Cycle No equal 0

        logging.info('----- Check if Supp Cycle No is NOT 0')

        error_message_id = 15

        #If Any Value is NOT N, report error
        exc_standard_values = self.calendar['SUPP_CYCLE_NO'].unique()

        if (all(x == 0 for x in exc_standard_values)):

            logging.info('SUPP_CYCLE_NO = 0: Pass')

        else:

            logging.error('SUPP_CYCLE_NO != 0: Fail')

            self.errors.loc[len(self.errors.index)] = [self.client_id,self.company_name, self.cal_id
                , 0, 'Error'
                , error_message_id,st.AVAL_ERRORS.loc[error_message_id,'Error Message']]

    def get_errors(self):
        return self.errors

















