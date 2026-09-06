# CleanCity Copilot — Frontend (Streamlit)

Frontend for Alibaba Cloud AI Hackathon 2026 project. Two views, as per the
spec: **Citizen Portal** and **Municipal Admin Dashboard**.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

- `app.py` → Citizen Portal (home page)
- `pages/1_📊_Admin_Dashboard.py` → Admin Dashboard (auto-appears in sidebar nav)

## Current state

The whole UI works standalone right now with **mock data** (`utils/mock_data.py`) —
no backend needed to demo it. `utils/api_client.py` already calls the real
endpoints first and only falls back to mock data if the backend isn't reachable.

## Connecting to Latif's backend

Once the FastAPI server is running, just point the frontend at it:

```bash
export CLEANCITY_BACKEND_URL="http://<latif-backend-host>:8000"
streamlit run app.py
```

No other code changes needed — `api_client.py` already implements the 3 endpoints
from the spec:
- `POST /api/submit-report` (multipart: image, audio, lat, lng, address)
- `GET /api/tickets` (filters: status, category)
- `PATCH /api/update-status/{ticket_id}`

If the response shape from the real backend differs even slightly from
`mock_data.py`'s ticket dict (keys: `ticket_id`, `category`, `severity`,
`status`, `location_name`, `lat`, `lng`, `created_at`, `reasoning`,
`recommended_action`, `transcribed_note`, `duplicate_count`, `image_url`),
tell Latif to match it, or adjust the dashboard's column mapping.

## TODO / things to wire up before the demo

- [ ] **GPS "Use current location" button** — needs a small JS component
  (e.g. `streamlit-geolocation` or `streamlit-js-eval`) to read browser
  geolocation. Currently shows a message asking for manual address entry.
- [ ] **Image display in Admin Dashboard detail view** — waiting on backend
  to return `image_url` per ticket (or a way to fetch the uploaded file).
- [ ] Swap in real severity colors / branding once team agrees on final palette.
- [ ] Add basic auth / login gate on the Admin Dashboard before demo day.
