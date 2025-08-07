import streamlit as st
import pandas as pd
import os
import re
import hashlib
import secrets
from datetime import date
import plotly.express as px

# Security: Path sanitization function
def sanitize_filename(filename):
    """Sanitize filename to prevent path traversal attacks"""
    # Remove any path separators and dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Limit length and ensure it's not empty
    sanitized = sanitized[:50] if sanitized else 'user'
    return sanitized

# Security: Password hashing
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Security: File size validation
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

def validate_csv_file(uploaded_file):
    """Validate uploaded CSV file for security"""
    if uploaded_file is None:
        return False, "No file uploaded"
    
    # Check file size
    if uploaded_file.size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # Check file type (basic check)
    if not uploaded_file.name.lower().endswith('.csv'):
        return False, "File must be a CSV file"
    
    return True, "File is valid"

# Benutzerdaten importieren
USERS = {}
try:
    # Versuche zuerst Streamlit Secrets (für Cloud-Deployment)
    if hasattr(st, 'secrets') and 'users' in st.secrets:
        USERS = dict(st.secrets.users)
        print("Loaded users from Streamlit secrets")
    else:
        # Fallback: Lokale users.py Datei
        try:
            from users import USERS
            print("Loaded users from users.py")
        except ImportError as e:
            print(f"Could not import users.py: {e}")
            # No fallback for security reasons
            USERS = {}
            print("No users available - please create users.py file")
except Exception as e:
    print(f"Error loading users: {e}")
    # No fallback for security reasons
    USERS = {}
    print("No users available due to error - please check configuration")

st.set_page_config(
    page_title="Drumlog - Your Practice Journal",
    page_icon="🥁",
    layout="wide"
)

# --- Session-State Initialisierung ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "session_token" not in st.session_state:
    st.session_state.session_token = ""

# Security: Generate session token
def generate_session_token():
    return secrets.token_urlsafe(32)

# --- Login-Formular ---
def login_form():
    st.title("🥁 Drumlog Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            # Security: Sanitize username
            sanitized_username = sanitize_filename(username)
            if sanitized_username != username:
                st.error("Invalid username format.")
                return
            
            # Security: Hash password for comparison
            hashed_password = hash_password(password)
            
            if username in USERS and USERS[username] == hashed_password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.session_token = generate_session_token()
                st.success(f"Welcome, {username}!")
                st.stop()  # Stoppt die Ausführung nach Login
            else:
                st.error("Wrong username or password.")
    
    # Hinweis für den Benutzer
    st.info("💡 If login doesn't work, try clicking again.")

if not st.session_state.logged_in:
    login_form()
    st.stop()

# Security: Validate session token
if not st.session_state.session_token:
    st.error("Invalid session. Please login again.")
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

# --- Nach Login: Benutzername holen und benutzerspezifische Datei setzen ---
username = st.session_state.username
# Security: Sanitize filename to prevent path traversal
safe_username = sanitize_filename(username)
DATA_FILE = f'practice_log_{safe_username}.csv'

st.title(f'🥁 Drumlog – Your Practice Journal ({username})')

# Formular zur Eingabe
with st.form('practice_form'):
    col1, col2 = st.columns(2)
    with col1:
        datum = st.date_input('Date', value=date.today())
        uebung = st.text_input('Exercise/Song', placeholder="e.g. Basic Beat, We Will Rock You")
        minuten = st.number_input('Minutes practiced', min_value=1, max_value=600, value=30)
    with col2:
        bpm = st.number_input('Tempo (BPM)', min_value=20, max_value=400, value=60)
        notizen = st.text_area('Notes (optional)', placeholder="How did it go? Difficulties?")
    abgeschickt = st.form_submit_button('💾 Save')

# Daten speichern
if abgeschickt and uebung.strip():
    try:
        # Security: Sanitize input data
        sanitized_uebung = uebung.strip()[:100]  # Limit length
        sanitized_notizen = notizen.strip()[:500] if notizen else ''  # Limit length
        
        new_entry = pd.DataFrame([{
            'Date': datum,
            'Exercise/Song': sanitized_uebung,
            'Minutes': minuten,
            'BPM': bpm,
            'Notes': sanitized_notizen
        }])
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            df = pd.concat([df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_csv(DATA_FILE, index=False)
        st.success('✅ Entry saved successfully!')
    except Exception as e:
        # Security: Don't expose detailed error messages
        st.error('❌ Error saving entry. Please try again.')
        print(f"Error saving entry: {str(e)}")  # Log for debugging
elif abgeschickt:
    st.warning('⚠️ Please enter an exercise/song!')

# Daten laden und anzeigen
if os.path.exists(DATA_FILE):
    try:
        df = pd.read_csv(DATA_FILE)
        
        # Validiere die Spaltenstruktur
        required_columns = ['Date', 'Exercise/Song', 'Minutes', 'BPM', 'Notes']
        if not all(col in df.columns for col in required_columns):
            st.error('❌ The uploaded CSV file does not have the expected format. Please use a file with the columns: Date, Exercise/Song, Minutes, BPM, Notes')
            st.stop()
        
        if not df.empty:
            # Validiere Datentypen
            try:
                df['Minutes'] = pd.to_numeric(df['Minutes'], errors='coerce')
                df['BPM'] = pd.to_numeric(df['BPM'], errors='coerce')
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                
                # Entferne Zeilen mit ungültigen Daten
                df = df.dropna(subset=['Date', 'Minutes', 'BPM'])
                
                if df.empty:
                    st.warning('⚠️ No valid data after cleanup.')
                    st.stop()
                    
            except Exception as e:
                st.error('❌ Error validating data. Please check your data format.')
                print(f"Error validating data: {str(e)}")  # Log for debugging
                st.stop()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total practice time", f"{df['Minutes'].sum():.0f} Min")
            with col2:
                st.metric("Number of entries", len(df))
            with col3:
                st.metric("Average BPM", f"{df['BPM'].mean():.0f}")
            
            st.subheader('📊 Your previous entries')
            st.dataframe(df, use_container_width=True)
            
            # Diagramme nur anzeigen, wenn genügend Daten vorhanden sind
            if len(df) > 0:
                st.subheader('📈 Practice time per day')
                zeit_pro_tag = df.groupby('Date')['Minutes'].sum().reset_index()
                if not zeit_pro_tag.empty:
                    fig1 = px.bar(zeit_pro_tag, x='Date', y='Minutes', 
                                  labels={'Minutes': 'Minutes', 'Date': 'Date'},
                                  color_discrete_sequence=['#FF6B6B'])
                    fig1.update_layout(showlegend=False)
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info('No data available for chart.')
                
                st.subheader('🎵 BPM progress per exercise/song')
                if len(df['Exercise/Song'].unique()) > 0:
                    fig2 = px.line(df, x='Date', y='BPM', color='Exercise/Song', 
                                  markers=True, labels={'BPM': 'Tempo (BPM)', 'Date': 'Date', 'Exercise/Song': 'Exercise/Song'})
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info('No BPM data yet.')
                
                st.subheader('⏱️ Total time per exercise/song')
                zeit_pro_uebung = df.groupby('Exercise/Song')['Minutes'].sum().reset_index()
                if not zeit_pro_uebung.empty:
                    fig3 = px.bar(zeit_pro_uebung, x='Exercise/Song', y='Minutes', 
                                  labels={'Minutes': 'Minutes', 'Exercise/Song': 'Exercise/Song'},
                                  color_discrete_sequence=['#4ECDC4'])
                    fig3.update_layout(showlegend=False)
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info('No data available for chart.')
            else:
                st.info('📝 No valid entries available.')
        else:
            st.info('📝 No entries yet. Add your first practice!')
    except Exception as e:
        st.error('❌ Error loading data. Please try again.')
        print(f"Error loading data: {str(e)}")  # Log for debugging
        st.info('💡 Tip: If you uploaded a CSV file, make sure it has the correct format.')
else:
    st.info('📝 No entries yet. Add your first practice!')

# --- Daten-Management Bereich ---
st.markdown("---")
st.subheader('📁 Data Management')

# Container für bessere Kontrolle
with st.container():
    # Export
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'rb') as f:
            st.download_button(
                label='📥 Download practice log',
                data=f,
                file_name=f'practice_log_{safe_username}.csv',  # Security: Use sanitized filename
                mime='text/csv'
            )
    else:
        st.info('No data available for download.')

    st.markdown("")  # Abstand
    
    # Import - einfacher File-Uploader
    uploaded_file = st.file_uploader('📤 Upload practice log', type='csv', key='upload_csv')
    if uploaded_file is not None:
        # Security: Validate uploaded file
        is_valid, error_message = validate_csv_file(uploaded_file)
        if not is_valid:
            st.error(f'❌ {error_message}')
        else:
            try:
                # Lese die hochgeladene Datei
                uploaded_df = pd.read_csv(uploaded_file)
                
                # Security: Limit number of rows to prevent DoS
                if len(uploaded_df) > 10000:
                    st.error('❌ File too large. Maximum 10,000 rows allowed.')
                else:
                    # Validiere die Spaltenstruktur
                    required_columns = ['Date', 'Exercise/Song', 'Minutes', 'BPM', 'Notes']
                    if not all(col in uploaded_df.columns for col in required_columns):
                        st.error('❌ The uploaded CSV file does not have the expected format. Please use a file with the columns: Date, Exercise/Song, Minutes, BPM, Notes')
                    else:
                        # Security: Sanitize data before saving
                        for col in ['Exercise/Song', 'Notes']:
                            if col in uploaded_df.columns:
                                uploaded_df[col] = uploaded_df[col].astype(str).str[:100]  # Limit length
                        
                        # Ersetze die vorhandene Datei komplett
                        uploaded_df.to_csv(DATA_FILE, index=False)
                        st.success('✅ File uploaded and data replaced successfully!')
                        st.info('💡 Click on "Update data" to see the new data.')
                        # Kein st.rerun() mehr - die App lädt die neuen Daten beim nächsten natürlichen Reload
            except Exception as e:
                st.error('❌ Error uploading file. Please check the file format.')
                print(f"Error uploading file: {str(e)}")  # Log for debugging

    st.markdown("")  # Abstand
    
    # Aktualisieren-Button
    if st.button('🔄 Update data'):
        st.rerun()

# --- Logout Bereich ---
st.markdown("---")
if st.button('🚪 Logout'):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.session_token = ""
    st.rerun()
