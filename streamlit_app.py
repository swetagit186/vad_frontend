import streamlit as st
import requests
import tempfile
import os
import base64
from PIL import Image
from io import BytesIO

# -----------------------------
# CONFIGURATION
# -----------------------------
# During local development:
BACKEND_URL = "http://localhost:8000/predict"

# For deployment, change to:
# BACKEND_URL = "https://vadbackend-production.up.railway.app/predict"

st.set_page_config(
    page_title="MRI Dementia Classifier",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <h1 style='text-align: center;'>🧠 MRI Dementia Classifier</h1>
    <h4 style='text-align: center; color: gray;'>Classifies MRI DICOM scans into Normal, Alzheimer, or VaD</h4>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# FILE UPLOAD
# -----------------------------
st.sidebar.header("Upload Patient ZIP File")

uploaded_zip = st.sidebar.file_uploader(
    "Upload a ZIP containing DICOM files:",
    type=["zip"]
)

submit = st.sidebar.button("Predict")

# -----------------------------
# PROCESSING
# -----------------------------
if submit:
    if uploaded_zip is None:
        st.error("Please upload a ZIP file first.")
        st.stop()

    with st.spinner("Uploading file to backend... Please wait ⏳"):
        # Save uploaded ZIP temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            tmp.write(uploaded_zip.read())
            tmp_path = tmp.name

        # Send to backend
        try:
            with open(tmp_path, "rb") as f:
                response = requests.post(
                    BACKEND_URL,
                    files={"file": (uploaded_zip.name, f, "application/zip")}
                )
        except Exception as e:
            st.error(f"❌ Could not connect to backend: {e}")
            st.stop()

        if response.status_code != 200:
            st.error(f"❌ Backend error: {response.text}")
            st.stop()

        result = response.json()

    # delete temporary file
    os.remove(tmp_path)

    # -----------------------------
    # DISPLAY RESULTS
    # -----------------------------
    st.success("Prediction done!")

    # --- Main Prediction ---
    st.markdown("## 🩺 Final Diagnosis")
    st.markdown(
        f"""
        <div style="font-size:30px; font-weight:bold;">
        {result['prediction']}
        </div>
        <div style="font-size:20px; color:gray;">
        Confidence: {result['confidence']*100:.2f}%
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Image Preview ---
    st.markdown("## 🧩 Middle MRI Slice")
    preview_b64 = result.get("preview_base64")

    if preview_b64:
        st.image(preview_b64, caption="Middle Slice Preview", use_column_width=False)
    else:
        st.warning("No preview slice provided.")

    # --- Patient Metadata ---
    st.markdown("## 👤 Patient Metadata")
    st.json(result["patient_metadata"])

    # --- Probability Table ---
    st.markdown("## 📊 Class Probabilities")

    prob_table = [
        {"Class": cls, "Probability (%)": f"{p*100:.2f}"}
        for cls, p in result["probabilities"].items()
    ]

    st.table(prob_table)

    # Number of slices used
    st.info(f"🧾 Number of slices used: **{result['num_slices_used']}**")


else:
    st.info("Upload a ZIP file and click Predict to begin analysis.")
