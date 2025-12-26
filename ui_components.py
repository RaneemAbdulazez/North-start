import streamlit as st

def apply_custom_css():
    st.markdown("""
    <style>
        /* إعدادات الخلفية العامة */
        .stApp { background-color: #0E1117; color: #E0E0E0; }
        section[data-testid="stSidebar"] { background-color: #1E1E1E; border-right: 1px solid #333; }
        
        /* تحسينات النصوص العربية */
        .stTextInput input, .stTextArea textarea, .stMarkdown p, div.stMarkdown { 
            direction: auto !important; 
            text-align: right !important; 
        }

        /* تصميم بطاقة العادة */
        .habit-card {
            border: 1px solid #333;
            background: #1A2332;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
            margin-bottom: 5px;
            transition: transform 0.2s;
        }
        .habit-card:hover { transform: scale(1.02); }

        /* تصميم شريط الجلسة (Timeline Row) */
        .session-row {
            background: #1A1C24;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left-width: 4px;
            border-left-style: solid;
        }
    </style>
    """, unsafe_allow_html=True)

def render_habit_card(habit, is_done):
    """رسم بطاقة العادة"""
    border_color = "#4CAF50" if is_done else "#333"
    opacity = "1.0" if is_done else "0.8"
    
    html = f"""
    <div class="habit-card" style="border-color:{border_color}; opacity:{opacity}">
        <div style="font-weight:bold; font-size:1.05em">{habit['title']}</div>
        <div style="color:gray; font-size:0.8em">🔥 {habit.get('streak', 0)}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_session_row(session):
    """رسم سطر الجلسة الزمنية"""
    pillar = session.get('pillar', 'General')
    
    # تحديد اللون حسب الركيزة
    if "Growth" in pillar: 
        color = "#E57CD8" # وردي للنمو
    elif "Vertical" in pillar: 
        color = "#4CAF50" # أخضر للمالية
    else: 
        color = "#888888" # رمادي للتنظيف

    # تنسيق الوقت والتاريخ
    date_str = session.get('date', '')
    start_time = session.get('start_time')
    
    time_str = ""
    if start_time:
        try:
            # تحويل timestamp إلى وقت مقروء
            dt = start_time.strftime("%I:%M %p") if hasattr(start_time, 'strftime') else ""
            time_str = f"{dt}"
        except: pass

    html = f"""
    <div class="session-row" style="border-left-color: {color};">
        <div>
            <div style="font-weight:bold; font-size:1.1em">{session.get('task', 'No Title')}</div>
            <div style="color:gray; font-size:0.8em; margin-top:2px">
                <span style="margin-right:10px">📅 {date_str}</span>
                <span style="margin-right:10px">⏰ {time_str}</span>
                <span>• {pillar}</span>
            </div>
        </div>
        <div style="font-family:monospace; font-weight:bold; font-size:1.1em; color:#E57CD8">
            {int(session.get('duration_min', 0))} m
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_progress_bar(label, value, target, unit="hrs"):
    """رسم شريط تقدم مخصص"""
    if target > 0:
        percent = min(100, int((value / target) * 100))
    else:
        percent = 0
        
    # Color Logic
    if percent < 30: color = "#EF5350" # Red
    elif percent < 70: color = "#FFCA28" # Yellow
    else: color = "#66BB6A" # Green
    
    html = f"""
    <div style="margin-bottom: 15px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
            <span style="font-weight:bold;">{label}</span>
            <span style="font-family:monospace; color:{color}">{value} / {target} {unit} ({percent}%)</span>
        </div>
        <div style="background:#333; border-radius:10px; height:10px; width:100%;">
            <div style="background:{color}; width:{percent}%; height:100%; border-radius:10px; transition: width 0.5s;"></div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)