# modules/report_generator.py
import pandas as pd
import streamlit as st

def generate_report(results_df):
    """
    Generate a report from the results DataFrame
    """
    if results_df.empty:
        st.warning("No fraud or discrepancy cases detected with the applied rules.")
        return pd.DataFrame()
    
    # Select only the relevant columns for the report
    report_columns = ['claim_id', 'rule_id', 'rule_desc', 'member_id', 'provider_npi']
    
    # Add additional columns based on what's available in the results
    optional_columns = [
        'procedure_cd', 'diag_cd', 'paid_amount', 'claim_service_from', 'claim_service_to',
        'member_gender', 'member_age', 'member_state'
    ]
    
    for col in optional_columns:
        if col in results_df.columns:
            report_columns.append(col)
    
    # Create the report dataframe
    report_df = results_df[report_columns].copy()
    
    # Remove duplicates based on claim_id and rule_id
    report_df = report_df.drop_duplicates(subset=['claim_id', 'rule_id'])
    
    # Sort by rule_id and claim_id for better readability
    report_df = report_df.sort_values(by=['rule_id', 'claim_id'])
    
    # Display the report
    st.subheader("Fraud/Discrepancy Detection Report")
    
    # Create tabs for different views of the results
    tab1, tab2 = st.tabs(["All Results", "Results by Rule"])
    
    with tab1:
        st.dataframe(report_df, use_container_width=True)
        
    with tab2:
        # Group results by rule
        rule_ids = report_df['rule_id'].unique()
        
        for rule_id in rule_ids:
            rule_results = report_df[report_df['rule_id'] == rule_id]
            rule_desc = rule_results['rule_desc'].iloc[0]
            
            st.subheader(f"Rule {rule_id}: {rule_desc}")
            st.dataframe(rule_results.drop(columns=['rule_id', 'rule_desc']), use_container_width=True)
            st.text(f"Found {len(rule_results)} potential violations for this rule")
            st.divider()
    
    return report_df
