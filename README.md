## Drumlog – Your Practice Journal (Single‑User, Local)

Streamlit app to track your drum practice, now simplified for single-user local use on macOS.

### Features

- Input practice data: Date, Exercise/Song, Minutes, BPM, Notes
- Visualizations:
  - Practice time per day
  - BPM progress per exercise/song
  - Total time per exercise/song
- Import/Export your log as CSV

### Data storage

- Data is stored locally in `practice_log.csv` in the project directory.

### Install & Run (macOS)

1. Clone the repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate it: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start the app: `streamlit run app.py`

No login or user accounts are required.
