# Architecture

## Version

Day 1 draft.

## Target Architecture

Input
→ FastAPI Backend
→ Validation + Analysis
→ Structured Output
→ Evaluation + Cost Logging
→ n8n Workflow / Human Review
→ Final Output

## Current State

Only the repository structure exists.

No backend, AI integration, RAG, n8n workflow or deployment exists yet.

## Architecture Rule

Build small, testable components first.

Do not add AI before the basic non-AI processing works.
