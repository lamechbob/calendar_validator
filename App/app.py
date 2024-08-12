import pandas as pd
import datetime
from datetime import datetime as dt
from datetime import date

from Locators.Settings import Settings as st
from Load.Load_Calendar import LoadCalendar as lc
from Load.Load_Calendar_Database import LoadCalendarDatabase as lcd
from Load.Load_Non_Validation_Data import LoadNonValidationData as lvd
from Transform.Validate_Calendar import ValidateCalendar as vc
from Extract.Write_Error import WriteErrors as we
from Extract.Calendar_Compare import CalendarCompare as cc

from Load.Load_Future_Ind import LoadFutureInd as lf

'''
#Get Clients Calendar
calendar_object = lc(st.FILE_NAME,st.SKIP_ROW_COUNT,st.TAB,st.DATA_ONLY_FLAG)

#Get Calendar Data
calendar = calendar_object.get_excel_data()
'''

#Get Clients Calendar via Database
calendar_object = lcd()

#Star Error List
error_list_object = we()

#Get All Rows From Database Data
get_all_calendar_rows = calendar_object.get_database_calendar()

# Get All Future Dated Event and Plan Year Dates Data
future_dates = lf().get_future_ind() #Read File
future_dates['YEAR_BEGIN_DATE'] = pd.to_datetime(future_dates['YEAR_BEGIN_DATE']
                                       , format='%d-%b-%y', errors='coerce')

future_dates['YEAR_END_DATE'] = pd.to_datetime(future_dates['YEAR_END_DATE']
                                       , format='%d-%b-%y', errors='coerce')



#Cyce through each calendar found in the databse data and evaluate
for cal_id in calendar_object.get_list_of_calendars():

    #Get Current Calendar Values
    current_calendar = get_all_calendar_rows.loc[get_all_calendar_rows['PAY_GROUP_ID'] == cal_id].reset_index()

    client_id = current_calendar['COMPANY_ID'][0]

    #Determine Future Dated Indicator
    try:
        future_dates_ind = str(
            future_dates.loc[future_dates['COMPANY_ID'] == client_id]['OG_FUTURE_DATED_EVENTS_IND'].values[0])
    except:
        future_dates_ind = 'N'

    #Determine Plan Year Beg Date and End Date
    try:
        plan_year_begin_date = future_dates.loc[future_dates['COMPANY_ID'] == client_id]['YEAR_BEGIN_DATE'].values[0]

        plan_year_end_date = future_dates.loc[future_dates['COMPANY_ID'] == client_id]['YEAR_END_DATE'].values[0]

    except:

        plan_year_begin_date = pd.to_datetime('2023-01-01')

        plan_year_end_date = pd.to_datetime('2023-12-31')


    #Send Calendar for Vaildation
    validate_object = vc(current_calendar, cal_id,client_id,future_dates_ind,plan_year_begin_date,plan_year_end_date)

    #Append any found errors to error list
    error_list_object.append_error_list(validate_object.errors)

#Gather Non Validated Data
non_validation_data_object = lvd()
error_list_object.append_error_list(non_validation_data_object.getOEDatesMatch())

#Write Error File
#Using the Error List from the Loop above, we're exporting thos values as a CSV
error_list_object.writeErrorFiles()

#Print Error Statistics
error_list_object.print_error_stats(calendar_object)

#Turn Notification List Into String
notification_emails = pd.read_csv(st.NOTIFICATION_FILE)
notification_emails = list(notification_emails['Email'].unique())
delim = '; '
notification_emails = delim.join(notification_emails)

#Copy Calendar for Historic Reference
cc_object = cc(get_all_calendar_rows)

#Get Calendar Changes and Add as a Sheet on the Excel Results
calendar_compare_results = cc.getCompareResults(cc_object)
error_list_object.writeExcelErrorFile(calendar_compare_results)

#Calc Days On Error List
#error_list_object.updateDaysOnErrorList()

if st.TEST_ENVIROMENT != 3:
    #GenerateIndividual Emails
    error_list_object.indidividualEmails()

    #Generate Email
    error_list_object.generateEmail('Database Payroll Calendar Check - Week {}'.format(str(dt.today().strftime('%U')))
                                    ,notification_emails,calendar_object)



