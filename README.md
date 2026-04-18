# Daily English Practice — Data Science & Coding Interview Prep

A bilingual (Korean/English) single-page web app for daily data science and coding interview practice.  
Live app: **https://daily-english-practice.vercel.app**

## Features

- 25 days of structured interview content (ML theory + Python + coding algorithms)
- Korean/English bilingual — questions and explanations in both languages
- IPA pronunciation guide for every topic
- Speaking practice prompt with a 90-second timer
- Progress tracking with streak counter (localStorage)
- Light/dark mode
- Telegram bot — sends the day's content at 8 AM KST

## Topics Covered (25 Days)

| Day | Topic |
|-----|-------|
| 1 | Bias-Variance Tradeoff |
| 2 | Supervised vs. Unsupervised Learning |
| 3 | Cross-Validation |
| 4 | Random Forest |
| 5 | Gradient Boosting & XGBoost |
| 6 | Neural Networks & Backpropagation |
| 7 | Regularization (L1 / L2) |
| 8 | Precision, Recall & F1 Score |
| 9 | Clustering (K-Means / DBSCAN) |
| 10 | Recommendation Systems |
| 11 | A/B Testing & Hypothesis Testing |
| 12 | SQL & Window Functions |
| 13 | MLOps & Model Deployment |
| 14 | Product Metrics & Experimentation |
| 15 | Statistics — Central Limit Theorem |
| 16 | Python — Memory Management & GIL |
| 17 | Python — NumPy Broadcasting & Pandas |
| 18 | Python — Generators & Context Managers |
| 19 | ML Pipeline & Feature Selection |
| 20 | LLMs, Transformers & RAG |
| 21 | Coding — Arrays & Hash Maps |
| 22 | Coding — String Manipulation |
| 23 | Coding — Trees & Graph Traversal |
| 24 | Coding — Binary Search Patterns |
| 25 | Coding — Dynamic Programming |

## Project Structure

```
dailyEnglishpractice/
├── index.html          # Single-file web app (all content + logic)
├── telegram_bot.py     # Telegram bot with APScheduler (8 AM KST)
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel static deployment config
└── .gitignore
```

## Telegram Bot Setup

1. Create a bot via [@BotFather](https://t.me/BotFather) and copy the token.
2. Set `BOT_TOKEN` in `telegram_bot.py`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run:
   ```bash
   python telegram_bot.py
   ```

Bot commands: `/start`, `/today`, `/day <n>`, `/list`, `/stop`, `/help`

## Deployment

Static site deployed on Vercel. To redeploy:

```bash
vercel deploy --prod --yes --scope tcgyvers-projects
```

## Tech Stack

- Vanilla HTML/CSS/JS (no build step)
- CSS custom properties for theming
- `python-telegram-bot` v20+ (async)
- `APScheduler` for cron scheduling
- `pytz` for KST timezone
