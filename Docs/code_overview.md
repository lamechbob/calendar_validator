# 🧠 Code Overview – Payroll Calendar Validation Tool

This document breaks down the core logic and structure of the Payroll Calendar Validation Tool. It explains the key modules, functions, and technologies used to proactively detect and resolve payroll calendar-related errors.

---

## 🧱 Project Structure

The project is organized into modular scripts for ease of testing, updates, and scalability:

---

## 🔄 Main Script Flow (`main_script.py`)

The main script acts as the weekly scheduler and orchestrates the entire process. Here's a step-by-step overview:

1. **Load Data**
   - Requires three CSVs to be placed in the `Data/Pay Calendars` folder using the following naming convention:
     - `2024_TEST_CALENDAR.csv`
     - `2024_TEST_FUTURE_INDICATORS.csv`
     - `2024_OE_MATCH_TEST.csv`
   - These files are loaded into pandas DataFrames using the following modules:
     - `Load_Calendar.py` – loads calendar records  
     - `Load_Future_Ind.py` – loads future indicator flags  
     - `Load_Non_Validation_Data.py` – loads OE run and supporting info
   - These DataFrames serve as the input for all validation logic
   - Original files are overwritten weekly as part of the process


2. **Run Validations**
   - All validation logic is handled in `Validate_Calendar.py`
   - The script applies a series of business rules to the loaded DataFrames, including:
     - Missing or misaligned pay periods
     - Incorrect frequency labeling (e.g., weekly vs. biweekly)
     - Out-of-sequence dates (e.g., run dates not in order)
     - Cutoff date violations based on deduction rules and OE logic
     - Plan year alignment issues (e.g., dates outside the valid year)
     - Previously approved exceptions are filtered out before reporting
   - Validation results are compiled into an error list for reporting and alerts


3. **Generate Outputs**

- Validation results are exported in multiple formats using `Extract/Write_Error.py`:
  - **CSV file** – Structured for use in dashboards and summaries
  - **Excel file** – Analyst-friendly format for easy review and sorting

- A detailed **log file** is also created, capturing:
  - Full error context
  - Triggered rule logic
  - Timestamps and environment metadata
  - Stored in: `Data/Logs`

- A backup of all evaluated calendars is generated before final output using `Extract/Calendar_Compare.py`:
  - Stored in: `Data/Pay Calendars History`
  - Filenames include environment and timestamp
  - Used to detect unexpected calendar changes and support rollback

These outputs provide clear visibility across technical teams, analysts, and compliance reviewers.


4. **Send Alerts**

- Email notifications are coordinated through `Extract/Write_Error.py` and sent in two tiers:

### 📤 Tier 1: Full Team Summary
- Sent to the entire Client Solutions team
- Includes:
  - A high-level summary of all clients with errors
  - Attached CSV error log covering all validation results

### 📤 Tier 2: Targeted Client Alerts
- Individual emails are sent to each client team that recorded one or more errors
- Each email includes:
  - Client name
  - Total number of errors specific to that client
  - Attached CSV error log

- If a client has no errors, they do not receive an alert for that cycle
- Emails are delivered using either `pywin32` via outlook

This two-layer system ensures full team visibility while still holding each team directly accountable for their own calendar accuracy.

---

## 🧪 Key Functions

| File                              | Function                      | Purpose                                                            |
|-----------------------------------|-------------------------------|--------------------------------------------------------------------|
| `Transform/Validate_Calendar.py`  | `get_errors(self)`            | Applies all business rules to calendar data and returns error list |
| `Extract/Write_Error.py`          | `write_error_files(self)`     | Generates CSV and Excel error files and dispatches alert emails    |
| `Extract/Calendar_Compare.py`     | `copy_calendar(self)`         | Backs up the current week's calendar data for audit and rollback   |
| `Load/Load_Calendar.py`           | `load_file(self)`             | Loads the main calendar dataset into a DataFrame                   |
| `Load/Load_Future_Ind.py`         | `get_future_ind(self)`        | Loads future indicator flags used in cutoff logic                  |
| `Load/Load_Non_Validation_Data.py`| `get_oe_dates_match(self)`    | Loads OE run date and first pay period match data                  |
| `Locators/Settings.py`            | *(module)*                    | Stores environment flags, plan year, and file paths for execution  |

---

## 🧰 Libraries Used

- `pandas` – Data transformation, filtering, and rule-based validation  
- `numpy` – Date math, numerical logic, and cutoff calculations  
- `openpyxl` – Excel file generation and formatting  
- `pywin32` – Automates Outlook email dispatch (via COM interface)  
- `smtplib` – Sends email alerts using standard SMTP (fallback or alternative)  
- `datetime` – Pay period interval logic and date-based filtering  
- `os` – File management and folder operations  
- `logging` – Generates timestamped logs for each weekly run

---

## 📌 Notes

- All error logs, reports, and backups are archived with timestamps to support audit trails and rollback analysis.
- The tool is modular: each core function can be tested and maintained independently.
- Runtime configuration is controlled via `Locators/Settings.py`, which stores:
  - Environment type
  - Plan year
  - Folder paths
  - Validation toggles

- Contact information for client-specific email alerts is stored in:  
  - `Data/Helpers/Active client teams.csv`
  - This list is pulled dynamically during each run to determine which teams should receive client-specific alerts.

- Notification recipients for the full-team summary email are defined in:  
  - `Data/Helpers/notification_list.csv`

- Approved exceptions are stored in:  
  - `Data/Helpers/Error_Exceptions_List.csv`  
  Skipped errors are logged weekly in `[ENVIRONMENT]_MMDDYYYY_EXCEPTION_LIST.csv`.

- Input and output files follow this naming pattern:  
  `[PLAN_YEAR]_[ENVIRONMENT]_FILENAME.csv`  
  e.g., `2024_TEST_CALENDAR.csv`

- The tool is typically run once per week, after manual refresh of SQL data.

