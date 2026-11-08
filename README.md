# ImplantLab — Admin-enabled learning app

## Run locally (Windows)
1. Extract this ZIP into a folder.
2. Open Command Prompt in that folder.
3. Run `py -m pip install -r requirements.txt`
4. Run `py -m streamlit run app.py`
5. Open the Local URL printed in the terminal (usually http://localhost:8501).

## Admin access
Open the **Admin access** section in the sidebar.
Default local admin password: `sarahadmin2026`

For a custom password, create `.streamlit/secrets.toml`:
```toml
admin_password = "your-own-password"
```
Or set the `IMPLANTLAB_ADMIN_PASSWORD` environment variable.

## What changed in this build
- All six modules and the Research Sandbox are available from the beginning; no sequential locks.
- Retains the admin panel and local session scoring controls.
- Removed rendered Python code blocks and code-display expanders.
- Removed live code editors and terminal execution; scored learning is only MCQs and short code-snippet fill-in-the-blanks.
- Removed repeated question prompts and repeated type/logic checks.
- Retains Sarah, score tracking, progress display and the dark blue/cyan UI.

## Data disclaimer
All datasets, experimental outcomes, reference values and process windows shown in ImplantLab are fictional demonstrations created for Python-learning purposes. They are not actual experimental results, validated specifications, clinical evidence or manufacturing instructions.

## Notes
This starter build stores progress in the current Streamlit session. It does not include persistent student accounts or a shared multi-user database.
