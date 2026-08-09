import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="ATA Assistant Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
        .stApp {
            background: #f6f8fc;
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

        [data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid #243044;
        }

        [data-testid="stSidebar"] * {
            color: #f8fafc;
        }

        [data-testid="stSidebar"]
        div[data-baseweb="select"] > div {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
        }

        .main .block-container {
            max-width: 1250px;
            padding-top: 2rem;
            padding-bottom: 4rem;
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
        }

        .side-title {
            color: white;
            font-size: 18px;
            font-weight: 750;
        }

        .side-subtitle {
            color: #94a3b8;
            font-size: 12px;
            margin-top: 3px;
        }

        .hero-card {
            padding: 29px 32px;
            margin-bottom: 24px;
            border-radius: 24px;
            color: white;
            background: linear-gradient(135deg, #172033, #263449);
            box-shadow: 0 16px 38px rgba(15, 23, 42, 0.15);
        }

        .hero-label {
            color: #fb923c;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.12em;
        }

        .hero-card h1 {
            margin: 9px 0 7px;
            font-size: 35px;
        }

        .hero-card p {
            margin: 0;
            color: #cbd5e1;
        }

        [data-testid="stMetric"] {
            padding: 18px;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            box-shadow: 0 5px 18px rgba(15, 23, 42, 0.05);
        }

        [data-testid="stMetricLabel"] {
            color: #64748b;
        }

        [data-testid="stMetricValue"] {
            color: #172033;
        }

        .section-title {
            margin: 18px 0 10px;
            color: #172033;
            font-size: 18px;
            font-weight: 750;
        }

        .demo-note {
            margin-top: 20px;
            padding: 13px 15px;
            border: 1px solid #fed7aa;
            border-radius: 13px;
            color: #9a3412;
            background: #fff7ed;
            font-size: 13px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="side-logo">📊</div>
            <div>
                <div class="side-title">ATA Analytics</div>
                <div class="side-subtitle">RAG Performance Dashboard</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    period = st.selectbox(
        "Reporting period",
        ["Last 7 days", "Last 30 days", "Last 90 days"]
    )

    st.markdown("---")
    st.markdown("**System status**")
    st.success("Chat interface: Online")
    st.info("Analytics data: Demo mode")
    st.warning("RAG backend: Pending integration")

period_metrics = {
    "Last 7 days": {
        "questions": 312,
        "answer_rate": 92.4,
        "retrieval": 0.81,
        "latency": 1.3,
        "tokens": 68420
    },
    "Last 30 days": {
        "questions": 1248,
        "answer_rate": 91.8,
        "retrieval": 0.79,
        "latency": 1.4,
        "tokens": 274850
    },
    "Last 90 days": {
        "questions": 3615,
        "answer_rate": 90.9,
        "retrieval": 0.78,
        "latency": 1.5,
        "tokens": 801240
    }
}

metrics = period_metrics[period]

st.markdown(
    """
    <div class="hero-card">
        <div class="hero-label">ATA UNIVERSITY · ADMIN PANEL</div>
        <h1>Assistant Analytics Dashboard</h1>
        <p>
            Monitor questions, retrieval quality, response speed,
            source usage and unanswered requests.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

metric_columns = st.columns(5)

metric_columns[0].metric(
    "Total questions",
    f"{metrics['questions']:,}",
    "8.2%"
)

metric_columns[1].metric(
    "Answer rate",
    f"{metrics['answer_rate']}%",
    "1.4%"
)

metric_columns[2].metric(
    "Retrieval score",
    f"{metrics['retrieval']:.2f}",
    "0.03"
)

metric_columns[3].metric(
    "Average latency",
    f"{metrics['latency']} s",
    "-0.2 s"
)

metric_columns[4].metric(
    "Token usage",
    f"{metrics['tokens']:,}",
    "6.1%"
)

daily_activity = pd.DataFrame(
    {
        "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Questions": [34, 48, 41, 56, 63, 39, 31],
        "Answered": [32, 44, 38, 51, 58, 36, 29]
    }
).set_index("Day")

common_questions = pd.DataFrame(
    {
        "Category": [
            "Admissions",
            "Required documents",
            "Tuition",
            "Semester dates",
            "Dean's office"
        ],
        "Questions": [84, 67, 55, 42, 36]
    }
).set_index("Category")

left_chart, right_chart = st.columns([1.4, 1])

with left_chart:
    st.markdown(
        '<div class="section-title">Question activity</div>',
        unsafe_allow_html=True
    )
    st.line_chart(daily_activity, height=300)

with right_chart:
    st.markdown(
        '<div class="section-title">Common question categories</div>',
        unsafe_allow_html=True
    )
    st.bar_chart(common_questions, height=300)

unanswered_questions = pd.DataFrame(
    {
        "Unanswered question": [
            "When will the new academic calendar be published?",
            "Is accommodation available for exchange students?",
            "Where can I download the internship agreement?"
        ],
        "Times asked": [12, 8, 6],
        "Best retrieval score": [0.52, 0.57, 0.61]
    }
)

source_performance = pd.DataFrame(
    {
        "Source": [
            "Admissions",
            "Student information",
            "Academic calendar",
            "Contact page"
        ],
        "Clicks": [146, 118, 93, 72],
        "Average score": [0.88, 0.84, 0.79, 0.76]
    }
)

left_table, right_table = st.columns(2)

with left_table:
    st.markdown(
        '<div class="section-title">Unanswered questions</div>',
        unsafe_allow_html=True
    )
    st.dataframe(
        unanswered_questions,
        hide_index=True,
        use_container_width=True
    )

with right_table:
    st.markdown(
        '<div class="section-title">Top-clicked sources</div>',
        unsafe_allow_html=True
    )
    st.dataframe(
        source_performance,
        hide_index=True,
        use_container_width=True
    )

feedback_positive = 86
st.markdown(
    '<div class="section-title">User feedback</div>',
    unsafe_allow_html=True
)
st.progress(feedback_positive / 100)
st.caption(
    f"👍 {feedback_positive}% helpful · "
    f"👎 {100 - feedback_positive}% not helpful"
)

st.markdown(
    """
    <div class="demo-note">
        <strong>Demo analytics:</strong>
        The current values are sample data. They will be replaced with live
        RAG metrics when the backend and database are integrated.
    </div>
    """,
    unsafe_allow_html=True
)