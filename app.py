import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# Configuration & Static Credentials
# ==========================================
st.set_page_config(page_title="Link Portal", layout="centered")

ADMIN_USER = "salman"
ADMIN_PASS = "pgt6i9fd4"

# ==========================================
# Database Initialization & Helpers
# ==========================================
def get_db_connection():
    # SQLite creates the file automatically if it doesn't exist
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

# Initialize DB on first run
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

# Sidebar for Authentication
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
    st.title("🛠️ Admin Dashboard")
    
    st.subheader("Add New Link")
    with st.form("add_link_form", clear_on_submit=True):
        title = st.text_input("Link Title")
        target_url = st.text_input("Target URL (e.g., https://example.com)")
        password = st.text_input("Password (Optional - leave blank for public link)", type="password")
        
        submitted = st.form_submit_button("Save Link")
        if submitted:
            if title and target_url:
                add_link(title, target_url, password)
                st.success(f"Link '{title}' added successfully!")
                st.rerun()
            else:
                st.error("Title and Target URL are required.")

    st.subheader("Manage Links")
    links_df = get_all_links()
    
    if not links_df.empty:
        # Display links and provide a toggle button for each
        for index, row in links_df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
            with col1:
                st.write(f"**{row['title']}**")
            with col2:
                # Truncate long URLs for display
                display_url = row['target_url'][:30] + "..." if len(row['target_url']) > 30 else row['target_url']
                st.caption(display_url)
            with col3:
                status = "🟢 Active" if row['is_active'] else "🔴 Inactive"
                st.write(status)
            with col4:
                btn_text = "Deactivate" if row['is_active'] else "Activate"
                if st.button(btn_text, key=f"toggle_{row['id']}"):
                    toggle_link_status(row['id'], row['is_active'])
                    st.rerun()
            st.divider()
    else:
        st.info("No links found in the database. Add one above.")

else:
    # --------------------------------------
    # GUEST VIEW
    # --------------------------------------
    st.title("🔗 Link Portal")
    st.write("Welcome! Here are the available resources.")
    
    active_links = get_active_links()
    
    if not active_links.empty:
        for index, row in active_links.iterrows():
            with st.container(border=True):
                st.subheader(row['title'])
                
                # Check if the link is password protected
                if row['password']:
                    st.warning("🔒 This link is password protected.")
                    # Use an expander for the password input to keep the UI clean
                    with st.expander("Unlock Link"):
                        pwd_input = st.text_input("Enter Password", type="password", key=f"pwd_{row['id']}")
                        if st.button("Unlock", key=f"btn_{row['id']}"):
                            if pwd_input == row['password']:
                                st.success("Access Granted!")
                                st.link_button(f"Go to {row['title']}", row['target_url'])
                            else:
                                st.error("Incorrect Password.")
                else:
                    # Public link, display directly
                    st.link_button(f"Go to {row['title']}", row['target_url'])
    else:
        st.info("No active links are currently available.")
