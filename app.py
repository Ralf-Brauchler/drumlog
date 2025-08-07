import streamlit as st
import pandas as pd
import os
from datetime import date
import plotly.express as px

# Benutzerdaten importieren
try:
    # Versuche zuerst Streamlit Secrets (für Cloud-Deployment)
    if hasattr(st, 'secrets') and 'users' in st.secrets:
        USERS = dict(st.secrets.users)
    else:
        # Fallback: Lokale users.py Datei
        from users import USERS
except ImportError:
    # Fallback für den Fall, dass users.py nicht existiert
    USERS = {
        "demo": "demo123"
    }

st.set_page_config(
    page_title="Drumlog - Dein Übungstagebuch",
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
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Willkommen, {username}!")
                st.stop()  # Stoppt die Ausführung nach Login
            else:
                st.error("Falscher Benutzername oder Passwort.")

if not st.session_state.logged_in:
    login_form()
    st.stop()

# --- Nach Login: Benutzername holen und benutzerspezifische Datei setzen ---
username = st.session_state.username
DATA_FILE = f'practice_log_{username}.csv'

st.title(f'🥁 Drumlog – Dein Übungstagebuch ({username})')

# Formular zur Eingabe
with st.form('practice_form'):
    col1, col2 = st.columns(2)
    with col1:
        datum = st.date_input('Datum', value=date.today())
        uebung = st.text_input('Übung/Song', placeholder="z.B. Basic Beat, We Will Rock You")
        minuten = st.number_input('Minuten geübt', min_value=1, max_value=600, value=30)
    with col2:
        bpm = st.number_input('Tempo (BPM)', min_value=20, max_value=400, value=60)
        notizen = st.text_area('Notizen (optional)', placeholder="Wie lief es? Schwierigkeiten?")
    abgeschickt = st.form_submit_button('💾 Speichern')

# Daten speichern
if abgeschickt and uebung.strip():
    try:
        new_entry = pd.DataFrame([{
            'Datum': datum,
            'Übung/Song': uebung.strip(),
            'Minuten': minuten,
            'BPM': bpm,
            'Notizen': notizen.strip() if notizen else ''
        }])
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            df = pd.concat([df, new_entry], ignore_index=True)
        else:
            df = new_entry
        df.to_csv(DATA_FILE, index=False)
        st.success('✅ Eintrag erfolgreich gespeichert!')
    except Exception as e:
        st.error(f'❌ Fehler beim Speichern: {str(e)}')
elif abgeschickt:
    st.warning('⚠️ Bitte gib eine Übung/Song ein!')

# Daten laden und anzeigen
if os.path.exists(DATA_FILE):
    try:
        df = pd.read_csv(DATA_FILE)
        
        # Validiere die Spaltenstruktur
        required_columns = ['Datum', 'Übung/Song', 'Minuten', 'BPM', 'Notizen']
        if not all(col in df.columns for col in required_columns):
            st.error('❌ Die hochgeladene CSV-Datei hat nicht das erwartete Format. Bitte verwende eine Datei mit den Spalten: Datum, Übung/Song, Minuten, BPM, Notizen')
            st.stop()
        
        if not df.empty:
            # Validiere Datentypen
            try:
                df['Minuten'] = pd.to_numeric(df['Minuten'], errors='coerce')
                df['BPM'] = pd.to_numeric(df['BPM'], errors='coerce')
                df['Datum'] = pd.to_datetime(df['Datum'], errors='coerce')
                
                # Entferne Zeilen mit ungültigen Daten
                df = df.dropna(subset=['Datum', 'Minuten', 'BPM'])
                
                if df.empty:
                    st.warning('⚠️ Nach der Bereinigung sind keine gültigen Daten vorhanden.')
                    st.stop()
                    
            except Exception as e:
                st.error(f'❌ Fehler beim Validieren der Daten: {str(e)}')
                st.stop()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gesamtübungszeit", f"{df['Minuten'].sum():.0f} Min")
            with col2:
                st.metric("Anzahl Einträge", len(df))
            with col3:
                st.metric("Durchschnitt BPM", f"{df['BPM'].mean():.0f}")
            
            st.subheader('📊 Deine bisherigen Einträge')
            st.dataframe(df, use_container_width=True)
            
            # Diagramme nur anzeigen, wenn genügend Daten vorhanden sind
            if len(df) > 0:
                st.subheader('📈 Übungszeit pro Tag')
                zeit_pro_tag = df.groupby('Datum')['Minuten'].sum().reset_index()
                if not zeit_pro_tag.empty:
                    fig1 = px.bar(zeit_pro_tag, x='Datum', y='Minuten', 
                                  labels={'Minuten': 'Minuten', 'Datum': 'Datum'},
                                  color_discrete_sequence=['#FF6B6B'])
                    fig1.update_layout(showlegend=False)
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info('Keine Daten für Diagramm verfügbar.')
                
                st.subheader('🎵 BPM-Fortschritt pro Übung/Song')
                if len(df['Übung/Song'].unique()) > 0:
                    fig2 = px.line(df, x='Datum', y='BPM', color='Übung/Song', 
                                  markers=True, labels={'BPM': 'Tempo (BPM)', 'Datum': 'Datum', 'Übung/Song': 'Übung/Song'})
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info('Noch keine BPM-Daten vorhanden.')
                
                st.subheader('⏱️ Gesamtzeit pro Übung/Song')
                zeit_pro_uebung = df.groupby('Übung/Song')['Minuten'].sum().reset_index()
                if not zeit_pro_uebung.empty:
                    fig3 = px.bar(zeit_pro_uebung, x='Übung/Song', y='Minuten', 
                                  labels={'Minuten': 'Minuten', 'Übung/Song': 'Übung/Song'},
                                  color_discrete_sequence=['#4ECDC4'])
                    fig3.update_layout(showlegend=False)
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info('Keine Daten für Diagramm verfügbar.')
            else:
                st.info('📝 Keine gültigen Einträge vorhanden.')
        else:
            st.info('📝 Noch keine Einträge vorhanden. Trage deine erste Übung ein!')
    except Exception as e:
        st.error(f'❌ Fehler beim Laden der Daten: {str(e)}')
        st.info('💡 Tipp: Falls du eine CSV-Datei hochgeladen hast, stelle sicher, dass sie das richtige Format hat.')
else:
    st.info('📝 Noch keine Einträge vorhanden. Trage deine erste Übung ein!')

# --- Daten-Management Bereich ---
st.markdown("---")
st.subheader('📁 Daten-Management')

# Container für bessere Kontrolle
with st.container():
    # Export
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'rb') as f:
            st.download_button(
                label='📥 Practice-Log herunterladen',
                data=f,
                file_name=DATA_FILE,
                mime='text/csv'
            )
    else:
        st.info('Noch keine Daten zum Download vorhanden.')

    st.markdown("")  # Abstand
    
    # Import - als Button statt File-Uploader
    if st.button('📤 Practice-Log hochladen'):
        uploaded_file = st.file_uploader('CSV-Datei auswählen', type='csv', key='upload_csv', label_visibility='collapsed')
        if uploaded_file is not None:
            try:
                with open(DATA_FILE, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                st.success('✅ Datei erfolgreich hochgeladen!')
                st.info('💡 Klicke auf "Daten aktualisieren" um die neuen Daten anzuzeigen.')
            except Exception as e:
                st.error(f'❌ Fehler beim Hochladen: {str(e)}')

    st.markdown("")  # Abstand
    
    # Aktualisieren-Button
    if st.button('🔄 Daten aktualisieren'):
        st.rerun()

# --- Logout Bereich ---
st.markdown("---")
if st.button('🚪 Logout'):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()
