"""
Daily English Practice — Telegram Bot
매일 아침 8시 (KST) 43일 커리큘럼 학습 내용을 자동 발송합니다.

설치: pip install python-telegram-bot apscheduler pytz
실행: python telegram_bot.py

명령어:
  /start    — 구독 시작 (매일 8시 자동 발송)
  /stop     — 구독 취소
  /today    — 오늘의 학습 즉시 받기
  /day N    — N번 날 학습 내용 요청 (1-43)
  /list     — 전체 커리큘럼 보기
  /stats    — 구독자 현황
  /share    — 공유 텍스트 받기
  /feedback — 피드백 안내
  /help     — 도움말
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
DAILY_HOUR = 8
DAILY_MINUTE = 0
APP_URL = "https://daily-english-practice.vercel.app"

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ── 학습 데이터 (43일 전체) ──────────────────────────────
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
            "• **Variance (분산)** — sensitivity to training noise → *overfitting*\n"
            "• Goal: find the *sweet spot* where total error is minimized"
        ),
        "vocab": [
            ("Bias /ˈbaɪ.əs/", "편향", "Error from oversimplified model assumptions"),
            ("Variance /ˈveər.i.əns/", "분산", "Sensitivity to training data fluctuations"),
            ("Overfitting", "과적합", "Model memorizes noise in training data"),
        ],
        "pronunciation": (
            "• *bias* → BY-uhs (stress on first syllable)\n"
            "• *variance* → VAIR-ee-uhns (stress on VAIR)"
        ),
        "prompt": "Explain the Bias-Variance Tradeoff using a decision tree depth example.",
    },
    {
        "day": 2,
        "topic": "Supervised vs Unsupervised Learning",
        "topic_ko": "지도 학습 vs 비지도 학습",
        "question": "What is the difference between supervised and unsupervised learning?",
        "question_ko": "지도 학습과 비지도 학습의 차이는 무엇인가요?",
        "summary": (
            "Key distinction: whether training data has **labels (정답)**.\n\n"
            "• **Supervised** — labeled data, input→output mapping (spam detection, price prediction)\n"
            "• **Unsupervised** — unlabeled data, finds hidden structure (clustering, anomaly detection)\n"
            "• Choose supervised when labels exist; unsupervised to explore unknown structure"
        ),
        "vocab": [
            ("Labeled data /ˈleɪ.bəld/", "레이블 데이터", "Data with known correct outputs"),
            ("Clustering /ˈklʌs.tər.ɪŋ/", "군집화", "Grouping similar points without labels"),
            ("Anomaly detection", "이상 탐지", "Identifying unusual patterns"),
        ],
        "pronunciation": (
            "• *supervised* → SOO-per-vyzd (un- is quick, unstressed)\n"
            "• *clustering* → KLUS-ter-ing"
        ),
        "prompt": "Describe a project where you used supervised learning. Why not unsupervised?",
    },
    {
        "day": 3,
        "topic": "Cross-Validation",
        "topic_ko": "교차 검증",
        "question": "What is cross-validation, and why is it important?",
        "question_ko": "교차 검증이란 무엇이며 왜 중요한가요?",
        "summary": (
            "**Cross-validation** evaluates how well a model generalizes by testing on multiple splits.\n\n"
            "• **K-Fold CV:** Split data into k folds → train on k-1, test on 1 → repeat → average\n"
            "• Prevents overfitting by testing on multiple unseen subsets\n"
            "• Enables reliable model comparison and hyperparameter tuning"
        ),
        "vocab": [
            ("K-Fold /keɪ foʊld/", "K-겹 교차 검증", "Data split into k equal test/train sets"),
            ("Stratified /ˈstræt.ɪ.faɪd/", "층화된", "Fold preserves class distribution"),
            ("Hold-out set", "홀드아웃 세트", "Data reserved only for final evaluation"),
        ],
        "pronunciation": (
            "• *cross-validation* → KRAWS-val-ih-DAY-shun (stress on DAY)\n"
            "• *stratified* → STRAT-ih-fyd"
        ),
        "prompt": "Describe your evaluation strategy for an imbalanced classification task.",
    },
    {
        "day": 4,
        "topic": "Random Forest",
        "topic_ko": "랜덤 포레스트",
        "question": "How does a Random Forest work?",
        "question_ko": "랜덤 포레스트는 어떻게 동작하나요?",
        "summary": (
            "**Random Forest** = ensemble of decision trees using two randomness sources:\n\n"
            "• **Bagging** — each tree trains on a bootstrap sample (rows, with replacement)\n"
            "• **Feature randomness** — at each split, only √p features are considered\n"
            "• Result: diverse, decorrelated trees that reduce variance without increasing bias"
        ),
        "vocab": [
            ("Ensemble /ɒnˈsɒm.bəl/", "앙상블", "Combining multiple models for better performance"),
            ("Bagging /ˈbæɡ.ɪŋ/", "배깅", "Training on random bootstrap samples"),
            ("Feature importance", "특성 중요도", "Score measuring each feature's contribution"),
        ],
        "pronunciation": (
            "• *ensemble* → ahn-SAHM-bul (French origin)\n"
            "• *bagging* → BAG-ing"
        ),
        "prompt": "Compare a single decision tree vs Random Forest for fraud detection.",
    },
    {
        "day": 5,
        "topic": "Gradient Boosting & XGBoost",
        "topic_ko": "그래디언트 부스팅 & XGBoost",
        "question": "How does Gradient Boosting differ from Random Forest?",
        "question_ko": "그래디언트 부스팅이 랜덤 포레스트와 어떻게 다른지 설명해 주세요.",
        "summary": (
            "**Gradient Boosting** builds trees *sequentially*, each correcting the previous tree's errors.\n\n"
            "• **Random Forest:** parallel trees, reduces variance via averaging\n"
            "• **Gradient Boosting:** sequential trees, reduces bias by fitting residuals\n"
            "• **XGBoost:** adds L1/L2 regularization, column subsampling, and efficient histogram splitting"
        ),
        "vocab": [
            ("Boosting /ˈbuː.stɪŋ/", "부스팅", "Sequential ensemble method correcting previous model errors"),
            ("Residuals /rɪˈzɪd.juː.əlz/", "잔차", "Differences between actual and predicted values"),
            ("Learning rate /ˈlɜr.nɪŋ reɪt/", "학습률", "Shrinks each tree's contribution to prevent overfitting"),
        ],
        "pronunciation": (
            "• *gradient* → GRAY-dee-unt (stress on GRAY)\n"
            "• *residual* → reh-ZID-yoo-ul (stress on ZID)"
        ),
        "prompt": "When would you choose XGBoost over Random Forest? Give a real scenario.",
    },
    {
        "day": 6,
        "topic": "Neural Networks & Backpropagation",
        "topic_ko": "신경망과 역전파",
        "question": "Explain how backpropagation trains a neural network.",
        "question_ko": "역전파가 신경망을 어떻게 훈련시키는지 설명해 주세요.",
        "summary": (
            "**Forward pass:** Input → layers → output → compute loss.\n\n"
            "• **Backpropagation:** Use chain rule to compute gradient of loss w.r.t. each weight\n"
            "• **Gradient descent:** Update weights: W = W − η·∇L\n"
            "• Vanishing gradient: gradients shrink in deep nets → solved by ReLU, BatchNorm, skip connections"
        ),
        "vocab": [
            ("Backpropagation", "역전파", "Algorithm computing gradients via the chain rule"),
            ("Chain rule", "연쇄 법칙", "Calculus rule for differentiating composite functions"),
            ("Vanishing gradient", "기울기 소실", "Gradients shrink to near-zero in deep networks"),
        ],
        "pronunciation": (
            "• *backpropagation* → bak-prop-uh-GAY-shun (stress on GAY)\n"
            "• *gradient* → GRAY-dee-unt"
        ),
        "prompt": "Explain why deep networks suffered before ReLU and how ReLU helps.",
    },
    {
        "day": 7,
        "topic": "Regularization — L1 & L2",
        "topic_ko": "정규화 — L1과 L2",
        "question": "Compare L1 (Lasso) and L2 (Ridge) regularization.",
        "question_ko": "L1(Lasso)과 L2(Ridge) 정규화를 비교해 주세요.",
        "summary": (
            "Regularization adds a penalty to the loss to prevent overfitting:\n\n"
            "• **L2 (Ridge):** penalty = λ·Σw² → shrinks weights toward zero, none exactly zero\n"
            "• **L1 (Lasso):** penalty = λ·Σ|w| → produces *sparse* solutions (some weights = exactly 0)\n"
            "• **ElasticNet:** L1 + L2 combined — good when many correlated features"
        ),
        "vocab": [
            ("Regularization", "정규화", "Adding a penalty to loss to reduce overfitting"),
            ("Sparsity /ˈspɑːr.sɪ.ti/", "희소성", "Most weights are exactly zero — implicit feature selection"),
            ("ElasticNet", "엘라스틱넷", "Combination of L1 and L2 regularization"),
        ],
        "pronunciation": (
            "• *regularization* → reg-yuh-luh-rih-ZAY-shun (stress on ZAY)\n"
            "• *Lasso* → LAH-soh"
        ),
        "prompt": "When would you prefer L1 over L2 regularization? Give a feature selection example.",
    },
    {
        "day": 8,
        "topic": "Precision, Recall & F1 Score",
        "topic_ko": "정밀도, 재현율, F1 점수",
        "question": "Explain Precision, Recall, and F1. When does each matter most?",
        "question_ko": "정밀도, 재현율, F1을 설명하고 각각이 중요한 상황을 말해 주세요.",
        "summary": (
            "• **Precision** = TP/(TP+FP) — of predicted positives, how many are correct?\n"
            "• **Recall** = TP/(TP+FN) — of actual positives, how many did we catch?\n"
            "• **F1** = 2·P·R/(P+R) — harmonic mean; use when precision and recall both matter\n"
            "• High precision critical: spam filter | High recall critical: cancer screening"
        ),
        "vocab": [
            ("Precision /prɪˈsɪʒ.ən/", "정밀도", "True positives / all predicted positives"),
            ("Recall /rɪˈkɔːl/", "재현율", "True positives / all actual positives"),
            ("AUC-ROC", "AUC-ROC", "Area under ROC curve; threshold-independent performance metric"),
        ],
        "pronunciation": (
            "• *precision* → preh-SIH-zhun (stress on SIH)\n"
            "• *recall* → reh-KAWL (stress on KAWL)"
        ),
        "prompt": "For a fraud detection model, which metric would you optimize and why?",
    },
    {
        "day": 9,
        "topic": "Clustering — K-Means & DBSCAN",
        "topic_ko": "클러스터링 — K-Means & DBSCAN",
        "question": "Compare K-Means and DBSCAN. When would you choose each?",
        "question_ko": "K-Means와 DBSCAN을 비교하고 각각의 사용 시점을 말해 주세요.",
        "summary": (
            "• **K-Means:** assign points to nearest centroid, recompute centroids, repeat\n"
            "  — O(n·k·i); requires k upfront; assumes spherical clusters\n"
            "• **DBSCAN:** density-based; no k required; finds arbitrary shapes; labels outliers as noise\n"
            "• Use K-Means for compact well-separated clusters; DBSCAN when shape/outliers matter"
        ),
        "vocab": [
            ("Centroid /ˈsen.trɔɪd/", "중심점", "Mean position of all points in a cluster"),
            ("DBSCAN", "밀도 기반 클러스터링", "Density-Based Spatial Clustering of Applications with Noise"),
            ("Inertia /ɪˈnɜr.ʃə/", "관성 (응집도)", "Sum of squared distances to cluster centroids — lower is better"),
        ],
        "pronunciation": (
            "• *centroid* → SEN-troyd (stress on SEN)\n"
            "• *inertia* → ih-NUR-shuh (stress on NUR)"
        ),
        "prompt": "How do you choose the right value of k in K-Means? Describe the elbow method.",
    },
    {
        "day": 10,
        "topic": "Recommendation Systems",
        "topic_ko": "추천 시스템",
        "question": "Compare collaborative filtering and content-based filtering.",
        "question_ko": "협업 필터링과 콘텐츠 기반 필터링을 비교해 주세요.",
        "summary": (
            "• **Collaborative filtering:** user-item interaction matrix; finds users/items with similar patterns\n"
            "  — Matrix Factorization (SVD, ALS) decomposes into latent factors\n"
            "• **Content-based:** recommends items similar to what a user already liked (item features)\n"
            "• **Cold-start problem:** new users/items have no history — hybrid or popularity fallback"
        ),
        "vocab": [
            ("Collaborative filtering", "협업 필터링", "Recommends based on similar user/item interactions"),
            ("Latent factors", "잠재 요인", "Hidden features learned from matrix factorization"),
            ("Cold-start problem", "콜드 스타트 문제", "No data for new users or items to make recommendations"),
        ],
        "pronunciation": (
            "• *collaborative* → kuh-LAB-uh-ruh-tiv (stress on LAB)\n"
            "• *latent* → LAY-tent (stress on LAY)"
        ),
        "prompt": "Describe how you'd build a movie recommendation system from scratch.",
    },
    {
        "day": 11,
        "topic": "A/B Testing & Hypothesis Testing",
        "topic_ko": "A/B 테스트와 가설 검정",
        "question": "How do you design and analyze an A/B test?",
        "question_ko": "A/B 테스트를 어떻게 설계하고 분석하나요?",
        "summary": (
            "**A/B test design:**\n"
            "• Define metric (conversion rate, revenue), set α=0.05, power=0.80\n"
            "• Calculate required sample size using power analysis\n"
            "• Run until sample size reached — never peek and stop early (p-hacking)\n"
            "• Analyze: two-sample t-test or z-test; check p-value vs α; report confidence interval"
        ),
        "vocab": [
            ("p-value /piː ˈvæl.juː/", "p값", "Probability of seeing results this extreme if null is true"),
            ("Statistical power", "통계적 검정력", "Probability of correctly detecting a true effect (1 - β)"),
            ("Novelty effect", "신기 효과", "Short-term user behavior change due to something being new"),
        ],
        "pronunciation": (
            "• *hypothesis* → hy-POTH-eh-sis (stress on POTH)\n"
            "• *significance* → sig-NIF-ih-kanse (stress on NIF)"
        ),
        "prompt": "An A/B test shows p=0.04. How would you present this result to a non-technical PM?",
    },
    {
        "day": 12,
        "topic": "SQL & Window Functions",
        "topic_ko": "SQL과 윈도우 함수",
        "question": "Explain ROW_NUMBER, RANK, LAG, and LEAD with examples.",
        "question_ko": "ROW_NUMBER, RANK, LAG, LEAD를 예시와 함께 설명해 주세요.",
        "summary": (
            "Window functions compute values across related rows without collapsing them:\n\n"
            "• **ROW_NUMBER()** — unique sequential integer per partition (no ties)\n"
            "• **RANK()** — ties get same rank, then skips (1,1,3)\n"
            "• **LAG(col,n)** — value from n rows before current\n"
            "• **LEAD(col,n)** — value from n rows after current"
        ),
        "vocab": [
            ("PARTITION BY", "파티션 기준", "Divides rows into groups for window function computation"),
            ("LAG /læɡ/", "이전 행 값", "Accesses a value from a preceding row in the result set"),
            ("Running total", "누적 합계", "Cumulative sum using ROWS UNBOUNDED PRECEDING"),
        ],
        "pronunciation": (
            "• *partition* → par-TISH-un (stress on TISH)\n"
            "• *aggregate* → AG-ruh-git"
        ),
        "prompt": "Write a SQL query to find the highest-paid employee per department.",
    },
    {
        "day": 13,
        "topic": "MLOps & Model Deployment",
        "topic_ko": "MLOps와 모델 배포",
        "question": "What is MLOps and how do you deploy a model to production?",
        "question_ko": "MLOps란 무엇이며 모델을 프로덕션에 배포하는 방법은?",
        "summary": (
            "**MLOps** = DevOps practices applied to ML lifecycle.\n\n"
            "• **Deployment patterns:** REST API (FastAPI/Flask), batch inference, streaming\n"
            "• **Model registry:** MLflow, W&B — version control for models\n"
            "• **Monitoring:** track data drift, prediction drift, model performance degradation\n"
            "• **CI/CD for ML:** automated retraining triggers when drift is detected"
        ),
        "vocab": [
            ("Model drift", "모델 드리프트", "Degradation of model performance due to changing data distribution"),
            ("Feature store", "피처 스토어", "Centralized repository for storing and serving ML features"),
            ("Canary deployment", "카나리 배포", "Rolling out model to a small % of traffic before full release"),
        ],
        "pronunciation": (
            "• *deployment* → deh-PLOY-ment (stress on PLOY)\n"
            "• *canary* → kuh-NAIR-ee (stress on NAIR)"
        ),
        "prompt": "Describe your process for deploying a model and monitoring it in production.",
    },
    {
        "day": 14,
        "topic": "Product Metrics & Experimentation",
        "topic_ko": "제품 지표와 실험",
        "question": "How do you choose and define product metrics for a data science project?",
        "question_ko": "데이터 사이언스 프로젝트의 제품 지표를 어떻게 선택하고 정의하나요?",
        "summary": (
            "• **North Star Metric:** single metric that best captures product value (DAU, GMV, retention)\n"
            "• **Guardrail metrics:** metrics that must NOT decrease (latency, revenue, NPS)\n"
            "• **Diagnostic metrics:** explain *why* the north star moved\n"
            "• Define metric before experiment; pre-register to avoid p-hacking"
        ),
        "vocab": [
            ("North Star Metric", "핵심 지표", "Single metric that best captures long-term product value"),
            ("Guardrail metric", "가드레일 지표", "Metric that must not decrease during experimentation"),
            ("DAU/MAU ratio", "DAU/MAU 비율", "Daily active users / monthly active users — measures engagement stickiness"),
        ],
        "pronunciation": (
            "• *metric* → MET-rik (stress on MET)\n"
            "• *retention* → reh-TEN-shun (stress on TEN)"
        ),
        "prompt": "You're launching a new feature. Define your primary metric and two guardrail metrics.",
    },
    {
        "day": 15,
        "topic": "Statistics — Central Limit Theorem",
        "topic_ko": "통계 — 중심 극한 정리",
        "question": "Explain the Central Limit Theorem and why it matters for data science.",
        "question_ko": "중심 극한 정리와 데이터 사이언스에서의 중요성을 설명해 주세요.",
        "summary": (
            "**CLT:** sampling distribution of the sample mean approaches **normal distribution** as n → ∞.\n\n"
            "• Justifies using z-tests and t-tests even when underlying data is not normal\n"
            "• Foundation for confidence intervals and A/B test analysis\n"
            "• **Bayesian vs Frequentist:** frequentist uses p-values; Bayesian incorporates prior beliefs"
        ),
        "vocab": [
            ("Central Limit Theorem", "중심 극한 정리", "Sample means approach normal distribution as sample size grows"),
            ("Confidence interval", "신뢰 구간", "Range of values likely to contain the true population parameter"),
            ("Type I error", "1종 오류", "False positive — rejecting a null hypothesis that is actually true"),
        ],
        "pronunciation": (
            "• *theorem* → THEE-uh-rum (3 syllables, not THEER-um)\n"
            "• *Bayesian* → BAY-zhun (stress on BAY)"
        ),
        "prompt": "Explain the difference between a confidence interval and a prediction interval.",
    },
    {
        "day": 16,
        "topic": "Python — Memory Management & GIL",
        "topic_ko": "파이썬 메모리 관리와 GIL",
        "question": "How does Python manage memory, and what is the Global Interpreter Lock?",
        "question_ko": "파이썬의 메모리 관리와 GIL을 설명해 주세요.",
        "summary": (
            "• Python uses **reference counting** + **cyclic garbage collector**\n"
            "• **GIL (Global Interpreter Lock):** only one thread executes Python bytecode at a time\n"
            "• I/O-bound → use `threading` (GIL released during I/O)\n"
            "• CPU-bound → use `multiprocessing` (separate processes, each with own GIL)"
        ),
        "vocab": [
            ("GIL", "전역 인터프리터 락", "Mutex ensuring only one thread runs Python bytecode at a time"),
            ("Reference counting", "참조 카운팅", "Tracking references to an object; free when count hits zero"),
            ("Multiprocessing", "멀티프로세싱", "Separate OS processes bypassing the GIL for CPU-bound work"),
        ],
        "pronunciation": (
            "• *interpreter* → in-TER-pruh-ter (stress on TER)\n"
            "• *mutex* → MYOO-teks"
        ),
        "prompt": "Why don't Python threads speed up a CPU-bound loop? What do you use instead?",
    },
    {
        "day": 17,
        "topic": "Python — NumPy Broadcasting & Pandas",
        "topic_ko": "NumPy 브로드캐스팅과 Pandas",
        "question": "Explain NumPy broadcasting and the difference between loc and iloc.",
        "question_ko": "NumPy 브로드캐스팅과 loc, iloc의 차이를 설명해 주세요.",
        "summary": (
            "• **Broadcasting:** operate on arrays of different shapes — dimensions compared right-to-left; size-1 expands\n"
            "• **loc:** label-based indexing — inclusive on both ends\n"
            "• **iloc:** integer position-based — exclusive end (like Python slicing)\n"
            "• Avoid row-by-row loops; use vectorized ops and `groupby().agg()`"
        ),
        "vocab": [
            ("Broadcasting", "브로드캐스팅", "NumPy rule for operating on arrays of compatible but different shapes"),
            ("loc", "레이블 기반 인덱싱", "Pandas label-based selector; both endpoints inclusive"),
            ("Vectorization", "벡터화", "Applying operations to entire arrays without Python loops"),
        ],
        "pronunciation": (
            "• *vectorization* → vek-tuh-rye-ZAY-shun (stress on ZAY)\n"
            "• *iloc* → eye-lock"
        ),
        "prompt": "Describe a Pandas data cleaning pipeline: missing values, duplicates, wrong dtypes.",
    },
    {
        "day": 18,
        "topic": "Python — Generators & Context Managers",
        "topic_ko": "제너레이터와 컨텍스트 매니저",
        "question": "What are generators and context managers? When do you use each?",
        "question_ko": "제너레이터와 컨텍스트 매니저가 무엇이며 각각 언제 사용하나요?",
        "summary": (
            "• **Generator:** function using `yield` — lazy, produces values on demand (great for large data)\n"
            "• **Context manager:** `with` statement — guarantees cleanup even on exceptions (files, DB connections, locks)\n"
            "• **Mutable default argument pitfall:** `def f(lst=[])` — list is shared across all calls!"
        ),
        "vocab": [
            ("Generator", "제너레이터", "Function using yield to lazily produce a sequence of values"),
            ("Context manager", "컨텍스트 매니저", "Object managing resource setup/teardown via the with statement"),
            ("Lazy evaluation", "지연 평가", "Computing values only when actually needed"),
        ],
        "pronunciation": (
            "• *generator* → JEN-uh-ray-ter (stress on JEN)\n"
            "• *mutable* → MYOO-tuh-bul"
        ),
        "prompt": "Write a generator that reads a 10 GB log file filtering 'ERROR' lines. Why not a list?",
    },
    {
        "day": 19,
        "topic": "End-to-End ML Pipeline",
        "topic_ko": "엔드투엔드 ML 파이프라인",
        "question": "Walk through a complete ML pipeline from raw data to production model.",
        "question_ko": "원시 데이터에서 프로덕션 모델까지 ML 파이프라인 전체를 설명해 주세요.",
        "summary": (
            "1. **EDA:** check shape, distributions, nulls, correlations\n"
            "2. **Preprocessing:** impute nulls, encode categoricals, scale numerics, handle imbalance (SMOTE)\n"
            "3. **Feature selection:** correlation, RFE, LASSO, tree importance\n"
            "4. **Modeling:** cross-validate, tune (Optuna), choose metric aligned with business goal\n"
            "5. **Production:** sklearn Pipeline + joblib/ONNX + drift monitoring"
        ),
        "vocab": [
            ("Feature engineering", "피처 엔지니어링", "Creating/transforming input variables to improve model performance"),
            ("SMOTE", "합성 소수 오버샘플링", "Synthetic Minority Over-sampling Technique for imbalanced data"),
            ("Data leakage", "데이터 누출", "Test/future info leaking into training, inflating performance"),
        ],
        "pronunciation": (
            "• *pipeline* → PYP-lyne (stress on PYP)\n"
            "• *impute* → im-PYOOT (stress on PYOOT)"
        ),
        "prompt": "For a churn prediction task with 80% non-churners, describe your full pipeline.",
    },
    {
        "day": 20,
        "topic": "LLMs, Transformers & RAG",
        "topic_ko": "LLM, 트랜스포머 및 RAG",
        "question": "Explain how Transformers work and describe the RAG architecture.",
        "question_ko": "트랜스포머와 RAG 아키텍처를 설명해 주세요.",
        "summary": (
            "• **Attention:** Attention(Q,K,V) = softmax(QKᵀ/√d_k)·V — each token attends to all others\n"
            "• **RAG:** embed documents → vector DB → retrieve top-k → inject into LLM context\n"
            "• RAG reduces hallucinations, stays up-to-date without retraining\n"
            "• Fine-tuning better when model needs new reasoning style; RAG when knowledge updates frequently"
        ),
        "vocab": [
            ("Self-attention", "셀프 어텐션", "Each token weighs all other tokens to build contextual representations"),
            ("Vector database", "벡터 데이터베이스", "Optimized for dense vector storage and approximate nearest-neighbor search"),
            ("Hallucination", "환각 (LLM)", "When an LLM generates confident but factually incorrect content"),
        ],
        "pronunciation": (
            "• *retrieval* → rih-TREE-vul (stress on TREE)\n"
            "• *transformer* → trans-FOR-mer (stress on FOR)"
        ),
        "prompt": "Compare RAG vs fine-tuning. Give one concrete use-case for each approach.",
    },
    {
        "day": 21,
        "topic": "Coding — Arrays & Hash Maps",
        "topic_ko": "코딩 — 배열과 해시맵",
        "question": "Solve Two Sum and Group Anagrams using hash maps.",
        "question_ko": "해시맵을 사용해 Two Sum과 Group Anagrams를 풀어보세요.",
        "summary": (
            "• **Two Sum O(n):** `seen={}`; for each n, check if target-n in seen; else seen[target-n]=i\n"
            "• **Group Anagrams O(n·k·log k):** key = `tuple(sorted(s))`; group by key with defaultdict\n"
            "• Hash map pattern: when you need O(1) lookup for complement, frequency, or grouping"
        ),
        "vocab": [
            ("Hash map", "해시맵", "O(1) average lookup, insert, delete via hash function"),
            ("Complement", "보수", "The value needed alongside the current element to reach a target sum"),
            ("Anagram", "애너그램", "A word formed by rearranging all letters of another word"),
        ],
        "pronunciation": (
            "• *enumerate* → ih-NYOO-muh-rayt (stress on NYOO)\n"
            "• *anagram* → AN-uh-gram (stress on AN)"
        ),
        "prompt": "Walk through Two Sum step by step: brute force → hash map insight → complexity.",
    },
    {
        "day": 22,
        "topic": "Coding — String Manipulation",
        "topic_ko": "코딩 — 문자열 조작",
        "question": "Solve Valid Anagram and Longest Common Prefix.",
        "question_ko": "Valid Anagram과 Longest Common Prefix를 풀어보세요.",
        "summary": (
            "• **Valid Anagram:** `Counter(s) == Counter(t)` — O(n); or frequency array of 26 ints\n"
            "• **Longest Common Prefix:** vertical scan — compare char by char across all strings\n"
            "• Key patterns: sliding window (max substr), two pointers (palindrome), Counter (anagram)"
        ),
        "vocab": [
            ("Palindrome", "팰린드롬", "String that reads the same forwards and backwards"),
            ("Sliding window", "슬라이딩 윈도우", "Moving range reducing O(n²) substring problems to O(n)"),
            ("Prefix", "접두사", "A substring at the start of a string"),
        ],
        "pronunciation": (
            "• *palindrome* → PAL-in-drohm (stress on PAL)\n"
            "• *prefix* → PREE-fiks (stress on PREE)"
        ),
        "prompt": "Without using sort or Counter, how would you check if two strings are anagrams?",
    },
    {
        "day": 23,
        "topic": "Coding — Trees & Graph Traversal",
        "topic_ko": "코딩 — 트리와 그래프 탐색",
        "question": "Solve Max Depth of Binary Tree and Number of Islands.",
        "question_ko": "이진 트리 최대 깊이와 섬의 개수 문제를 풀어보세요.",
        "summary": (
            "• **Max Depth:** `return 0 if not root else 1 + max(maxDepth(L), maxDepth(R))` — O(n)\n"
            "• **Number of Islands:** DFS flood-fill — find '1', increment count, mark connected '1's as '0'\n"
            "• BFS = shortest path (unweighted); DFS = exhaustive search, cycle detection, topological sort"
        ),
        "vocab": [
            ("DFS", "깊이 우선 탐색", "Traversal exploring as deep as possible before backtracking"),
            ("BFS", "너비 우선 탐색", "Traversal exploring all nodes at current depth before going deeper"),
            ("Flood fill", "플러드 필", "DFS/BFS technique to mark all connected cells in a grid"),
        ],
        "pronunciation": (
            "• *traversal* → truh-VER-sul (stress on VER)\n"
            "• *recursive* → reh-KUR-siv (stress on KUR)"
        ),
        "prompt": "Explain Number of Islands: why DFS, how you avoid revisiting, time/space complexity.",
    },
    {
        "day": 24,
        "topic": "Coding — Binary Search Patterns",
        "topic_ko": "코딩 — 이진 탐색 패턴",
        "question": "Explain the binary search template and solve Find Min in Rotated Sorted Array.",
        "question_ko": "이진 탐색 템플릿과 회전 배열에서 최솟값 찾기를 설명해 주세요.",
        "summary": (
            "• **Template:** `l,r=0,len-1; while l<=r: mid=l+(r-l)//2`\n"
            "• **Find Min Rotated:** compare nums[mid] vs nums[r]; if mid>r, min is right; else left\n"
            "• Always use `l+(r-l)//2` to avoid overflow (good habit even in Python)"
        ),
        "vocab": [
            ("Binary search", "이진 탐색", "Halving search space each iteration; requires sorted input"),
            ("Rotated array", "회전 배열", "Sorted array shifted at a pivot point"),
            ("Left boundary", "왼쪽 경계", "Smallest valid index satisfying a condition; found by collapsing r"),
        ],
        "pronunciation": (
            "• *binary* → BY-nuh-ree (3 syllables, stress on BY)\n"
            "• *rotated* → ROH-tay-tid (stress on ROH)"
        ),
        "prompt": "Walk through binary search on a rotated sorted array. Why compare mid to rightmost?",
    },
    {
        "day": 25,
        "topic": "Coding — Dynamic Programming",
        "topic_ko": "코딩 — 동적 프로그래밍",
        "question": "Solve Climbing Stairs, House Robber, and Kadane's Algorithm.",
        "question_ko": "계단 오르기, 집 털기, Kadane 알고리즘을 풀어보세요.",
        "summary": (
            "• **Climbing Stairs:** dp[i] = dp[i-1] + dp[i-2] (Fibonacci); space-optimize to 2 variables\n"
            "• **House Robber:** dp[i] = max(dp[i-1], dp[i-2]+nums[i]); space-optimize similarly\n"
            "• **Kadane's (Max Subarray):** `cur=max(n, cur+n); max_sum=max(max_sum, cur)` — O(n)/O(1)"
        ),
        "vocab": [
            ("Dynamic programming", "동적 프로그래밍", "Storing subproblem results to avoid recomputation"),
            ("Memoization", "메모이제이션", "Top-down DP: caching recursive call results"),
            ("Recurrence relation", "점화식", "Equation expressing dp[i] in terms of smaller subproblems"),
        ],
        "pronunciation": (
            "• *memoization* → mem-oh-eye-ZAY-shun (stress on ZAY)\n"
            "• *Kadane* → kuh-DAHN"
        ),
        "prompt": "Explain Kadane's algorithm on [-2,1,-3,4,-1,2,1,-5,4] step by step.",
    },
    {
        "day": 26,
        "topic": "Deep Learning — CNNs",
        "topic_ko": "딥러닝 — CNN",
        "question": "How do CNNs work and why are they suited for image data?",
        "question_ko": "CNN의 작동 원리와 이미지 데이터에 적합한 이유를 설명해 주세요.",
        "summary": (
            "• Filters slide across image computing dot products — detect edges → shapes → objects\n"
            "• **Parameter sharing:** one filter scans whole image → far fewer params than dense layer\n"
            "• **MaxPooling:** downsamples, adds translation invariance\n"
            "• **ResNet skip connections:** solve vanishing gradient — enable 100+ layer training"
        ),
        "vocab": [
            ("Kernel/Filter", "커널/필터", "Learnable weight matrix slid across input to detect local features"),
            ("Receptive field", "수용 영역", "Region of input a neuron can see; grows with depth"),
            ("Skip connection", "스킵 연결", "ResNet technique adding input directly to output"),
        ],
        "pronunciation": (
            "• *convolutional* → kon-vuh-LOO-shun-ul (5 syllables, stress on LOO)\n"
            "• *hierarchical* → hy-uh-RAR-kih-kul (stress on RAR)"
        ),
        "prompt": "Why can a ResNet be trained much deeper than a plain CNN? What problem do skip connections solve?",
    },
    {
        "day": 27,
        "topic": "Deep Learning — RNNs & LSTMs",
        "topic_ko": "딥러닝 — RNN과 LSTM",
        "question": "How do RNNs work, what is the vanishing gradient problem, and how does LSTM solve it?",
        "question_ko": "RNN, 기울기 소실 문제, LSTM의 해결 방법을 설명해 주세요.",
        "summary": (
            "• **RNN:** h_t = tanh(W_h·h_{t-1} + W_x·x_t) — same weights at every step\n"
            "• **Vanishing gradient:** gradients shrink exponentially through time → forgets long dependencies\n"
            "• **LSTM:** cell state C_t is a linear 'highway' — gates control what to keep/write/expose\n"
            "• **GRU:** simpler (2 gates, no separate cell state); often comparable performance"
        ),
        "vocab": [
            ("Hidden state", "은닉 상태", "Vector summarizing sequence history passed between RNN timesteps"),
            ("LSTM gates", "LSTM 게이트", "Forget/input/output gates controlling information flow in cell state"),
            ("Gradient clipping", "기울기 클리핑", "Capping gradient norm to prevent exploding gradients"),
        ],
        "pronunciation": (
            "• *recurrent* → reh-KUR-ent (stress on KUR)\n"
            "• *vanishing* → VAN-ish-ing"
        ),
        "prompt": "Why use LSTM over plain RNN for month-long time-series? Give the technical reason.",
    },
    {
        "day": 28,
        "topic": "Deep Learning — Optimization Algorithms",
        "topic_ko": "딥러닝 — 최적화 알고리즘",
        "question": "Compare SGD, Momentum, RMSProp, and Adam.",
        "question_ko": "SGD, Momentum, RMSProp, Adam을 비교해 주세요.",
        "summary": (
            "• **SGD:** noisy but fast; noise helps escape local minima\n"
            "• **Momentum:** accumulates velocity → damps oscillations, accelerates flat dims\n"
            "• **RMSProp:** per-parameter adaptive LR (squared gradient running avg) — great for RNNs\n"
            "• **Adam:** Momentum + RMSProp + bias correction. Default choice. AdamW = decoupled weight decay"
        ),
        "vocab": [
            ("Momentum", "모멘텀", "Accumulates past gradient directions to smooth updates"),
            ("Adaptive LR", "적응형 학습률", "Per-parameter learning rate adjusting based on gradient history"),
            ("Warm-up", "웜업", "Ramping learning rate from low to target to prevent early instability"),
        ],
        "pronunciation": (
            "• *stochastic* → stuh-KAS-tik (stress on KAS)\n"
            "• *annealing* → uh-NEEL-ing (stress on NEEL)"
        ),
        "prompt": "Why might Adam generalize worse than SGD+Momentum despite converging faster?",
    },
    {
        "day": 29,
        "topic": "Deep Learning — Loss & Activation Functions",
        "topic_ko": "딥러닝 — 손실 함수와 활성화 함수",
        "question": "When do you use cross-entropy vs MSE? Compare ReLU, sigmoid, tanh, GELU.",
        "question_ko": "크로스 엔트로피 vs MSE 사용 시점과 ReLU, sigmoid, tanh, GELU를 비교해 주세요.",
        "summary": (
            "• **MSE:** regression; **Cross-entropy:** classification (with softmax)\n"
            "• **Sigmoid:** output (0,1); **Tanh:** output (-1,1); both vanish for large |x|\n"
            "• **ReLU:** max(0,x) — fast, sparse, but dying ReLU problem\n"
            "• **GELU:** smooth, non-monotonic — used in BERT, GPT, modern Transformers"
        ),
        "vocab": [
            ("Cross-entropy", "크로스 엔트로피", "Loss measuring divergence between predicted probs and true labels"),
            ("ReLU", "렐루", "Rectified Linear Unit: max(0,x) — most common hidden activation"),
            ("Logits", "로짓", "Raw unnormalized scores before softmax"),
        ],
        "pronunciation": (
            "• *entropy* → EN-truh-pee (3 syllables)\n"
            "• *sigmoid* → SIG-moyd (rhymes with 'big void')"
        ),
        "prompt": "Why don't we use MSE for classification? Give statistical and gradient-flow reasons.",
    },
    {
        "day": 30,
        "topic": "Deep Learning — BatchNorm, Dropout & Weight Decay",
        "topic_ko": "딥러닝 — 배치 정규화, 드롭아웃, 가중치 감쇠",
        "question": "Explain Batch Normalization and Dropout. How do they prevent overfitting?",
        "question_ko": "배치 정규화와 드롭아웃을 설명하고 과적합 방지 원리를 말해 주세요.",
        "summary": (
            "• **BatchNorm:** normalize activations to zero mean/unit var per mini-batch + learnable γ,β\n"
            "  — reduces internal covariate shift; allows higher LR; mild regularizer\n"
            "• **Dropout:** randomly zero neurons with prob p during training — forces redundant representations\n"
            "• **Weight decay (L2):** shrinks weights each step — use AdamW (decoupled) with Adam"
        ),
        "vocab": [
            ("Batch Normalization", "배치 정규화", "Normalizing activations per mini-batch to stabilize training"),
            ("Dropout", "드롭아웃", "Randomly zeroing neurons to prevent co-adaptation"),
            ("AdamW", "AdamW", "Adam with decoupled weight decay — preferred over Adam + L2"),
        ],
        "pronunciation": (
            "• *normalization* → nor-muh-lih-ZAY-shun (stress on ZAY)\n"
            "• *covariate* → koh-VAIR-ee-it (stress on VAIR)"
        ),
        "prompt": "Why is Dropout turned off at inference? What happens if you forget to scale outputs?",
    },
    {
        "day": 31,
        "topic": "AI/ML — Transfer Learning & Fine-Tuning",
        "topic_ko": "AI/ML — 전이 학습과 파인튜닝",
        "question": "Compare feature extraction vs fine-tuning vs LoRA for transfer learning.",
        "question_ko": "피처 추출, 파인튜닝, LoRA를 비교해 주세요.",
        "summary": (
            "• **Feature extraction:** freeze backbone, train new head — use when data is small + domains similar\n"
            "• **Fine-tuning:** load pretrained, retrain all/some layers with low LR — moderate data, different domain\n"
            "• **LoRA:** add small trainable low-rank matrices to frozen LLM layers — <1% params fine-tuned\n"
            "• Discriminative LRs: lower LR for early layers, higher for later layers"
        ),
        "vocab": [
            ("Transfer learning", "전이 학습", "Reusing a model trained on one task to accelerate a related task"),
            ("LoRA", "저랭크 적응", "Low-Rank Adaptation — efficient fine-tuning adding small trainable matrices"),
            ("Domain adaptation", "도메인 적응", "Bridging training and target data distribution gaps"),
        ],
        "pronunciation": (
            "• *discriminative* → dis-KRIM-ih-nuh-tiv (stress on KRIM)\n"
            "• *LoRA* → LOH-ruh"
        ),
        "prompt": "You have 500 medical X-ray images and ImageNet ResNet. Describe your strategy.",
    },
    {
        "day": 32,
        "topic": "AI/ML — Generative Models (GANs & VAEs)",
        "topic_ko": "AI/ML — 생성 모델 (GAN과 VAE)",
        "question": "How do GANs and VAEs work? What are their failure modes?",
        "question_ko": "GAN과 VAE의 작동 원리와 실패 유형을 설명해 주세요.",
        "summary": (
            "• **GAN:** Generator (noise→fake) vs Discriminator (real/fake) — adversarial minimax game\n"
            "• **GAN failures:** mode collapse (few output types), training instability\n"
            "• **VAE:** encoder→(μ,σ)→sample z→decoder; loss = reconstruction + KL divergence\n"
            "• **Diffusion models** now dominate: no adversarial training, no mode collapse, better diversity"
        ),
        "vocab": [
            ("Mode collapse", "모드 붕괴", "GAN failure where generator produces only a few output types"),
            ("KL divergence", "KL 발산", "Measures how much one probability distribution differs from another"),
            ("Diffusion model", "디퓨전 모델", "Generative model learning to reverse a gradual noise-adding process"),
        ],
        "pronunciation": (
            "• *adversarial* → ad-ver-SAIR-ee-ul (5 syllables, stress on SAIR)\n"
            "• *variational* → vair-ee-AY-shun-ul (stress on AY)"
        ),
        "prompt": "Explain mode collapse in GANs and two techniques to prevent it.",
    },
    {
        "day": 33,
        "topic": "AI/ML — Reinforcement Learning",
        "topic_ko": "AI/ML — 강화 학습",
        "question": "Explain MDP, Q-learning, policy gradient, and actor-critic.",
        "question_ko": "MDP, Q-러닝, 정책 경사, 액터-크리틱을 설명해 주세요.",
        "summary": (
            "• **MDP:** agent in state s takes action a, gets reward r, transitions to s'; maximize Σγᵏrₜ\n"
            "• **Q-learning (value-based):** learn Q(s,a) via Bellman equation; DQN uses neural net + replay\n"
            "• **Policy gradient:** directly optimize π_θ; high variance → add baseline\n"
            "• **Actor-Critic:** actor=policy, critic=value function; PPO most widely used today"
        ),
        "vocab": [
            ("MDP", "마르코프 결정 과정", "Mathematical framework for sequential decision-making under uncertainty"),
            ("Q-value", "Q 값", "Expected return from state s taking action a then acting optimally"),
            ("PPO", "근위 정책 최적화", "Proximal Policy Optimization — stable, widely-used actor-critic algorithm"),
        ],
        "pronunciation": (
            "• *Markov* → MAR-kov (stress on MAR)\n"
            "• *stochastic* → stuh-KAS-tik (stress on KAS)"
        ),
        "prompt": "Compare model-based vs model-free RL: tradeoffs in sample efficiency and planning.",
    },
    {
        "day": 34,
        "topic": "AI/ML — Attention & Transformer Deep Dive",
        "topic_ko": "AI/ML — 어텐션 메커니즘 심화",
        "question": "Explain scaled dot-product attention, multi-head attention, and positional encoding.",
        "question_ko": "스케일드 닷-프로덕트 어텐션, 멀티헤드 어텐션, 위치 인코딩을 설명해 주세요.",
        "summary": (
            "• **Attention:** softmax(QKᵀ/√d_k)·V — scaling prevents softmax saturation\n"
            "• **Multi-head:** h parallel heads with separate Q/K/V projections → different relationship types\n"
            "• **Positional encoding:** sinusoidal (extrapolatable) or learned; RoPE encodes relative position\n"
            "• **Flash Attention:** IO-aware exact attention — 2-4× faster, O(n) memory vs O(n²)"
        ),
        "vocab": [
            ("Query/Key/Value", "쿼리/키/값", "Three projections: Q selects, K matches, V contributes content"),
            ("Causal masking", "인과적 마스킹", "Masking future positions so each token only attends to past"),
            ("Flash Attention", "플래시 어텐션", "IO-aware attention reducing memory from O(n²) to O(n)"),
        ],
        "pronunciation": (
            "• *sinusoidal* → sy-nyuh-SOY-dul (stress on SOY)\n"
            "• *concatenate* → kon-KAT-uh-nayt (stress on KAT)"
        ),
        "prompt": "Why did Transformers replace RNNs? Cover parallelism, attention complexity, positional encoding.",
    },
    {
        "day": 35,
        "topic": "AI/ML — GNNs & Diffusion Models",
        "topic_ko": "AI/ML — 그래프 신경망과 디퓨전 모델",
        "question": "How do GNNs work? Explain latent diffusion models.",
        "question_ko": "GNN의 작동 원리와 잠재 디퓨전 모델을 설명해 주세요.",
        "summary": (
            "• **GNN message passing:** h_v^(l+1) = UPDATE(h_v, AGGREGATE({h_u : u∈N(v)}))\n"
            "• **Diffusion:** forward = add noise T steps; reverse = U-Net predicts noise; sample by denoising\n"
            "• **Latent diffusion (Stable Diffusion):** run diffusion in VAE latent space — much faster\n"
            "• Text conditioning via CLIP embeddings injected via cross-attention"
        ),
        "vocab": [
            ("Message passing", "메시지 전달", "GNN operation aggregating information from graph neighbors"),
            ("Denoising", "노이즈 제거", "Predicting and removing noise at each reverse diffusion step"),
            ("Latent space", "잠재 공간", "Compressed representation; Stable Diffusion runs diffusion here"),
        ],
        "pronunciation": (
            "• *diffusion* → dih-FYOO-zhun (stress on FYOO)\n"
            "• *denoising* → dee-NOY-zing (stress on NOY)"
        ),
        "prompt": "Explain latent diffusion: why run diffusion in latent space? How does text control the output?",
    },
    {
        "day": 36,
        "topic": "SQL — Fundamentals & Execution Order",
        "topic_ko": "SQL — 기초와 실행 순서",
        "question": "Explain SQL query execution order and the difference between WHERE and HAVING.",
        "question_ko": "SQL 실행 순서와 WHERE와 HAVING의 차이를 설명해 주세요.",
        "summary": (
            "**Execution order:** FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT\n\n"
            "• **WHERE:** filters rows *before* grouping — cannot use aggregates\n"
            "• **HAVING:** filters groups *after* GROUP BY — can use COUNT(), SUM() etc.\n"
            "• `COUNT(*)` counts all rows; `COUNT(col)` excludes NULLs"
        ),
        "vocab": [
            ("Aggregate function", "집계 함수", "Computes a single result from multiple rows (COUNT, SUM, AVG)"),
            ("HAVING", "그룹 필터", "Filters groups after GROUP BY; allows aggregate conditions"),
            ("Predicate", "조건절", "Boolean expression in WHERE/HAVING determining which rows are kept"),
        ],
        "pronunciation": (
            "• *aggregate* → AG-ruh-git (noun); stress on AG\n"
            "• *predicate* → PRED-ih-kit; stress on PRED"
        ),
        "prompt": "Find the top 3 product categories by revenue this year with at least 100 orders.",
    },
    {
        "day": 37,
        "topic": "SQL — All JOIN Types",
        "topic_ko": "SQL — 모든 JOIN 유형",
        "question": "Explain INNER, LEFT, FULL OUTER, SELF, and CROSS JOINs.",
        "question_ko": "INNER, LEFT, FULL OUTER, SELF, CROSS JOIN을 설명해 주세요.",
        "summary": (
            "• **INNER JOIN:** only matching rows in both tables\n"
            "• **LEFT JOIN:** all left rows + NULLs where no right match\n"
            "• **FULL OUTER JOIN:** all rows from both; NULLs where unmatched\n"
            "• **Anti-JOIN:** `LEFT JOIN … WHERE right.id IS NULL` — rows with no match"
        ),
        "vocab": [
            ("INNER JOIN", "내부 조인", "Returns only rows with matching values in both tables"),
            ("Cartesian product", "카르테시안 곱", "Every combination of rows from two tables (CROSS JOIN result)"),
            ("Anti-join", "안티 조인", "Rows from one table with no match in another"),
        ],
        "pronunciation": (
            "• *Cartesian* → kar-TEE-zhun (stress on TEE)\n"
            "• *alias* → AY-lee-us (stress on AY)"
        ),
        "prompt": "Find users who have NEVER made a purchase — write it with LEFT JOIN and NOT EXISTS.",
    },
    {
        "day": 38,
        "topic": "SQL — Window Functions",
        "topic_ko": "SQL — 윈도우 함수",
        "question": "Explain ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD with examples.",
        "question_ko": "ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD를 예시와 함께 설명해 주세요.",
        "summary": (
            "• **ROW_NUMBER():** unique sequential integer — no ties\n"
            "• **RANK():** ties share rank, skips after (1,1,3); **DENSE_RANK():** no skips (1,1,2)\n"
            "• **LAG(col,n):** value n rows before; **LEAD(col,n):** value n rows after\n"
            "• Running total: `SUM(rev) OVER (ORDER BY date ROWS UNBOUNDED PRECEDING)`"
        ),
        "vocab": [
            ("Window function", "윈도우 함수", "Computes over a set of rows without collapsing them"),
            ("LAG/LEAD", "이전값/다음값", "Access values from preceding or following rows"),
            ("Running total", "누적 합계", "Cumulative sum computed row-by-row"),
        ],
        "pronunciation": (
            "• *partition* → par-TISH-un (stress on TISH)\n"
            "• *preceding* → preh-SEED-ing (stress on SEED)"
        ),
        "prompt": "Write a query calculating the 7-day rolling average of daily active users.",
    },
    {
        "day": 39,
        "topic": "SQL — CTEs & Recursive Queries",
        "topic_ko": "SQL — CTE와 재귀 쿼리",
        "question": "Compare CTEs, subqueries, and derived tables. What is a recursive CTE?",
        "question_ko": "CTE, 서브쿼리, 파생 테이블을 비교하고 재귀 CTE를 설명해 주세요.",
        "summary": (
            "• **Subquery:** inline; correlated subquery re-runs for each outer row (slow on large tables)\n"
            "• **CTE (WITH clause):** named, readable, reusable within query — prefer over nested subqueries\n"
            "• **Recursive CTE:** `WITH RECURSIVE … UNION ALL` — traverses hierarchies (org charts, trees)\n"
            "• Base case + recursive case joined by UNION ALL"
        ),
        "vocab": [
            ("CTE", "공통 테이블 표현식", "Named temporary result set defined with the WITH clause"),
            ("Correlated subquery", "상관 서브쿼리", "Subquery referencing outer query; re-executes per row"),
            ("Recursive CTE", "재귀 CTE", "CTE referencing itself to traverse hierarchical data"),
        ],
        "pronunciation": (
            "• *correlated* → KOR-uh-lay-tid (stress on KOR)\n"
            "• *hierarchical* → hy-uh-RAR-kih-kul (stress on RAR)"
        ),
        "prompt": "Write a recursive CTE returning each employee and their depth in the org hierarchy.",
    },
    {
        "day": 40,
        "topic": "SQL — NULL Handling, CASE & Date Functions",
        "topic_ko": "SQL — NULL 처리, CASE, 날짜 함수",
        "question": "How does SQL handle NULLs? Explain CASE, COALESCE, and key date functions.",
        "question_ko": "SQL의 NULL 처리, CASE, COALESCE, 주요 날짜 함수를 설명해 주세요.",
        "summary": (
            "• **NULL:** unknown — any comparison with NULL returns NULL; use IS NULL not = NULL\n"
            "• **COALESCE(a,b,c):** returns first non-NULL; **NULLIF(a,b):** returns NULL if a=b\n"
            "• **CASE:** `CASE WHEN … THEN … ELSE … END` — conditional inline; use inside SUM() for pivoting\n"
            "• `DATE_TRUNC('month', ts)` — truncate to period; `DATEDIFF(day, start, end)` — days between"
        ),
        "vocab": [
            ("COALESCE", "코얼레스", "Returns first non-NULL value from a list of expressions"),
            ("CASE expression", "CASE 표현식", "Conditional logic returning different values based on conditions"),
            ("DATE_TRUNC", "날짜 자르기", "Truncates a timestamp to a specified unit (day, month, year)"),
        ],
        "pronunciation": (
            "• *coalesce* → koh-uh-LESS (stress on LESS)\n"
            "• *truncate* → TRUNK-ayt (stress on TRUNK)"
        ),
        "prompt": "Pivot a status column: count 'paid', 'pending', 'failed' orders per user in separate columns.",
    },
    {
        "day": 41,
        "topic": "SQL — Query Optimization & Indexes",
        "topic_ko": "SQL — 쿼리 최적화와 인덱스",
        "question": "How do indexes work? How do you diagnose a slow query?",
        "question_ko": "인덱스의 작동 원리와 느린 쿼리 진단 방법을 설명해 주세요.",
        "summary": (
            "• **B-Tree index:** O(log n) lookup; supports equality, range, ORDER BY\n"
            "• **Composite index:** left-prefix rule — (a,b,c) helps filter on a, a+b, a+b+c, NOT b alone\n"
            "• **EXPLAIN ANALYZE:** check for Seq Scan on large tables, missing index coverage\n"
            "• Avoid functions on indexed columns: `WHERE YEAR(date)=2024` defeats the index"
        ),
        "vocab": [
            ("B-Tree index", "B-트리 인덱스", "Balanced tree enabling O(log n) lookup; default in most databases"),
            ("Query plan", "쿼리 실행 계획", "Database's chosen execution strategy; viewed with EXPLAIN"),
            ("Cardinality", "카디널리티", "Number of distinct values; high cardinality = good index candidate"),
        ],
        "pronunciation": (
            "• *cardinality* → kar-dih-NAL-ih-tee (5 syllables, stress on NAL)\n"
            "• *sequential* → sih-KWEN-shul (stress on KWEN)"
        ),
        "prompt": "Two 10M-row tables JOIN is taking 30 seconds. Walk through your diagnosis process.",
    },
    {
        "day": 42,
        "topic": "SQL — Cohort & Funnel Analysis",
        "topic_ko": "SQL — 코호트 및 퍼널 분석",
        "question": "How do you write SQL for cohort retention and funnel conversion analysis?",
        "question_ko": "SQL로 코호트 리텐션과 퍼널 전환 분석을 어떻게 작성하나요?",
        "summary": (
            "• **Cohort retention:** group by MIN(event_date) → month offset → COUNT(DISTINCT user_id) / cohort_size\n"
            "• **Funnel:** `COUNT(DISTINCT CASE WHEN step='view' THEN user_id END)` per stage\n"
            "• Ensure ordered funnel: step B timestamp > step A timestamp\n"
            "• Churn = active last month but not this month: LEFT JOIN with IS NULL"
        ),
        "vocab": [
            ("Cohort", "코호트", "Group sharing a common starting characteristic (e.g., signup month)"),
            ("Retention rate", "리텐션율", "Percentage of cohort returning and active in a later period"),
            ("Funnel", "퍼널", "Sequential steps toward a goal; conversion measures drop-off at each step"),
        ],
        "pronunciation": (
            "• *cohort* → KOH-hort (stress on KOH)\n"
            "• *retention* → reh-TEN-shun (stress on TEN)"
        ),
        "prompt": "Build a 30-day rolling retention report for a mobile app. Walk through your CTE structure.",
    },
    {
        "day": 43,
        "topic": "SQL — Database Design & Normalization",
        "topic_ko": "SQL — 데이터베이스 설계와 정규화",
        "question": "Explain 1NF, 2NF, 3NF and the OLTP vs OLAP schema tradeoff.",
        "question_ko": "1NF, 2NF, 3NF와 OLTP/OLAP 스키마 트레이드오프를 설명해 주세요.",
        "summary": (
            "• **1NF:** atomic values, no repeating groups\n"
            "• **2NF:** no partial dependencies on composite PK\n"
            "• **3NF:** no transitive dependencies (non-key→non-key)\n"
            "• **OLTP:** normalized — fewer writes anomalies; **OLAP/star schema:** denormalized for fast reads"
        ),
        "vocab": [
            ("Normalization", "정규화", "Organizing tables to reduce redundancy and ensure data integrity"),
            ("Star schema", "스타 스키마", "Fact table + dimension tables — controlled denormalization for analytics"),
            ("Referential integrity", "참조 무결성", "Foreign key values always correspond to existing primary keys"),
        ],
        "pronunciation": (
            "• *transitive* → TRAN-zih-tiv (stress on TRAN)\n"
            "• *referential* → ref-uh-REN-shul (stress on REN)"
        ),
        "prompt": "Design e-commerce schema (users, products, orders, order_items). Explain normalization decisions.",
    },
]

TOTAL_DAYS = len(DAYS)


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
    subs = load_subscribers()
    key = str(chat_id)
    sub = subs.get(key, {})
    current = sub.get("current_day", 0)
    available = [d["day"] for d in DAYS]
    next_days = [d for d in available if d > current]
    return next_days[0] if next_days else available[0]


def advance_day(chat_id: int):
    subs = load_subscribers()
    key = str(chat_id)
    if key not in subs:
        return
    next_day = get_next_day(chat_id)
    subs[key]["current_day"] = next_day
    subs[key]["last_sent"] = date.today().isoformat()
    save_subscribers(subs)


# ── 메시지 포매팅 ────────────────────────────────────────

def _md(text: str) -> str:
    import re
    return re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)


def format_day_message(day_num: int) -> str:
    d = next((x for x in DAYS if x["day"] == day_num), None)
    if not d:
        return f"Day {day_num}의 내용을 찾을 수 없습니다."

    vocab_lines = "\n".join(
        f"  • {v[0]} — {v[1]}: {v[2]}" for v in d["vocab"]
    )

    msg = (
        f"🌅 *Daily English Practice — Day {d['day']}/{TOTAL_DAYS}*\n"
        f"_{d['topic']} · {d['topic_ko']}_\n"
        f"{'─' * 28}\n\n"
        f"📌 *Interview Question*\n"
        f"{d['question']}\n"
        f"_{d['question_ko']}_\n\n"
        f"💡 *핵심 정리*\n{_md(d['summary'])}\n\n"
        f"📚 *Key Vocabulary*\n{vocab_lines}\n\n"
        f"🔊 *발음 포인트*\n{d['pronunciation']}\n\n"
        f"🎤 *Speaking Practice (90초 목표)*\n{d['prompt']}\n\n"
        f"{'─' * 28}\n"
        f"📱 전체 내용 보기: {APP_URL}\n"
        f"/today - 오늘 내용  /day N - 특정 날  /share - 친구에게 공유"
    )
    return msg


def format_curriculum() -> str:
    categories = [
        ("ML 이론 (Days 1–15)", range(1, 16)),
        ("Python & 코딩 (Days 16–25)", range(16, 26)),
        ("AI/ML/딥러닝 (Days 26–35)", range(26, 36)),
        ("SQL (Days 36–43)", range(36, 44)),
    ]
    lines = [f"📋 *전체 커리큘럼 ({TOTAL_DAYS}일)*\n"]
    for cat_name, day_range in categories:
        lines.append(f"\n*{cat_name}*")
        for d in DAYS:
            if d["day"] in day_range:
                lines.append(f"  Day {d['day']:2d}: {d['topic']}")
    lines.append(f"\n📱 웹앱: {APP_URL}")
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
        f"🎉 *구독 완료!*\n\n"
        f"매일 아침 *8시 (한국 시간)* 에 오늘의 영어 인터뷰 학습 내용을 보내드립니다.\n\n"
        f"📚 *{TOTAL_DAYS}일 커리큘럼*\n"
        f"• Days 1–15: ML 이론 (Bias-Variance, Cross-Validation, XGBoost...)\n"
        f"• Days 16–25: Python & 코딩 알고리즘\n"
        f"• Days 26–35: AI/ML/딥러닝 (CNNs, Transformers, RAG...)\n"
        f"• Days 36–43: SQL (Window Functions, Cohort Analysis...)\n\n"
        f"📱 웹앱 (전체 내용 + 발음 연습): {APP_URL}\n\n"
        f"지금 바로 첫 번째 학습을 받으려면 /today 를 입력하세요!\n\n"
        f"/list — 전체 커리큘럼  /share — 친구에게 공유  /stop — 구독 취소",
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
        await update.message.reply_text("먼저 /start 로 구독하세요! 📚")
        return

    day_num = get_next_day(chat_id)
    msg = format_day_message(day_num)
    await update.message.reply_text(msg, parse_mode="Markdown")
    advance_day(chat_id)


async def cmd_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(f"사용법: /day 1  (1–{TOTAL_DAYS} 범위)")
        return

    try:
        day_num = int(context.args[0])
    except ValueError:
        await update.message.reply_text("숫자를 입력해주세요. 예: /day 5")
        return

    if not 1 <= day_num <= TOTAL_DAYS:
        await update.message.reply_text(f"Day 1부터 Day {TOTAL_DAYS} 사이의 숫자를 입력해주세요.")
        return

    msg = format_day_message(day_num)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_curriculum(), parse_mode="Markdown")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subs = load_subscribers()
    total = len(subs)
    now_kst = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    await update.message.reply_text(
        f"📊 *Daily English Practice — 현황*\n\n"
        f"• 구독자 수: *{total}명*\n"
        f"• 총 커리큘럼: *{TOTAL_DAYS}일*\n"
        f"• 웹앱: {APP_URL}\n\n"
        f"_{now_kst} 기준_\n\n"
        f"친구에게 공유하려면 /share 를 입력하세요!",
        parse_mode="Markdown",
    )


async def cmd_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    share_text = (
        f"📚 *Daily English Practice*\n\n"
        f"데이터 사이언스 & ML 영어 인터뷰 준비 앱!\n\n"
        f"✅ {TOTAL_DAYS}일 커리큘럼 (ML · Python · AI/DL · SQL · 코딩)\n"
        f"✅ 한국어/영어 이중 언어 설명\n"
        f"✅ IPA 발음 가이드 + 90초 스피킹 연습\n"
        f"✅ 매일 아침 8시 텔레그램 자동 발송\n\n"
        f"🔗 웹앱: {APP_URL}\n"
        f"🤖 이 봇 공유: @daily\\_english\\_practice\\_bot\n\n"
        f"친구에게 복사해서 보내세요!"
    )
    await update.message.reply_text(share_text, parse_mode="Markdown")


async def cmd_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💬 *피드백 남기기*\n\n"
        f"학습 내용이 도움이 되었나요? 개선할 점이 있나요?\n\n"
        f"1️⃣ *웹앱 내 피드백:*\n"
        f"   각 Day 하단의 👍 / 👎 버튼으로 평가해주세요\n"
        f"   {APP_URL}\n\n"
        f"2️⃣ *이메일 피드백:*\n"
        f"   tcgyver@gmail.com 으로 자유롭게 보내주세요\n\n"
        f"여러분의 피드백이 콘텐츠 개선에 큰 도움이 됩니다! 🙏",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"*Daily English Practice Bot — 도움말*\n\n"
        f"/start    — 매일 8시 자동 발송 구독\n"
        f"/stop     — 구독 취소\n"
        f"/today    — 오늘의 학습 즉시 받기\n"
        f"/day N    — 특정 날 학습 요청 (1–{TOTAL_DAYS})\n"
        f"/list     — 전체 {TOTAL_DAYS}일 커리큘럼 보기\n"
        f"/stats    — 구독자 현황\n"
        f"/share    — 친구에게 공유할 텍스트 받기\n"
        f"/feedback — 피드백 남기기\n"
        f"/help     — 도움말\n\n"
        f"📱 웹앱: {APP_URL}",
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

    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("stop",     cmd_stop))
    app.add_handler(CommandHandler("today",    cmd_today))
    app.add_handler(CommandHandler("day",      cmd_day))
    app.add_handler(CommandHandler("list",     cmd_list))
    app.add_handler(CommandHandler("stats",    cmd_stats))
    app.add_handler(CommandHandler("share",    cmd_share))
    app.add_handler(CommandHandler("feedback", cmd_feedback))
    app.add_handler(CommandHandler("help",     cmd_help))

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
    print(f"📚 커리큘럼: {TOTAL_DAYS}일")
    print(f"📱 웹앱: {APP_URL}")
    print("종료: Ctrl+C\n")

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
