import pandas as pd
import numpy as np
import re
from datetime import datetime as dt
from Locators.Settings import Settings as st
from Extract.Calendar_Compare import CalendarCompare as cc

#import matplotlib.pyplot as plt


import logging

logging.basicConfig(filename=st.LOG_PATH + '\{}_{}.log'
                    .format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y')),
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w')

logger = logging.getLogger()

logger.setLevel(logging.DEBUG)

class WriteErrors:

    def __init__(self):

        #Empty Dataframe to hold errors that are found during validation
        self.error_list = pd.DataFrame(columns = ['Company ID','Company','Pay Group ID','Pay Period','Status','Error ID','Notes'],dtype=str)

        #Error Chart Name and Path
        self.error_chart_file = st.REPORT_PATH + '{}_{}_ERROR_CHART.png'.format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y'))

        #Error Report File Name and Path
        self.error_report_file = st.REPORT_PATH + '{}_{}_ERROR_LIST.csv'.format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y'))

        #Error Report Exception List and Path
        self.exception_list_file = st.REPORT_PATH + '{}_{}_EXCEPTION_LIST.csv'.format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y'))

    def append_error_list(self,new_errors):
        self.error_list = self.error_list.append(new_errors, ignore_index = True)

    def remove_exceptions(self):

        #This method will read the exceptions file and remove any error that has been deemed and exception

        #Getting exception data
        #Removing Company column and converting data to integers
        current_plan_year_exceptions = st.ERROR_EXCEPT_DATA.loc[st.ERROR_EXCEPT_DATA['Plan Year'] == st.DESIRED_PLAY_YEAR]
        current_plan_year_exceptions = current_plan_year_exceptions.drop(['Company'], axis=1)
        current_plan_year_exceptions[['Company ID','Pay Group ID','Plan Year','Error ID']] = current_plan_year_exceptions[['Company ID','Pay Group ID','Plan Year','Error ID']]

        #Getting Temp List of current Errors
        #Adding plan year and conveting data to integers
        temp_errors_list = self.error_list[['Company ID','Pay Group ID','Error ID']]
        temp_errors_list.insert(1, 'Plan Year', st.DESIRED_PLAY_YEAR, True)
        temp_errors_list[['Company ID','Pay Group ID','Plan Year','Error ID']] = temp_errors_list[['Company ID','Pay Group ID','Plan Year','Error ID']]

        #Errors from the exception file found in the current error log
        errors_in_index = temp_errors_list.merge(current_plan_year_exceptions, indicator=True, how='left').loc[lambda x: x['_merge'] == 'both']

        #Remove each excpetion from the current error log
        for index, row in errors_in_index.iterrows():
            self.error_list = self.error_list.drop(index=index)

        #Write Exclusion Report
        companies = self.error_list[['Company ID','Company']].drop_duplicates()
        companies['Company ID'] = companies['Company ID'].astype(int)

        #Being process of writing errors that were deemed exceptions
        #and removed from the final error list

        #Merge Company Names BACK before we write, its easier for the user to read
        #than an ID
        errors_in_index['Company ID'] = errors_in_index['Company ID'].astype(int)
        errors_in_index = errors_in_index.merge(companies, on='Company ID', how='left')
        errors_in_index = errors_in_index.drop(['_merge'], axis=1)

        #Get Error Messages
        errors_in_index = errors_in_index.merge(st.AVAL_ERRORS, on='Error ID', how='left')
        errors_in_index = errors_in_index.drop(['Error ID'], axis=1)

        #Rearrange Exclusion Report
        errors_in_index = errors_in_index[['Company ID','Company','Pay Group ID','Plan Year','Error Message']]

        #Writing Exclusion Report
        errors_in_index.to_csv(self.exception_list_file,index=False)

    def get_total_num_errors(self):

        #Removes Warnings from the list and returns # of errors
        errors_only = self.error_list.loc[self.error_list['Status'] == 'Error']

        #Returns nimber of errors, no warnings
        return len(errors_only.index)

    def get_errors_only_list(self):

        # Removes Warnings from the list and returns # of errors
        errors_only = self.error_list.loc[self.error_list['Status'] == 'Error']

        #returns list of erros, no warnings
        return errors_only

    def get_errors_only_list_count(self):

        # Gets list of errors only, removes warnings
        errors_only = self.get_errors_only_list()

        #returns count of errors, no warnings
        return errors_only['Notes'].value_counts().to_string()

    def print_error_stats(self,calendar_object):

        # Print Stats
        print('--------')
        print('Quick Stats \n')

        print('Calendars Evaluated: {}'.format(len(calendar_object.get_list_of_calendars())))
        print('Total Errors Found: {}\n'.format(self.get_total_num_errors()))

        print('--------')
        print('Most Common Errors \n')

        print(self.get_errors_only_list_count())

    def updateDaysOnErrorList(self):

        logging.info('--- Updating Date Error Added Log')

        #This Method will add Clients whom just triggered an error
        #and remove those whom previously trigger an error, but are no longer

        #Gahter Company IDs of all clients on Error Report
        clients_in_error_id = list(self.get_errors_only_list()['Company ID'].unique())

        #Cycle Through Client IDs and determine if they were previously Added to the
        #Date Added Log
        for client in clients_in_error_id:

            if st.DATE_ERROR_ADDED.loc[st.DATE_ERROR_ADDED['COMPANY_ID'] == client].empty:

                st.DATE_ERROR_ADDED.loc[len(st.DATE_ERROR_ADDED.index)] = [client,
                                                                           pd.to_datetime('today').strftime('%Y-%m-%d')
                                                                           ,np.nan]

                logging.info('{} Added as of {}'.format(client,pd.to_datetime('today').strftime('%Y-%m-%d')))

            else:
                pass
                logging.info('{} Has been skipped'.format(client))

        #Save New Date Added Log w/ Updates
        st.DATE_ERROR_ADDED.to_csv(st.DATE_ERROR_ADDED_FILE_NAME,index=None)
        logging.info('Date Error Added Log has been UPDATED!')


    def writeErrorFiles(self):

        #Remove Exceptions from list
        self.remove_exceptions()

        #Sort Error List
        self.error_list = self.error_list.sort_values(by=['Pay Group ID','Pay Period'])

        if len(self.error_list.index) == 0:
            self.error_list.loc[len(self.error_list.index)] = ['N/A', 'Passed'
                , 'No errors found']

        self.error_list.to_csv(st.REPORT_PATH + '{}_{}_Error_List.csv'
                               .format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y')),index=False)

        logging.info('----- Saving Error Report')
        logging.info('{}'.format(self.error_report_file))

    def indidividualEmails(self):

        logging.info('----- Creating Individual Emails')

        colleague_data = st.COLLEAGUE_TEAM_DATA
        colleague_data = colleague_data[['Client OneCode','CD Specialist','CD Manager','CD Project Manager'
            ,'Client Solution Consultant','Client Solution Sr Consultant']]

        temp_error_list = self.get_errors_only_list()

        clients_w_erorr = temp_error_list['Company ID'].unique()
        future_ind_data = pd.read_csv(st.FUTURE_IND_FILE)

        for company in clients_w_erorr:

            company_errors = temp_error_list.loc[temp_error_list['Company ID'] == company]

            #Company Info
            company_name = company_errors['Company'].head().values[0]
            company_one_code = future_ind_data.loc[future_ind_data['COMPANY_ID'] == company,'MERCER_ONECODE'].values[0]

            logging.info('Sending {} {} ...'.format(company,company_one_code))

            #Gather Colleaue Information
            #To and CC Emails

            try:
                client_colleague_data = colleague_data.loc[colleague_data['Client OneCode'] == company_one_code]

                cc_emails = '{};{};{};{};'.format(client_colleague_data['CD Specialist'].values[0]
                                               ,client_colleague_data['CD Manager'].values[0]
                                               ,client_colleague_data['CD Project Manager'].values[0]
                                               ,client_colleague_data['Client Solution Sr Consultant'].values[0])

                to_emails = '{};'.format(client_colleague_data['Client Solution Consultant'].values[0])
            except:
                cc_emails = ''
                to_emails = 'tina.dillon@mercer.com'

            import win32com.client as win32

            outlook = win32.Dispatch('outlook.application')
            mail = outlook.CreateItem(0)
            mail.To = to_emails
            mail.CC = cc_emails
            mail.Subject = '{} - {} Payroll Calendar Errors - Attention Required!'.format(company_name
                                                                                          ,st.DESIRED_PLAY_YEAR)
#
            body_test = '''<style>

                            body,p{
                              font-size: 14.5px;
                              font-family:calibri;
                              }

                            h3{
                                font-family:calibri
                            }

                            table, td, th {
                                 border: 1px solid black;
                                 text-align: left;
                                 border-collapse: collapse;
                                 padding: 5px;
                              }

                            </style>'''

            body_test+='''
            Good Morning,<br /><br />
                
                The client has been identified as having errors within the current configuration of their payroll calendar(s).
            Action to correct these items should occur as soon as possible, thus to not cause any issues with the client's
            future payroll files.
            
            <br /><br />
            
            <i>Discovered Errors</i><br /><br />
            '''

            body_test += '''<table>
                              <tr>
                                <th>Pay Group</th>
                                <th>Pay Period</th>
                                <th>Error</th>
                              </tr>
                            '''

            for index, row in company_errors.iterrows():
                body_test += '''<tr>
                                    <td>{}</td>
                                    <td>{}</td>
                                    <td>{}</td>
                                  </tr>
                                '''.format(row['Pay Group ID'], row['Pay Period'], row['Notes'])

            body_test += '''</table>'''

            mail.HtmlBody = body_test

            mail.Display(True)

            logging.info('Email Sent!')


    def generateEmail(self,subject,recipient,calendar_object):

        logging.info('----- Creating Email')

        import win32com.client as win32

        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)
        mail.To = recipient
        mail.Subject = subject
        mail.Attachments.Add(st.REPORT_PATH + '{}_{}_Error_List.xlsx'
                               .format(st.TEST_CAL,pd.to_datetime('today').strftime('%m%d%Y')))

        body_test = '''<style>

                        body,p{
                          font-size: 14.5px;
                          font-family:calibri;
                          }

                        h3{
                            font-family:calibri
                        }

                        table, td, th {
                             border: 1px solid black;
                             text-align: left;
                             border-collapse: collapse;
                             padding: 5px;
                          }

                        </style>'''

        body_test += '<h3>Quick Stats</h3>'

        body_test += 'Calendars Evaluated: {}<br />'.format(len(calendar_object.get_list_of_calendars()))

        body_test += 'Total Errors Found: {}'.format(self.get_total_num_errors())

        #If NO errors are found then the error stats part of the email will not display
        #This part of the email contains:
        #1) Pie Chart
        #2) List of Companies w/ Errors
        #3)Most Common Errors

        if self.get_total_num_errors() > 0:

            body_test += '<h3>Most Common Errors</h3>'

            errors_email = self.get_errors_only_list_count()

            error_message_text_list = []
            error_message_count_list = []

            for line in errors_email.split('\n'):

                #Not Used Yet
                erorr_count_list = line.rsplit(' ', 1)

                error_message_text = erorr_count_list[0].rstrip()
                error_message_text_list.append(error_message_text)

                error_message_count = erorr_count_list[1].rstrip()
                error_message_count_list.append(error_message_count)

                body_test += '{}<br />'.format(line)

            clients_in_error = list(self.get_errors_only_list()['Company'].unique())

            body_test += '<h3>Companies With Errors</h3>'

            for company in clients_in_error:
                body_test += '{}<br />'.format(company)

            #Create Pie Chart of Errors
            #If no errros are found, then Chart w/ not create nor display

            #self.createErrorsChart(error_message_text_list,error_message_count_list)

            body_test += '<br />'

            #Create Attachment in order to insert image
            #Will Attached Chart Generated Today
            #attachment = mail.Attachments.Add(self.error_chart_file)
            #attachment.PropertyAccessor.SetProperty('http://schemas.microsoft.com/mapi/proptag/0x3712001F', 'MyId1')

            #Add Chart Image To Email
            body_test += '<img src=\'cid:MyId1\' alt=\'Errors\' width=\'600\' height=\'600\'>'

        mail.HtmlBody = body_test

        mail.Display(True)

    def createErrorsChart(self,labels,counts):

        y = counts
        mylabels = labels

       # plt.pie(y, labels=counts)
        #plt.legend(title='Errors: ',loc='upper right',bbox_to_anchor=(1.1, 1.05),labels=mylabels,fontsize='xx-small')
        #plt.gcf().set_size_inches(8, 8)

        #Save Created Chart
        #plt.savefig(self.error_chart_file, bbox_inches='tight')

        logging.info('----- Saving Error Chart')
        logging.info('{}'.format(self.error_chart_file))

    def writeExcelErrorFile(self,calendar_compae_results):

        #Method Generates the excel spreadsheet that will be delivered.
        #contains all data involved w/ the project
        #Switched from CSV to XLXS on 5/22/2023

        logging.info('----- Writing Excel File')

        with pd.ExcelWriter(st.REPORT_PATH + '{}_{}_Error_List.xlsx'.format(st.TEST_CAL,pd.to_datetime('today')
                .strftime('%m%d%Y'))) as writer:

            #Error List Tab
            self.error_list.to_excel(writer, sheet_name='Calendar Errors',index=None)

            #Calendar Compare Tab
            calendar_compae_results.to_excel(writer, sheet_name='Calendar Changes',index=None)


