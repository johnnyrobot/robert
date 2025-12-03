# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Canvas Color Updater is a Streamlit web application for automating re-branding of Canvas LMS course content across LACCD (Los Angeles Community College District) colleges. It replaces hex color codes and uses AI to update text references when migrating courses between campuses.

## Commands

```bash
# Local development
pip install -r requirements.txt
streamlit run app.py

# Docker build and run
docker build -t canvas-color-updater .
docker run -p 8501:8501 canvas-color-updater

# Docker Compose
docker-compose up --build
```

## Tech Stack

- **Framework:** Python 3.11 with Streamlit
- **Authentication:** Firebase Auth REST API (optional)
- **Canvas Integration:** `canvasapi` Python library
- **AI Integration:** OpenAI Python library configured for OpenRouter (`base_url="https://openrouter.ai/api/v1"`)

## Key Files

- `app.py` - Main Streamlit application with all UI and processing logic
- `auth.py` - Firebase authentication module (optional, disabled if no API key)
- `Dockerfile` - Production container configuration for Coolify deployment
- `docker-compose.yml` - Local Docker development setup

## Architecture

1. **Authentication Layer:** Optional Firebase Auth validates users (disabled if `FIREBASE_API_KEY` not set)
2. **Configuration:** Canvas API tokens and OpenRouter keys stored in `st.session_state` (RAM only, never persisted)
3. **Processing Pipeline:**
   - Layer 1: Regex-based hex color replacement (primary→primary, secondary→secondary, accent→accent)
   - Layer 2: Optional AI text polish via OpenRouter for college name/branding updates
4. **Canvas API:** Fetches and updates Pages, Assignments, Quizzes, Discussions, Announcements, and Syllabus

## LACCD Color Mapping

The `COLOR_MAP` dict in `app.py` contains all 10 campus color schemes (9 colleges + District). Each has:
- `primary` - Header/main color
- `secondary` - Text/footer color
- `accent` - Links/buttons color
- `full_name` - Full college name for AI replacement

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FIREBASE_API_KEY` | No | Enables Firebase user authentication. Without it, the app allows open access. |

## Implementation Notes

- Default Canvas URL is `https://ilearn.laccd.edu` (LACCD's Canvas instance)
- Classic Quizzes use the `canvasapi` library; New Quizzes use direct REST API calls to `/api/quiz/v1/`
- Rate limiting: 0.5s `time.sleep()` between Canvas API write requests to avoid throttling
- AI responses are cleaned of markdown code block wrappers before saving

## Security

- Canvas API tokens and OpenRouter keys exist only in session memory (never persisted)
- Non-root user in Docker container
