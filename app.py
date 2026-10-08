import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Hệ Thống Quản Lý Thư Viện", page_icon="📚", layout="wide"
)


# 1. HÀM KẾT NỐI & TỰ ĐỘNG BỔ SUNG CỘT CSDL NẾU THIẾU
def get_connection():
  conn = sqlite3.connect("quanlythuvien.db")
  conn.execute("PRAGMA foreign_keys = ON;")
  cursor = conn.cursor()

  try:
    cursor.execute("PRAGMA table_info(ChiTietPhieuMuon);")
    cols = [row[1] for row in cursor.fetchall()]
    if cols and "NgayTraReality" not in cols:
      cursor.execute(
          "ALTER TABLE ChiTietPhieuMuon ADD COLUMN NgayTraReality TEXT;"
      )
      if "NgayTraThucTe" in cols:
        cursor.execute(
            "UPDATE ChiTietPhieuMuon SET NgayTraReality = NgayTraThucTe;"
        )
      conn.commit()
  except Exception:
    pass

  return conn


st.title("📚 HỆ THỐNG QUẢN LÝ THƯ VIỆN")
st.caption(
    "Đồ án môn CS201 - Tin học ứng dụng | Môi trường: Fedora Linux & Streamlit"
    " Cloud"
)

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
                   (S.TongSoLuong - COALESCE(SUM(CT.SoLuong), 0)) AS SoLuongCon
            FROM Sach S
            LEFT JOIN TheLoai TL ON S.MaTheLoai = TL.MaTheLoai
            LEFT JOIN ChiTietPhieuMuon CT ON S.MaSach = CT.MaSach AND (CT.NgayTraReality IS NULL OR CT.NgayTraReality = '')
            GROUP BY S.MaSach, S.TenSach, TL.TenTheLoai, S.TacGia, S.TongSoLuong;
        """, conn)
    st.dataframe(df, use_container_width=True)
  except Exception as e:
    st.error(f"Lỗi truy vấn: {e}")

elif menu == "2. Lập phiếu mượn sách":
  st.subheader("📝 Lập phiếu mượn sách")
  with st.form("form_muon", clear_on_submit=False):
    col1, col2 = st.columns(2)
    ma_phieu = col1.text_input("Mã phiếu mượn (Ví dụ: PM005, PM099...)")

    try:
      doc_gia_df = pd.read_sql_query(
          "SELECT MaDocGia, HoTen FROM DocGia", conn
      )
      dg_dict = (
          dict(zip(doc_gia_df["HoTen"], doc_gia_df["MaDocGia"]))
          if not doc_gia_df.empty
          else {}
      )
    except Exception:
      doc_gia_df = pd.read_sql_query(
          "SELECT MaDocGia, TenDocGia FROM DocGia", conn
      )
      dg_dict = (
          dict(zip(doc_gia_df["TenDocGia"], doc_gia_df["MaDocGia"]))
          if not doc_gia_df.empty
          else {}
      )

    selected_dg = (
        col2.selectbox("Chọn độc giả", list(dg_dict.keys())) if dg_dict else None
    )

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

    col_d1, col_d2 = st.columns(2)
    ngay_muon = col_d1.date_input("Ngày mượn", datetime.now())
    ngay_hen = col_d2.date_input("Ngày hẹn trả", datetime.now())

    btn = st.form_submit_button("Xác nhận mượn")
    if btn:
      if ma_phieu and selected_dg and selected_book:
        try:
          cursor = conn.cursor()
          cursor.execute(
              "INSERT INTO PhieuMuon (MaPhieuMuon, MaDocGia, NgayMuon,"
              " NgayTraDuKien, TrangThai) VALUES (?, ?, ?, ?, 'DangMuon')",
              (
                  ma_phieu,
                  dg_dict[selected_dg],
                  ngay_muon.strftime("%Y-%m-%d"),
                  ngay_hen.strftime("%Y-%m-%d"),
              ),
          )
          cursor.execute(
              "INSERT INTO ChiTietPhieuMuon (MaPhieuMuon, MaSach, SoLuong,"
              " NgayTraReality) VALUES (?, ?, 1, NULL)",
              (ma_phieu, sach_dict[selected_book]),
          )
          conn.commit()

          # THÊM HIỆU ỨNG BONG BÓNG & THÔNG BÁO XANH ĐẸP MẮT
          st.balloons()
          st.success(
              f"🎉 MƯỢN SÁCH THÀNH CÔNG cho phiếu {ma_phieu}! Dữ liệu đã được"
              " lưu vào CSDL."
          )
        except sqlite3.IntegrityError:
          st.error(
              f"⚠️ Mã phiếu mượn '{ma_phieu}' này đã tồn tại trong CSDL! Vui"
              " lòng nhập mã mới (ví dụ: PM099)."
          )
        except Exception as e:
          st.error(f"❌ Lỗi lập phiếu: {e}")
      else:
        st.warning(
            "⚠️ Vui lòng nhập đầy đủ thông tin mã phiếu, chọn độc giả và chọn"
            " sách!"
        )

elif menu == "3. Trả sách & Phạt":
  st.subheader("🔄 Xử lý trả sách")
  try:
    df_muon = pd.read_sql_query("""
            SELECT CT.MaPhieuMuon, S.TenSach, DG.HoTen, PM.NgayTraDuKien
            FROM ChiTietPhieuMuon CT
            JOIN PhieuMuon PM ON CT.MaPhieuMuon = PM.MaPhieuMuon
            JOIN DocGia DG ON PM.MaDocGia = DG.MaDocGia
            JOIN Sach S ON CT.MaSach = S.MaSach
            WHERE CT.NgayTraReality IS NULL OR CT.NgayTraReality = ''
        """, conn)

    if df_muon.empty:
      st.info("Hiện không có phiếu mượn nào chưa trả.")
    else:
      st.dataframe(df_muon, use_container_width=True)
      pm_sel = st.selectbox(
          "Chọn mã phiếu cần trả", df_muon["MaPhieuMuon"].unique()
      )
      if st.button("Xác nhận trả"):
        cursor = conn.cursor()
        today_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "UPDATE ChiTietPhieuMuon SET NgayTraReality = ? WHERE MaPhieuMuon ="
            " ?",
            (today_str, pm_sel),
        )
        try:
          cursor.execute(
              "UPDATE ChiTietPhieuMuon SET NgayTraThucTe = ? WHERE MaPhieuMuon"
              " = ?",
              (today_str, pm_sel),
          )
        except Exception:
          pass
        cursor.execute(
            "UPDATE PhieuMuon SET TrangThai = 'DaTra' WHERE MaPhieuMuon = ?",
            (pm_sel,),
        )
        conn.commit()

        # HIỆU ỨNG BONG BÓNG KHI TRẢ SÁCH
        st.balloons()
        st.success(f"✅ Đã trả sách thành công cho phiếu {pm_sel}!")
  except Exception as e:
    st.error(f"Lỗi trả sách: {e}")

elif menu == "4. Báo cáo & Query":
  st.subheader("📊 Báo cáo Thống kê & Phạt")
  opt = st.radio(
      "Chọn loại báo cáo:",
      ["Top 3 sách mượn nhiều nhất", "Danh sách phiếu phạt"],
  )
  if opt == "Top 3 sách mượn nhiều nhất":
    df_top = pd.read_sql_query("""
            SELECT S.TenSach, COUNT(CT.MaChiTiet) AS SoLuotMuon
            FROM Sach S
            JOIN ChiTietPhieuMuon CT ON S.MaSach = CT.MaSach
            GROUP BY S.MaSach, S.TenSach ORDER BY SoLuotMuon DESC LIMIT 3
        """, conn)
    st.table(df_top)
  else:
    try:
      df_phat = pd.read_sql_query("""
                SELECT PP.MaPhieuPhat, PP.MaPhieuMuon, DG.HoTen, PP.SoTienPhat, PP.LyDoPhat, PP.TrangThaiThanhToan
                FROM PhieuPhat PP
                JOIN DocGia DG ON PP.MaDocGia = DG.MaDocGia;
            """, conn)
    except Exception:
      df_phat = pd.read_sql_query("SELECT * FROM PhieuPhat", conn)
    st.table(df_phat)

conn.close()

