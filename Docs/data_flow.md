# 🔁 Data Flow – Payroll Calendar Validation Tool

This section outlines the full data lifecycle of the Payroll Calendar Validation Tool, from ingestion to validation, alerting, and reporting.

---

## 1. 🏁 Data Ingestion

**Sources:**
- Live data pulls via SQL (Oracle)
- Optional uploads via Excel (Web Validator)

**Process:**
- SQL queries run weekly in designated environments (TEST, SIMULATION, AUTHORING, DELIVERY)
- Three datasets extracted:
  - Payroll Calendars
  - Future Indicator Flags
  - OE Run Date & Pay Period Alignment
- Saved as CSV files in `Data/Pay Calendars`, named by plan year and environment

---

## 2. 🔍 Validation Logic (Python)

The tool applies a comprehensive set of business rules to evaluate each calendar row. Checks include:

- **Cutoff Date Validations**
  - First pay period cutoff date is prior to mid-year (1/2 of the plan year)
  - Cutoff dates fall outside the designated plan year
  - Deduction cutoff date occurs before or after the run date
  - Final pay period has a cutoff date in the following plan year
  - Cutoff date exceeds the next pay period’s cutoff date

- **Pay Period Structure**
  - Invalid number of pay periods
  - Misaligned start or end dates between pay periods
  - Multiple pay periods run dates fall on the same day
  - Run dates are not in chronological order

- **Plan Year Alignment**
  - Calendar includes dates outside of the designated plan year
  - OE file run date is equal to or later than the first pay period run date

- **Configuration Flags**
  - `OG_FUTURE_DATED_EVENTS_IND` not set to `Y` when required
  - `EXC_STANDARD` not set to `'N'` on `PAYROLL_SCHEDULE`
  - `SUPP_CYCLE_NO` not equal to `0`

- **Data Format Validations**
  - Invalid or inconsistent date formatting across entries

**Tooling:**
- Python (`pandas`, `numpy`, `datetime`)
- Custom business logic implemented in `Validate_Calendar.py`

---

## 3. 💾 Backups & Archiving

- All evaluated calendars are backed up automatically during each run
- Files are saved in the `Data/Pay Calendars History` directory
- Each file is named with client ID, environment, and timestamp for traceability
- These backups support rollback, auditing, and detection of silent data changes

---

## 4. 📝 Logging & Output Files

Each run of the validator generates multiple outputs for error tracking, exception handling, and audit documentation.

### 📂 Error Reports

- Stored in: `Data/Pay Calendars History`
- Files include:
  - **Error Log (CSV)**: `[ENVIRONMENT]_MMDDYYYY_Error_List.csv`
  - **Error Log (XLSX)**: Excel version of the error log for readability  
    _(e.g., `TEST_06182025_Error_List.xlsx`)_

### ⚠️ Exception Process

- Some errors may be reviewed and approved for exclusion by the client or internal team.
- Once approved, the error is added to a master file located at:  
  - `Data/Helpers/Error_Exceptions_List.csv`
- During each weekly run, the tool checks this list and suppresses any matching records from the main error report.

**Weekly Exception Tracking:**
- Any errors that were skipped (based on the master exception list) are recorded in a run-specific file stored in `Data/Pay Calendars History`:
  - `[ENVIRONMENT]_MMDDYYYY_EXCEPTION_LIST.csv`  
  _(e.g., `TEST_06182025_EXCEPTION_LIST.csv`)_
- This file serves as a log of which records were intentionally ignored in that cycle.

This dual-file setup ensures transparency: errors are only excluded once formally approved, and all exclusions are tracked week-to-week.

### 📂 Background Logs

- Stored in: `Data/Logs`
- Includes:
  - Raw validation output
  - Internal diagnostic logs
  - Timestamped run metadata

All outputs are archived and time-stamped to support audit, rollback, and long-term trend analysis.

---

## 5. 📬 Alerting & Distribution

**Email Notifications:**
- Personalized emails sent to responsible team leads when errors are found
- Individual recipients are retrieved from a live SharePoint list maintained by the Client Solutions team.

- Includes:
  - Client name
  - Calendar ID
  - Pay Period
  - Error Message
  - Attached error log (CSV)

**Global Reports:**
- Full error summary sent to the broader client solutions team

---

## 6. 🌐 Web Validator (Streamlit)

- Launched in 2025 as a lightweight, browser-based front-end
- Allows users to upload Excel-based payroll calendars for on-demand validation
- Reuses the same business logic from `Validate_Calendar.py` to ensure consistency with backend automation
- Instantly returns validation results in a user-friendly format
- Hosted via AWS for secure and scalable access

---

## 📊 Dashboard Integration

- Weekly logs is ingested into a Power BI dashboard
- Dashboard tracks:
  - Weekly issue trends
  - Top recurring clients & issues

---

## 🧭 Text-Based Flow Diagram

```plaintext
[SQL Extracts / Excel Uploads] 
         ↓
[Python Validator (Backend or Web)]
         ↓
[Backups]   [Error Logs]
     ↓             ↓             
[Email Alerts]   →   [Power BI Dashboard]
