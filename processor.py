import pandas as pd


def process_encounter_data(df):
    """
    Converts raw form-response data into
    encounter-wise patient data with patient numbering
    """

    # --- 1. Safe datetime conversion ---
    df["response_created_at"] = pd.to_datetime(
        df["response_created_at"],
        errors="coerce",
        utc=True
    )

    # --- 2. Assign Patient Number ---
    # Each unique patient_user_id gets a sequential number
    patient_map = {
        pid: idx + 1
        for idx, pid in enumerate(df["patient_user_id"].dropna().unique())
    }

    # --- 3. Question mapping ---
    QUESTION_MAP = {
        "gender": ["What was your sex assigned at birth?"],
        "weight_primary": ["What is your current weight (lbs)?"],
        "weight_fallback": ["What is your weight in pounds?"],
        "bmi": ["Your BMI is"],
        "weight_change": ["How much weight have you lost in the past month?"],
        "dosage_change": ["Do you have any requests regarding your medication dosage?"],
        "other_meds_change": [
            "Are you taking any new prescription medications, over-the-counter medications, or supplements you have started taking since last month?"
        ],
        "height_feet": ["Height (Feet)"],
        "height_inches": ["Height (Inches)"],
        "height_text": ["What is your height in feet and inches?"]
    }

    rows = []

    # --- 4. Group by patient and encounter ---
    for (patient_id, encounter), grp in df.groupby(
        ["patient_user_id", "form_response_rank"]
    ):

        row = {
            "Patient Number": patient_map.get(patient_id),
            "Patient ID": patient_id,
            "Encounter": encounter,
            "Medication formulation": grp["product_bundle_name"].iloc[0],
            "Date on which form was filled": grp["response_created_at"].min()
        }

        # Helper to always return a single value
        def get_value(keys):
            s = grp.loc[
                grp["question_text"].isin(keys),
                "question_response_text"
            ]
            return s.iloc[0] if not s.empty else None

        # --- Gender ---
        row["Gender"] = get_value(QUESTION_MAP["gender"])

        # --- Weight ---
        weight = (
            get_value(QUESTION_MAP["weight_primary"])
            or get_value(QUESTION_MAP["weight_fallback"])
        )
        row["Weight in lb"] = pd.to_numeric(weight, errors="coerce")

        # --- BMI ---
        row["BMI"] = pd.to_numeric(
            get_value(QUESTION_MAP["bmi"]),
            errors="coerce"
        )

        # --- Weight change ---
        row["Change in weight (lbs)"] = pd.to_numeric(
            get_value(QUESTION_MAP["weight_change"]),
            errors="coerce"
        )

        # --- Dosage change ---
        dosage = get_value(QUESTION_MAP["dosage_change"])
        row["Dosage change of Rx"] = (
            "Yes" if dosage and str(dosage).lower() != "no" else "No"
        )

        # --- Other medication change ---
        other = get_value(QUESTION_MAP["other_meds_change"])
        row["Change in other medications"] = (
            "Yes" if other and str(other).lower() == "yes" else "No"
        )

        # --- Height ---
        feet = get_value(QUESTION_MAP["height_feet"])
        inches = get_value(QUESTION_MAP["height_inches"])

        if feet is not None and inches is not None:
            row["Height"] = f"{feet}'{inches}\""
        else:
            row["Height"] = get_value(QUESTION_MAP["height_text"])

        rows.append(row)

    # --- 5. Final DataFrame ---
    out_df = pd.DataFrame(rows)

    # --- 6. Sort encounters properly ---
    out_df = out_df.sort_values(
        ["Patient Number", "Date on which form was filled"]
    )

    # --- 7. Days between encounters ---
    out_df["Days between encounter"] = (
        out_df.groupby("Patient Number")["Date on which form was filled"]
        .diff()
        .dt.days
        .fillna(0)
        .astype(int)
    )

    return out_df
