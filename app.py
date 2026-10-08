import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. Cấu hình trang
st.set_page_config(
    page_title="Hệ Thống Quản Lý Thư Viện",
    page_icon="📚",
    layout="wide"
)

# 2. CHÈN HÌNH NỀN BẰNG CSS (Thay link ảnh trường bạn vào đây nếu muốn)
background_image_url = "https://images.unsplash.com/photo-1541829070764-84a7d30dd3f3?q=80&w=1920"

custom_css = f"""
<style>
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.88)), 
                    url('{background_image_url}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 3. HÀM TỰ ĐỘNG TẠO CSDL VÀ BẢNG (TỰ SỬA LỖI DỮ LIỆU)
def get_connection():
    conn = sqlite3.connect('quanlythuvien.db')
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    # Tạo cấu trúc 6 bảng chuẩn nếu chưa có
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS TheLoai (
            MaTheLoai TEXT PRIMARY KEY,
            TenTheLoai TEXT NOT NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Sach (
            MaSach TEXT PRIMARY KEY,
            TenSach TEXT NOT NULL,
            MaTheLoai TEXT,
            TacGia TEXT,
            TongSoLuong INTEGER DEFAULT 1,
            FOREIGN KEY (MaTheLoai) REFERENCES TheLoai(MaTheLoai)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS DocGia (
            MaDocGia TEXT PRIMARY KEY,
            TenDocGia TEXT NOT NULL,
            Lop TEXT,
            Email TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PhieuMuon (
            MaPhieu TEXT PRIMARY KEY,
            MaDocGia TEXT,
            NgayMuon TEXT,
            FOREIGN KEY (MaDocGia) REFERENCES DocGia(MaDocGia)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ChiTietPhieuMuon (
            MaPhieu TEXT,
            MaSach TEXT,
            NgayTraHen TEXT,
            NgayTraThucTe TEXT,
            PRIMARY KEY (MaPhieu, MaSach),
            FOREIGN KEY (MaPhieu) REFERENCES PhieuMuon(MaPhieu),
            FOREIGN KEY (MaSach) REFERENCES Sach(MaSach)
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PhieuPhat (
            MaPhieuPhat TEXT PRIMARY KEY,
            MaPhieu TEXT,
            SoTienPhat REAL,
            LyDo TEXT,
            FOREIGN KEY (MaPhieu) REFERENCES PhieuMuon(MaPhieu)
        );
    """)
    
    # Nếu chưa có dữ liệu sách, tự động nạp dữ liệu mẫu
    cursor.execute("SELECT COUNT(*) FROM Sach")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT OR IGNORE INTO TheLoai VALUES (?, ?)", [
            ('TL01', 'Giáo trình CNTT'),
            ('TL02', 'Khoa học máy tính'),
            ('TL03', 'Kỹ năng sống')
        ])
        cursor.executemany("INSERT OR IGNORE INTO Sach VALUES (?, ?, ?, ?, ?)", [
            ('S01', 'Lập trình Python cơ bản', 'TL01', 'Nguyễn Văn A', 10),
            ('S02', 'Cấu trúc dữ liệu & Giải thuật', 'TL02', 'Trần Thị B', 5),
            ('S03', 'Hệ quản trị CSDL SQLite', 'TL01', 'Lê Văn C', 8),
            ('S04', 'Nhập môn AI & Machine Learning', 'TL02', 'Phạm Hoàng D', 4)
        ])
        cursor.executemany("INSERT OR IGNORE INTO DocGia VALUES (?, ?, ?, ?)", [
            ('DG01', 'Từ Thiện Nhân', 'CS201K', 'nhantuthien@gmail.com'),
            ('DG02', 'Nguyễn Văn Nam', 'CS201I', 'namnguyen@gmail.com')
        ])
        cursor.executemany("INSERT OR IGNORE INTO PhieuMuon VALUES (?, ?, ?)", [
            ('PM01', 'DG01', '2026-10-01'),
            ('PM02', 'DG02', '2026-10-02')
        ])
        cursor.executemany("INSERT OR IGNORE INTO ChiTietPhieuMuon VALUES (?, ?, ?, ?)", [
            ('PM01', 'S01', '2026-10-08', None),
            ('PM02', 'S02', '2026-10-05', '2026-10-07')
        ])
        conn.commit()
        
    return conn

# Header ứng dụng
st.title("📚 HỆ THỐNG QUẢN LÝ THƯ VIỆN")
st.caption("Đồ án môn CS201 - Tin học ứng dụng | Môi trường: Fedora Linux & Streamlit Cloud")

# 4. HÀNG THỐNG KÊ KPI
conn = get_connection()
try:
    total_books = pd.read_sql_query("SELECT SUM(TongSoLuong) AS Total FROM Sach", conn)['Total'].iloc[0] or 0
    total_borrowed = pd.read_sql_query("SELECT COUNT(*) AS Count FROM ChiTietPhieuMuon WHERE NgayTraThucTe IS NULL", conn)['Count'].iloc[0] or 0
    overdue_count = pd.read_sql_query("SELECT COUNT(*) AS Count FROM PhieuPhat", conn)['Count'].iloc[0] or 0
except Exception:
    total_books, total_borrowed, overdue_count = 0, 0, 0
conn.close()

col1, col2, col3 = st.columns(3)
col1.metric(label="📖 Tổng số sách trong kho", value=f"{int(total_books):,} cuốn")
col2.metric(label="🔄 Lượt sách đang mượn", value=f"{total_borrowed} lượt")
col3.metric(label="⚠️ Lượt vi phạm / Phạt quá hạn", value=f"{overdue_count} lượt")

st.divider()

# 5. GIAO DIỆN TAB CHỨC NĂNG NGANG
tab1, tab2, tab3, tab4 = st.tabs(["📊 Tổng quan kho sách", "📖 Mượn sách", "🔄 Trả sách", "🔍 Báo cáo & Query"])

# TAB 1: Danh sách sách
with tab1:
    st.subheader("📚 Danh mục sách hiện có")
    conn = get_connection()
    df_sach = pd.read_sql_query("""
        SELECT S.MaSach, S.TenSach, TL.TenTheLoai, S.TacGia, S.TongSoLuong, 
               (S.TongSoLuong - COALESCE(COUNT(CT.MaPhieu), 0)) AS SoLuongCon
        FROM Sach S
        LEFT JOIN TheLoai TL ON S.MaTheLoai = TL.MaTheLoai
        LEFT JOIN ChiTietPhieuMuon CT ON S.MaSach = CT.MaSach AND CT.NgayTraThucTe IS NULL
        GROUP BY S.MaSach;
    """, conn)
    conn.close()
    st.dataframe(df_sach, use_container_width=True)

# TAB 2: Lập phiếu mượn
with tab2:
    st.subheader("📝 Lập phiếu mượn sách mới")
    with st.form("borrow_form"):
        col_a, col_b = st.columns(2)
        ma_phieu = col_a.text_input("Mã phiếu mượn (Ví dụ: PM005)")
        ma_doc_gia = col_b.text_input("Mã độc giả (Ví dụ: DG001)")
        
        conn = get_connection()
        sach_df = pd.read_sql_query("SELECT MaSach, TenSach FROM Sach", conn)
        conn.close()
        
        sach_dict = dict(zip(sach_df['TenSach'], sach_df['MaSach'])) if not sach_df.empty else {}
        selected_book = st.selectbox("Chọn sách cần mượn", list(sach_dict.keys())) if sach_dict else None
        
        ngay_muon = st.date_input("Ngày mượn", datetime.now())
        ngay_tra_hen = st.date_input("Ngày hẹn trả", datetime.now())
        
        submitted = st.form_submit_button("Xác nhận mượn sách")
        if submitted:
            if not ma_phieu or not ma_doc_gia or not selected_book:
                st.error("❌ Vui lòng điền đầy đủ thông tin!")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO PhieuMuon VALUES (?, ?, ?)", (ma_phieu, ma_doc_gia, ngay_muon.strftime('%Y-%m-%d')))
                    cursor.execute("INSERT INTO ChiTietPhieuMuon (MaPhieu, MaSach, NgayTraHen, NgayTraThucTe) VALUES (?, ?, ?, NULL)", 
                                   (ma_phieu, sach_dict[selected_book], ngay_tra_hen.strftime('%Y-%m-%d')))
                    conn.commit()
                    conn.close()
                    st.success("✅ Mượn sách thành công!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi mượn sách: {e}")

# TAB 3: Trả sách & Tính phạt
with tab3:
    st.subheader("🔄 Xử lý trả sách")
    conn = get_connection()
    df_dang_muon = pd.read_sql_query("""
        SELECT CT.MaPhieu, S.TenSach, PM.MaDocGia, CT.NgayTraHen 
        FROM ChiTietPhieuMuon CT
        JOIN PhieuMuon PM ON CT.MaPhieu = PM.MaPhieu
        JOIN Sach S ON CT.MaSach = S.MaSach
        WHERE CT.NgayTraThucTe IS NULL
    """, conn)
    conn.close()
    
    if df_dang_muon.empty:
        st.info("Hiện không có phiếu mượn nào chưa trả.")
    else:
        st.dataframe(df_dang_muon, use_container_width=True)
        pm_chon = st.selectbox("Chọn Mã phiếu mượn cần trả", df_dang_muon['MaPhieu'].unique())
        if st.button("Xác nhận trả sách"):
            conn = get_connection()
            cursor = conn.cursor()
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("UPDATE ChiTietPhieuMuon SET NgayTraThucTe = ? WHERE MaPhieu = ?", (today, pm_chon))
            conn.commit()
            conn.close()
            st.success(f"✅ Đã trả sách cho phiếu {pm_chon}!")
            st.rerun()

# TAB 4: Báo cáo & Queries
with tab4:
    st.subheader("🔍 Truy vấn báo cáo nâng cao (Advanced SQL)")
    q_type = st.radio("Chọn báo cáo cần xem:", ["Top 3 sách mượn nhiều nhất", "Danh sách phiếu phạt quá hạn"])
    conn = get_connection()
    if q_type == "Top 3 sách mượn nhiều nhất":
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
