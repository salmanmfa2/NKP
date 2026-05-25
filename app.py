import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# Configuration & Static Credentials
# ==========================================
st.set_page_config(page_title="Link Portal", layout="centered")

ADMIN_USER = "mpk"
ADMIN_PASS = "persibjuara"

# ==========================================
# Database Initialization & Helpers
# ==========================================
def get_db_connection():
    conn = sqlite3.connect('links.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target_url TEXT NOT NULL,
            password TEXT,
            is_active BOOLEAN NOT NULL DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def add_link(title, target_url, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO links (title, target_url, password, is_active) VALUES (?, ?, ?, 1)', 
              (title, target_url, password))
    conn.commit()
    conn.close()

def update_link(link_id, title, target_url, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE links SET title = ?, target_url = ?, password = ? WHERE id = ?', 
              (title, target_url, password, link_id))
    conn.commit()
    conn.close()

def delete_link(link_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM links WHERE id = ?', (link_id,))
    conn.commit()
    conn.close()

def toggle_link_status(link_id, current_status):
    conn = get_db_connection()
    c = conn.cursor()
    new_status = 0 if current_status else 1
    c.execute('UPDATE links SET is_active = ? WHERE id = ?', (new_status, link_id))
    conn.commit()
    conn.close()

def get_all_links():
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT * FROM links', conn)
    conn.close()
    return df

def get_active_links():
    conn = get_db_connection()
    df = pd.read_sql_query('SELECT * FROM links WHERE is_active = 1', conn)
    conn.close()
    return df

init_db()

# ==========================================
# Authentication Logic
# ==========================================
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

def login():
    if st.session_state.username == ADMIN_USER and st.session_state.password == ADMIN_PASS:
        st.session_state.admin_logged_in = True
        st.success("Logged in successfully!")
    else:
        st.error("Invalid credentials")

def logout():
    st.session_state.admin_logged_in = False
    st.session_state.username = ""
    st.session_state.password = ""

with st.sidebar:
    if not st.session_state.admin_logged_in:
        st.header("Admin Login")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=login)
    else:
        st.header("Admin Panel")
        st.write(f"Logged in as: **{ADMIN_USER}**")
        st.button("Logout", on_click=logout)

# ==========================================
# Main View logic
# ==========================================
if st.session_state.admin_logged_in:
    # --------------------------------------
    # ADMIN VIEW
    # --------------------------------------
    st.title("🛠️ Upload NKP -  Administrator")
    
    with st.expander("➕ Add New Link"):
        with st.form("add_link_form", clear_on_submit=True):
            title = st.text_input("Link Title")
            target_url = st.text_input("Target URL (e.g., https://example.com)")
            password = st.text_input("Password (Optional)", type="password")
            
            if st.form_submit_button("Save Link"):
                if title and target_url:
                    add_link(title, target_url, password)
                    st.success(f"Link '{title}' added!")
                    st.rerun()
                else:
                    st.error("Title and Target URL are required.")

    st.subheader("Manage Links")
    
    # 1. SEARCH FUNCTIONALITY (ADMIN)
    search_query = st.text_input("🔍 Cari Unit Kerja...", key="admin_search")
    
    links_df = get_all_links()
    
    if not links_df.empty:
        # Filter dataframe based on search query
        if search_query:
            links_df = links_df[links_df['title'].str.contains(search_query, case=False, na=False)]
        
        for index, row in links_df.iterrows():
            col1, col2, col3 = st.columns([5, 2, 2])
            with col1:
                st.write(f"**{row['title']}**")
                # Truncate long URLs for display
                display_url = row['target_url'][:30] + "..." if len(row['target_url']) > 30 else row['target_url']
                st.caption(display_url)
            with col2:
                status = "🟢 Active" if row['is_active'] else "🔴 Inactive"
                st.write(status)
            with col3:
                # 2. EDIT / DELETE FUNCTIONALITY via Popover menu
                with st.popover("⚙️ Manage"):
                    # Edit Form
                    with st.form(f"edit_form_{row['id']}"):
                        st.write("**Edit Link**")
                        edit_title = st.text_input("Title", value=row['title'])
                        edit_url = st.text_input("URL", value=row['target_url'])
                        edit_pwd = st.text_input("Password", value=row['password'] if row['password'] else "", type="password")
                        if st.form_submit_button("Save Changes"):
                            update_link(row['id'], edit_title, edit_url, edit_pwd)
                            st.rerun()
                    
                    # Status Toggle
                    btn_text = "Deactivate" if row['is_active'] else "Activate"
                    if st.button(btn_text, key=f"toggle_{row['id']}", use_container_width=True):
                        toggle_link_status(row['id'], row['is_active'])
                        st.rerun()
                    
                    # Delete Button
                    if st.button("🗑️ Delete", key=f"delete_{row['id']}", type="primary", use_container_width=True):
                        delete_link(row['id'])
                        st.rerun()
            st.divider()
        
        if links_df.empty and search_query:
            st.warning("No links match your search.")
    else:
        st.info("No links found in the database. Add one above.")

else:
    # --------------------------------------
    # GUEST VIEW
    # --------------------------------------
    st.title("🔗 Upload NKP - Guest")
    st.write("Silahkan klik link sesuai dengan Unit Kerja Bapak/Ibu dan masukkan password yang telah diberikan admin")
    
    # 3. SEARCH FUNCTIONALITY (GUEST)
    search_query = st.text_input("🔍 Cari Unit Kerja...", key="guest_search")
    st.divider()
    
    active_links = get_active_links()
    
    if not active_links.empty:
        # Filter dataframe based on search query
        if search_query:
            active_links = active_links[active_links['title'].str.contains(search_query, case=False, na=False)]
        
        if active_links.empty:
            st.warning("No resources match your search.")
        else:
            # 4. COMPACT UI (Buttons & Popovers instead of large containers)
            for index, row in active_links.iterrows():
                if row['password']:
                    # Protected link: Looks like a button, opens a small menu for password
                    with st.popover(f"🔒 {row['title']}"):
                        pwd_input = st.text_input("Enter Password", type="password", key=f"pwd_{row['id']}")
                        if st.button("Unlock", key=f"btn_{row['id']}", use_container_width=True):
                            if pwd_input == row['password']:
                                st.success("Access Granted!")
                                st.link_button(f"Go to {row['title']}", row['target_url'], type="primary", use_container_width=True)
                            else:
                                st.error("Incorrect Password")
                else:
                    # Public link: Standard button
                    st.link_button(f"🔗 {row['title']}", row['target_url'], use_container_width=False)
    else:
        st.info("No active links are currently available.")
