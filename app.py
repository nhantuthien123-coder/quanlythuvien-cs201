import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Hệ Thống Quản Lý Thư Viện", page_icon="📚", layout="wide"
)


def get_connection():
  conn = sqlite3.connect("quanlythuvien.db")
  conn.execute("PRAGMA foreign_keys = ON;")
  return conn


st.title("📚 HỆ THỐNG QUẢN LÝ THƯ VIỆN")
st.caption("Đồ án môn CS201 - Tin học ứng dụng | Môi trường: Fedora Linux")

menu = st.sidebar.selectbox("Chọn chức năng", [
    "1. Danh mục sách & Tồn kho",
    "2. Lập phiếu mượn sách",
    "3. Trả sách & Phạt",
    "4. Báo cáo & Query",
])

conn = get_connection()

if menu == "1. Danh mục sách & Tồn kho":
  st.subheader("📚 Danh sách các cuốn sách trong thư viện")
  try:
    df = pd.read_sql_query("""
            SELECT S.MaSach, S.TenSach, TL.TenTheLoai, S.TacGia, S.TongSoLuong,
                   (S.TongSoLuong - COALESCE(COUNT(CT.MaPhieu), 0)) AS SoLuongCon
            FROM Sach S
            LEFT JOIN TheLoai TL ON S.MaTheLoai = TL.MaTheLoai
            LEFT JOIN ChiTietPhieuMuon CT ON S.MaSach = CT.MaSach AND CT.NgayTraReality IS NULL
            GROUP BY S.MaSach;
        """, conn)
    st.dataframe(df, use_container_width=True)
  except Exception as e:
    st.error(f"Lỗi truy vấn: {e}")

elif menu == "2. Lập phiếu mượn sách":
  st.subheader("📝 Lập phiếu mượn sách")
  with st.form("form_muon"):
    col1, col2 = st.columns(2)
    ma_phieu = col1.text_input("Mã phiếu mượn (Ví dụ: PM005)")
    ma_doc_gia = col2.text_input("Mã độc giả (Ví dụ: DG001)")

    sach_df = pd.read_sql_query("SELECT MaSach, TenSach FROM Sach", conn)
    sach_dict = (
        dict(zip(sach_df["TenSach"], sach_df["MaSach"]))
        if not sach_df.empty
        else {}
    )
    selected_book = (
        st.selectbox("Chọn sách mượn", list(sach_dict.keys()))
        if sach_dict
        else None
    )

    ngay_muon = st.date_input("Ngày mượn", datetime.now())
    ngay_hen = st.date_input("Ngày hẹn trả", datetime.now())

    btn = st.form_submit_button("Xác nhận mượn")
    if btn:
      if ma_phieu and ma_doc_gia and selected_book:
        try:
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO PhieuMuon VALUES (?, ?, ?)",
              (ma_phieu, ma_doc_gia, ngay_muon.strftime("%Y-%m-%d")),
          )
          cursor.execute(
              "INSERT INTO ChiTietPhieuMuon (MaPhieu, MaSach, NgayTraHen,"
              " NgayTraReality) VALUES (?, ?, ?, NULL)",
              (
                  ma_phieu,
                  sach_dict[selected_book],
                  ngay_hen.strftime("%Y-%m-%d"),
              ),
          )
          conn.commit()
          st.success("✅ Mượn sách thành công!")
          st.rerun()
        except Exception as e:
          st.error(f"Lỗi: {e}")
      else:
        st.warning("Vui lòng nhập đủ thông tin!")

elif menu == "3. Trả sách & Phạt":
  st.subheader("🔄 Trả sách")
  try:
    df_muon = pd.read_sql_query("""
            SELECT CT.MaPhieu, S.TenSach, PM.MaDocGia, CT.NgayTraHen 
            FROM ChiTietPhieuMuon CT
            JOIN PhieuMuon PM ON CT.MaPhieu = PM.MaPhieu
            JOIN Sach S ON CT.MaSach = S.MaSach
            WHERE CT.NgayTraReality IS NULL
        """, conn)
    st.dataframe(df_muon, use_container_width=True)

    if not df_muon.empty:
      pm_sel = st.selectbox("Chọn mã phiếu trả", df_muon["MaPhieu"].unique())
      if st.button("Xác nhận trả"):
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ChiTietPhieuMuon SET NgayTraReality = ? WHERE MaPhieu = ?",
            (datetime.now().strftime("%Y-%m-%d"), pm_sel),
        )
        conn.commit()
        st.success(f"✅ Đã trả phiếu {pm_sel}")
        st.rerun()
  except Exception as e:
    st.error(f"Lỗi: {e}")

elif menu == "4. Báo cáo & Query":
  st.subheader("📊 Báo cáo")
  opt = st.radio(
      "Chọn loại báo cáo:",
      ["Top 3 sách mượn nhiều nhất", "Danh sách phiếu phạt"],
  )
  if opt == "Top 3 sách mượn nhiều nhất":
    df_top = pd.read_sql_query("""
            SELECT S.TenSach, COUNT(CT.MaPhieu) AS SoLuotMuon
            FROM Sach S
            JOIN ChiTietPhieuMuon CT ON S.MaSach = CT.MaSach
            GROUP BY S.MaSach ORDER BY SoLuotMuon DESC LIMIT 3
        """, conn)
    st.table(df_top)
  else:
    df_phat = pd.read_sql_query("SELECT * FROM PhieuPhat", conn)
    st.table(df_phat)

conn.close()
