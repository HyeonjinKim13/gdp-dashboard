"""
생활화학제품 위반정보 분석 대시보드 (Streamlit 시제품)
실행:  streamlit run app.py

- analysis_long.csv 가 같은 폴더에 있으면 그 데이터를 사용합니다.
- 없으면 '가짜(데모) 데이터'로 화면을 띄워서, 전처리가 끝나기 전에도 틀을 먼저 만들어볼 수 있습니다.

analysis_long.csv 에 필요한 컬럼 (1행 = 제품 1개의 '위반사유 1개'):
    prdt_mstr_no : 제품마스터번호
    품목         : 정제된 품목명
    위반유형     : 안전기준 위반 / 안전기준 확인 위반 / 표시기준 위반 ...
    위반물질     : 폼알데하이드, MIT ... (물질이 없는 사유는 '해당없음')
    조치유형     : 회수명령 / 판매금지 ...
    조치연도     : 2016, 2017 ...
"""
import platform
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib import font_manager

# ---------------------------------------------------------------- 기본 설정
st.set_page_config(page_title="생활화학제품 위반정보 대시보드", layout="wide")
sns.set_theme(style="whitegrid")


def set_korean_font():
    """그래프 한글 깨짐 방지 (OS별로 설치된 한글 폰트를 자동 선택)"""
    candidates = {
        "Windows": ["Malgun Gothic"],
        "Darwin": ["AppleGothic"],
        "Linux": ["NanumGothic", "Noto Sans CJK KR"],
    }.get(platform.system(), [])
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in installed:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False


set_korean_font()


# ---------------------------------------------------------------- 데이터 불러오기
@st.cache_data
def load_data():
    path = Path(__file__).parent / "analysis_long.csv"
    if path.exists():
        return pd.read_csv(path), False

    # 데모 데이터 (전처리 완료 전 화면 설계용) -----------------------------
    rng = np.random.default_rng(0)
    품목 = ["코팅제", "물체탈/염색제", "가습기용 항균·소독제제", "김서림 방지제", "합성세제", "틈새충진제"]
    유형 = ["안전기준 위반", "안전기준 확인 위반", "표시기준 위반"]
    물질 = ["폼알데하이드", "아세트알데하이드", "MIT", "CMIT", "벤젠", "해당없음"]
    조치 = ["회수명령", "판매금지", "개선명령"]
    n = 600
    df = pd.DataFrame({
        "prdt_mstr_no": rng.integers(1, 350, n),
        "품목": rng.choice(품목, n, p=[.35, .2, .1, .1, .15, .1]),
        "위반유형": rng.choice(유형, n, p=[.55, .25, .2]),
        "위반물질": rng.choice(물질, n),
        "조치유형": rng.choice(조치, n),
        "조치연도": rng.integers(2016, 2026, n),
    })
    return df, True


df, is_demo = load_data()

# ---------------------------------------------------------------- 사이드바 (필터)
st.sidebar.header("필터")
all_items = sorted(df["품목"].unique())
sel_items = st.sidebar.multiselect("품목 선택 (비우면 전체)", all_items, default=[])
y_min, y_max = int(df["조치연도"].min()), int(df["조치연도"].max())
sel_years = st.sidebar.slider("조치연도", y_min, y_max, (y_min, y_max))
all_types = sorted(df["위반유형"].unique())
sel_types = st.sidebar.multiselect("위반유형", all_types, default=all_types)

# 필터 적용: 선택한 값에 맞게 데이터를 걸러냄 (이게 대시보드의 핵심 원리)
f = df[df["조치연도"].between(*sel_years) & df["위반유형"].isin(sel_types)]
if sel_items:
    f = f[f["품목"].isin(sel_items)]

# ---------------------------------------------------------------- 본문
st.title("생활화학제품 품목별 위반 특성 대시보드")
if is_demo:
    st.warning("⚠️ 지금은 데모(가짜) 데이터입니다. analysis_long.csv 를 넣으면 실제 데이터로 바뀝니다.")

if f.empty:
    st.info("선택한 조건에 해당하는 데이터가 없습니다. 필터를 조정해 주세요.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("위반 제품 수", f["prdt_mstr_no"].nunique())
c2.metric("위반사유 건수", len(f))
c3.metric("품목 수", f["품목"].nunique())

tab1, tab2, tab3, tab4 = st.tabs(["전체 통합", "품목 간 비교", "품목 상세", "원자료"])

# ---- 탭1: 전체 통합
with tab1:
    left, right = st.columns(2)

    with left:
        st.subheader("품목별 위반 제품 수")
        cnt = f.groupby("품목")["prdt_mstr_no"].nunique().sort_values()
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.barh(cnt.index, cnt.values, color="#4C72B0")
        ax.set_xlabel("제품 수")
        st.pyplot(fig)
        plt.close(fig)

    with right:
        st.subheader("연도별 추이")
        yr = f.groupby("조치연도")["prdt_mstr_no"].nunique()
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(yr.index, yr.values, marker="o")
        ax.set_xlabel("조치연도")
        ax.set_ylabel("제품 수")
        st.pyplot(fig)
        plt.close(fig)

    st.subheader("품목별 위반유형 구성 (누적 막대)")
    ct = pd.crosstab(f["품목"], f["위반유형"])
    fig, ax = plt.subplots(figsize=(10, 4))
    ct.plot(kind="bar", stacked=True, ax=ax)
    ax.set_xlabel("")
    ax.set_ylabel("위반사유 건수")
    plt.xticks(rotation=30, ha="right")
    st.pyplot(fig)
    plt.close(fig)

# ---- 탭2: 품목 간 비교 (히트맵)
with tab2:
    st.subheader("품목 × 위반유형")
    ct = pd.crosstab(f["품목"], f["위반유형"])
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.heatmap(ct, annot=True, fmt="d", cmap="Blues", ax=ax)
    ax.set_xlabel("")
    ax.set_ylabel("")
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("품목 × 위반물질 (상위 N개)")
    top_n = st.slider("표시할 물질 수", 3, 15, 8)
    sub = f[f["위반물질"] != "해당없음"]
    if sub.empty:
        st.info("위반물질이 있는 데이터가 없습니다.")
    else:
        top = sub["위반물질"].value_counts().head(top_n).index
        ct2 = pd.crosstab(sub["품목"], sub["위반물질"])[top]
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.heatmap(ct2, annot=True, fmt="d", cmap="Reds", ax=ax)
        ax.set_xlabel("")
        ax.set_ylabel("")
        st.pyplot(fig)
        plt.close(fig)

# ---- 탭3: 품목 하나 골라서 자세히
with tab3:
    one = st.selectbox("품목 선택", sorted(f["품목"].unique()))
    g = f[f["품목"] == one]
    st.write(f"**{one}** : 제품 {g['prdt_mstr_no'].nunique()}개 / 위반사유 {len(g)}건")

    a, b = st.columns(2)
    with a:
        st.caption("위반유형 비율")
        s = g["위반유형"].value_counts()
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(s.values, labels=s.index, autopct="%1.0f%%", startangle=90)
        st.pyplot(fig)
        plt.close(fig)
    with b:
        st.caption("주요 위반물질")
        s = g[g["위반물질"] != "해당없음"]["위반물질"].value_counts().head(8).sort_values()
        if s.empty:
            st.info("위반물질 데이터 없음")
        else:
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.barh(s.index, s.values, color="#C44E52")
            st.pyplot(fig)
            plt.close(fig)

# ---- 탭4: 원자료 + 다운로드
with tab4:
    st.dataframe(f, use_container_width=True)
    st.download_button("필터링된 데이터 CSV 다운로드",
                       f.to_csv(index=False).encode("utf-8-sig"),
                       "filtered.csv", "text/csv")
