import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, date
import streamlit as st
import pandas as pd

# 1. الاتصال بقاعدة البيانات
@st.cache_resource
def get_db():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate("firestore_key.json")
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"⚠️ Database Error: {e}")
        st.stop()

db = get_db()

# ==========================================
# 1. TIME TRACKING (The Engine)
# ==========================================
def save_session(task, pillar, start_time, end_time, duration_minutes):
    """حفظ جلسة عمل"""
    db.collection('work_sessions').add({
        'task': task,
        'pillar': pillar,
        'start_time': start_time,
        'end_time': end_time,
        'duration_min': duration_minutes,
        'date': str(date.today()),
        'created_at': datetime.now()
    })

def get_today_sessions():
    """جلب جلسات اليوم"""
    today = str(date.today())
    # استخدام الترتيب البرمجي لتجنب مشاكل الفهرس مؤقتاً
    docs = db.collection('work_sessions').where('date', '==', today).stream()
    data = [d.to_dict() for d in docs]
    data.sort(key=lambda x: x['created_at'], reverse=True)
    return data

def get_recent_sessions(limit=10):
    """جلب آخر الجلسات (للسجل)"""
    docs = db.collection('work_sessions').order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit).stream()
    return [d.to_dict() for d in docs]

def get_total_time_today():
    """حساب مجموع وقت اليوم"""
    sessions = get_today_sessions()
    total_min = sum([s['duration_min'] for s in sessions])
    hours = int(total_min // 60)
    minutes = int(total_min % 60)
    return f"{hours}h {minutes}m"

# ==========================================
# 2. ANALYTICS (For Strategy Room)
# ==========================================
def get_all_sessions_df():
    """جلب كل البيانات للتحليل"""
    docs = db.collection('work_sessions').stream()
    data = [d.to_dict() for d in docs]
    return pd.DataFrame(data)

def get_pillar_stats():
    """تجميع الساعات حسب الركيزة"""
    df = get_all_sessions_df()
    if df.empty:
        return {}
    if 'pillar' not in df.columns or 'duration_min' not in df.columns:
        return {}
        
    stats = df.groupby('pillar')['duration_min'].sum().to_dict()
    # تحويل الدقائق لساعات
    return {k: round(v/60, 1) for k, v in stats.items()}

# ==========================================
# 3. HABITS (Legacy Support) - هذا ما كان ناقصاً
# ==========================================
def add_habit(title):
    db.collection('habits').add({
        'title': title, 
        'streak': 0, 
        'last_done': None, 
        'created_at': datetime.now()
    })

def get_habits():
    docs = db.collection('habits').order_by('created_at').stream()
    return [{**d.to_dict(), 'id': d.id} for d in docs]

def toggle_habit(habit_id, current_data):
    today = str(date.today())
    last = current_data.get('last_done')
    
    if last == today: # Undo
        db.collection('habits').document(habit_id).update({
            'last_done': None, 
            'streak': max(0, current_data.get('streak', 0) - 1)
        })
    else: # Do
        db.collection('habits').document(habit_id).update({
            'last_done': today, 
            'streak': current_data.get('streak', 0) + 1
        })

def delete_habit(habit_id):
    db.collection('habits').document(habit_id).delete()

# ==========================================
# 4. FREEZER & EXTRAS
# ==========================================
def freeze_idea(idea):
    db.collection('freezer').add({'idea': idea, 'created_at': datetime.now()})


# ... (Keep previous code) ...

# ==========================================
# 5. ADVANCED ANALYTICS (For Dashboard)
# ==========================================
def get_daily_summary_df():
    """تجهيز بيانات لرسم الـ Heatmap والتريند الأسبوعي"""
    df = get_all_sessions_df()
    
    if df.empty:
        return pd.DataFrame()

    # تحويل عمود التاريخ لـ datetime
    df['date_dt'] = pd.to_datetime(df['date'])
    
    # تجميع الساعات حسب اليوم
    daily = df.groupby('date_dt')['duration_min'].sum().reset_index()
    daily['hours'] = round(daily['duration_min'] / 60, 1)
    
    # إضافة معلومات إضافية للرسم (اسم اليوم، رقم الأسبوع)
    daily['day_name'] = daily['date_dt'].dt.day_name()
    daily['week_num'] = daily['date_dt'].dt.isocalendar().week
    daily['date_str'] = daily['date_dt'].dt.strftime('%Y-%m-%d')
    
    return daily

def get_time_metrics():
    """حساب الساعات لليوم، الأسبوع، والشهر"""
    df = get_all_sessions_df()
    if df.empty:
        return {'daily': 0, 'weekly': 0, 'monthly': 0}
        
    df['date_dt'] = pd.to_datetime(df['date'])
    now = datetime.now()
    today = now.date()
    
    # Daily
    daily_mask = df['date_dt'].dt.date == today
    daily_hours = df[daily_mask]['duration_min'].sum() / 60
    
    # Weekly (Start Monday)
    current_week = now.isocalendar().week
    weekly_mask = (df['date_dt'].dt.isocalendar().week == current_week) & (df['date_dt'].dt.year == now.year)
    weekly_hours = df[weekly_mask]['duration_min'].sum() / 60
    
    # Monthly
    monthly_mask = (df['date_dt'].dt.month == now.month) & (df['date_dt'].dt.year == now.year)
    monthly_hours = df[monthly_mask]['duration_min'].sum() / 60
    
    return {
        'daily': round(daily_hours, 1), 
        'weekly': round(weekly_hours, 1), 
        'monthly': round(monthly_hours, 1)
    }

def get_quarter_progress(quarter_str):
    """حساب الساعات المنجزة لكل ركيزة في ربع معين"""
    df = get_all_sessions_df()
    if df.empty: return {}
    
    df['date_dt'] = pd.to_datetime(df['date'])
    year = datetime.now().year
    
    q_map = {
        "Q1": [1, 2, 3],
        "Q2": [4, 5, 6],
        "Q3": [7, 8, 9],
        "Q4": [10, 11, 12]
    }
    
    months = q_map.get(quarter_str, [])
    if not months: return {}
    
    mask = (df['date_dt'].dt.month.isin(months)) & (df['date_dt'].dt.year == year)
    q_df = df[mask]
    
    if q_df.empty: return {}
    
    stats = q_df.groupby('pillar')['duration_min'].sum().to_dict()
    return {k: round(v/60, 1) for k, v in stats.items()}