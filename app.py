import streamlit as st
import pandas as pd
import os
import subprocess
from datetime import date, datetime
import plotly.express as px
import time

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

def get_recent_exercises_with_bpm():
    """Get the last 10 unique exercises/songs with their most recent BPM from the log"""
    try:
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            if not df.empty and 'Exercise/Song' in df.columns and 'BPM' in df.columns:
                # Group by Exercise/Song and get the most recent entry for each
                recent_data = []
                for song in df['Exercise/Song'].dropna().unique():
                    song_entries = df[df['Exercise/Song'] == song].sort_values('Date', ascending=False)
                    if not song_entries.empty:
                        latest_entry = song_entries.iloc[0]
                        recent_data.append({
                            'song': song,
                            'bpm': latest_entry['BPM'] if pd.notna(latest_entry['BPM']) else 60
                        })
                
                # Sort by most recent (assuming Date is in chronological order)
                # Return the last 10 unique exercises with their BPM
                return recent_data[-10:]
        return []
    except Exception as e:
        print(f"Error getting recent exercises with BPM: {e}")
        return []

def safe_read_csv(file_path):
    """Safely read CSV file with error handling"""
    try:
        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        return pd.DataFrame()
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}")
        return pd.DataFrame()

def create_backup(file_path):
    """Create backup of data file before modifications"""
    try:
        if os.path.exists(file_path):
            import shutil
            backup_path = file_path + '.backup'
            shutil.copy2(file_path, backup_path)
            return True
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False

def format_time(seconds):
    """Format seconds into HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_time_minutes(seconds):
    """Format seconds into minutes only"""
    minutes = int(seconds // 60)
    return f"{minutes} min"

def round_to_minutes(seconds):
    """Round seconds to nearest minute, minimum 1 minute"""
    minutes = round(seconds / 60)
    return max(1, minutes)  # Ensure minimum of 1 minute

st.set_page_config(
    page_title="Drumlog - Your Practice Journal",
    page_icon="🥁",
    layout="wide"
)

# --- Single-user local setup ---
DATA_FILE = 'practice_log.csv'

st.title('🥁 Drumlog – Your Practice Journal')

# --- Timer Section ---
st.markdown("---")
st.caption("⏱️ Practice Timer")

# Initialize timer session state safely
st.session_state.setdefault('timer_running', False)
st.session_state.setdefault('timer_start_time', None)
st.session_state.setdefault('timer_elapsed', 0)

# Timer controls - compact layout
if not st.session_state.timer_running:
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button('▶️ Start', key='start_timer', use_container_width=True):
            st.session_state.timer_running = True
            st.session_state.timer_start_time = time.time()
            st.session_state.timer_elapsed = 0
            st.rerun()
    
    with col2:
        st.write("")  # Empty space for alignment
    
    with col3:
        if st.button('📝 Use', key='use_timer', use_container_width=True):
            if st.session_state.timer_elapsed > 0:
                st.session_state.timer_minutes = round_to_minutes(st.session_state.timer_elapsed)
                st.rerun()
            else:
                st.warning("No timer data to use")
else:
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button('⏸️ Stop', key='stop_timer', use_container_width=True):
            st.session_state.timer_running = False
            # Safe timer calculation to prevent negative values
            elapsed = max(0, time.time() - st.session_state.timer_start_time)
            st.session_state.timer_elapsed = elapsed
            st.rerun()
    
    with col2:
        st.write("")  # Empty space for alignment
    
    with col3:
        if st.button('📝 Use', key='use_timer_running', use_container_width=True):
            if st.session_state.timer_elapsed > 0:
                st.session_state.timer_minutes = round_to_minutes(st.session_state.timer_elapsed)
                st.rerun()
            else:
                st.warning("No timer data to use")

# Display timer (static, no auto-refresh to avoid app freezing)
if st.session_state.timer_running:
    st.metric("⏱️ Timer Running", "⏱️ Running...")
    st.caption("Timer is running - click 'Stop' when done")
elif st.session_state.timer_elapsed > 0:
    st.metric("⏱️ Timer Stopped", format_time_minutes(st.session_state.timer_elapsed))
    st.caption(f"📝 Click 'Use' to add {round_to_minutes(st.session_state.timer_elapsed)} minutes to your entry")
else:
    st.metric("⏱️ Timer", "Ready")
    st.caption("Click 'Start' to begin timing")

# --- Manual Entry Section ---
st.markdown("---")
st.subheader('✏️ Manual Entry')

# Get recent exercises with BPM and prepare song selection
recent_exercises_data = get_recent_exercises_with_bpm()

# Initialize session state for song input safely
st.session_state.setdefault('song_input', "")
st.session_state.setdefault('bpm_input', 60)

# Create options list with recent exercises
exercise_options = [item['song'] for item in recent_exercises_data]

# Show recent songs as clickable buttons (outside the form)
if recent_exercises_data:
    st.caption("Recent songs (click to select song and BPM):")
    cols = st.columns(min(3, len(recent_exercises_data)))
    for i, item in enumerate(recent_exercises_data):
        col_idx = i % 3
        with cols[col_idx]:
            song = item['song']
            bpm = item['bpm']
            button_text = f"{song} ({bpm} BPM)"
            if st.button(button_text, key=f"song_btn_{i}"):
                st.session_state.song_input = song
                st.session_state.bpm_input = bpm
                st.rerun()

# Formular zur Eingabe
with st.form('practice_form'):
    col1, col2 = st.columns(2)
    with col1:
        datum = st.date_input('Date', value=date.today())
        
        # Use text_input for song name (can be typed or selected from buttons above)
        uebung = st.text_input(
            'Exercise/Song',
            value=st.session_state.song_input,
            placeholder="Type song name or select from recent songs above",
            key='song_input',
            help="Type a new song name or click on a recent song above"
        )
        
        # Use timer minutes if available, otherwise default to 30
        default_minutes = st.session_state.get('timer_minutes', 30)
        # Ensure default_minutes is at least 1
        if default_minutes < 1:
            default_minutes = 30
        minuten = st.number_input('Minutes practiced', min_value=1, max_value=600, value=default_minutes)
    with col2:
        # Validate BPM input with better error handling
        bpm = st.number_input('Tempo (BPM)', min_value=20, max_value=400, value=st.session_state.bpm_input, help="Enter tempo between 20-400 BPM")
        notizen = st.text_area('Notes (optional)', placeholder="How did it go? Difficulties?")
    abgeschickt = st.form_submit_button('💾 Save')

# Daten speichern
if abgeschickt and uebung.strip():
    try:
        # Security: Sanitize input data
        sanitized_uebung = uebung.strip()[:100]  # Limit length
        sanitized_notizen = notizen.strip()[:500] if notizen else ''  # Limit length
        
        # Validate numeric inputs
        if not isinstance(minuten, (int, float)) or minuten < 1:
            st.error('❌ Invalid minutes value. Please enter a valid number.')
        elif not isinstance(bpm, (int, float)) or bpm < 20 or bpm > 400:
            st.error('❌ Invalid BPM value. Please enter a value between 20-400.')
        else:
            # Create backup before saving
            create_backup(DATA_FILE)
            
            # Use safe CSV reading
            df = safe_read_csv(DATA_FILE)
            
            # Check if this song already exists and update BPM if different
            existing_songs = df['Exercise/Song'].dropna().unique() if not df.empty else []
            if sanitized_uebung in existing_songs:
                # Get the most recent BPM for this song
                song_entries = df[df['Exercise/Song'] == sanitized_uebung]
                if not song_entries.empty:
                    last_bpm = song_entries.iloc[-1]['BPM']
                    if last_bpm != bpm:
                        st.info(f"🎵 Updated BPM for '{sanitized_uebung}' from {last_bpm} to {bpm}")
            
            new_entry = pd.DataFrame([{
                'Date': datum,
                'Exercise/Song': sanitized_uebung,
                'Minutes': minuten,
                'BPM': bpm,
                'Notes': sanitized_notizen
            }])
            
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success('✅ Entry saved successfully!')
    except Exception as e:
        # Security: Don't expose detailed error messages
        st.error('❌ Error saving entry. Please try again.')
        print(f"Error saving entry: {str(e)}")  # Log for debugging
elif abgeschickt:
    st.warning('⚠️ Please enter an exercise/song!')

# Daten laden und anzeigen
df = safe_read_csv(DATA_FILE)

if not df.empty:
    # Validiere die Spaltenstruktur
    required_columns = ['Date', 'Exercise/Song', 'Minutes', 'BPM', 'Notes']
    if not all(col in df.columns for col in required_columns):
        st.error('❌ The uploaded CSV file does not have the expected format. Please use a file with the columns: Date, Exercise/Song, Minutes, BPM, Notes')
        st.stop()
    
    # Validiere Datentypen
    try:
        df['Minutes'] = pd.to_numeric(df['Minutes'], errors='coerce')
        df['BPM'] = pd.to_numeric(df['BPM'], errors='coerce')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Entferne nur Zeilen wo ALLE kritischen Spalten fehlen (nicht einzelne)
        df = df.dropna(subset=['Date', 'Minutes', 'BPM'], how='all')
        
        if df.empty:
            st.warning('⚠️ No valid data after cleanup.')
            st.stop()
            
    except Exception as e:
        st.error('❌ Error validating data. Please check your data format.')
        print(f"Error validating data: {str(e)}")  # Log for debugging
        st.stop()
    
    # Display metrics and data
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
                        
                        # Create backup before replacing data
                        create_backup(DATA_FILE)
                        
                        # Ersetze die vorhandene Datei komplett
                        uploaded_df.to_csv(DATA_FILE, index=False)
                        st.success('✅ File uploaded and data replaced successfully!')
                        st.info('💡 Click on "Update data" to see the new data.')
            except Exception as e:
                st.error('❌ Error uploading file. Please check the file format.')
                print(f"Error uploading file: {str(e)}")  # Log for debugging

    st.markdown("")  # Abstand
    
    # Aktualisieren-Button
    if st.button('🔄 Update data'):
        st.rerun()

# End of app
