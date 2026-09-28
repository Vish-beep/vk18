# Alwis + Document RAG Chatbot (v3)

This version supports two knowledge sources:

1. Uploaded PDF/DOCX documents.
2. A built-in Alwis website knowledge base.

## Alwis improvements in v3

- Company-level intent detection for natural questions such as:
  - `What does Alwis do?`
  - `What is Alwis based on?`
  - `What is the Alwis company based on?`
  - `What industry is Alwis in?`
  - `Tell me about Alwis`
  - `Where is Alwis based?`
- Product/entity normalization for `ZiNex`, `zi nex`, `Zi Nex`, etc.
- Product recognition for ZiSmart, ZiCapPro, ZiNex, ZiTrack, ZiQuel, ReTrans, ReGenX and ScoMed.
- Intent-aware lexical retrieval that prioritizes the Alwis About/Home pages for company questions and the relevant product page for product questions.
- Stronger prompt instructions so the LLM interprets informal/grammatically imperfect questions by intent instead of rejecting them.
- Existing PDF/DOCX document RAG remains separate and is not overwritten by the Alwis knowledge base.
- `/alwis/update` can refresh the website snapshot when the deployment machine has internet access.

## Official Alwis source pages represented in the built-in snapshot

- https://alwisgroup.com/
- https://alwisgroup.com/about-us/
- https://alwisgroup.com/platforms/
- https://alwisgroup.com/category/events/

## Run

```bash
pip install -r requirements.txt
ollama pull llama3.2
python app.py
```

Then open the local Flask page shown by the application.
