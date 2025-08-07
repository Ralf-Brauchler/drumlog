import streamlit as st
import pandas as pd
import os
from datetime import date
import plotly.express as px

# Konfiguration für bessere Performance
st.set_page_config(
    page_title="Drumlog - Dein Übungstagebuch",
    page_icon="🥁",
    layout="wide"
)

DATA_FILE = 'practice_log.csv'

st.title('🥁 Drumlog – Dein Übungstagebuch')

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
if abgeschickt and uebung.strip():  # Prüfe, ob Übung eingegeben wurde
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
        
        if not df.empty:
            # Zusammenfassung
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Gesamtübungszeit", f"{df['Minuten'].sum()} Min")
            with col2:
                st.metric("Anzahl Einträge", len(df))
            with col3:
                st.metric("Durchschnitt BPM", f"{df['BPM'].mean():.0f}")
            
            st.subheader('📊 Deine bisherigen Einträge')
            st.dataframe(df, use_container_width=True)

            # Diagramme
            df['Datum'] = pd.to_datetime(df['Datum'])
            
            # Diagramm 1: Übungszeit pro Tag
            st.subheader('📈 Übungszeit pro Tag')
            zeit_pro_tag = df.groupby('Datum')['Minuten'].sum().reset_index()
            fig1 = px.bar(zeit_pro_tag, x='Datum', y='Minuten', 
                          labels={'Minuten': 'Minuten', 'Datum': 'Datum'},
                          color_discrete_sequence=['#FF6B6B'])
            fig1.update_layout(showlegend=False)
            st.plotly_chart(fig1, use_container_width=True)

            # Diagramm 2: BPM-Fortschritt pro Übung/Song
            st.subheader('🎵 BPM-Fortschritt pro Übung/Song')
            if len(df['Übung/Song'].unique()) > 0:
                fig2 = px.line(df, x='Datum', y='BPM', color='Übung/Song', 
                              markers=True, labels={'BPM': 'Tempo (BPM)', 'Datum': 'Datum', 'Übung/Song': 'Übung/Song'})
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info('Noch keine BPM-Daten vorhanden.')

            # Diagramm 3: Gesamtzeit pro Übung/Song
            st.subheader('⏱️ Gesamtzeit pro Übung/Song')
            zeit_pro_uebung = df.groupby('Übung/Song')['Minuten'].sum().reset_index()
            fig3 = px.bar(zeit_pro_uebung, x='Übung/Song', y='Minuten', 
                          labels={'Minuten': 'Minuten', 'Übung/Song': 'Übung/Song'},
                          color_discrete_sequence=['#4ECDC4'])
            fig3.update_layout(showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info('📝 Noch keine Einträge vorhanden. Trage deine erste Übung ein!')
            
    except Exception as e:
        st.error(f'❌ Fehler beim Laden der Daten: {str(e)}')
else:
    st.info('📝 Noch keine Einträge vorhanden. Trage deine erste Übung ein!')
