import os

import streamlit as st
from api_client import ask_rag

st.set_page_config(
    page_title="ATA RAG Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

TEXTS = {
    "English": {
        "title": "Your ATA University Assistant",
        "subtitle": (
            "Ask questions about ATA University and receive clear, "
            "source-grounded answers."
        ),
        "welcome": (
            "Hello! 👋 I’m the ATA University Assistant. "
            "What would you like to learn today?"
        ),
        "placeholder": "Ask a question about ATA University...",
        "try_asking": "Try asking one of these questions",
        "suggestions": [
            "What are the admission requirements?",
            "Where is ATA University located?",
            "How can I contact the university?"
        ],
        "demo_reply": (
            "I received your question successfully. The RAG backend will be "
            "connected during the integration stage. This demonstration shows "
            "how a grounded answer and its source will appear."
        ),
        "source": "Verified source",
        "open_source": "Open source ↗",
        "clear": "Clear conversation",
        "grounded": "Source-grounded",
        "demo": "Demo response"
    },
    "Türkçe": {
        "title": "ATA Üniversitesi Asistanınız",
        "subtitle": (
            "ATA Üniversitesi hakkında sorular sorun ve "
            "kaynaklara dayalı net yanıtlar alın."
        ),
        "welcome": (
            "Merhaba! 👋 Ben ATA Üniversitesi Asistanıyım. "
            "Bugün ne öğrenmek istersiniz?"
        ),
        "placeholder": "ATA Üniversitesi hakkında bir soru sorun...",
        "try_asking": "Bu sorulardan birini deneyebilirsiniz",
        "suggestions": [
            "Kabul şartları nelerdir?",
            "ATA Üniversitesi nerede bulunuyor?",
            "Üniversiteyle nasıl iletişim kurabilirim?"
        ],
        "demo_reply": (
            "Sorunuzu başarıyla aldım. RAG backend sistemi entegrasyon "
            "aşamasında bağlanacak. Bu demo, kaynaklı cevabın ekranda "
            "nasıl görüneceğini göstermektedir."
        ),
        "source": "Doğrulanmış kaynak",
        "open_source": "Kaynağı aç ↗",
        "clear": "Konuşmayı temizle",
        "grounded": "Kaynak destekli",
        "demo": "Demo cevap"
    },
    "Polski": {
        "title": "Twój Asystent Uniwersytetu ATA",
        "subtitle": (
            "Zadawaj pytania o Uniwersytet ATA i otrzymuj "
            "jasne odpowiedzi oparte na źródłach."
        ),
        "welcome": (
            "Cześć! 👋 Jestem Asystentem Uniwersytetu ATA. "
            "Czego chcesz się dzisiaj dowiedzieć?"
        ),
        "placeholder": "Zadaj pytanie o Uniwersytet ATA...",
        "try_asking": "Wypróbuj jedno z tych pytań",
        "suggestions": [
            "Jakie są wymagania rekrutacyjne?",
            "Gdzie znajduje się Uniwersytet ATA?",
            "Jak mogę skontaktować się z uczelnią?"
        ],
        "demo_reply": (
            "Twoje pytanie zostało odebrane. Backend RAG zostanie połączony "
            "na etapie integracji. Ta demonstracja pokazuje sposób "
            "wyświetlania odpowiedzi i jej źródła."
        ),
        "source": "Zweryfikowane źródło",
        "open_source": "Otwórz źródło ↗",
        "clear": "Wyczyść rozmowę",
        "grounded": "Oparte na źródłach",
        "demo": "Odpowiedź demonstracyjna"
    }
}

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(
                    circle at 90% 5%,
                    rgba(249, 115, 22, 0.12),
                    transparent 25rem
                ),
                #f6f8fc;
            color: #172033;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        #MainMenu,
footer {
    visibility: hidden;
}

[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    display: block !important;
    visibility: visible !important;
}

        .main .block-container {
            max-width: 1000px;
            padding-top: 2rem;
            padding-bottom: 8rem;
        }

        [data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid #243044;
        }

        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] label {
            color: #f8fafc !important;
        }

        [data-testid="stSidebar"] div[data-baseweb="select"] > div {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
        }

        [data-testid="stSidebar"]
        div[data-baseweb="select"] span {
            color: #f8fafc !important;
        }

        .side-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 8px 0 30px;
        }

        .side-logo {
            display: grid;
            place-items: center;
            width: 46px;
            height: 46px;
            border-radius: 14px;
            background: linear-gradient(135deg, #fb923c, #ea580c);
            font-size: 23px;
            box-shadow: 0 8px 22px rgba(249, 115, 22, 0.28);
        }

        .side-title {
            color: white;
            font-size: 18px;
            font-weight: 750;
            line-height: 1.15;
        }

        .side-subtitle {
            color: #94a3b8;
            font-size: 12px;
            margin-top: 4px;
        }

        .side-label {
            margin: 4px 0 8px;
            color: #cbd5e1 !important;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .side-card {
            margin-top: 24px;
            padding: 16px;
            border: 1px solid #334155;
            border-radius: 15px;
            background: #1e293b;
        }

        .side-card-title {
            color: #f8fafc;
            font-weight: 700;
            margin-bottom: 12px;
        }

        .side-row {
            display: flex;
            justify-content: space-between;
            margin-top: 9px;
            color: #cbd5e1;
            font-size: 13px;
        }

        .ready {
            color: #4ade80;
            font-weight: 700;
        }

        .pending {
            color: #fbbf24;
            font-weight: 700;
        }

        [data-testid="stSidebar"] .stButton > button {
            width: 100%;
            margin-top: 12px;
            color: #f8fafc;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            color: white;
            border-color: #f97316;
            background: #263449;
        }

        .hero-card {
            padding: 34px 38px;
            margin-bottom: 24px;
            border-radius: 26px;
            color: white;
            background:
                radial-gradient(
                    circle at 90% 10%,
                    rgba(255, 255, 255, 0.20),
                    transparent 13rem
                ),
                linear-gradient(135deg, #fb7a1a, #e9550b);
            box-shadow: 0 20px 45px rgba(234, 88, 12, 0.20);
        }

        .hero-top {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 22px;
        }

        .hero-icon {
            display: grid;
            place-items: center;
            width: 42px;
            height: 42px;
            border-radius: 13px;
            background: rgba(255, 255, 255, 0.18);
            font-size: 21px;
        }

        .hero-brand {
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 0.10em;
        }

        .verified-pill {
            margin-left: auto;
            padding: 7px 11px;
            border: 1px solid rgba(255, 255, 255, 0.35);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.15);
            font-size: 12px;
            font-weight: 650;
        }

        .hero-card h1 {
            max-width: 700px;
            margin: 0;
            font-size: clamp(30px, 4vw, 43px);
            line-height: 1.12;
            letter-spacing: -0.035em;
        }

        .hero-card p {
            max-width: 680px;
            margin: 14px 0 0;
            color: rgba(255, 255, 255, 0.92);
            font-size: 16px;
            line-height: 1.65;
        }

        [data-testid="stChatMessage"] {
            margin-bottom: 12px;
            padding: 16px 18px;
            color: #172033;
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            box-shadow: 0 7px 20px rgba(15, 23, 42, 0.05);
        }

        [data-testid="stChatMessage"] p {
            color: #263449 !important;
            line-height: 1.65;
        }

        .question-title {
            margin: 24px 0 10px;
            color: #64748b;
            font-size: 13px;
            font-weight: 750;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .main .stButton > button {
            min-height: 70px;
            color: #334155;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid #e2e8f0;
            border-radius: 15px;
            text-align: left;
            box-shadow: 0 5px 15px rgba(15, 23, 42, 0.04);
        }

        .main .stButton > button:hover {
            color: #c2410c;
            background: #fff7ed;
            border-color: #fb923c;
        }

        .demo-badge {
            display: inline-block;
            margin-top: 8px;
            padding: 5px 9px;
            color: #9a3412;
            background: #ffedd5;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 750;
        }

        .source-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 14px;
            margin-top: 12px;
            padding: 12px 14px;
            border: 1px solid #fed7aa;
            border-radius: 13px;
            background: #fff7ed;
            color: #7c2d12;
            font-size: 13px;
        }

        .source-card a {
            color: #c2410c;
            font-weight: 750;
            text-decoration: none;
            white-space: nowrap;
        }

        .source-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            margin-right: 7px;
            border-radius: 50%;
            background: #22c55e;
        }

        [data-testid="stChatInput"] {
            background: white;
            border: 1px solid #cbd5e1;
            border-radius: 17px;
            box-shadow: 0 12px 35px rgba(15, 23, 42, 0.12);
        }

        [data-testid="stChatInput"] textarea {
            color: #172033 !important;
        }

        [data-testid="stChatInput"] textarea::placeholder {
            color: #94a3b8 !important;
        }

        [data-testid="stBottom"] {
            background:
                linear-gradient(
                    to bottom,
                    rgba(246, 248, 252, 0),
                    #f6f8fc 38%
                );
        }

        @media (max-width: 700px) {
            .hero-card {
                padding: 27px 23px;
            }

            .verified-pill {
                display: none;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)

if "language" not in st.session_state:
    st.session_state.language = "English"

with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="side-logo">🎓</div>
            <div>
                <div class="side-title">ATA Assistant</div>
                <div class="side-subtitle">University Knowledge Hub</div>
            </div>
        </div>
        <p class="side-label">Language / Dil / Język</p>
        """,
        unsafe_allow_html=True
    )

    language = st.selectbox(
        "Language",
        ["English", "Türkçe", "Polski"],
        key="language",
        label_visibility="collapsed"
    )

text = TEXTS[language]
backend_is_configured = bool(os.getenv("ATA_RAG_API_URL", "").strip())
backend_status_class = "ready" if backend_is_configured else "pending"
backend_status_label = "Connected" if backend_is_configured else "Pending"

if (
    "messages" not in st.session_state
    or st.session_state.get("last_language") != language
):
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": text["welcome"],
            "source_url": None
        }
    ]
    st.session_state.last_language = language

with st.sidebar:
    st.markdown(
        f"""
        <div class="side-card">
            <div class="side-card-title">MVP Status</div>
            <div class="side-row">
                <span>Chat interface</span>
                <span class="ready">Ready</span>
            </div>
            <div class="side-row">
                <span>3 languages</span>
                <span class="ready">Ready</span>
            </div>
            <div class="side-row">
                <span>RAG backend</span>
                <span class="{backend_status_class}">{backend_status_label}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(f"🗑️ {text['clear']}", width="stretch"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": text["welcome"],
                "source_url": None
            }
        ]
        st.rerun()

st.markdown(
    f"""
    <div class="hero-card">
        <div class="hero-top">
            <div class="hero-icon">🎓</div>
            <div class="hero-brand">ATA UNIVERSITY</div>
            <div class="verified-pill">● {text["grounded"]}</div>
        </div>
        <h1>{text["title"]}</h1>
        <p>{text["subtitle"]}</p>
    </div>
    """,
    unsafe_allow_html=True
)

for message in st.session_state.messages:
    avatar = "🎓" if message["role"] == "assistant" else "👤"

    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])

        if message.get("source_url"):
            if message.get("is_demo", False):
                st.markdown(
                    f'<span class="demo-badge">{text["demo"]}</span>',
                    unsafe_allow_html=True
                )

            source_label = message.get(
                "source_label",
                "akademiata.pl"
            )

            st.markdown(
                f"""
                <div class="source-card">
                    <div>
                        <span class="source-dot"></span>
                        <strong>{text["source"]}:</strong> {source_label}
                    </div>
                    <a href="{message["source_url"]}" target="_blank">
                        {text["open_source"]}
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )

selected_question = None

if len(st.session_state.messages) == 1:
    st.markdown(
        f'<div class="question-title">{text["try_asking"]}</div>',
        unsafe_allow_html=True
    )

    columns = st.columns(3)

    for index, suggestion in enumerate(text["suggestions"]):
        with columns[index]:
            if st.button(
                f"↗  {suggestion}",
                key=f"suggestion-{language}-{index}",
                width="stretch"
            ):
                selected_question = suggestion

typed_question = st.chat_input(text["placeholder"])
question = typed_question or selected_question

if question and question.strip():
    clean_question = question.strip()

    st.session_state.messages.append(
        {
            "role": "user",
            "content": clean_question,
            "source_url": None
        }
    )

    api_result = ask_rag(clean_question, language)

    if api_result["success"]:
        sources = api_result["sources"]
        first_source = sources[0] if sources else {}

        assistant_message = {
            "role": "assistant",
            "content": api_result["answer"],
            "source_url": first_source.get("url"),
            "source_label": first_source.get(
                "title",
                text["source"]
            ),
            "is_demo": False
        }

    else:
        assistant_message = {
            "role": "assistant",
            "content": text["demo_reply"],
            "source_url": "https://akademiata.pl",
            "source_label": "akademiata.pl",
            "is_demo": True
        }

    st.session_state.messages.append(assistant_message)
    st.rerun()
