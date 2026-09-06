# CleanCity Copilot 

**AI-powered municipal complaint management system built for the Alibaba Cloud AI Hackathon 2026.**

CleanCity Copilot bridges the gap between citizens and municipal authorities by eliminating high-friction manual reporting. Our unified platform leverages Multimodal AI and Spatial-Temporal Geo-deduplication to automate civic issue triage.

### 🌟 Key Features
* **Built-in 3D Cyberpunk Web Dashboard:** A single unified interface for both citizens and municipal admins built entirely in Streamlit.
* **Multimodal AI Pipeline:** Powered by Gemini Vision LLM and Whisper STT for automated categorization, severity scoring, and repair plan generation.
* **Smart Geo-Deduplication:** Utilizes the Haversine formula (50m radius / 48hr window) to automatically merge duplicate citizen reports.
* **Automated Dispatch:** Unconditional email alert dispatch system to immediately notify relevant municipal committees.

### 📂 Repository Structure
This repository follows a clean separation of concerns:

1. **`/Backend`**: Contains the complete FastAPI engine, SQLite WAL database layer, AI stubs, and secure Admin endpoints. 
   * 👉 *[Click here to view detailed Backend Architecture & API Docs](Backend/README.md)*
2. **`/cleancity-frontend`**: Contains the Streamlit-based citizen portal and municipal admin dashboard.

---
*Developed with ❤️ for Alibaba Cloud AI Hackathon.*
