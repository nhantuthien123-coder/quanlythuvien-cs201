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

# 2. CHÈN HÌNH NỀN TRƯỜNG BẰNG CSS
# 💡 BẠN THAY ĐƯỜNG LINK ẢNH TRƯỜNG BẠN VÀO DÒNG 'background-image' DƯỚI ĐÂY:
background_image_url = "https://files02.duytan.edu.vn/svruploads/news-duytan/uploads/media/408_256/images/19ds2-14.jpg" # <--- Thay link ảnh trường vào đây

custom_css = f"""
<style>
    /* Hình nền toàn bộ ứng dụng */
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), 
                    url('{background_image_url}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    /* Làm đẹp các thẻ Card / Box */
    .metric-card {{
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Hàm kết nối CSDL
def get_connection():
    conn = sqlite3.connect('quanlythuvien.db')
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# Header ứng dụng
st.title("📚 HỆ THỐNG QUẢN LÝ THƯ VIỆN")
st.caption("Đồ án môn CS201 - Tin học ứng dụng | Môi trường: Fedora Linux & Streamlit Cloud")

# 3. HÀNG THỐNG KÊ KPI (Dashboard Overview)
conn = get_connection()
try:
    total_books = pd.read_sql_query("SELECT SUM(TongSoLuong) AS Total FROM Sach", conn)['Total'].iloc[0] or 0
    total_borrowed = pd.read_sql_query("SELECT COUNT(*) AS Count FROM ChiTietPhieuMuon WHERE NgayTra Reality IS NULL", conn)['Count'].iloc[0] or 0
    overdue_count = pd.read_sql_query("SELECT COUNT(*) AS Count FROM PhieuPhat", conn)['Count'].iloc[0] or 0
except:
    total_books, total_borrowed, overdue_count = 0, 0, 0
conn.close()

col1, col2, col3 = st.columns(3)
col1.metric(label="📖 Tổng số sách trong kho", value=f"{total_books:,} cuốn")
col2.metric(label="🔄 Lượt sách đang mượn", value=f"{total_borrowed} lượt")
col3.metric(label="⚠️ Lượt vi phạm / Phạt quá hạn", value=f"{overdue_count} lượt", delta_color="inverse")

st.divider()

# 4. GIAO DIỆN TAB CHỨC NĂNG NGANG
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
        LEFT JOIN ChiTietPhieuMuon CT ON S.MaSach = CT.MaSach AND CT.NgayTraReality IS NULL
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
        
        sach_dict = dict(zip(sach_df['TenSach'], sach_df['MaSach']))
        selected_book = st.selectbox("Chọn sách cần mượn", list(sach_dict.keys())) if not sach_df.empty else None
        
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
                    cursor.execute("INSERT INTO ChiTietPhieuMuon (MaPhieu, MaSach, NgayTraHen) VALUES (?, ?, ?)", 
                                   (ma_phieu, sach_dict[selected_book], ngay_tra_hen.strftime('%Y-%m-%d')))
                    conn.commit()
                    conn.close()
                    st.success("✅ Mượn sách thành công! Dữ liệu đã lưu vào SQLite.")
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
        WHERE CT.NgayTraReality IS NULL
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
            cursor.execute("UPDATE ChiTietPhieuMuon SET NgayTraReality = ? WHERE MaPhieu = ?", (today, pm_chon))
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

