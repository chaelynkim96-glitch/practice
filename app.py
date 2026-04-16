import calendar
from datetime import date, datetime, timedelta
from io import StringIO

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="롯데백화점 이벤트마케팅 AI 리서치 툴",
    page_icon="📅",
    layout="wide",
)

STATUS_ORDER = {"예정": 0, "진행중": 1, "종료": 2}
DEFAULT_REGIONS = ["서울", "수도권", "부산", "대구", "광주", "대전", "기타"]
DEFAULT_TYPES = ["전시", "팝업", "경쟁사 이벤트", "지자체 행사", "브랜드 협업", "기타"]
DEFAULT_TARGETS = ["가족", "2030", "VIP", "관광객", "지역고객", "일반"]
IMPORTANCE_MAP = {"상": 3, "중": 2, "하": 1}


def to_date(value):
    if pd.isna(value) or value in ("", None):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def normalize_text(value, default="-"):
    if pd.isna(value) or value is None or str(value).strip() == "":
        return default
    return str(value).strip()


def infer_status(start_date, end_date, today=None):
    today = today or date.today()
    if start_date is None or end_date is None:
        return "예정"
    if today < start_date:
        return "예정"
    if start_date <= today <= end_date:
        return "진행중"
    return "종료"


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def load_sample_data():
    csv_text = """
id,collected_at,event_name,event_type,host_brand,venue_name,region,start_date,end_date,status,source_site,source_link,source_summary,ai_summary,keywords,target_estimate,importance,benchmark_value,lotte_idea,duplicate_flag,review_flag,one_line_summary,visual_feature,experience_element,buzz_basis,internal_similarity,internal_performance
1,2026-04-10,아트 협업 전시,전시,브랜드A,성수 팝업홀,서울,2026-04-10,2026-05-20,진행중,공식 사이트,https://example.com/1,브랜드와 작가 협업 전시 소개,브랜드와 미술 작가의 협업형 전시로 포토존과 한정 굿즈가 결합된 행사,"아트,포토존,협업",2030,상,상,롯데 문화홀 시즌 전시와 굿즈 연계를 결합,False,True,작가 협업과 포토존 중심의 체험형 전시,대형 오브제와 감각적 동선,굿즈 구매와 포토 체험,SNS 언급 증가,2024 아트페어 연계 행사,집객 우수 / 체류시간 증가
2,2026-04-15,캐릭터 브랜드 팝업,팝업,브랜드B,잠실몰 이벤트존,서울,2026-04-15,2026-04-28,진행중,뉴스,https://example.com/2,캐릭터 브랜드 팝업 오픈 기사,체험형 요소와 한정판 판매가 결합된 단기 팝업,"캐릭터,굿즈,체험형",가족,상,상,키즈/패밀리 고객 대상 단기 시즌 팝업에 적합,False,True,가족 고객 유입이 기대되는 캐릭터 체험형 팝업,캐릭터 조형물,스탬프 투어와 굿즈 판매,오픈 초기 대기줄 발생,2023 캐릭터 팝업,매출 우수 / 가족 방문 비중 높음
3,2026-04-18,지역문화축제,지자체 행사,부산시,부산 시민공원,부산,2026-04-22,2026-05-01,예정,지자체 사이트,https://example.com/3,부산 지역문화축제 일정 공지,지역 연계형 문화 축제로 체험 부스와 공연이 포함,"지역연계,축제,공연",지역고객,중,중,로컬 협업 행사 기획 시 참고 가능,False,False,지역성과 체험 요소를 결합한 대형 축제,야외 무대 중심,체험 부스와 지역 브랜드 참여,지역 커뮤니티 확산,2022 지역 상생 행사,인지도 상승 / 직접 매출 제한적
4,2026-04-08,백화점 아트 살롱,경쟁사 이벤트,경쟁사백화점,강남점 문화홀,수도권,2026-04-12,2026-04-30,진행중,경쟁사 페이지,https://example.com/4,경쟁사 문화행사 안내,VIP 고객 초청형 전시와 아트 토크를 결합한 행사,"VIP,전시,토크",VIP,중,상,VIP 라운지 연계 프라이빗 프로그램 기획 참고,False,True,VIP 대상 프라이빗 전시 경험 강화 사례,고급 연출,도슨트 토크와 예약제 관람,언론 기사 및 커뮤니티 후기,2025 VIP 아트 나이트,객단가 우수 / 초청 반응 좋음
5,2026-04-20,브랜드 협업 미디어전,브랜드 협업,브랜드C x 스튜디오D,더현대 특별관,서울,2026-04-25,2026-06-10,예정,블로그,https://example.com/5,브랜드 협업 미디어전 예고,미디어아트와 브랜드 스토리텔링을 결합한 몰입형 전시,"미디어아트,협업,몰입형",2030,상,상,시즌 브랜드 캠페인과 전시형 콘텐츠 결합 가능,False,False,브랜드 스토리텔링을 강화한 몰입형 미디어 전시,LED 미디어월,인터랙티브 체험,사전 화제성 높음,2024 미디어 파사드 행사,브랜드 인지도 상승
6,2026-04-12,지역 미식 페스티벌,기타,지자체/민간,대전 엑스포광장,대전,2026-04-19,2026-04-27,진행중,행사 페이지,https://example.com/6,지역 미식 페스티벌 안내,푸드와 공연을 결합한 체류형 행사,"푸드,지역,체류형",관광객,중,중,식음/라이프스타일 행사에 응용 가능,False,False,체류 시간을 늘리는 복합형 페스티벌,야외 부스형,시식과 무대 프로그램,방문 인증 리뷰 증가,2023 F&B 페스티벌,체류시간 증가 / 구매전환 보통
"""
    df = pd.read_csv(StringIO(csv_text))
    return prepare_dataframe(df)


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()

    column_defaults = {
        "id": "",
        "collected_at": "",
        "event_name": "",
        "event_type": "기타",
        "host_brand": "",
        "venue_name": "",
        "region": "기타",
        "start_date": "",
        "end_date": "",
        "status": "",
        "source_site": "",
        "source_link": "",
        "source_summary": "",
        "ai_summary": "",
        "keywords": "",
        "target_estimate": "일반",
        "importance": "중",
        "benchmark_value": "중",
        "lotte_idea": "",
        "duplicate_flag": False,
        "review_flag": False,
        "one_line_summary": "",
        "visual_feature": "",
        "experience_element": "",
        "buzz_basis": "",
        "internal_similarity": "",
        "internal_performance": "",
    }

    for col, default in column_defaults.items():
        if col not in working.columns:
            working[col] = default

    working["start_date"] = working["start_date"].apply(to_date)
    working["end_date"] = working["end_date"].apply(to_date)
    working["status"] = working.apply(
        lambda row: infer_status(row["start_date"], row["end_date"]) if normalize_text(row["status"], "") == "" else normalize_text(row["status"]),
        axis=1,
    )

    text_cols = [
        "event_name",
        "event_type",
        "host_brand",
        "venue_name",
        "region",
        "status",
        "source_site",
        "source_link",
        "source_summary",
        "ai_summary",
        "keywords",
        "target_estimate",
        "importance",
        "benchmark_value",
        "lotte_idea",
        "one_line_summary",
        "visual_feature",
        "experience_element",
        "buzz_basis",
        "internal_similarity",
        "internal_performance",
    ]
    for col in text_cols:
        working[col] = working[col].apply(lambda x: normalize_text(x, ""))

    working["duplicate_flag"] = working["duplicate_flag"].astype(str).str.lower().isin(["true", "1", "yes", "y"])
    working["review_flag"] = working["review_flag"].astype(str).str.lower().isin(["true", "1", "yes", "y"])

    working["duration_days"] = working.apply(
        lambda row: ((row["end_date"] - row["start_date"]).days + 1) if row["start_date"] and row["end_date"] else 0,
        axis=1,
    )
    working["importance_score"] = working["importance"].map(IMPORTANCE_MAP).fillna(2)
    working["benchmark_score"] = working["benchmark_value"].map(IMPORTANCE_MAP).fillna(2)
    working["sort_start"] = working["start_date"].apply(lambda x: x or date.max)
    working["sort_end"] = working["end_date"].apply(lambda x: x or date.max)

    return working


def filter_dataframe(
    df: pd.DataFrame,
    view_type: str,
    selected_date: date,
    selected_types,
    selected_regions,
    selected_targets,
    keyword: str,
):
    filtered = df.copy()

    if selected_types:
        filtered = filtered[filtered["event_type"].isin(selected_types)]
    if selected_regions:
        filtered = filtered[filtered["region"].isin(selected_regions)]
    if selected_targets:
        filtered = filtered[filtered["target_estimate"].isin(selected_targets)]
    if keyword.strip():
        kw = keyword.strip().lower()
        searchable_cols = [
            "event_name",
            "host_brand",
            "venue_name",
            "ai_summary",
            "one_line_summary",
            "keywords",
            "lotte_idea",
        ]
        mask = False
        for col in searchable_cols:
            mask = mask | filtered[col].str.lower().str.contains(kw, na=False)
        filtered = filtered[mask]

    if view_type == "월":
        month_start = selected_date.replace(day=1)
        month_end = date(selected_date.year, selected_date.month, calendar.monthrange(selected_date.year, selected_date.month)[1])
        filtered = filtered[
            (filtered["start_date"] <= month_end) &
            (filtered["end_date"] >= month_start)
        ]
    elif view_type == "주":
        week_start = selected_date - timedelta(days=selected_date.weekday())
        week_end = week_start + timedelta(days=6)
        filtered = filtered[
            (filtered["start_date"] <= week_end) &
            (filtered["end_date"] >= week_start)
        ]

    return filtered


def sort_dataframe(df: pd.DataFrame, sort_by: str):
    working = df.copy()
    if sort_by == "오픈일 순":
        working = working.sort_values(["sort_start", "importance_score"], ascending=[True, False])
    elif sort_by == "종료일 임박 순":
        working = working.sort_values(["sort_end", "importance_score"], ascending=[True, False])
    else:
        working = working.sort_values(["importance_score", "benchmark_score", "sort_start"], ascending=[False, False, True])
    return working


def event_matches_day(row, target_day: date):
    if row["start_date"] is None or row["end_date"] is None:
        return False
    return row["start_date"] <= target_day <= row["end_date"]


def format_period(start_date, end_date):
    if not start_date or not end_date:
        return "-"
    return f"{start_date.strftime('%m.%d')}~{end_date.strftime('%m.%d')}"


def importance_badge(importance: str):
    if importance == "상":
        return "🔴 상"
    if importance == "중":
        return "🟡 중"
    return "🟢 하"


def build_event_card_html(row):
    return f"""
    <div style="
        border:1px solid #e5e7eb;
        border-left:6px solid #1f77b4;
        border-radius:10px;
        padding:10px;
        margin-bottom:8px;
        background:#ffffff;
    ">
        <div style="font-weight:700; font-size:14px; margin-bottom:4px;">
            [{row['event_type']}] {row['event_name']}
        </div>
        <div style="font-size:12px; color:#4b5563; margin-bottom:4px;">
            {row['venue_name']} · {row['region']} · {format_period(row['start_date'], row['end_date'])}
        </div>
        <div style="font-size:12px; color:#111827; margin-bottom:4px;">
            {normalize_text(row['one_line_summary'])}
        </div>
        <div style="font-size:11px; color:#6b7280;">
            중요도 {importance_badge(row['importance'])}
        </div>
    </div>
    """


def render_month_calendar(df: pd.DataFrame, selected_date: date):
    year = selected_date.year
    month = selected_date.month
    cal = calendar.Calendar(firstweekday=0)
    weeks = cal.monthdatescalendar(year, month)

    st.markdown(f"### {year}년 {month}월 캘린더")
    header_cols = st.columns(7)
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    for idx, wd in enumerate(weekdays):
        header_cols[idx].markdown(f"**{wd}**")

    for week in weeks:
        cols = st.columns(7)
        for idx, day in enumerate(week):
            daily_events = df[df.apply(lambda row: event_matches_day(row, day), axis=1)]
            with cols[idx]:
                in_month = day.month == month
                box_style = "#ffffff" if in_month else "#f3f4f6"
                st.markdown(
                    f"""
                    <div style="
                        min-height:190px;
                        border:1px solid #e5e7eb;
                        border-radius:12px;
                        padding:8px;
                        background:{box_style};
                    ">
                        <div style="font-weight:700; margin-bottom:8px;">{day.day}</div>
                    """,
                    unsafe_allow_html=True,
                )
                if daily_events.empty:
                    st.caption("일정 없음")
                else:
                    daily_events = daily_events.sort_values(["importance_score", "sort_end"], ascending=[False, True]).head(3)
                    for _, row in daily_events.iterrows():
                        st.markdown(
                            f"""
                            <div style="
                                font-size:12px;
                                padding:6px 8px;
                                border-radius:8px;
                                margin-bottom:6px;
                                background:#eef5ff;
                                border:1px solid #dbeafe;
                            ">
                                <strong>[{row['event_type']}]</strong> {row['event_name']}<br/>
                                <span style="color:#6b7280;">{row['region']} · {row['venue_name']}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    extra_count = len(df[df.apply(lambda row: event_matches_day(row, day), axis=1)]) - 3
                    if extra_count > 0:
                        st.caption(f"+ {extra_count}건 더 보기")
                st.markdown("</div>", unsafe_allow_html=True)


def render_week_view(df: pd.DataFrame, selected_date: date):
    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_days = [week_start + timedelta(days=i) for i in range(7)]
    st.markdown(f"### 주간 보기 ({week_start.strftime('%Y-%m-%d')} ~ {(week_start + timedelta(days=6)).strftime('%Y-%m-%d')})")

    cols = st.columns(7)
    for idx, day in enumerate(week_days):
        with cols[idx]:
            st.markdown(f"**{day.strftime('%m.%d')} ({['월', '화', '수', '목', '금', '토', '일'][idx]})**")
            daily_events = df[df.apply(lambda row: event_matches_day(row, day), axis=1)].sort_values(
                ["importance_score", "sort_end"], ascending=[False, True]
            )
            if daily_events.empty:
                st.caption("일정 없음")
            else:
                for _, row in daily_events.iterrows():
                    st.markdown(
                        f"""
                        <div style="
                            border:1px solid #e5e7eb;
                            border-radius:10px;
                            padding:8px;
                            margin-bottom:8px;
                            background:#ffffff;
                        ">
                            <div style="font-size:12px; font-weight:700;">[{row['event_type']}] {row['event_name']}</div>
                            <div style="font-size:11px; color:#6b7280;">{row['venue_name']} · {row['region']}</div>
                            <div style="font-size:11px; color:#111827;">{row['one_line_summary']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


def render_list_view(df: pd.DataFrame):
    st.markdown("### 리스트 보기")
    if df.empty:
        st.info("조건에 맞는 행사가 없습니다.")
        return

    for _, row in df.iterrows():
        st.markdown(build_event_card_html(row), unsafe_allow_html=True)


def build_insights(df: pd.DataFrame, base_date: date):
    if df.empty:
        return {
            "summary_lines": ["조건에 맞는 데이터가 없어 인사이트를 생성할 수 없습니다."],
            "top_refs": pd.DataFrame(),
            "weekly_open": pd.DataFrame(),
            "ending_soon": pd.DataFrame(),
            "next_two_weeks": pd.DataFrame(),
        }

    week_start = base_date - timedelta(days=base_date.weekday())
    week_end = week_start + timedelta(days=6)
    next_two_weeks_end = week_end + timedelta(days=14)

    weekly_open = df[(df["start_date"] >= week_start) & (df["start_date"] <= week_end)].copy()
    ending_soon = df[(df["end_date"] >= base_date) & (df["end_date"] <= base_date + timedelta(days=7))].copy()
    next_two_weeks = df[(df["start_date"] > week_end) & (df["start_date"] <= next_two_weeks_end)].copy()

    type_counts = df["event_type"].value_counts()
    target_counts = df["target_estimate"].value_counts()
    region_counts = df["region"].value_counts()

    experiential_keywords = ["체험", "포토", "인터랙티브", "굿즈", "스탬프", "몰입"]
    experiential_count = df["ai_summary"].str.contains("|".join(experiential_keywords), case=False, na=False).sum()

    collaboration_count = df["event_type"].eq("브랜드 협업").sum()
    local_count = df["event_type"].eq("지자체 행사").sum()
    popup_count = df["event_type"].eq("팝업").sum()

    summary_lines = [
        f"이번 화면 기준 총 {len(df)}건의 행사가 포착되었고, 가장 많은 유형은 '{type_counts.index[0]}'입니다.",
        f"체험형 요소가 언급된 행사는 {experiential_count}건으로, 포토존·굿즈·참여형 구성의 비중이 높습니다.",
        f"주요 타깃은 '{target_counts.index[0]}'이며, 지역은 '{region_counts.index[0]}' 중심으로 집중됩니다.",
    ]

    if popup_count >= collaboration_count and popup_count > 0:
        summary_lines.append("팝업형 이벤트가 강세이며, 짧은 운영 기간 안에 화제성을 높이는 설계가 유효해 보입니다.")
    if local_count > 0:
        summary_lines.append("지자체·지역 연계 행사도 관측되어 로컬 파트너십형 기획의 참고 가치가 있습니다.")

    top_refs = df.sort_values(
        ["importance_score", "benchmark_score", "sort_start"], ascending=[False, False, True]
    ).head(5)

    return {
        "summary_lines": summary_lines,
        "top_refs": top_refs,
        "weekly_open": weekly_open.sort_values(["importance_score", "sort_start"], ascending=[False, True]),
        "ending_soon": ending_soon.sort_values(["sort_end", "importance_score"], ascending=[True, False]),
        "next_two_weeks": next_two_weeks.sort_values(["sort_start", "importance_score"], ascending=[True, False]),
    }


def render_detail_panel(df: pd.DataFrame):
    st.markdown("### 상세 정보")
    if df.empty:
        st.info("표시할 행사가 없습니다.")
        return

    options = {f"[{row.event_type}] {row.event_name} · {row.region}": idx for idx, row in df.iterrows()}
    selected_label = st.selectbox("행사 선택", list(options.keys()))
    selected_idx = options[selected_label]
    row = df.loc[selected_idx]

    st.markdown(f"#### {row['event_name']}")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**행사 유형**: {row['event_type']}")
        st.write(f"**장소**: {row['venue_name']}")
        st.write(f"**지역**: {row['region']}")
        st.write(f"**진행 기간**: {format_period(row['start_date'], row['end_date'])}")
        st.write(f"**상태**: {row['status']}")
        st.write(f"**중요도**: {importance_badge(row['importance'])}")
    with col2:
        st.write(f"**주최/운영 주체**: {normalize_text(row['host_brand'])}")
        st.write(f"**예상 타깃**: {normalize_text(row['target_estimate'])}")
        st.write(f"**벤치마킹 가치**: {normalize_text(row['benchmark_value'])}")
        st.write(f"**키워드**: {normalize_text(row['keywords'])}")
        st.write(f"**검수 여부**: {'완료' if row['review_flag'] else '미검수'}")

    st.markdown("**핵심 포인트**")
    st.write(normalize_text(row["ai_summary"] or row["source_summary"] or row["one_line_summary"]))

    st.markdown("**주목 이유**")
    st.write(normalize_text(row["buzz_basis"]))

    st.markdown("**시각적 특징 / 체험 요소**")
    st.write(f"- 시각적 특징: {normalize_text(row['visual_feature'])}")
    st.write(f"- 체험 요소: {normalize_text(row['experience_element'])}")

    st.markdown("**내부 활용 아이디어**")
    st.write(normalize_text(row["lotte_idea"]))

    st.markdown("**내부 히스토리 연결**")
    st.write(f"- 유사 행사 이력: {normalize_text(row['internal_similarity'])}")
    st.write(f"- 당시 성과: {normalize_text(row['internal_performance'])}")

    if normalize_text(row["source_link"], ""):
        st.markdown(f"**참고 링크**: [원문 바로가기]({row['source_link']})")


def render_weekly_report(df: pd.DataFrame, insights: dict, base_date: date):
    st.markdown("## 주간 이벤트마케팅 트렌드 리포트")
    week_start = base_date - timedelta(days=base_date.weekday())
    week_end = week_start + timedelta(days=6)

    weekly_open = insights["weekly_open"]
    ending_soon = insights["ending_soon"]
    next_two_weeks = insights["next_two_weeks"]
    top_refs = insights["top_refs"]

    total_new = len(weekly_open)
    counts = weekly_open["event_type"].value_counts() if not weekly_open.empty else pd.Series(dtype=int)

    st.write(f"**기준 주차**: {week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')}")
    st.write(f"**작성일**: {date.today().strftime('%Y-%m-%d')}")
    st.write("**작성 담당**: AI 초안")

    st.markdown("### 1) 한 주 요약")
    st.write(f"- 이번 주 신규 포착 행사 수: {total_new}건")
    for category in ["전시", "팝업", "경쟁사 이벤트", "지자체 행사", "브랜드 협업"]:
        st.write(f"- {category}: {safe_int(counts.get(category, 0))}건")
    if insights["summary_lines"]:
        st.write(f"- 이번 주 핵심 한줄 요약: {insights['summary_lines'][0]}")

    st.markdown("### 2) 캘린더 핵심 일정")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**이번 주 오픈**")
        if weekly_open.empty:
            st.caption("없음")
        else:
            for _, row in weekly_open.head(7).iterrows():
                st.write(
                    f"- {row['event_name']} / {row['venue_name']} / {format_period(row['start_date'], row['end_date'])} / {row['event_type']}"
                )

    with col2:
        st.markdown("**이번 주 종료 임박**")
        if ending_soon.empty:
            st.caption("없음")
        else:
            for _, row in ending_soon.head(7).iterrows():
                need = "예" if row["benchmark_score"] >= 2 else "보통"
                st.write(f"- {row['event_name']} / {row['venue_name']} / 종료일 {row['end_date']} / 벤치마킹 {need}")

    with col3:
        st.markdown("**다음 2주 내 예정**")
        if next_two_weeks.empty:
            st.caption("없음")
        else:
            for _, row in next_two_weeks.head(7).iterrows():
                st.write(f"- {row['event_name']} / {row['venue_name']} / 오픈 {row['start_date']} / 참고 이유 {row['benchmark_value']}")

    st.markdown("### 3) 주목할 레퍼런스 TOP 5")
    if top_refs.empty:
        st.info("추천할 레퍼런스가 없습니다.")
    else:
        for i, (_, row) in enumerate(top_refs.iterrows(), start=1):
            with st.expander(f"TOP {i}. {row['event_name']}"):
                st.write(f"**유형**: {row['event_type']}")
                st.write(f"**장소**: {row['venue_name']} / {row['region']}")
                st.write(f"**기간**: {format_period(row['start_date'], row['end_date'])}")
                st.write(f"**주최**: {row['host_brand']}")
                st.write(f"**핵심 포인트 3줄**: {normalize_text(row['ai_summary'])}")
                st.write(f"**왜 주목해야 하는가**: {normalize_text(row['buzz_basis'])}")
                st.write(f"**롯데백화점 적용 가능 아이디어**: {normalize_text(row['lotte_idea'])}")

    st.markdown("### 4) AI 인사이트")
    for line in insights["summary_lines"]:
        st.write(f"- {line}")

    if not df.empty:
        st.write(f"- 최근 증가 가능성이 높은 행사 유형: {df['event_type'].value_counts().index[0]}")
        st.write(f"- 많이 보이는 타깃 경향: {df['target_estimate'].value_counts().index[0]}")
        st.write(f"- 지역별 특징: {df['region'].value_counts().index[0]} 중심으로 행사 밀집")

    st.markdown("### 5) 내부 히스토리 연결")
    history_df = df[df["internal_similarity"] != ""].head(3)
    if history_df.empty:
        st.caption("내부 히스토리 연결 정보가 없습니다.")
    else:
        for _, row in history_df.iterrows():
            st.write(f"- 유사 행사 이력: {row['internal_similarity']} / 당시 성과: {row['internal_performance']}")

    st.markdown("### 6) 액션 제안")
    immediate_actions = top_refs.head(3)
    if immediate_actions.empty:
        st.caption("추천 액션이 없습니다.")
    else:
        for _, row in immediate_actions.iterrows():
            st.write(f"- 바로 검토할 행사: {row['event_name']} / 이유: {normalize_text(row['lotte_idea'])}")

    visit_candidates = ending_soon.head(2)
    if not visit_candidates.empty:
        st.write("**현장 방문 후보 2건**")
        for _, row in visit_candidates.iterrows():
            st.write(f"- {row['event_name']} / 종료 임박 / {row['venue_name']}")

    st.write("**아이디어 회의 안건 3개**")
    st.write("- 체험형 요소를 강화한 팝업 포맷 적용 가능성 검토")
    st.write("- 지역 연계 행사와 백화점 공간의 결합 방식 점검")
    st.write("- 브랜드 협업 전시의 포토존·굿즈 구조 도입 여부 검토")


def dataframe_download(df: pd.DataFrame):
    export_df = df.copy()
    for col in ["start_date", "end_date", "sort_start", "sort_end"]:
        if col in export_df.columns:
            export_df[col] = export_df[col].astype(str)
    csv = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "현재 결과 CSV 다운로드",
        data=csv,
        file_name="lotte_event_ai_research_filtered.csv",
        mime="text/csv",
    )


def main():
    st.title("롯데백화점 이벤트마케팅 AI 리서치 툴")
    st.caption("캘린더 중심으로 외부 전시·팝업·문화 이벤트를 보고, AI 인사이트와 주간 리포트까지 확인하는 Streamlit 앱")

    with st.sidebar:
        st.header("데이터 설정")
        uploaded_file = st.file_uploader("CSV 업로드", type=["csv"])
        st.caption("업로드가 없으면 샘플 데이터로 실행됩니다.")

        if uploaded_file is not None:
            raw_df = pd.read_csv(uploaded_file)
            df = prepare_dataframe(raw_df)
            st.success(f"업로드 완료: {len(df)}건")
        else:
            df = load_sample_data()
            st.info(f"샘플 데이터 사용 중: {len(df)}건")

        st.divider()
        st.header("보기 옵션")
        view_type = st.radio("기간 선택", ["월", "주", "리스트"], horizontal=True)
        selected_date = st.date_input("기준 날짜", value=date.today())

        event_types = sorted(set(DEFAULT_TYPES) | set(df["event_type"].dropna().tolist()))
        selected_types = st.multiselect("유형 필터", event_types, default=event_types)

        regions = sorted(set(DEFAULT_REGIONS) | set(df["region"].dropna().tolist()))
        selected_regions = st.multiselect("지역 필터", regions, default=regions)

        targets = sorted(set(DEFAULT_TARGETS) | set(df["target_estimate"].dropna().tolist()))
        selected_targets = st.multiselect("타깃 필터", targets, default=targets)

        sort_by = st.selectbox("정렬 기준", ["오픈일 순", "종료일 임박 순", "화제성 순"])
        keyword = st.text_input("키워드 검색", placeholder="행사명, 장소, 키워드, 아이디어 등")

    filtered = filter_dataframe(
        df=df,
        view_type=view_type,
        selected_date=selected_date,
        selected_types=selected_types,
        selected_regions=selected_regions,
        selected_targets=selected_targets,
        keyword=keyword,
    )
    filtered = sort_dataframe(filtered, sort_by)
    insights = build_insights(filtered, selected_date)

    tab1, tab2, tab3, tab4 = st.tabs(["캘린더", "상세 패널", "AI 인사이트", "주간 리포트"])

    with tab1:
        metric_cols = st.columns(4)
        metric_cols[0].metric("현재 표시 행사", f"{len(filtered)}건")
        metric_cols[1].metric("진행중", f"{(filtered['status'] == '진행중').sum()}건")
        metric_cols[2].metric("종료 임박 7일 내", f"{((filtered['end_date'] >= selected_date) & (filtered['end_date'] <= selected_date + timedelta(days=7))).sum()}건")
        metric_cols[3].metric("중요도 상", f"{(filtered['importance'] == '상').sum()}건")

        if view_type == "월":
            render_month_calendar(filtered, selected_date)
        elif view_type == "주":
            render_week_view(filtered, selected_date)
        else:
            render_list_view(filtered)

        st.divider()
        st.markdown("### 빠른 조회 테이블")
        quick_columns = [
            "event_name", "event_type", "region", "venue_name", "start_date",
            "end_date", "status", "target_estimate", "importance", "benchmark_value"
        ]
        st.dataframe(filtered[quick_columns], use_container_width=True, hide_index=True)
        dataframe_download(filtered)

    with tab2:
        render_detail_panel(filtered)

    with tab3:
        st.markdown("## 하단 인사이트 영역")
        for line in insights["summary_lines"]:
            st.write(f"- {line}")

        st.markdown("### 주목할 레퍼런스 TOP 5")
        top_refs = insights["top_refs"]
        if top_refs.empty:
            st.info("표시할 레퍼런스가 없습니다.")
        else:
            display_cols = [
                "event_name", "event_type", "region", "venue_name",
                "start_date", "end_date", "importance", "benchmark_value", "lotte_idea"
            ]
            st.dataframe(top_refs[display_cols], use_container_width=True, hide_index=True)

        st.markdown("### 이번 주 오픈 / 종료 임박 / 다음 2주 예정")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**이번 주 오픈**")
            if insights["weekly_open"].empty:
                st.caption("없음")
            else:
                st.dataframe(
                    insights["weekly_open"][["event_name", "event_type", "start_date", "venue_name"]],
                    use_container_width=True,
                    hide_index=True,
                )
        with c2:
            st.markdown("**종료 임박**")
            if insights["ending_soon"].empty:
                st.caption("없음")
            else:
                st.dataframe(
                    insights["ending_soon"][["event_name", "event_type", "end_date", "venue_name"]],
                    use_container_width=True,
                    hide_index=True,
                )
        with c3:
            st.markdown("**다음 2주 예정**")
            if insights["next_two_weeks"].empty:
                st.caption("없음")
            else:
                st.dataframe(
                    insights["next_two_weeks"][["event_name", "event_type", "start_date", "venue_name"]],
                    use_container_width=True,
                    hide_index=True,
                )

    with tab4:
        render_weekly_report(filtered, insights, selected_date)

    with st.expander("CSV 컬럼 가이드"):
        st.write("아래 컬럼명을 쓰면 앱 기능을 가장 잘 활용할 수 있습니다.")
        st.code(
            "id, collected_at, event_name, event_type, host_brand, venue_name, region, "
            "start_date, end_date, status, source_site, source_link, source_summary, "
            "ai_summary, keywords, target_estimate, importance, benchmark_value, "
            "lotte_idea, duplicate_flag, review_flag, one_line_summary, visual_feature, "
            "experience_element, buzz_basis, internal_similarity, internal_performance",
            language="text",
        )


if __name__ == "__main__":
    main()
