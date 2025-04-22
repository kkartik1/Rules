# modules/file_handler.py
import pandas as pd
import streamlit as st
import io
import traceback

def upload_files():
    """
    Provide UI for uploading rules and claims files and return the DataFrames
    """
    st.title("Healthcare Claims Fraud Detection")
    
    st.subheader("Upload Files")
    
    # Upload rules file
    rules_file = st.file_uploader("Upload Rules Excel File", type=["xlsx", "xls", "csv"])
    
    # Upload claims file
    claims_file = st.file_uploader("Upload Claims Excel File", type=["xlsx", "xls", "csv"])
    
    rules_df = None
    claims_df = None
    
    if rules_file is not None:
        try:
            if rules_file.name.endswith('.csv'):
                rules_df = pd.read_csv(rules_file)
            else:
                rules_df = pd.read_excel(rules_file)
                
            # Validate rules dataframe structure
            required_columns = ['Rule_ID', 'Rule_Desc', 'Level', 'Rule_Allegation']
            missing_columns = [col for col in required_columns if col not in rules_df.columns]
            
            if missing_columns:
                st.error(f"Rules file is missing required columns: {', '.join(missing_columns)}")
                rules_df = None
            else:
                st.success(f"Rules file uploaded successfully with {len(rules_df)} rules")
                
                # Show info about rules
                st.info(f"Rule types: {rules_df['Level'].value_counts().to_dict()}")
        except Exception as e:
            st.error(f"Error reading rules file: {e}")
            st.error(traceback.format_exc())
    
    if claims_file is not None:
        try:
            if claims_file.name.endswith('.csv'):
                claims_df = pd.read_csv(claims_file)
            else:
                claims_df = pd.read_excel(claims_file)
                
            claims_df['procedure_cd'] = claims_df['procedure_cd'].astype(str)
            
            # Convert date columns to datetime
            date_columns = [col for col in claims_df.columns if 'date' in col.lower() or 'from' in col.lower() or 'to' in col.lower()]
            for col in date_columns:
                try:
                    claims_df[col] = pd.to_datetime(claims_df[col], errors='coerce')
                except:
                    # If conversion fails, continue with original format
                    pass
            
            st.success(f"Claims file uploaded successfully with {len(claims_df)} claims")
            
            # Display basic statistics
            st.info(f"Claims data spans {claims_df['claim_service_from'].min()} to {claims_df['claim_service_to'].max()}")
            st.info(f"Total members: {claims_df['member_id'].nunique()}, Total providers: {claims_df['provider_npi'].nunique()}")
            
        except Exception as e:
            st.error(f"Error reading claims file: {e}")
            st.error(traceback.format_exc())
    
    return rules_df, claims_df

def convert_df_to_excel(df):
    """
    Convert a dataframe to Excel bytes for download
    """
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Results', index=False)
        return output.getvalue()
    except Exception as e:
        st.error(f"Error creating Excel file: {e}")
        st.error(traceback.format_exc())
        return None
