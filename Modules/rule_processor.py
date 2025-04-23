# modules/rule_processor.py
import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

def parse_condition_for_record_rule(rule_condition):
    """
    Parse a rule condition string into a pandas query string for record level rules
    """
    # Replace equals with double equals for comparison
    parsed = re.sub(r'(?<![<>=!])=(?!=)', '==', rule_condition)
    
    # Handle quoted strings properly - don't change equality operators inside quotes
    def replace_quoted_equals(match):
        inside = match.group(1)
        # Don't replace equality operators inside quotes
        return f'"{inside}"'
    
    # First, temporarily remove content in quotes
    quoted_parts = {}
    i = 0
    
    def replace_quotes(match):
        nonlocal i
        placeholder = f"__QUOTE_{i}__"
        quoted_parts[placeholder] = match.group(0)
        i += 1
        return placeholder
    
    parsed = re.sub(r'"([^"]*)"', replace_quotes, parsed)
    
    # Now put the quoted parts back in
    for placeholder, original in quoted_parts.items():
        parsed = parsed.replace(placeholder, original)
    
    return parsed

def apply_record_level_rule(claims_df, rule_id, rule_desc, rule_condition):
    """
    Apply a rule that operates on individual records
    Uses pandas query functionality for flexible rule application
    """
    try:
        # Make a working copy of claims dataframe
        df = claims_df.copy()
        
        # Parse the rule condition into a pandas query
        query_str = parse_condition_for_record_rule(rule_condition)
        print("query:", query_str)
        # Apply the query
        result_df = df.query(query_str)
        
        if not result_df.empty:
            # Add rule information to the result
            result_df['rule_id'] = rule_id
            result_df['rule_desc'] = rule_desc
            return result_df
        else:
            return pd.DataFrame()  # Return empty DataFrame if no claims match
    
    except Exception as e:
        print(f"Error applying record-level rule {rule_id}: {e}")
        print(f"Rule condition: {rule_condition}")
        print(f"Processed query: {query_str if 'query_str' in locals() else 'Query string not generated'}")
        return pd.DataFrame()  # Return empty DataFrame on error

def extract_self_comparisons(rule_condition):
    """
    Extract field self-comparisons (field = field) from a rule condition
    """
    matches = re.finditer(r'(\w+)\s*=\s*\1', rule_condition)
    return [match.group(1) for match in matches]

def extract_value_comparisons(rule_condition):
    """
    Extract field value comparisons (field op value) from a rule condition
    """
    # For numeric comparisons
    numeric_matches = re.finditer(r'(\w+)\s*([<>=!]+)\s*(\d+(?:\.\d+)?)', rule_condition)
    numeric_comparisons = [(m.group(1), m.group(2), float(m.group(3))) for m in numeric_matches]
    
    # For string comparisons
    string_matches = re.finditer(r'(\w+)\s*([<>=!]+)\s*"([^"]*)"', rule_condition)
    string_comparisons = [(m.group(1), m.group(2), m.group(3)) for m in string_matches]
    
    return numeric_comparisons + string_comparisons

def extract_field_differences(rule_condition):
    """
    Extract field difference comparisons (field1 - field2 op value) from a rule condition
    """
    matches = re.finditer(r'(\w+)\s*-\s*(\w+)\s*([<>=!]+)\s*(\d+(?:\.\d+)?)', rule_condition)
    return [(m.group(1), m.group(2), m.group(3), float(m.group(4))) for m in matches]

def apply_dataset_level_rule(claims_df, rule_id, rule_desc, rule_condition):
    """
    Apply a rule that operates on the entire dataset, comparing multiple rows
    """
    try:
        # Parse the different types of comparisons in the rule
        self_comparisons = extract_self_comparisons(rule_condition)
        print(self_comparisons)
        value_comparisons = extract_value_comparisons(rule_condition)
        print(value_comparisons)
        field_differences = extract_field_differences(rule_condition)
        print(field_differences)
        # First apply any value-based filters to reduce the dataset
        filtered_df = claims_df.copy()
        
        for field, op, value in value_comparisons:
            if field in filtered_df.columns:
                if op == '==':
                    filtered_df = filtered_df[filtered_df[field] == value]
                elif op == '!=':
                    filtered_df = filtered_df[filtered_df[field] != value]
                elif op == '>':
                    filtered_df = filtered_df[filtered_df[field] > value]
                elif op == '>=':
                    filtered_df = filtered_df[filtered_df[field] >= value]
                elif op == '<':
                    filtered_df = filtered_df[filtered_df[field] < value]
                elif op == '<=':
                    filtered_df = filtered_df[filtered_df[field] <= value]
        
        if filtered_df.empty:
            return pd.DataFrame()
        
        # For rules that involve self-comparisons across rows
        if self_comparisons:
            # If we have field self-comparisons, we're looking for duplicates/similarities
            if all(field in filtered_df.columns for field in self_comparisons):
                # Look for duplicate values in the specified fields
                duplicate_mask = filtered_df.duplicated(subset=self_comparisons, keep=False)
                potential_matches = filtered_df[duplicate_mask].copy()
                
                if potential_matches.empty:
                    return pd.DataFrame()
                
                # Now for each group of matches, check field differences if any exist
                if field_differences:
                    results = []
                    
                    # Group by the self-comparison fields
                    grouped = potential_matches.groupby(self_comparisons)
                    
                    for _, group in grouped:
                        # For each group, compare each pair of rows
                        for i, row1 in group.iterrows():
                            for j, row2 in group.iterrows():
                                if i >= j:  # Skip comparing a row to itself or duplicate checks
                                    continue
                                
                                # Check if the field differences meet the criteria
                                differences_met = True
                                
                                for field1, field2, op, threshold in field_differences:
                                    if field1 in row1.index and field2 in row2.index:
                                        # Handle date differences
                                        if 'date' in field1.lower() or 'from' in field1.lower() or 'to' in field1.lower():
                                            try:
                                                date1 = pd.to_datetime(row1[field1])
                                                date2 = pd.to_datetime(row2[field2])
                                                diff = abs((date1 - date2).days)
                                            except:
                                                diff = float('inf')  # Set to infinity if conversion fails
                                        else:
                                            # Handle numeric differences
                                            try:
                                                diff = abs(float(row1[field1]) - float(row2[field2]))
                                            except:
                                                diff = float('inf')  # Set to infinity if conversion fails
                                        
                                        # Apply the comparison operator
                                        if op == '<' and not (diff < threshold):
                                            differences_met = False
                                            break
                                        elif op == '<=' and not (diff <= threshold):
                                            differences_met = False
                                            break
                                        elif op == '>' and not (diff > threshold):
                                            differences_met = False
                                            break
                                        elif op == '>=' and not (diff >= threshold):
                                            differences_met = False
                                            break
                                        elif op == '==' and not (diff == threshold):
                                            differences_met = False
                                            break
                                        elif op == '!=' and not (diff != threshold):
                                            differences_met = False
                                            break
                                
                                if differences_met:
                                    results.append(row1)
                                    results.append(row2)
                    
                    if results:
                        result_df = pd.DataFrame(results).drop_duplicates()
                        result_df['rule_id'] = rule_id
                        result_df['rule_desc'] = rule_desc
                        return result_df
                else:
                    # If no field differences to check, just return the duplicates
                    potential_matches['rule_id'] = rule_id
                    potential_matches['rule_desc'] = rule_desc
                    return potential_matches
        
        # If we get here, the rule didn't match our recognized patterns
        print(f"Warning: Dataset-level rule {rule_id} structure not recognized: {rule_condition}")
        return pd.DataFrame()
    
    except Exception as e:
        print(f"Error applying dataset-level rule {rule_id}: {e}")
        print(f"Rule condition: {rule_condition}")
        return pd.DataFrame()

def apply_rules(rules_df, claims_df):
    """
    Apply all rules to the claims data sequentially
    Each claim can only be identified by one rule - the first rule that matches it
    """
    all_results = []
    remaining_claims = claims_df.copy()
    
    # Sort rules by Rule_ID to ensure we process in the correct sequence
    # Assuming Rule_ID can be converted to numeric for proper sorting
    rules_df = rules_df.sort_values(by='Rule_ID')
    
    # Process each rule sequentially
    for _, rule in rules_df.iterrows():
        rule_id = rule['Rule_ID']
        rule_desc = rule['Rule_Desc']
        rule_level = rule['Level']
        rule_condition = rule['Rule_Allegation']
        
        print(f"Processing rule {rule_id}: {rule_desc}")
        print(f"Remaining claims for consideration: {len(remaining_claims)}")
        
        # Skip processing if no claims remain
        if remaining_claims.empty:
            print("No claims left to process. Stopping rule application.")
            break
        
        if rule_level == 'Record':
            result = apply_record_level_rule(remaining_claims, rule_id, rule_desc, rule_condition)
        elif rule_level == 'DataSet':
            result = apply_dataset_level_rule(remaining_claims, rule_id, rule_desc, rule_condition)
        else:
            print(f"Unknown rule level: {rule_level}")
            continue
            
        if not result.empty:
            print(f"Rule {rule_id} found {len(result)} matches")
            all_results.append(result)
            
            # Remove identified claims from the pool of remaining claims
            # First, create a key to identify unique claims
            # We'll use all columns except those added by the rule application
            key_columns = [col for col in result.columns if col not in ['rule_id', 'rule_desc']]
            
            # Get the identified claim IDs
            # We need a reliable way to identify unique claims - using all columns as a composite key
            identified_claims = result[key_columns].copy()
            
            # Create a merge key for efficient matching
            identified_claims['__merge_key__'] = identified_claims.apply(lambda row: hash(tuple(row)), axis=1)
            remaining_claims['__merge_key__'] = remaining_claims.apply(lambda row: hash(tuple(row)), axis=1)
            
            # Remove claims that were identified by this rule
            remaining_claims = remaining_claims[~remaining_claims['__merge_key__'].isin(identified_claims['__merge_key__'])]
            
            # Remove the temporary merge key
            remaining_claims = remaining_claims.drop(columns=['__merge_key__'])
        else:
            print(f"Rule {rule_id} found no matches")
    
    if all_results:
        # Combine all results into a single DataFrame
        results_df = pd.concat(all_results, ignore_index=True)
        return results_df
    else:
        # Return empty DataFrame with appropriate columns if no results
        empty_df = pd.DataFrame(columns=list(claims_df.columns) + ['rule_id', 'rule_desc'])
        return empty_df
