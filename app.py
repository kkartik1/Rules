# app.py
import streamlit as st
import pandas as pd
import traceback
import time
from modules.file_handler import upload_files, convert_df_to_excel
from modules.rule_processor import apply_rules
from modules.report_generator import generate_report
from modules.stats_calculator import calculate_statistics

def init_session_state():
    """Initialize session state variables"""
    if 'processing_log' not in st.session_state:
        st.session_state.processing_log = []
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'report' not in st.session_state:
        st.session_state.report = None

def log_message(message, level="info"):
    """Add a message to the processing log"""
    timestamp = time.strftime("%H:%M:%S")
    st.session_state.processing_log.append((timestamp, level, message))

def display_logs():
    """Display the processing logs"""
    if st.session_state.processing_log:
        st.subheader("Processing Log")
        log_df = pd.DataFrame(st.session_state.processing_log, 
                            columns=["Time", "Level", "Message"])
        
        # Apply color coding based on log level
        def color_log_level(val):
            if val == "error":
                return "background-color: #ffcccc"
            elif val == "warning":
                return "background-color: #ffffcc"
            else:
                return ""
        
        st.dataframe(log_df.style.applymap(color_log_level, subset=["Level"]))
        
        if st.button("Clear Log"):
            st.session_state.processing_log = []
            st.experimental_rerun()

def main():
    # Set page config
    st.set_page_config(
        page_title="Healthcare Fraud Detection",
        page_icon="🔍",
        layout="wide"
    )
    
    # Initialize session state
    init_session_state()
    
    # Upload files
    rules_df, claims_df = upload_files()
    
    # Continue only if both files are uploaded
    if rules_df is not None and claims_df is not None:
        # Display data preview
        with st.expander("Preview Data"):
            st.subheader("Rules Preview")
            st.dataframe(rules_df)
            
            st.subheader("Claims Preview")
            st.dataframe(claims_df)
        
        # Process button
        col1, col2 = st.columns([1, 3])
        with col1:
            process_button = st.button("Process Rules")
        
        if process_button:
            try:
                log_message("Starting rule processing")
                
                with st.spinner("Processing rules and analyzing claims..."):
                    # Apply rules to claims
                    log_message(f"Processing {len(rules_df)} rules against {len(claims_df)} claims")
                    
                    # Apply rules
                    start_time = time.time()
                    results_df = apply_rules(rules_df, claims_df)
                    end_time = time.time()
                    
                    # Log processing time
                    log_message(f"Rule processing completed in {end_time - start_time:.2f} seconds")
                    
                    # Store results in session state for later use
                    st.session_state.results = results_df
                    
                    if results_df.empty:
                        log_message("No violations found for the applied rules.", "warning")
                        st.warning("No violations found for the applied rules.")
                    else:
                        log_message(f"Found {len(results_df)} potential violations across {results_df['rule_id'].nunique()} rules")
                        
                        # Generate report
                        report_df = generate_report(results_df)
                        
                        # Store report in session state
                        if not report_df.empty:
                            st.session_state.report = report_df
                            
                            # Calculate statistics
                            calculate_statistics(results_df)
                            
                            # Download button for report
                            excel_data = convert_df_to_excel(report_df)
                            if excel_data:
                                st.download_button(
                                    label="Download Report as Excel",
                                    data=excel_data,
                                    file_name="fraud_detection_report.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
            except Exception as e:
                error_msg = str(e)
                log_message(f"Error during processing: {error_msg}", "error")
                st.error(f"An error occurred while processing: {error_msg}")
                st.error(traceback.format_exc())
    
    # Display logs at the bottom
    display_logs()

if __name__ == "__main__":
    main()
