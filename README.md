# Canvas Color Updater

A Streamlit web application for automating re-branding of Canvas LMS course content across LACCD (Los Angeles Community College District) colleges.

## What It Does

When faculty share course content across LACCD campuses, the visual branding (colors) remains from the original college. This tool automates the tedious process of finding and replacing hex color codes in Canvas course HTML.

- Scans Pages, Assignments, Discussions, Announcements, Syllabus, and Quizzes
- Replaces hex color codes with your target college's brand colors
- Maps colors intelligently: Primary→Primary, Secondary→Secondary, Accent→Accent
- Optional "Replace ALL colors" mode for courses with custom colors
- Optional AI-powered text replacement (e.g., "Welcome to ELAC" → "Welcome to Pierce College")

## Supported Colleges

| College | Primary | Secondary | Accent |
|---------|---------|-----------|--------|
| LACCD (District) | #005a95 | #00345f | #bb9e6d |
| ELAC (East LA) | #447D29 | #33511D | #FDB913 |
| LACC (LA City) | #C13C40 | #305589 | #112844 |
| LAHC (LA Harbor) | #5F7FE2 | #002663 | #FFC72C |
| LAMC (LA Mission) | #004590 | #FF611A | #718089 |
| LAPC (LA Pierce) | #BF2116 | #1F1F1F | #FFFFFF |
| LASC (LA Southwest) | #C5B358 | #000000 | #FFFFFF |
| LATTC (LA Trade-Tech) | #562c82 | #1c1c1c | #aea4eb |
| LAVC (LA Valley) | #00593F | #FFC72C | #FFFFFF |
| WLAC (West LA) | #4169E1 | #003594 | #FFD700 |

## Quick Start

### Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Docker

```bash
docker build -t canvas-color-updater .
docker run -p 8501:8501 canvas-color-updater
```

### Docker Compose

```bash
docker-compose up --build
```

Then open http://localhost:8501

## Usage

1. Enter your Canvas API token (generate at: Canvas → Account → Settings → New Access Token)
2. Enter the Course ID (from your course URL)
3. Select the target college whose colors you want to apply
4. Check "Replace ALL colors" if the course uses custom colors not in the LACCD palette
5. Run a **Dry Run** first to preview changes
6. Uncheck "Dry run" and run again to apply changes

## AI Features (Optional)

Enable AI-powered text replacement to automatically update college name references in your content. Requires an [OpenRouter](https://openrouter.ai/) API key.

### Supported Models

**Free Models:**
| Model | ID |
|-------|-----|
| Grok 4.1 Fast | `x-ai/grok-4.1-fast:free` |
| GLM 4.5 Air | `z-ai/glm-4.5-air:free` |
| Nemotron Nano 12B | `nvidia/nemotron-nano-12b-v2-vl:free` |
| Qwen3 Coder | `qwen/qwen3-coder:free` |
| GPT-OSS 20B | `openai/gpt-oss-20b:free` |
| Qwen3 235B | `qwen/qwen3-235b-a22b:free` |
| Gemini 2.0 Flash Exp | `google/gemini-2.0-flash-exp:free` |
| Kimi K2 | `moonshotai/kimi-k2:free` |
| Gemma 3 12B | `google/gemma-3-12b-it:free` |

**Paid Models:**
| Model | ID |
|-------|-----|
| GPT 5.1 | `openai/gpt-5.1` |
| GPT 5.1 Codex | `openai/gpt-5.1-codex` |
| Claude Sonnet 4.5 | `anthropic/claude-sonnet-4.5` |
| Claude Haiku 4.5 | `anthropic/claude-haiku-4.5` |
| Gemini 2.5 Flash Lite | `google/gemini-2.5-flash-lite` |
| Gemini 2.5 Flash | `google/gemini-2.5-flash` |
| Gemini 3 Pro Preview | `google/gemini-3-pro-preview` |

## Deployment (Coolify)

1. Push this repo to GitHub/GitLab
2. In Coolify, create a new service with Docker build pack
3. Set port to `8501`
4. (Optional) Add `FIREBASE_API_KEY` environment variable to enable user authentication
5. Deploy

## Security

- **Zero persistence**: Canvas API tokens and OpenRouter keys are stored only in session memory (RAM)
- Credentials are never written to disk or database
- When the session ends, all sensitive data is cleared
- Optional Firebase authentication for multi-user deployments

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FIREBASE_API_KEY` | No | Enables user authentication. Without it, the app is open access. |

## License

MIT
