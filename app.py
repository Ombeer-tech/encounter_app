import streamlit as st
import pandas as pd
from processor import process_encounter_data

# --- Page configuration ---
st.set_page_config(
    page_title="Encounter Data Processor",
    layout="wide"
)

st.title("🩺 Patient Encounter Data Processor")

# --- File upload ---
uploaded_file = st.file_uploader(
    "Upload your raw CSV or Excel file",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:

    # Read uploaded file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully")

    # Process data
    with st.spinner("Processing data..."):
        result_df = process_encounter_data(df)

    # --- Show patient count ---
    total_patients = result_df["Patient Number"].nunique()
    st.info(f"👥 Total Patients: {total_patients}")

    # --- Show table ---
    st.subheader("📊 Processed Encounter Data")
    st.dataframe(result_df, use_container_width=True)

    # --- Download CSV ---
    csv = result_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="⬇️ Download Result CSV",
        data=csv,
        file_name="filtered_encounter_data.csv",
        mime="text/csv"
    )
