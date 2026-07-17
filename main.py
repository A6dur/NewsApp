import os
from datetime import datetime, timedelta

import requests
import streamlit as st

BASE_URL = "https://newsapi.org/v2/everything"

# ----------------------------------------------------------------------------
# Page config & styling
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="News Reader",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .stApp { background-color: #0f1117; }

    .app-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .app-subtitle {
        color: #9aa0ac;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
    }

    .article-card {
        background: #1a1d27;
        border: 1px solid #2a2e3a;
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1.1rem;
        transition: border-color 0.15s ease;
    }
    .article-card:hover {
        border-color: #4a6cf7;
    }
    .article-title {
        font-size: 1.15rem;
        font-weight: 700;
        line-height: 1.4;
        margin-bottom: 0.4rem;
    }
    .article-meta {
        color: #8a90a0;
        font-size: 0.85rem;
        margin-bottom: 0.6rem;
    }
    .article-desc {
        color: #cdd1da;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .badge {
        display: inline-block;
        background: #2a2e3a;
        color: #b8bfcc;
        border-radius: 999px;
        padding: 0.1rem 0.6rem;
        font-size: 0.75rem;
        margin-right: 0.4rem;
    }
    a.read-more {
        text-decoration: none;
        font-weight: 600;
        color: #4a6cf7 !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
if "articles" not in st.session_state:
    st.session_state.articles = []
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# ----------------------------------------------------------------------------
# Sidebar: API key + search controls
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    env_key = os.environ.get("NEWSAPI_KEY", "")
    secrets_key = ""
    try:
        secrets_key = st.secrets.get("NEWSAPI_KEY", "")
    except Exception:
        pass

    default_key = secrets_key or env_key

    if not default_key:
        st.info(
            "🔑 You'll need a free NewsAPI key to use this app.\n\n"
            "Get one at **[newsapi.org](https://newsapi.org/register)** "
            "(takes about 30 seconds), then paste it below."
        )

    api_key = st.text_input(
        "NewsAPI Key",
        value=default_key,
        type="password",
        help="Get a free key at https://newsapi.org. Stored only for this "
             "session — not saved anywhere. Prefer setting NEWSAPI_KEY as an "
             "env var or in .streamlit/secrets.toml instead of pasting it here.",
    )

    st.markdown("---")
    st.markdown("### 🔎 Search")

    query = st.text_input("Topic", placeholder="e.g. artificial intelligence")

    col_a, col_b = st.columns(2)
    with col_a:
        sort_by = st.selectbox("Sort by", ["popularity", "relevancy", "publishedAt"])
    with col_b:
        language = st.selectbox(
            "Language",
            ["en", "es", "fr", "de", "it", "pt", "ar", "zh", "ru"],
            index=0,
        )

    num_articles = st.slider("Number of articles", min_value=1, max_value=50, value=10)

    date_range = st.selectbox(
        "Time range",
        ["Any time", "Past 24 hours", "Past week", "Past month"],
        index=0,
    )

    search_clicked = st.button("🔍 Search News", use_container_width=True, type="primary")

# ----------------------------------------------------------------------------
# Fetch logic
# ----------------------------------------------------------------------------
def get_news(q, key, sort, lang, limit, time_range):
    params = {
        "q": q,
        "sortBy": sort,
        "language": lang,
        "pageSize": limit,
        "apiKey": key,
    }

    if time_range == "Past 24 hours":
        params["from"] = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    elif time_range == "Past week":
        params["from"] = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    elif time_range == "Past month":
        params["from"] = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            st.error(f"❌ API Error: {data.get('message', 'Unknown error')}")
            return []

        return data.get("articles", [])

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network error: {e}")
        return []


if search_clicked:
    if not api_key:
        st.error("Please enter your NewsAPI key in the sidebar.")
    elif not query.strip():
        st.error("Please enter a topic to search for.")
    else:
        with st.spinner(f"Fetching news about '{query}'..."):
            st.session_state.articles = get_news(
                query.strip(), api_key, sort_by, language, num_articles, date_range
            )
            st.session_state.last_query = query.strip()

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown('<div class="app-title">📰 News Reader</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Search live headlines from around the web, powered by NewsAPI.</div>',
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------------
articles = st.session_state.articles

if not articles:
    if not api_key:
        st.info(
            "🔑 To get started, grab a free API key from "
            "**[newsapi.org](https://newsapi.org/register)**, paste it into the "
            "sidebar, then enter a topic and hit **Search News**."
        )
    else:
        st.info("👈 Enter a topic in the sidebar and click **Search News** to get started.")
else:
    st.success(f"Found {len(articles)} articles for **{st.session_state.last_query}**")

    # Filter out removed/broken entries NewsAPI sometimes returns
    articles = [a for a in articles if a.get("title") and a.get("title") != "[Removed]"]

    view = st.radio("View", ["Card list", "Grid"], horizontal=True, label_visibility="collapsed")

    def render_article(article, idx):
        title = article.get("title") or "No Title"
        author = article.get("author") or "Unknown"
        description = article.get("description") or "No description available."
        source = article.get("source", {}).get("name", "Unknown")
        published = article.get("publishedAt") or "Unknown"
        url = article.get("url") or "#"
        image = article.get("urlToImage")

        with st.container():
            st.markdown('<div class="article-card">', unsafe_allow_html=True)
            cols = st.columns([1, 3]) if (image and view == "Card list") else [st.container()]

            if image and view == "Card list":
                with cols[0]:
                    try:
                        st.image(image, use_container_width=True)
                    except Exception:
                        pass
                text_col = cols[1]
            else:
                if image:
                    try:
                        st.image(image, use_container_width=True)
                    except Exception:
                        pass
                text_col = st.container()

            with text_col:
                st.markdown(f'<div class="article-title">{title}</div>', unsafe_allow_html=True)
                pub_display = published
                try:
                    pub_display = datetime.strptime(published, "%Y-%m-%dT%H:%M:%SZ").strftime(
                        "%b %d, %Y · %H:%M UTC"
                    )
                except Exception:
                    pass
                st.markdown(
                    f'<div class="article-meta">'
                    f'<span class="badge">🏢 {source}</span>'
                    f'<span class="badge">✍ {author}</span>'
                    f'<span class="badge">📅 {pub_display}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(f'<div class="article-desc">{description}</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<a class="read-more" href="{url}" target="_blank">🔗 Read full article →</a>',
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

    if view == "Card list":
        for i, article in enumerate(articles):
            render_article(article, i)
    else:
        grid_cols = st.columns(3)
        for i, article in enumerate(articles):
            with grid_cols[i % 3]:
                render_article(article, i)
