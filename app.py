import streamlit as st
import pandas as pd
import os
from datetime import date
import plotly.express as px

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
            # Fallback für den Fall, dass users.py nicht existiert
            USERS = {
                "demo": "demo123"
            }
            print("Using fallback demo user")
except Exception as e:
    print(f"Error loading users: {e}")
    # Final fallback
    USERS = {
        "demo": "demo123"
    }
    print("Using final fallback demo user")

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

# --- Login-Formular ---
def login_form():
    st.title("🥁 Drumlog Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome, {username}!")
                st.stop()  # Stoppt die Ausführung nach Login
            else:
                st.error("Wrong username or password.")
    
    # Hinweis für den Benutzer
    st.info("💡 If login doesn't work, try clicking again.")

if not st.session_state.logged_in:
    login_form()
    st.stop()

# --- Nach Login: Benutzername holen und benutzerspezifische Datei setzen ---
username = st.session_state.username
DATA_FILE = f'practice_log_{username}.csv'

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
        new_entry = pd.DataFrame([{
            'Date': datum,
            'Exercise/Song': uebung.strip(),
            'Minutes': minuten,
            'BPM': bpm,
            'Notes': notizen.strip() if notizen else ''
        }])
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            df = pd.concat([df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_csv(DATA_FILE, index=False)
        st.success('✅ Entry saved successfully!')
    except Exception as e:
        st.error(f'❌ Error saving entry: {str(e)}')
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
                st.error(f'❌ Error validating data: {str(e)}')
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
        st.error(f'❌ Error loading data: {str(e)}')
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
                file_name=DATA_FILE,
                mime='text/csv'
            )
    else:
        st.info('No data available for download.')

    st.markdown("")  # Abstand
    
    # Import - einfacher File-Uploader
    uploaded_file = st.file_uploader('📤 Upload practice log', type='csv', key='upload_csv')
    if uploaded_file is not None:
        try:
            # Lese die hochgeladene Datei
            uploaded_df = pd.read_csv(uploaded_file)
            
            # Validiere die Spaltenstruktur
            required_columns = ['Date', 'Exercise/Song', 'Minutes', 'BPM', 'Notes']
            if not all(col in uploaded_df.columns for col in required_columns):
                st.error('❌ The uploaded CSV file does not have the expected format. Please use a file with the columns: Date, Exercise/Song, Minutes, BPM, Notes')
            else:
                # Ersetze die vorhandene Datei komplett
                uploaded_df.to_csv(DATA_FILE, index=False)
                st.success('✅ File uploaded and data replaced successfully!')
                st.info('💡 Click on "Update data" to see the new data.')
                # Kein st.rerun() mehr - die App lädt die neuen Daten beim nächsten natürlichen Reload
        except Exception as e:
            st.error(f'❌ Error uploading file: {str(e)}')

    st.markdown("")  # Abstand
    
    # Aktualisieren-Button
    if st.button('🔄 Update data'):
        st.rerun()

# --- Logout Bereich ---
st.markdown("---")
if st.button('🚪 Logout'):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()
