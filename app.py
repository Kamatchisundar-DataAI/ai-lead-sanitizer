import pandas as pd
import streamlit as st
import io
import json
from openai import OpenAI

# -----------------------------------------------------------------------------
# 1. AI CLEANING ENGINE (VIA OPENROUTER SECRETS)
# -----------------------------------------------------------------------------

def get_openrouter_client():
    """Safely fetches the API key from your hidden secrets file."""
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    except KeyError:
        return None

def clean_batch(client, batch_records, columns_to_clean):
    """Sends a micro-chunk of records to Gemini for deep data sanitation and accent stripping."""
    
    prompt = f"""
    You are an advanced enterprise data sanitation engine. Clean and optimize the provided JSON array of records.
    
    CRITICAL FIELD-SPECIFIC HEURISTICS:
    1. TEXT & ENCODING REPAIRS (STRICT CLEANING):
       - Reconstruct missing letters marked by '?' based on language context (e.g., 'Tr?vis' -> 'Travis', 'A?ron' -> 'Aaron').
       - REMOVE OR CONVERT ALL SPECIAL INTERNATIONAL ACCENT MARKS AND NON-STANDARD CHARACTERS to their clean English equivalents (e.g., change 'Mariø' to 'Mario', change 'Ågale' to 'Agale', change 'RÉbecca' to 'Rebecca'). No foreign characters should remain in names.
       - Always format standard text strings, names, and job titles to beautiful Title Case.
    
    2. COMPANY NAMES & WEBSITES:
       - Trim trailing punctuation and strip corporate structures like 'LLC', 'Inc.' from Company fields.
       - Convert Websites to lowercase (e.g., 'bol.com', 'trofck.com').
    
    3. PHONE NUMBERS & ZIP CODES:
       - Keep these strictly as numerical digits. Strip out '?' completely. Do not add decimals.
    
    4. EMAILS:
       - Lowercase entirely, eliminate spacing gaps.
    
    OUTPUT FORMAT:
    You must output a single, raw JSON object with a root key named "data" containing the cleaned array. Do not include markdown wraps (```json).

    Data to process:
    {json.dumps(batch_records)}
    """
    
    response = client.chat.completions.create(
        model="google/gemini-2.5-flash", 
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3500,
        response_format={"type": "json_object"}
    )
    
    ai_output = response.choices[0].message.content.strip()
    
    if "```json" in ai_output:
        ai_output = ai_output.split("```json")[1].split("```")[0].strip()
    elif "```" in ai_output:
        ai_output = ai_output.split("```")[1].strip()

    parsed = json.loads(ai_output)
    return parsed.get("data", parsed)

def clean_all_fields_with_ai(df, columns_to_clean):
    """Coordinates batching loops and updates dataframes smoothly without type assignment crashes."""
    client = get_openrouter_client()
    if not client:
        st.error("❌ API Key Missing! Check your secrets configuration.")
        return df

    for col in columns_to_clean:
        if col in df.columns:
            df[col] = df[col].astype(object)

    all_records = []
    for idx, row in df.iterrows():
        record = {"id": int(idx)}
        for col in columns_to_clean:
            if col in df.columns:
                val = row[col]
                if isinstance(val, float) and val.is_integer():
                    record[col] = str(int(val))
                elif pd.isna(val) or str(val).lower() in ["none", "nan", ""]:
                    record[col] = ""
                else:
                    record[col] = str(val)
        all_records.append(record)

    batch_size = 15
    cleaned_records = []
    
    progress_bar = st.progress(0.0)
    status_text = st.empty()
    total_batches = (len(all_records) + batch_size - 1) // batch_size

    for i in range(0, len(all_records), batch_size):
        current_batch_idx = i // batch_size
        status_text.markdown(f"🧠 *AI is executing data transformations on batch segment {current_batch_idx + 1} of {total_batches}...*")
        
        chunk = all_records[i : i + batch_size]
        try:
            active_cols = [c for c in columns_to_clean if c in df.columns]
            cleaned_chunk = clean_batch(client, chunk, active_cols)
            cleaned_records.extend(cleaned_chunk)
        except Exception as e:
            st.error(f"Error compiling chunk starting at index {i}: {e}")
            cleaned_records.extend(chunk)
            
        progress_bar.progress(float(current_batch_idx + 1) / total_batches)

    status_text.success("✨ Comprehensive AI Data Optimization Complete!")

    for record in cleaned_records:
        if "id" not in record:
            continue
        row_id = int(record["id"])
        for col in columns_to_clean:
            if col in df.columns and col in record:
                val = str(record[col]).strip()
                df.at[row_id, col] = "" if val.lower() in ["none", "nan"] else val
                    
    return df

# -----------------------------------------------------------------------------
# 2. STREAMLIT USER INTERFACE & PERFECT CELL POSITION REPLACEMENT
# -----------------------------------------------------------------------------

st.set_page_config(page_title="Universal AI Lead Sanitizer", page_icon="🧼", layout="wide")

st.title("🧼 Universal AI-Powered Lead Sanitizer")
st.markdown("Upload your spreadsheets to automatically distribute combined text cells and run full AI pipeline formatting.")

uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='cp1252')
        else:
            df = pd.read_excel(uploaded_file)
            
        st.success("File uploaded successfully!")
        st.subheader("📋 Original Upload Preview")
        st.dataframe(df.head(10))
        
        all_columns = list(df.columns)
        
        # --- PRE-PROCESSING STEP: EXACT POSITIONAL DISTRIBUTION ---
        st.markdown("---")
        st.subheader("🔀 Word-by-Word Column Splitter")
        st.markdown("Select your master column containing multi-word text strings (like `bolo bol.com agale itok`) to cleanly split them into consecutive sheet locations:")
        
        split_col = st.selectbox("Select column to split (e.g., 'Company')", options=["-- Do Not Split Any Column --"] + all_columns)
        
        target_destinations = []
        if split_col != "-- Do Not Split Any Column --":
            split_idx = all_columns.index(split_col)
            # Find up to 4 sequential columns starting DIRECTLY from the selected column index
            target_destinations = all_columns[split_idx : split_idx + 4]
            
            st.info(f"📋 **Verified Mapping Rule:**")
            mapping_elements = []
            for idx, col_name in enumerate(target_destinations):
                mapping_elements.append(f"Word {idx+1} ➡️ `{col_name}`")
            st.markdown(" | ".join(mapping_elements))
            st.caption("ℹ️ Splitting only executes on rows where the text contains spaces and consecutive target columns are unpopulated.")

        # --- SELECTION CHECKBOX DASHBOARD ---
        st.markdown("---")
        st.subheader("🛠️ Select Fields to Clean with AI")
        st.markdown("Check the boxes for all columns you want cleaned, case-corrected, and polished by the AI:")
        
        columns_per_row = 4
        selected_columns = []
        
        for i in range(0, len(all_columns), columns_per_row):
            row_cols = all_columns[i:i+columns_per_row]
            st_cols = st.columns(len(row_cols))
            for idx, col_name in enumerate(row_cols):
                with st_cols[idx]:
                    if st.checkbox(f"Clean: **{col_name}**", key=f"chk_{col_name}", value=True):
                        selected_columns.append(col_name)
                        
        st.markdown("---")
        
        if st.button("🚀 Run Universal AI Correction Engine", type="primary"):
            cleaned_df = df.copy()
            
            # Standardize empty values into clean text elements
            for c in cleaned_df.columns:
                cleaned_df[c] = cleaned_df[c].fillna("").astype(str).str.strip()
            
            # 1. Execute precise index positioning for string values
            if split_col != "-- Do Not Split Any Column --" and target_destinations:
                with st.spinner("Executing cell level splitting transformations..."):
                    for idx, row in cleaned_df.iterrows():
                        source_val = row[split_col].strip()
                        
                        if " " in source_val:
                            # Split string cleanly into pieces by whitespace
                            parts = source_val.split()
                            
                            # Check if the surrounding destination columns are empty (except the source column itself)
                            dest_cols_to_check = target_destinations[1:]
                            is_empty_row = all(row[col] == "" or row[col].lower() in ["none", "nan"] for col in dest_cols_to_check if col in row)
                            
                            if is_empty_row:
                                # Word 1 -> Column 0 (Company)
                                # Word 2 -> Column 1 (Website)
                                # Word 3 -> Column 2 (First Name)
                                # Word 4 -> Column 3 (Last Name)
                                for part_idx, dest_col in enumerate(target_destinations):
                                    if part_idx < len(parts):
                                        cleaned_df.at[idx, dest_col] = parts[part_idx]
            
            # 2. Process everything through the AI Clean Engine
            if not selected_columns:
                st.warning("Please select at least one column checkbox to run AI correction processes.")
            else:
                cleaned_df = clean_all_fields_with_ai(cleaned_df, selected_columns)

                st.subheader("✨ AI Cleaned Data Preview")
                st.dataframe(cleaned_df.head(25))
                
                csv_buffer = io.StringIO()
                cleaned_df.to_csv(csv_buffer, index=False)
                csv_bytes = csv_buffer.getvalue().encode('utf-8')
                
                st.download_button(
                    label="📥 Download Complete Cleaned CSV",
                    data=csv_bytes,
                    file_name="universal_cleaned_leads.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
    except Exception as e:
        st.error(f"An error occurred while parsing the file: {e}")
else:
    st.info("Please upload a CSV or Excel data file to view available fields.")