**Usage Instructions
**
Upload Files:

Use the file upload widgets to upload your rules and claims Excel files
The application supports Excel (.xlsx, .xls) and CSV formats


Process Rules:

Click the "Process Rules" button to apply the rules to the claims data
The application will analyze the claims based on the rules provided


View Results:

The application will display a report showing claims that match the rules
Statistics about the detected cases will be shown


Download Report:

Click the "Download Report as Excel" button to download the results as an Excel file



Technical Details
This application uses:

Streamlit: For the web interface
Pandas: For data processing
XlsxWriter: For Excel file generation

The code is modular with separate components for:

File handling
Rule processing (distinguishing between record-level and dataset-level rules)
Report generation
Statistics calculation

For dataset-level rules, the application compares rows against each other based on the specified conditions. Record-level rules are applied to each row individually.
