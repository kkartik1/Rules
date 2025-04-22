# modules/stats_calculator.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def calculate_statistics(results_df):
    """
    Calculate statistics from the results DataFrame
    """
    if results_df.empty:
        return
    
    st.subheader("Statistics")
    
    # Use columns layout for better organization
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_claims = len(results_df['claim_id'].unique())
        st.metric("Total Claims", total_claims)
        
        total_rules = len(results_df['rule_id'].unique())
        st.metric("Rules Triggered", total_rules)
    
    with col2:
        total_providers = len(results_df['provider_npi'].unique())
        st.metric("Total Providers", total_providers)
        
        if 'member_state' in results_df.columns:
            total_states = len(results_df['member_state'].unique())
            st.metric("Total States", total_states)
    
    with col3:
        total_members = len(results_df['member_id'].unique())
        st.metric("Total Members", total_members)
        
        if 'paid_amount' in results_df.columns:
            total_paid = results_df['paid_amount'].sum()
            st.metric("Total Paid Amount", f"${total_paid:.2f}")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["Rule Analysis", "Member Analysis", "Provider Analysis"])
    
    with tab1:
        # Rule breakdown
        st.subheader("Rule Breakdown")
        rule_counts = results_df.groupby(['rule_id', 'rule_desc']).size().reset_index(name='count')
        
        # Create a pie chart
        fig = px.pie(rule_counts, values='count', names='rule_desc', 
                    title='Distribution of Violations by Rule')
        st.plotly_chart(fig, use_container_width=True)
        
        # Display as table with better formatting
        st.dataframe(rule_counts, use_container_width=True)
    
    with tab2:
        # Member analysis
        st.subheader("Member Analysis")
        
        member_counts = results_df.groupby('member_id').size().reset_index(name='violation_count')
        member_counts = member_counts.sort_values('violation_count', ascending=False)
        
        if 'paid_amount' in results_df.columns:
            member_amounts = results_df.groupby('member_id')['paid_amount'].sum().reset_index()
            member_counts = member_counts.merge(member_amounts, on='member_id')
            
            # Show members with most violations and highest amounts
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Members with Most Violations")
                st.dataframe(member_counts.head(10), use_container_width=True)
            
            with col2:
                st.subheader("Members with Highest Paid Amounts")
                st.dataframe(member_counts.sort_values('paid_amount', ascending=False).head(10), use_container_width=True)
        else:
            st.subheader("Members with Most Violations")
            st.dataframe(member_counts.head(10), use_container_width=True)
    
    with tab3:
        # Provider analysis
        st.subheader("Provider Analysis")
        
        provider_counts = results_df.groupby('provider_npi').size().reset_index(name='violation_count')
        provider_counts = provider_counts.sort_values('violation_count', ascending=False)
        
        if 'paid_amount' in results_df.columns:
            provider_amounts = results_df.groupby('provider_npi')['paid_amount'].sum().reset_index()
            provider_counts = provider_counts.merge(provider_amounts, on='provider_npi')
            
            # Show providers with most violations and highest amounts
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Providers with Most Violations")
                st.dataframe(provider_counts.head(10), use_container_width=True)
            
            with col2:
                st.subheader("Providers with Highest Paid Amounts")
                st.dataframe(provider_counts.sort_values('paid_amount', ascending=False).head(10), use_container_width=True)
        else:
            st.subheader("Providers with Most Violations")
            st.dataframe(provider_counts.head(10), use_container_width=True)
