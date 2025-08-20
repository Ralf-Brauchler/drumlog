import streamlit as st
import pandas as pd
import os
import subprocess
import json
from datetime import date, datetime
import plotly.express as px

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

def get_logic_pro_info():
    """Get current Logic Pro project info using AppleScript"""
    try:
        # AppleScript to get Logic Pro info
        script = '''
        tell application "System Events"
            if not (exists process "Logic Pro X") and not (exists process "Logic Pro") then
                return "not_running"
            end if
        end tell
        
        tell application "Logic Pro X"
            try
                set projectName to name of front document
                set projectTempo to tempo of front document
                return projectName & "|" & (projectTempo as string)
            on error
                return "no_project"
            end try
        end tell
        '''
        
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if output == "not_running":
                return {"status": "not_running", "message": "Logic Pro is not running"}
            elif output == "no_project":
                return {"status": "no_project", "message": "No Logic Pro project is open"}
            else:
                # Parse project name and tempo
                parts = output.split("|")
                if len(parts) == 2:
                    project_name = parts[0].strip()
                    try:
                        tempo = float(parts[1])
                        return {
                            "status": "success",
                            "project_name": project_name,
                            "tempo": tempo
                        }
                    except ValueError:
                        return {"status": "error", "message": "Could not parse tempo"}
                else:
                    return {"status": "error", "message": "Unexpected response format"}
        else:
            return {"status": "error", "message": f"AppleScript error: {result.stderr}"}
            
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Logic Pro took too long to respond"}
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}

def auto_log_logic_session():
    """Automatically log current Logic Pro session"""
    info = get_logic_pro_info()
    
    if info["status"] == "success":
        # Create entry with current Logic Pro info
        new_entry = pd.DataFrame([{
            'Date': date.today(),
            'Exercise/Song': info["project_name"],
            'Minutes': 30,  # Default 30 minutes - user can adjust
            'BPM': int(info["tempo"]),
            'Notes': f"Auto-logged from Logic Pro session"
        }])
        
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            df = pd.concat([df, new_entry], ignore_index=True)
        else:
            df = new_entry
            
        df.to_csv(DATA_FILE, index=False)
        return True, f"✅ Auto-logged: {info['project_name']} at {int(info['tempo'])} BPM"
    else:
        return False, f"❌ {info['message']}"

st.set_page_config(
    page_title="Drumlog - Your Practice Journal",
    page_icon="🥁",
    layout="wide"
)

# --- Single-user local setup ---
DATA_FILE = 'practice_log.csv'

st.title('🥁 Drumlog – Your Practice Journal')

# --- Logic Pro Auto-Logging Section ---
st.markdown("---")
st.subheader('🎹 Logic Pro Auto-Logging')

# Check Logic Pro status
logic_info = get_logic_pro_info()

if logic_info["status"] == "success":
    st.success(f"🎵 **Logic Pro detected!**")
    st.info(f"**Current project:** {logic_info['project_name']} | **Tempo:** {int(logic_info['tempo'])} BPM")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button('📝 Auto-Log Current Session', type='primary'):
            success, message = auto_log_logic_session()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        st.info("💡 Click to automatically log your current Logic Pro session with today's date and 30 minutes practice time.")
        
elif logic_info["status"] == "not_running":
    st.warning("⚠️ **Logic Pro is not running**")
    st.info("Start Logic Pro and open a project to use auto-logging.")
    
elif logic_info["status"] == "no_project":
    st.warning("⚠️ **No Logic Pro project is open**")
    st.info("Open a project in Logic Pro to use auto-logging.")
    
else:
    st.error(f"❌ **Error:** {logic_info['message']}")

# --- Manual Entry Section ---
st.markdown("---")
st.subheader('✏️ Manual Entry')

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
                file_name='practice_log.csv',
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

# End of app
