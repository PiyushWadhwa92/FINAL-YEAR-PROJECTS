# app.py
import streamlit as st
from PIL import Image
import os
import subprocess
import sys
import time
import pandas as pd
from io import BytesIO

# Page config: full width / full-screen like app
st.set_page_config(page_title="Automatic Attendance System", layout="wide", initial_sidebar_state="collapsed")

# Basic CSS for a full-screen look and nicer cards
st.markdown(
    """
    <style>
    /* full viewport height minus header */
    .appview-container .main > div {
        padding-top: 1rem;
    }
    /* make the body take full height */
    html, body, [data-testid="stAppViewContainer"] > .main {
        height: 100vh;
        margin: 0;
    }
    /* card-like buttons */
    .card {
        background: linear-gradient(180deg, #ffffffcc 0%, #f6f8ffcc 100%);
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 6px 18px rgba(20,20,60,0.08);
        transition: transform .12s ease-in-out, box-shadow .12s ease-in-out;
        text-align: center;
    }
    .card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 30px rgba(20,20,60,0.12);
    }
    .big-btn {
        font-size: 18px;
        padding: 10px 16px;
        border-radius: 10px;
    }
    .muted {
        color: #555;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Ensure folders exist
IMAGES_DIR = os.path.join(os.getcwd(), "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

ATT_DIR = os.path.join(os.getcwd(), "attendence_sheet")
os.makedirs(ATT_DIR, exist_ok=True)

# Main layout
st.title("Automatic Attendance System")

home_col1, home_col2, home_col3 = st.columns([1, 1, 1], gap="large")

with home_col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Register")
    st.write("Upload a person's photo to `images/` (used for registration).")
    uploaded = st.file_uploader("Upload image (jpg / png)", type=['jpg', 'jpeg', 'png'], key="register_uploader")
    roll_input = st.text_input("Enter name / roll number (used as filename)", key="register_name")
    if uploaded is not None and roll_input.strip():
        # Save button
        if st.button("Save to images folder", key="save_image_btn"):
            try:
                # sanitize filename
                base_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in roll_input).strip()
                if not base_name:
                    st.error("Filename would be empty after sanitizing. Use a different name.")
                else:
                    ext = os.path.splitext(uploaded.name)[1].lower()
                    filename = f"{base_name}{ext}"
                    save_path = os.path.join(IMAGES_DIR, filename)
                    with open(save_path, "wb") as f:
                        f.write(uploaded.getbuffer())
                    st.success(f"Saved: {save_path}")
                    # preview
                    img = Image.open(save_path)
                    st.image(img, use_column_width=True, caption=filename)
            except Exception as e:
                st.exception(e)
    elif uploaded is not None and not roll_input.strip():
        st.info("Enter a name / roll number above before saving.")
    st.markdown('</div>', unsafe_allow_html=True)

with home_col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Mark attendance")
    st.write("Run the face recognition script. This will open your camera and mark attendance in CSV files.")
    st.write('<div class="muted">Note: the process runs locally and will block the Streamlit process while running (it uses your webcam and opens an OpenCV window). Close the window or press `q` in the window to stop.</div>', unsafe_allow_html=True)
    # Path to your face recognition script (from your uploaded files)
    FACE_REC_SCRIPT = r"face_rec.py"  # path you provided / uploaded
    st.write("Face-recognition script:", FACE_REC_SCRIPT)

    run_col1, run_col2 = st.columns([2, 1])
    with run_col1:
        run_button = st.button("Run Mark Attendance", key="run_att")
    with run_col2:
        threshold = st.slider("Distance threshold", 0.3, 1.2, 0.6, 0.05, key="threshold_slider")
        st.caption("(If your face recognition script reads threshold differently, edit the script directly.)")

    if run_button:
        # execute the script with a spinner while it runs
        st.info("Starting face recognition. Camera window will open. Logs will appear below.")
        log_placeholder = st.empty()
        # Run the face recognition script as a blocking subprocess so the user can interact with the camera
        try:
            with st.spinner("Running... open the camera window and press 'q' in that window to quit."):
                # Call python with the script; pass threshold as an environment variable or argument if needed
                # Here we pass it as an environment variable to the subprocess (the script would need to read it).
                env = os.environ.copy()
                env["FR_THRESHOLD"] = str(threshold)
                # blocking run
                completed = subprocess.run([sys.executable, FACE_REC_SCRIPT], env=env, capture_output=True, text=True, check=False)
                # Show stdout/stderr
                out = completed.stdout
                err = completed.stderr
                if out:
                    log_placeholder.code(out)
                if err:
                    log_placeholder.code(err)
                st.success("Face recognition script finished (or was stopped). Check the CSV in 'attendence_sheet/'.")
        except Exception as e:
            st.exception(e)

    st.markdown('</div>', unsafe_allow_html=True)

with home_col3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("See CSV attendance sheet")
    st.write("View and download attendance CSVs produced by the face recognition script.")
    # List CSV files
    csv_files = []
    for f in sorted(os.listdir(ATT_DIR), reverse=True):
        if f.lower().endswith(".csv"):
            csv_files.append(f)
    if not csv_files:
        st.info(f"No CSV attendance files found in `{ATT_DIR}` yet.")
    else:
        selected = st.selectbox("Select attendance CSV", options=csv_files, key="select_csv")
        file_path = os.path.join(ATT_DIR, selected)
        if st.button("Load CSV", key="load_csv"):
            try:
                df = pd.read_csv(file_path)
                st.write(f"Preview: **{selected}** (rows: {len(df)})")
                st.dataframe(df, use_container_width=True)
                # download
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", data=csv_bytes, file_name=selected, mime="text/csv")
            except Exception as e:
                st.exception(e)
    st.markdown('</div>', unsafe_allow_html=True)

# footer 
st.markdown("---")

