import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Quản Lý Thư Viện CS201", layout="wide", page_icon="📚")

def get_connection():
    return sqlite3.connect('quanlythuvien.db')

st.title("📚 HỆ THỐNG QUẢN LÝ THƯ VIỆN & MƯỢN TRẢ SÁCH (CS201)")
st.caption("Đề tài cá nhân 13 - Mô hình ứng dụng công nghệ AI & Web App")

# Sidebar
st.sidebar.header("DANH MỤC CHỨC NĂNG")
menu = st.sidebar.radio("Chọn chức năng:", [
    "1. Form Mượn / Trả Sách",
    "2. Tra Cứu & Query Nghiệp Vụ",
    "3. Báo Cáo & Phiếu Phạt"
])

conn = get_connection()

if menu == "1. Form Mượn / Trả Sách":
    st.header("📝 Giao Diện Form Mượn / Trả Sách")
    
    tab1, tab2 = st.tabs(["Lập Phiếu Mượn Mới", "Ghi Nhận Trả Sách"])
    
    with tab1:
        st.subheader("Lập Phiếu Mượn Sách")
        
        docgia_df = pd.read_sql_query("SELECT MaDocGia, HoTen FROM DocGia", conn)
        sach_df = pd.read_sql_query("SELECT MaSach, TenSach, SoLuongCon FROM Sach", conn)
        
        col1, col2 = st.columns(2)
        with col1:
            ma_pm = st.text_input("Mã Phiếu Mượn", value="PM08")
            docgia_options = [f"{row['MaDocGia']} - {row['HoTen']}" for _, row in docgia_df.iterrows()]
            docgia_select = st.selectbox("Chọn Độc Giả", options=docgia_options)
            ngay_muon = st.date_input("Ngày Mượn", datetime.now())
            ngay_tra = st.date_input("Ngày Trả Dự Kiến", datetime.now() + timedelta(days=14))
            
        with col2:
            sach_options = [f"{row['MaSach']} - {row['TenSach']} (Tồn: {row['SoLuongCon']})" for _, row in sach_df.iterrows()]
            sach_select = st.selectbox("Chọn Sách Mượn", options=sach_options)
            so_luong = st.number_input("Số Lượng Mượn", min_value=1, value=1)
            
            selected_sach_id = sach_select.split(" - ")[0]
            selected_dg_id = docgia_select.split(" - ")[0]
            
            so_ton_list = sach_df[sach_df['MaSach'] == selected_sach_id]['SoLuongCon'].values
            so_ton = int(so_ton_list[0]) if len(so_ton_list) > 0 else 0
            
            if so_ton < so_luong:
                st.error(f"⚠️ Rất tiếc, sách này chỉ còn {so_ton} cuốn trong kho! Không đủ số lượng cho mượn.")
            else:
                st.success(f"✅ Hợp lệ (Sách còn {so_ton} cuốn trong kho).")
                
        if st.button("Xác Nhận Cho Mượn"):
            if so_ton >= so_luong:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO PhieuMuon VALUES (?, ?, ?, ?, 'DangMuon')",
                        (ma_pm, selected_dg_id, str(ngay_muon), str(ngay_tra))
                    )
                    cursor.execute(
                        "INSERT INTO ChiTietPhieuMuon (MaPhieuMuon, MaSach, SoLuong) VALUES (?, ?, ?)",
                        (ma_pm, selected_sach_id, so_luong)
                    )
                    cursor.execute(
                        "UPDATE Sach SET SoLuongCon = SoLuongCon - ? WHERE MaSach = ?",
                        (so_luong, selected_sach_id)
                    )
                    conn.commit()
                    st.balloons()
                    st.success(f"🎉 Đã lập thành công Phiếu Mượn {ma_pm}!")
                except sqlite3.IntegrityError:
                    st.error(f"⚠️ Mã Phiếu Mượn '{ma_pm}' đã tồn tại trong hệ thống! Vui lòng đổi Mã Phiếu Mượn khác (ví dụ: PM08, PM09...).")

    with tab2:
        st.subheader("Ghi Nhận Trả Sách")
        pm_active = pd.read_sql_query(
            "SELECT pm.MaPhieuMuon, dg.HoTen, s.TenSach, ct.MaSach, ct.SoLuong FROM PhieuMuon pm "
            "JOIN DocGia dg ON pm.MaDocGia = dg.MaDocGia "
            "JOIN ChiTietPhieuMuon ct ON pm.MaPhieuMuon = ct.MaPhieuMuon "
            "JOIN Sach s ON ct.MaSach = s.MaSach WHERE pm.TrangThai != 'DaTra'", conn
        )
        st.dataframe(pm_active, use_container_width=True)
        
        if not pm_active.empty:
            pm_to_return = st.selectbox("Chọn Phiếu Mượn Cần Trả", pm_active['MaPhieuMuon'].unique())
            if st.button("Xác Nhận Trả Sách"):
                cursor = conn.cursor()
                cursor.execute("UPDATE PhieuMuon SET TrangThai = 'DaTra' WHERE MaPhieuMuon = ?", (pm_to_return,))
                sach_info = pm_active[pm_active['MaPhieuMuon'] == pm_to_return]
                for idx, row in sach_info.iterrows():
                    cursor.execute(
                        "UPDATE Sach SET SoLuongCon = SoLuongCon + ? WHERE MaSach = ?",
                        (row['SoLuong'], row['MaSach'])
                    )
                conn.commit()
                st.success(f"✅ Đã nhận trả sách cho phiếu {pm_to_return} và cộng lại số lượng vào kho!")

elif menu == "2. Tra Cứu & Query Nghiệp Vụ":
    st.header("🔍 Tra Cứu Dữ Liệu & Thống Kê Query")
    
    st.subheader("1. Bảng Quản Lý Tồn Kho Sách")
    sach_df = pd.read_sql_query("SELECT * FROM Sach", conn)
    st.dataframe(sach_df, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("2. Top 3 Sách Mượn Nhiều Nhất")
        top_sach = pd.read_sql_query('''
            SELECT s.MaSach, s.TenSach, COUNT(ct.MaChiTiet) AS SoLanMuon 
            FROM ChiTietPhieuMuon ct 
            JOIN Sach s ON ct.MaSach = s.MaSach 
            GROUP BY s.MaSach, s.TenSach 
            ORDER BY SoLanMuon DESC LIMIT 3;
        ''', conn)
        st.table(top_sach)
        
    with col2:
        st.subheader("3. Sách Mượn Quá Hạn")
        qua_han = pd.read_sql_query('''
            SELECT pm.MaPhieuMuon, dg.HoTen, s.TenSach, pm.NgayTraDuKien, pm.TrangThai
            FROM PhieuMuon pm 
            JOIN DocGia dg ON pm.MaDocGia = dg.MaDocGia 
            JOIN ChiTietPhieuMuon ct ON pm.MaPhieuMuon = ct.MaPhieuMuon 
            JOIN Sach s ON ct.MaSach = s.MaSach 
            WHERE pm.TrangThai = 'QuaHan' OR (pm.TrangThai = 'DangMuon' AND pm.NgayTraDuKien < DATE('now'));
        ''', conn)
        st.table(qua_han)

elif menu == "3. Báo Cáo & Phiếu Phạt":
    st.header("📋 Quản Lý Phiếu Phạt & Lưu Thông Sách")
    phieu_phat = pd.read_sql_query('''
        SELECT pp.MaPhieuPhat, pp.MaPhieuMuon, dg.HoTen, pp.SoTienPhat, pp.LyDoPhat, pp.TrangThaiThanhToan
        FROM PhieuPhat pp
        JOIN DocGia dg ON pp.MaDocGia = dg.MaDocGia;
    ''', conn)
    st.dataframe(phieu_phat, use_container_width=True)

conn.close()
