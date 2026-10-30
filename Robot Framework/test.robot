*** Settings ***
Library           SeleniumLibrary
Library           ${CURDIR}${/}helper.py
Suite Teardown    Close All Browsers

*** Variables ***
${REPORT_FILE}       ${CURDIR}${/}logs${/}report.html
${PARQUET_FOLDER}    ${CURDIR}${/}data${/}facility_type_avg_time_spent_per_visit_date
${FILTER_DATE}       2026-09-28
${TABLE_LOCATOR}     css:.plotly-graph-div g.table

*** Test Cases ***
Report Table Matches Filtered Parquet Data
	${report_url}=        Get Local File Url    ${REPORT_FILE}
	Open Browser          ${report_url}    chrome
	Wait Until Element Is Visible    ${TABLE_LOCATOR}    timeout=20s
	${table_element}=     Get WebElement    ${TABLE_LOCATOR}
	${report_data}=       Read Html Table    ${table_element}    ${FILTER_DATE}
	${parquet_data}=      Read Partitioned Parquet    ${PARQUET_FOLDER}    ${FILTER_DATE}
	${differences}=       Compare Dataframes    ${report_data}    ${parquet_data}
	Should Be Empty       ${differences}

*** Keywords ***
