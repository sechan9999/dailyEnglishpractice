"""
Daily English Practice — Telegram Bot
매일 아침 8시 (KST) 학습 내용을 자동 발송합니다.

설치: pip install python-telegram-bot apscheduler pytz
실행: python telegram_bot.py

명령어:
  /start  — 구독 시작 (매일 8시 자동 발송)
  /stop   — 구독 취소
  /today  — 오늘의 학습 즉시 받기
  /day N  — N번 날 학습 내용 요청
  /list   — 전체 커리큘럼 보기
"""

import json
import logging
import os
from datetime import datetime, date
import pytz
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ── 설정 ────────────────────────────────────────────────
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # BotFather에서 받은 토큰으로 교체
SUBSCRIBERS_FILE = "subscribers.json"
KST = pytz.timezone("Asia/Seoul")
DAILY_HOUR = 8    # 발송 시각 (KST 기준)
DAILY_MINUTE = 0

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── 학습 데이터 ──────────────────────────────────────────
DAYS = [
    {
        "day": 1,
        "topic": "Bias-Variance Tradeoff",
        "topic_ko": "편향-분산 트레이드오프",
        "question": "Explain the Bias-Variance Tradeoff.",
        "question_ko": "편향-분산 트레이드오프를 설명해 주세요.",
        "summary": (
            "The **Bias-Variance Tradeoff** describes the relationship between model complexity "
            "and its ability to generalize.\n\n"
            "• **Bias (편향)** — error from oversimplified assumptions → *underfitting*\n"
            "• **Variance (분산)** — sensitivity to training data noise → *overfitting*\n\n"
            "Goal: find the *sweet spot* where total error is minimized."
        ),
        "vocab": [
            ("Bias /ˈbaɪ.əs/", "편향", "Error from oversimplified model assumptions"),
            ("Variance /ˈveər.i.əns/", "분산", "Sensitivity to training data fluctuations"),
            ("Underfitting", "과소적합", "Model too simple to capture patterns"),
            ("Overfitting", "과적합", "Model memorizes noise in training data"),
            ("Generalization", "일반화", "Ability to perform well on unseen data"),
        ],
        "pronunciation": (
            "• *bias* → BY-uhs (stress on first syllable)\n"
            "• *variance* → VAIR-ee-uhns (3 syllables, stress on VAIR)\n"
            "• *tradeoff* → TRAYD-awf (say as one word)"
        ),
        "prompt": (
            "🎤 *Speaking Practice (60–90초 목표):*\n"
            "Explain the Bias-Variance Tradeoff to a hiring manager, "
            "using a concrete example (e.g., decision tree depth)."
        ),
    },
    {
        "day": 2,
        "topic": "Supervised vs Unsupervised",
        "topic_ko": "지도 학습 vs 비지도 학습",
        "question": "What is the difference between supervised and unsupervised learning?",
        "question_ko": "지도 학습과 비지도 학습의 차이는 무엇인가요?",
        "summary": (
            "Key distinction: whether training data has **labels (정답)**.\n\n"
            "• **Supervised (지도 학습)** — labeled data, learns input→output mapping. "
            "Examples: spam detection, price prediction\n"
            "• **Unsupervised (비지도 학습)** — unlabeled data, finds hidden structure. "
            "Examples: customer segmentation, anomaly detection\n\n"
            "Choose supervised when labels exist; unsupervised to explore unknown structure."
        ),
        "vocab": [
            ("Labeled data /ˈleɪ.bəld/", "레이블 데이터", "Data with known correct outputs"),
            ("Classification", "분류", "Predicting a discrete category"),
            ("Clustering /ˈklʌs.tər.ɪŋ/", "군집화", "Grouping similar points without labels"),
            ("Anomaly detection", "이상 탐지", "Identifying unusual patterns"),
            ("Dimensionality reduction", "차원 축소", "Reducing features while retaining info"),
        ],
        "pronunciation": (
            "• *supervised* → SOO-per-vyzd (un- is quick, unstressed)\n"
            "• *algorithm* → AL-goh-rith-um (stress on AL)\n"
            "• *clustering* → KLUS-ter-ing"
        ),
        "prompt": (
            "🎤 *Speaking Practice (60–90초 목표):*\n"
            "Describe a project where you used supervised learning. "
            "Explain why you didn't use an unsupervised approach."
        ),
    },
    {
        "day": 3,
        "topic": "Cross-Validation",
        "topic_ko": "교차 검증",
        "question": "What is cross-validation, and why is it important?",
        "question_ko": "교차 검증이란 무엇이며 왜 중요한가요?",
        "summary": (
            "**Cross-validation** evaluates how well a model generalizes by testing on multiple splits.\n\n"
            "**K-Fold CV:** Split data into k folds → train on k-1, test on 1 → repeat k times → average.\n\n"
            "Why it matters:\n"
            "• Prevents overfitting (tests on multiple unseen subsets)\n"
            "• Maximizes data use (all samples used for training and validation)\n"
            "• Enables reliable model comparison / hyperparameter tuning"
        ),
        "vocab": [
            ("K-Fold /keɪ foʊld/", "K-겹 교차 검증", "Data split into k equal test/train sets"),
            ("Stratified /ˈstræt.ɪ.faɪd/", "층화된", "Fold preserves class distribution"),
            ("Generalizability", "일반화 능력", "How well a model handles unseen data"),
            ("Hyperparameter", "하이퍼파라미터", "Settings configured before training"),
            ("Hold-out set", "홀드아웃 세트", "Data reserved only for final evaluation"),
        ],
        "pronunciation": (
            "• *cross-validation* → KRAWS-val-ih-DAY-shun (stress on DAY)\n"
            "• *stratified* → STRAT-ih-fyd (stress on STRAT)\n"
            "• *hyperparameter* → HY-per-PAIR-uh-mee-ter"
        ),
        "prompt": (
            "🎤 *Speaking Practice (60–90초 목표):*\n"
            "Describe your evaluation strategy for an imbalanced classification task. "
            "Which CV method would you choose and why?"
        ),
    },
    {
        "day": 4,
        "topic": "Random Forest",
        "topic_ko": "랜덤 포레스트",
        "question": "How does a Random Forest work?",
        "question_ko": "랜덤 포레스트는 어떻게 동작하나요?",
        "summary": (
            "**Random Forest** = ensemble of decision trees using two randomness sources:\n\n"
            "1. **Bagging** — each tree trains on a different bootstrap sample (rows, with replacement)\n"
            "2. **Feature randomness** — at each split, only √p features are considered\n\n"
            "**Prediction:** Classification → majority vote | Regression → average\n\n"
            "Result: diverse, decorrelated trees that reduce variance without increasing bias."
        ),
        "vocab": [
            ("Ensemble /ɒnˈsɒm.bəl/", "앙상블", "Combining multiple models for better performance"),
            ("Bagging /ˈbæɡ.ɪŋ/", "배깅", "Training on random bootstrap samples"),
            ("Bootstrap sampling", "부트스트랩 샘플링", "Random sampling with replacement"),
            ("Feature importance", "특성 중요도", "Score measuring each feature's contribution"),
            ("Decorrelated", "비상관화", "Trees that make errors independently"),
        ],
        "pronunciation": (
            "• *ensemble* → ahn-SAHM-bul (French origin; final -e is silent)\n"
            "• *bagging* → BAG-ing (not BAY-ging)\n"
            "• *bootstrap* → BOOT-strap"
        ),
        "prompt": (
            "🎤 *Speaking Practice (60–90초 목표):*\n"
            "Compare a single decision tree vs. Random Forest for fraud detection. "
            "Discuss interpretability, performance, and when NOT to use Random Forest."
        ),
    },
    {"day": 5,  "topic": "Regularization (L1/L2)", "topic_ko": "정규화 기법", "locked": True},
    {"day": 6,  "topic": "Performance Metrics",    "topic_ko": "성능 지표",     "locked": True},
    {"day": 7,  "topic": "Gradient Descent",       "topic_ko": "경사 하강법",   "locked": True},
    {"day": 8,  "topic": "Dimensionality Reduction","topic_ko": "차원 축소",    "locked": True},
    {"day": 9,  "topic": "Data Preprocessing",     "topic_ko": "데이터 전처리", "locked": True},
    {"day": 10, "topic": "Statistical Foundations", "topic_ko": "통계 기초",   "locked": True},
    {"day": 11, "topic": "Feature Engineering",    "topic_ko": "피처 엔지니어링","locked": True},
    {"day": 12, "topic": "Model Evaluation",       "topic_ko": "모델 평가",     "locked": True},
    {"day": 13, "topic": "Neural Networks",        "topic_ko": "신경망 기초",   "locked": True},
    {"day": 14, "topic": "Ensemble Methods",       "topic_ko": "앙상블 기법",   "locked": True},
    {"day": 15, "topic": "Advanced ML Review",     "topic_ko": "ML 종합 복습",  "locked": True},
]

AVAILABLE_DAYS = [d for d in DAYS if not d.get("locked")]


# ── 구독자 관리 ──────────────────────────────────────────

def load_subscribers() -> dict:
    if not os.path.exists(SUBSCRIBERS_FILE):
        return {}
    try:
        with open(SUBSCRIBERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_subscribers(data: dict):
    with open(SUBSCRIBERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_next_day(chat_id: int) -> int:
    """구독자의 다음 학습 날 반환 (순환)."""
    subs = load_subscribers()
    key = str(chat_id)
    sub = subs.get(key, {})
    current = sub.get("current_day", 0)
    available = [d["day"] for d in AVAILABLE_DAYS]
    if not available:
        return 1
    # 다음 날 찾기
    next_days = [d for d in available if d > current]
    return next_days[0] if next_days else available[0]


def advance_day(chat_id: int):
    """구독자의 current_day를 다음으로 업데이트."""
    subs = load_subscribers()
    key = str(chat_id)
    if key not in subs:
        return
    next_day = get_next_day(chat_id)
    subs[key]["current_day"] = next_day
    subs[key]["last_sent"] = date.today().isoformat()
    save_subscribers(subs)


# ── 메시지 포매팅 ────────────────────────────────────────

def format_day_message(day_num: int) -> str:
    d = next((x for x in AVAILABLE_DAYS if x["day"] == day_num), None)
    if not d:
        return f"Day {day_num}의 내용은 아직 준비 중입니다. 🔒"

    vocab_lines = "\n".join(
        f"  • *{v[0]}* — {v[1]}: {v[2]}" for v in d["vocab"]
    )

    msg = (
        f"🌅 *Daily English Practice — Day {d['day']}*\n"
        f"_{d['topic']} · {d['topic_ko']}_\n"
        f"{'─' * 30}\n\n"
        f"📌 *Interview Question*\n"
        f"_{d['question']}_\n"
        f"({d['question_ko']})\n\n"
        f"📝 *핵심 정리*\n{d['summary']}\n\n"
        f"📚 *Key Vocabulary*\n{vocab_lines}\n\n"
        f"🔊 *발음 포인트*\n{d['pronunciation']}\n\n"
        f"{d['prompt']}\n\n"
        f"{'─' * 30}\n"
        f"_/today — 오늘 내용 다시 받기 | /day N — 특정 날 요청_"
    )
    return msg


def format_curriculum() -> str:
    lines = ["📋 *전체 커리큘럼 (15일)*\n"]
    for d in DAYS:
        if d.get("locked"):
            lines.append(f"  🔒 Day {d['day']}: {d['topic']} ({d['topic_ko']})")
        else:
            lines.append(f"  ✅ Day {d['day']}: {d['topic']} ({d['topic_ko']})")
    return "\n".join(lines)


# ── 봇 핸들러 ────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subs = load_subscribers()
    key = str(chat_id)

    if key in subs:
        await update.message.reply_text(
            "✅ 이미 구독 중입니다!\n"
            "매일 아침 8시 (한국 시간)에 학습 내용을 보내드립니다.\n\n"
            "/today — 오늘의 학습 즉시 받기\n"
            "/stop — 구독 취소",
            parse_mode="Markdown",
        )
        return

    subs[key] = {
        "chat_id": chat_id,
        "subscribed_at": date.today().isoformat(),
        "current_day": 0,
        "last_sent": None,
    }
    save_subscribers(subs)
    log.info("New subscriber: %s", chat_id)

    await update.message.reply_text(
        "🎉 *구독 완료!*\n\n"
        "매일 아침 *8시 (한국 시간)* 에 오늘의 영어 인터뷰 학습 내용을 보내드립니다.\n\n"
        "📚 총 15일 커리큘럼 (Day 1 → Day 15 순서로 진행)\n\n"
        "지금 바로 첫 번째 학습을 받으려면 /today 를 입력하세요!\n\n"
        "/list — 전체 커리큘럼 보기\n"
        "/stop — 구독 취소",
        parse_mode="Markdown",
    )


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subs = load_subscribers()
    key = str(chat_id)

    if key not in subs:
        await update.message.reply_text("구독 중이 아닙니다. /start 로 구독하세요.")
        return

    del subs[key]
    save_subscribers(subs)
    log.info("Unsubscribed: %s", chat_id)
    await update.message.reply_text(
        "👋 구독이 취소되었습니다.\n다시 구독하려면 /start 를 입력하세요."
    )


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    subs = load_subscribers()
    key = str(chat_id)

    if key not in subs:
        await update.message.reply_text(
            "먼저 /start 로 구독하세요! 📚"
        )
        return

    day_num = get_next_day(chat_id)
    msg = format_day_message(day_num)
    await update.message.reply_text(msg, parse_mode="Markdown")
    advance_day(chat_id)


async def cmd_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /day 1  (예: /day 3)")
        return

    try:
        day_num = int(context.args[0])
    except ValueError:
        await update.message.reply_text("숫자를 입력해주세요. 예: /day 2")
        return

    if not 1 <= day_num <= 15:
        await update.message.reply_text("Day 1부터 Day 15 사이의 숫자를 입력해주세요.")
        return

    msg = format_day_message(day_num)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_curriculum(), parse_mode="Markdown")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Daily English Practice Bot*\n\n"
        "/start — 매일 8시 자동 발송 구독\n"
        "/stop  — 구독 취소\n"
        "/today — 오늘의 학습 즉시 받기\n"
        "/day N — 특정 날 학습 요청 (예: /day 3)\n"
        "/list  — 전체 15일 커리큘럼 보기\n"
        "/help  — 도움말",
        parse_mode="Markdown",
    )


# ── 매일 발송 ────────────────────────────────────────────

async def send_daily_to_all(bot: Bot):
    subs = load_subscribers()
    if not subs:
        log.info("No subscribers.")
        return

    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    log.info("[%s] Sending daily content to %d subscribers...", now_kst, len(subs))

    for key, sub in list(subs.items()):
        chat_id = sub["chat_id"]
        day_num = get_next_day(chat_id)
        msg = format_day_message(day_num)

        try:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
            advance_day(chat_id)
            log.info("Sent Day %d to %s", day_num, chat_id)
        except Exception as e:
            log.warning("Failed to send to %s: %s", chat_id, e)
            # 봇 차단된 사용자 자동 제거
            if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                subs_now = load_subscribers()
                if key in subs_now:
                    del subs_now[key]
                    save_subscribers(subs_now)
                    log.info("Removed blocked subscriber: %s", chat_id)


# ── 메인 ────────────────────────────────────────────────

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("=" * 50)
        print("⚠️  BOT_TOKEN을 설정해주세요!")
        print("  1. 텔레그램에서 @BotFather 검색")
        print("  2. /newbot 명령어로 봇 생성")
        print("  3. 발급받은 토큰을 BOT_TOKEN에 입력")
        print("=" * 50)
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("today", cmd_today))
    app.add_handler(CommandHandler("day", cmd_day))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("help", cmd_help))

    scheduler = AsyncIOScheduler(timezone=KST)
    scheduler.add_job(
        send_daily_to_all,
        trigger="cron",
        hour=DAILY_HOUR,
        minute=DAILY_MINUTE,
        args=[app.bot],
        id="daily_send",
    )
    scheduler.start()

    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    print(f"✅ 봇 시작됨 [{now_kst} KST]")
    print(f"📅 매일 {DAILY_HOUR:02d}:{DAILY_MINUTE:02d} KST 자동 발송 예정")
    print("종료: Ctrl+C\n")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
