# HandoverIQ — AI Knowledge Handover

HandoverIQ turns scattered project documents into traceable handovers and answers questions using Google Gemini.

**Status:** Hackathon demo; SQLite on Vercel is temporary, not durable. Use only synthetic or authorized documents.

## Features
- PDF, DOCX, text and Markdown source import
- Evidence-linked project reconstruction and document chatbot
- Human review, approval and acknowledgement
- Role-based document visibility
- Seven-day continuation plan

## Local run
```bash
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
Set `GEMINI_API_KEY` in your environment for cloud AI. Never commit API keys or database files.

## Vercel
Configure `GEMINI_API_KEY` and a strong `DEMO_PASSWORD` as environment variables. Vercel's ephemeral SQLite storage resets; deploy with a persistent database before using real data.

Generated with AI assistance; follow event rules for disclosure and build windows.
