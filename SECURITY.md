## Security Notes (Single‑User Local)

This project is now single-user and local-only. The following still apply:

- File upload validation: CSV type, 10MB size limit, and row-cap limits to avoid resource exhaustion
- Input sanitization: text length limits to reduce risk of malformed data in the CSV
- Generic error messages in UI; detailed messages printed to console for local debugging

No authentication, sessions, or multi-user access are present anymore. Data is stored locally in `practice_log.csv`.
