import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date
import time

# --- IMPORT MODULES ---
# تأكدي أن الملفات database.py و ui_components.py و ai_engine.py موجودة في نفس المجلد
import database as db
import ui_components as ui
import ai_engine as ai

# --- CONFIGURATION ---
st.set_page_config(page_title="NorthStar OS", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")
ui.apply_custom_css()

# --- SESSION STATE INITIALIZATION ---
if 'running' not in st.session_state:
    st.session_state.running = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'current_task' not in st.session_state:
    st.session_state.current_task = ""
if 'current_pillar' not in st.session_state:
    st.session_state.current_pillar = "Growth"
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🧭 NorthStar OS")
    # تعريف الصفحات كثوابت لضمان التطابق
    PAGE_FOCUS = "🚀 Focus Mode"
    PAGE_STRATEGY = "🧠 Strategy Room"
    PAGE_AI = "🤖 AI Coach"
    
    page = st.radio("Navigate:", [PAGE_FOCUS, PAGE_STRATEGY, PAGE_AI])
    
    st.divider()
    
    # Quick Freezer
    with st.expander("❄️ Quick Freeze"):
        with st.form("sb_frz", clear_on_submit=True):
            idea = st.text_area("Idea:", height=60, label_visibility="collapsed", placeholder="Distracting thought?")
            if st.form_submit_button("Freeze"):
                if idea: 
                    db.freeze_idea(idea)
                    st.toast("Frozen successfully! ❄️")

# ==================================================
# PAGE 1: 🚀 FOCUS MODE (Execution & Tracker)
# ==================================================
if page == PAGE_FOCUS:
    st.markdown("<h2 style='color:#66BB6A'>🟢 Execution Zone</h2>", unsafe_allow_html=True)
    
    # 1. HEADER: Total Time Today
    # ملاحظة: إذا ظهر خطأ هنا تأكدي أن دالة get_total_time_today موجودة في database.py
    # إذا لم تكن موجودة، سنعرض "0h 0m" مؤقتاً لتجنب توقف التطبيق
    try:
        total_time_str = db.get_total_time_today()
    except:
        total_time_str = "0h 0m"
        
    st.markdown(f"<div style='text-align:right; font-size:1.2em; color:#E57CD8; margin-bottom:10px'>Today's Focus: <b>{total_time_str}</b></div>", unsafe_allow_html=True)

    # 2. THE TIMER (Toggl Style)
    # استخدام حاوية (Container) لفصل المؤقت عن باقي الصفحة
    timer_container = st.container(border=True)
    
    with timer_container:
        # الحالة A: المؤقت متوقف (أظهر زر البدء)
        if not st.session_state.running:
            c1, c2, c3 = st.columns([5, 2, 1])
            with c1:
                task_in = st.text_input("What are you working on?", placeholder="e.g., Recording Course Video...", label_visibility="collapsed")
            with c2:
                pillar_in = st.selectbox("Project", ["🚀 Growth", "💰 Vertical", "🧼 Cleanup"], label_visibility="collapsed")
            with c3:
                # زر البدء
                if st.button("START ▶️", use_container_width=True, type="primary"):
                    if task_in:
                        st.session_state.running = True
                        st.session_state.start_time = datetime.now()
                        st.session_state.current_task = task_in
                        st.session_state.current_pillar = pillar_in
                        st.rerun() # إعادة تحميل فورية لتحديث الواجهة
                    else:
                        st.toast("⚠️ Please name your task first!")

        # الحالة B: المؤقت يعمل (أظهر العداد وزر الإيقاف)
        else:
            col_info, col_timer, col_stop = st.columns([4, 3, 2])
            
            with col_info:
                st.markdown(f"**Working on:**")
                st.markdown(f"### ⚡ {st.session_state.current_task}")
                st.caption(f"Project: {st.session_state.current_pillar}")
            
            with col_timer:
                # حساب الوقت المنقضي
                elapsed = datetime.now() - st.session_state.start_time
                elapsed_str = str(elapsed).split('.')[0] # صيغة HH:MM:SS
                st.markdown(f"<h1 style='text-align:center; color:#E57CD8; font-family:monospace'>{elapsed_str}</h1>", unsafe_allow_html=True)
            
            with col_stop:
                st.markdown("<br>", unsafe_allow_html=True) # مسافة لضبط المحاذاة
                if st.button("STOP ⏹️", type="primary", use_container_width=True):
                    end_time = datetime.now()
                    duration = (end_time - st.session_state.start_time).total_seconds() / 60
                    
                    # حفظ الجلسة في قاعدة البيانات
                    db.save_session(
                        st.session_state.current_task,
                        st.session_state.current_pillar,
                        st.session_state.start_time,
                        end_time,
                        duration
                    )
                    
                    # تصفير الحالة
                    st.session_state.running = False
                    st.session_state.start_time = None
                    st.success("Session Saved!")
                    time.sleep(1)
                    st.rerun()
            
            # تحديث تلقائي كل ثانية لتحريك العداد
            time.sleep(1)
            st.rerun()

    st.divider()

    # 3. HABITS
    st.subheader("☀️ Daily Rituals")
    habits = db.get_habits()
    if habits:
        cols = st.columns(4)
        for i, h in enumerate(habits):
            is_done = (h.get('last_done') == str(date.today()))
            with cols[i % 4]:
                ui.render_habit_card(h, is_done)
                btn_text = "Undo" if is_done else "Done"
                if st.button(btn_text, key=f"h_{h['id']}", use_container_width=True):
                    db.toggle_habit(h['id'], h)
                    st.rerun()
    
    st.divider()

    # 4. RECENT ACTIVITY
    st.subheader("📝 Recent Activity")
    try:
        sessions = db.get_recent_sessions(limit=10)
        if sessions:
            for s in sessions:
                ui.render_session_row(s)
        else:
            st.info("No sessions yet. Start the timer!")
    except Exception as e:
        st.warning("Creating Database Index... Please wait 1-2 minutes.")

# ==================================================
# PAGE 2: 🧠 STRATEGY ROOM (Dashboard & Plan)
# ==================================================
elif page == "🧠 Strategy Room":
    st.markdown("<h2 style='color:#EF5350'>🔴 Command Center</h2>", unsafe_allow_html=True)

    # 1. TOP METRICS (Multi-Scale)
    metrics = db.get_time_metrics()
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Daily Focus", f"{metrics['daily']} hrs", "Today")
    k2.metric("Weekly Focus", f"{metrics['weekly']} hrs", "This Week")
    k3.metric("Monthly Focus", f"{metrics['monthly']} hrs", "This Month")
    
    st.divider()

    # 2. MAIN TABS
    tab1, tab2, tab3 = st.tabs(["📊 Performance Dashboard", "🗺️ 2026 Roadmap", "🤖 AI Audit"])

    # --- TAB 1: PERFORMANCE (The Mirror) ---
    with tab1:
        st.subheader("🔥 Consistency Heatmap")
        
        daily_df = db.get_daily_summary_df()
        
        if not daily_df.empty:
            # A. HEATMAP (GitHub Style)
            heatmap = alt.Chart(daily_df).mark_rect(cornerRadius=4).encode(
                x=alt.X('week_num:O', title='Week'),
                y=alt.Y('day_name:O', title=None, sort=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']),
                color=alt.Color('hours:Q', scale=alt.Scale(scheme='greens'), title='Hours'),
                tooltip=['date_str', 'hours', 'day_name']
            ).properties(height=200).configure_view(strokeWidth=0)
            
            st.altair_chart(heatmap, use_container_width=True)
            
            # B. WEEKLY TREND & PILLAR SPLIT
            c_trend, c_dist = st.columns(2)
            
            with c_trend:
                st.markdown("#### 📅 Last 7 Days Trend")
                # فلترة آخر 7 أيام فقط
                last_7 = daily_df.sort_values('date_dt').tail(7)
                bar_chart = alt.Chart(last_7).mark_bar(color='#E57CD8').encode(
                    x=alt.X('date_str', title=None),
                    y=alt.Y('hours', title='Hours'),
                    tooltip=['date_str', 'hours']
                ).properties(height=250)
                st.altair_chart(bar_chart, use_container_width=True)

            with c_dist:
                st.markdown("#### 🍰 Project Split")
                stats = db.get_pillar_stats()
                if stats:
                    p_data = pd.DataFrame(list(stats.items()), columns=['Pillar', 'Hours'])
                    pie = alt.Chart(p_data).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta("Hours"),
                        color=alt.Color("Pillar"),
                        tooltip=["Pillar", "Hours"]
                    ).properties(height=250)
                    st.altair_chart(pie, use_container_width=True)
        else:
            st.info("📊 Not enough data yet. Complete some sessions in Focus Mode to see your Heatmap!")

    # --- TAB 2: ROADMAP (Quantitative) ---
    with tab2:
        st.subheader("📅 Master Plan (Targets vs Actuals)")
        
        # Updated Master Plan with Targets
        MASTER_PLAN_2026 = {
            "Q1": {
                "title": "التنظيف + الإطلاق 🧹🚀", 
                "initiatives": ["تسليم مشاريع (AI Agent)", "إطلاق كورس Marla (MVP)", "تثبيت العادات"],
                "targets": {"Growth": 100, "Vertical": 50, "Cleanup": 30} 
            },
            "Q2": {
                "title": "التأسيس المالي 💰🏗️", 
                "initiatives": ["دراسة المالية (الكلية)", "تصميم Offer", "تحويل الكورس لـ Evergreen"],
                "targets": {"Growth": 120, "Vertical": 80, "Cleanup": 20}
            },
            "Q3": {
                "title": "مبيعات High-Ticket 💼", 
                "initiatives": ["حملة LinkedIn", "بيع 3 عقود", "Case Studies"],
                "targets": {"Growth": 150, "Vertical": 100, "Cleanup": 10}
            },
            "Q4": {
                "title": "الاستدامة 💎", 
                "initiatives": ["رفع الأسعار", "توظيف VA", "تخطيط 2027"],
                "targets": {"Growth": 150, "Vertical": 150, "Cleanup": 10}
            }
        }
        
        # Select Quarter to View
        selected_q = st.selectbox("Select Quarter:", ["Q1", "Q2", "Q3", "Q4"], index=0)
        q_data = MASTER_PLAN_2026[selected_q]
        
        st.markdown(f"### 🎯 {selected_q}: {q_data['title']}")
        
        # Get Actuals from DB
        actuals = db.get_quarter_progress(selected_q)
        
        # Render Progress Bars
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("#### 📊 Progress Tracker")
            for pillar, target in q_data['targets'].items():
                # Map pillar names if needed, or ensure they match DB
                # Assuming DB uses "🚀 Growth", "💰 Vertical", "🧼 Cleanup"
                # We need to match partial strings or standardize
                
                # Simple matching logic: Sum actuals for keys containing the pillar name
                val = 0
                for db_pillar, db_val in actuals.items():
                    if pillar in db_pillar:
                        val += db_val
                
                ui.render_progress_bar(pillar, val, target)
                
        with c2:
            st.markdown("#### 📝 Initiatives")
            for i in q_data['initiatives']:
                st.markdown(f"- {i}")

        st.divider()
        with st.expander("⚙️ Manage Habits"):
            with st.form("add_h"):
                if st.form_submit_button("Add") and (new_h := st.text_input("Name")):
                    db.add_habit(new_h); st.rerun()
            for h in db.get_habits():
                if st.button(f"🗑️ {h['title']}", key=f"del_{h['id']}"):
                    db.delete_habit(h['id']); st.rerun()

    # --- TAB 3: AI AUDIT ---
    with tab3:
        st.subheader("👮‍♀️ The Judge")
        if st.button("Generate Weekly Report 📑"):
            with st.spinner("Analyzing data..."):
                try:
                    raw_data = db.get_all_sessions_df()
                    if not raw_data.empty:
                        data_str = raw_data[['date', 'task', 'pillar', 'duration_min']].to_string()
                        prompt = f"Analyze my work logs: {data_str}. Am I productive? Give strict advice."
                        response = ai.ask_coach(prompt, "Performance Audit")
                        st.markdown(response)
                    else:
                        st.warning("Not enough data.")
                except Exception as e:
                    st.error(f"Error: {e}")

# ==================================================
# PAGE 3: 🤖 AI COACH (Chat)
# ==================================================
elif page == PAGE_AI:
    st.title("🤖 Strategy Partner")
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Ask me anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    stats = db.get_pillar_stats()
                    context = f"Current Stats: {stats}. Focus: 2026 Roadmap."
                except:
                    context = "Stats loading..."
                
                response = ai.ask_coach(prompt, context)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})