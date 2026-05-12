# Nistula Guest Message Handler & Messaging Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Claude AI](https://img.shields.io/badge/Claude%20AI-D97757?style=for-the-badge&logo=anthropic)](https://www.anthropic.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql)](https://www.postgresql.org)

A robust, AI-powered guest communication handler designed for **Nistula**, a premium villa management company. This system normalizes inbound messages from multiple channels, classifies guest intent, and drafts context-aware replies using LLMs.

---

## 🏛️ Architecture Overview

The system is built on a **Modular Service Architecture**:

1.  **Webhook Gateway**: A FastAPI-based endpoint that receives and validates payloads using Pydantic.
2.  **Normalization Layer**: Maps multi-channel data (WhatsApp, Airbnb, Booking.com) into a unified internal schema.
3.  **Intelligence Engine**: Intelligence Engine: Integrates with Claude Sonnet 4 (`claude-sonnet-4-20250514`) to process guest intent against property-specific context.
4.  **Action Orchestrator**: Determines the message lifecycle (`auto_send`, `agent_review`, or `escalate`) based on confidence thresholds and intent classification.

---

## 📂 Repository Structure

```text
src/
├── main.py
├── models.py
├── services.py
├── classifier.py

schema.sql
thinking.md
README.md
test_webhook.py
```
## 🌐 Live Deployment

Base URL:
https://nistula-api.onrender.com

Swagger API Docs:
https://nistula-api.onrender.com/docs

Health Endpoint:
https://nistula-api.onrender.com/health

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- An Anthropic (Claude) API Key

### Installation

1.  **Clone and Setup**:
    ```bash
    git clone https://github.com/yourusername/nistula-technical-assessment
    cd nistula-technical-assessment
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Configuration**:
    Create a `.env` file in the root directory:
    ```env
    CLAUDE_API_KEY=your_actual_key_here
    MODEL_NAME=claude-sonnet-4-20250514
    ```

### Running the System

Start the development server:
```bash
python -m uvicorn src.main:app --reload
```

Run the validation suite:
```bash
python test_webhook.py
```

---

## 🧠 Intelligence Design: Confidence & Actions

We employ a "Human-in-the-Loop" (HITL) strategy to ensure brand safety while maintaining high response speeds.

### Confidence Scoring Model
- **90% - 100%**: High-fidelity matches. The query is explicitly answered by the property factsheet (e.g., WiFi password, standard check-in time).
- **75% - 89%**: High-probability inference. Requires basic calculation or standard policy application (e.g., pricing for extra guests).
- **55% - 74%**: Ambiguous intent or sensitive topic (Complaints). These require caution.
- **< 55%**: Critical failure or unknown territory.

### Action Mapping
| Intent | Confidence | Action | Outcome |
| :--- | :--- | :--- | :--- |
| **Inquiry** | > 85% | `auto_send` | Message sent instantly to guest. |
| **Inquiry** | 60% - 85% | `agent_review` | Draft prepared for agent approval. |
| **Inquiry** | < 60% | `escalate` | Flagged for senior management. |
| **Complaint** | Any | `escalate` | Immediate notification to operations; no auto-replies. |

---

## 💾 Database Design Philosophy

The included `schema.sql` follows a **Unified Identity** approach:
- **Relational Integrity**: Strict foreign key constraints link guests to reservations and conversations.
- **Workflow Auditing**: Every message tracks its "Handling Path" (AI-drafted vs. Agent-edited) to monitor automation ROI.
- **Extensibility**: The schema is designed to scale from a single villa to a global portfolio of properties.

  ## 📘 Interactive API Documentation

Once the server is running:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

  ## ✅ Validation & Error Handling Tests

The system was tested against multiple edge cases:

| Test Case | Expected Result |
|---|---|
| Invalid source channel | 422 validation error |
| Empty message | 400 bad request |
| Claude API failure | Graceful fallback + escalation |
| Complaint message | Escalation workflow triggered |

---

## 🛠️ Error Handling & Robustness
- **Payload Validation**: Strict Pydantic models prevent malformed data from entering the pipeline.
- **API Fallback**: Graceful handling of LLM timeouts or outages, ensuring the guest is never left without a "Human-is-coming" acknowledgment.
- **Input Sanitization**: Handles empty strings, invalid channel types, and malformed timestamps.

---

## 📬 Contact & Submission
**Candidate**: Nagachinmay K N  
**Assessment**: Nistula Summer Technology Internship 2026
