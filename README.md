# Payroll Calendar Validation Tool

**One-line summary:**  
Python tool that scans and validates payroll calendars across 170 clients, reducing critical calendar errors from 71% to 1%.

---

## 📌 Problem Statement

In 2019, 71% of all reported payroll issues were tied to inaccurate or misaligned payroll calendars. These errors led to missed payments, client escalations, and time-consuming manual fixes across multiple departments.

---

## ✅ Solution Overview

This custom-built Python tool was developed to proactively validate payroll calendars before errors could occur. Each week, it scans over **500 calendars** (more than **20,000 rows**) across **170 clients**, performing the following actions:

- Checks for calendar inconsistencies, missing entries and unusual date patterns
- Generates error logs, as well as CSV and Excel reports
- Creates backups of all payroll calendars
- Sends personalized alert emails to aligned team members
- Feeds dashboard reports for at-a-glance tracking

The tool runs weekly to align with payroll cycles and ensure early detection of potential issues.

---

## 🚀 Key Outcomes

- 📉 **Reduced calendar-related errors from 71% (2019) to just 1% (2025)**
- ⏱ Saved hours of manual QA and back-and-forth communication
- 🔒 Improved data integrity and audit readiness
- 📊 Increased client trust and service delivery consistency

---

## 🛠 Technologies Used

- **Python**: pandas, numpy, os, smtplib, openpyxl, datetime, logging, pywin32  
- **SQL**: Oracle  
- **Other Tools**: Outlook (for emails), Excel, Power BI

---

## ▶️ How to Run

> ⚠️ This project contains sensitive client logic and is **not run publicly**. However, you can clone the structure and modify the logic with sample data.

### 🛠️ How to Run

1. Navigate to `Settings.py` under the **Locators** section.

2. Update the `DESIRED_PLAN_YEAR` to reflect the year you’re evaluating. For example, if you're currently working on Open Enrollment, you're most likely evaluating calendars for the **upcoming plan year**, not the current one.

3. Determine which **region** you're testing in. There are four available regions:

   - `TEST`
   - `AUTHORING`
   - `SIMULATION`
   - `DELIVERY`

4. Update the `TEST_ENVIRONMENT` variable to reflect the region you are evaluating:

   - 0 = AUTHORING  
   - 1 = SIMULATION  
   - 2 = DELIVERY  
   - 3 = TEST

5. Run the following three queries and save the output as individual CSV files in the `Data/Pay Calendars` folder.  
   All queries can be found in the `Query` directory.

   > ⚠️ **Warning**: Be sure that the `PLAN_YEAR` in all three queries has been updated to match the desired plan year.

   > **Note**: `TEST_ENVIRONMENT` and `DESIRED_PLAN_YEAR` are variable placeholders and should match the values set in `settings.py`.  
   > Do not include brackets in the file names.

   - **Query #1**: `Get_Calendar.sql`  
     Save as → `DESIRED_PLAN_YEAR_TEST_ENVIRONMENT_CALENDAR.csv`

   - **Query #2**: `Get_Future_Indicator.sql`  
     Save as → `DESIRED_PLAN_YEAR_TEST_ENVIRONMENT_FUTURE_INDICATORS.csv`

   - **Query #3**: `Get_OE_Run_Date_First_Pay_Period_Match.sql`  
     Save as → `DESIRED_PLAN_YEAR_OE_MATCH_TEST_ENVIRONMENT.csv`

   > **Example**: If you're evaluating the `TEST` environment for the 2026 plan year,  
   > `Get_Calendar.sql` should be saved as `2026_TEST_CALENDAR.csv`
   
6. Execute the script.

   ⚠️ **Note**: Warning email logic has been disabled for this version of the tool.
