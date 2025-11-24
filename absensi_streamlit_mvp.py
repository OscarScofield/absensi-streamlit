# app.py - MVP Sistem Absensi Karyawan dengan Streamlit + Google Sheets

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import bcrypt

# ============================
# Google Sheets Setup
# ============================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# TODO: ganti dengan file kredensial JSON kamu
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet_users = client.open("absensi_db").worksheet("users")
sheet_absen = client.open("absensi_db").worksheet("absensi")

# ============================
# Helper Functions
# ============================
def load_users():
    data = sheet_users.get_all_records()
    return pd.DataFrame(data)

def load_absensi():
    data = sheet_absen.get_all_records()
    return pd.DataFrame(data)

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ============================
# Login System
# ============================
def login_page():
    st.title("Login Karyawan")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        df = load_users()
        user = df[df["username"] == username]

        if not user.empty:
            stored_hash = user.iloc[0]['password_hash']
            if verify_password(password, stored_hash):
                st.session_state.logged_in = True
                st.session_state.user_id = user.iloc[0]['id']
                st.session_state.nama = user.iloc[0]['nama']
                st.session_state.role = user.iloc[0]['role']
                st.rerun()
            else:
                st.error("Password salah")
        else:
            st.error("Username tidak ditemukan")

# ============================
# Absen Functions
# ============================
def absen_masuk(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    df = load_absensi()
    existing = df[(df['user_id'] == user_id) & (df['tanggal'] == today)]

    if not existing.empty and existing.iloc[0]['jam_masuk'] != "":
        st.warning("Anda sudah absen masuk hari ini")
        return

    jam = datetime.now().strftime("%H:%M:%S")
    sheet_absen.append_row([str(len(df)+1), user_id, today, jam, "", "", ""])
    st.success(f"Absen masuk berhasil: {jam}")

def absen_keluar(user_id):
    df = load_absensi()
    today = datetime.now().strftime("%Y-%m-%d")
    idx = df[(df['user_id'] == user_id) & (df['tanggal'] == today)].index

    if len(idx) == 0:
        st.error("Anda belum absen masuk")
        return

    row = df.loc[idx[0]]
    if row['jam_keluar'] != "":
        st.warning("Anda sudah absen keluar hari ini")
        return

    jam = datetime.now().strftime("%H:%M:%S")
    sheet_absen.update_cell(idx[0]+2, 5, jam)
    st.success(f"Absen keluar berhasil: {jam}")

# ============================
# Dashboard Karyawan
# ============================
def karyawan_dashboard():
    st.title(f"Halo, {st.session_state.nama}")

    st.subheader("Menu Absensi")
    if st.button("Absen Masuk"):
        absen_masuk(st.session_state.user_id)
    if st.button("Absen Keluar"):
        absen_keluar(st.session_state.user_id)

    st.subheader("Riwayat Absensi Anda")
    df = load_absensi()
    user_df = df[df['user_id'] == st.session_state.user_id]
    st.dataframe(user_df)

# ============================
# Admin Dashboard
# ============================
def admin_dashboard():
    st.title("Admin Dashboard")

    st.subheader("Data Absensi Semua Karyawan")
    df = load_absensi()
    st.dataframe(df)

    st.download_button("Download CSV", df.to_csv(index=False), "absensi.csv")

# ============================
# Main App Controller
# ============================
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
    else:
        role = st.session_state.role
        if role == "admin":
            admin_dashboard()
        else:
            karyawan_dashboard()

        st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

if __name__ == "__main__":
    main()
