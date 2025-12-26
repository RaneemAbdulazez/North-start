import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
from datetime import datetime

# --- 1. الإعدادات والتهيئة (CONFIG) ---
st.set_page_config(page_title="NorthStar OS", page_icon="🧭", layout="wide", initial_sidebar_state="collapsed")
load_dotenv() # تحميل مفتاح جوجل

# --- 2. التصميم ودعم اللغة (CSS STYLING) ---
st.markdown("""
<style>
    /* إخفاء القوائم الافتراضية */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* الثيم الداكن */
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    
    /* === ⚡ سحر الاتجاهات (RTL/LTR Auto) === */
    /* يجعل النصوص وحقول الإدخال تتكيف تلقائياً مع لغة الكتابة */
    .stTextInput input, .stTextArea textarea, .stMarkdown p, .stMarkdown li, div.stMarkdown {
        direction: auto !important;
        unicode-bidi: plaintext !important;
        text-align: start !important;
    }
    
    /* تصميم البطاقات */
    .metric-card {
        background-color: #1E1E1E; 
        border-radius: 12px; 
        padding: 20px;
        border: 1px solid #333; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
        text-align: center;
    }
    .metric-value { font-size: 2em; font-weight: bold; color: #4CAF50; }
    .metric-label { font-size: 0.9em; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    
    /* تحسين الشات */
    .stChatMessage { direction: auto; unicode-bidi: plaintext; }
</style>
""", unsafe_allow_html=True)

# --- 3. الاتصال بقاعدة البيانات (FIREBASE) ---
# --- تعديل دالة الاتصال لتلائم السحابة والمحلي ---
@st.cache_resource
def get_db():
    try:
        # التأكد من عدم تهيئة التطبيق مرتين
        if not firebase_admin._apps:
            # 1. محاولة القراءة من أسرار السحابة (Streamlit Secrets)
            if "firestore" in st.secrets:
                # تحويل إعدادات الـ secrets إلى Dictionary
                key_dict = dict(st.secrets["firestore"])
                # إصلاح مشكلة السطور الجديدة في المفتاح الخاص (Private Key Fix)
                if "private_key" in key_dict:
                    key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(key_dict)
            
            # 2. إذا لم نجدها، نحاول القراءة من الملف المحلي (Localhost)
            else:
                cred = credentials.Certificate("firestore_key.json")
                
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        st.stop()

db = get_db()

# --- 4. إعداد الذكاء الاصطناعي (GEMINI AI) ---
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception:
    st.warning("⚠️ لم يتم العثور على مفتاح Google AI في ملف .env")

def ask_coach(query, active_count):
    # System Prompt: شخصية المدرب
    sys_prompt = f"""
    أنت خبير استراتيجي صارم (Executive Coach).
    الهدف: $10,000 شهرياً في 2026.
    المهام النشطة حالياً: {active_count}.
    
    القواعد:
    1. إذا كانت المهام النشطة > 3، امنع المستخدم من بدء أي شيء جديد.
    2. كن مختصراً ومباشراً.
    3. ادعم اللغتين العربية والإنجليزية.
    """
    try:
        # استخدام الموديل الأحدث والأسرع
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(f"{sys_prompt}\n\nUser: {query}")
        return response.text
    except Exception as e:
        return f"حدث خطأ في الاتصال بالذكاء الاصطناعي: {e}"

# --- 5. وظائف البيانات (CRUD Functions) ---
def add_task(title):
    db.collection('tasks').add({
        'title': title, 'is_done': False, 'created_at': datetime.now()
    })

def get_tasks():
    docs = db.collection('tasks').stream()
    tasks = []
    for doc in docs:
        t = doc.to_dict()
        t['id'] = doc.id
        tasks.append(t)
    # ترتيب: غير المنجز أولاً
    return sorted(tasks, key=lambda x: (x['is_done'], str(x.get('created_at', ''))))

def toggle_task(task_id, current_status):
    db.collection('tasks').document(task_id).update({'is_done': not current_status})

def delete_task(task_id):
    db.collection('tasks').document(task_id).delete()

def freeze_idea(idea):
    db.collection('freezer').add({'idea': idea, 'created_at': datetime.now()})

def get_frozen_ideas():
    docs = db.collection('freezer').order_by('created_at', direction=firestore.Query.DESCENDING).stream()
    return [doc.to_dict().get('idea') for doc in docs]

# --- 6. إدارة الحالة والتبديل (STATE & TOGGLE) ---
if 'mode' not in st.session_state:
    st.session_state.mode = 'Focus'

# Header & Toggle
c_logo, c_empty, c_toggle = st.columns([2, 5, 2])
with c_logo:
    st.markdown("### 🧭 NorthStar OS")
with c_toggle:
    # زر التبديل الرئيسي
    is_strategy = st.toggle('Strategy Mode 🧠', value=(st.session_state.mode == 'Strategy'))
    st.session_state.mode = 'Strategy' if is_strategy else 'Focus'

st.divider()

# ==========================================
#  🟢 MODE 1: FOCUS (EXECUTION)
# ==========================================
if st.session_state.mode == 'Focus':
    st.markdown("<h1 style='text-align: center; color: #66BB6A; letter-spacing: 2px;'>🟢 DEEP FOCUS</h1>", unsafe_allow_html=True)
    
    # 1. Input Section
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("new_task", clear_on_submit=True):
            col_in, col_btn = st.columns([5, 1])
            title = col_in.text_input("New Task", placeholder="ما هي المهمة الواحدة الآن؟", label_visibility="collapsed")
            if col_btn.form_submit_button("➕"):
                if title:
                    add_task(title)
                    st.rerun()

        # 2. Tasks List
        tasks = get_tasks()
        if tasks:
            for task in tasks:
                cc1, cc2, cc3 = st.columns([1, 10, 1])
                with cc1:
                    done = st.checkbox("", value=task['is_done'], key=task['id'])
                    if done != task['is_done']:
                        toggle_task(task['id'], task['is_done'])
                        st.rerun()
                with cc2:
                    if task['is_done']:
                        st.markdown(f"<s style='color: #555'>{task['title']}</s>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<span style='font-size:1.1em'>{task['title']}</span>", unsafe_allow_html=True)
                with cc3:
                    if st.button("✕", key=f"del_{task['id']}"):
                        delete_task(task['id'])
                        st.rerun()
        else:
            st.info("No tasks. Pure freedom or pure procrastination?")

        # 3. Real Pomodoro Timer
        st.write("---")
        if st.button("Start 25m Deep Work ⏳", use_container_width=True):
            t_placeholder = st.empty()
            bar = st.progress(0)
            total_seconds = 25 * 60
            
            for i in range(total_seconds):
                # التحديث كل ثانية
                percent = (i + 1) / total_seconds
                bar.progress(percent)
                
                rem_sec = total_seconds - (i + 1)
                mins, secs = divmod(rem_sec, 60)
                t_placeholder.markdown(f"<h2 style='text-align:center; color:#66BB6A'>{mins:02d}:{secs:02d}</h2>", unsafe_allow_html=True)
                time.sleep(1) # ثانية حقيقية
            
            st.success("Session Done! Take a break.")
            st.balloons()

# ==========================================
#  🔴 MODE 2: STRATEGY (PLANNING & AI)
# ==========================================
else:
    st.markdown("<h1 style='text-align: center; color: #EF5350; letter-spacing: 2px;'>🔴 WAR ROOM</h1>", unsafe_allow_html=True)
    
    # Live Metrics
    all_tasks = get_tasks()
    active_tasks_count = len([t for t in all_tasks if not t['is_done']])
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Goal</div><div class="metric-value">$10,000</div></div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Current MRR</div><div class="metric-value" style="color:white">$2,000</div></div>""", unsafe_allow_html=True)
    with m3:
        color = "#EF5350" if active_tasks_count > 3 else "#FFA726"
        st.markdown(f"""<div class="metric-card"><div class="metric-label">Active WIP</div><div class="metric-value" style="color:{color}">{active_tasks_count}</div></div>""", unsafe_allow_html=True)

    st.write("---")
    
    # Freezer & Vault
    c_left, c_right = st.columns(2)
    with c_left:
        st.subheader("🧊 The Freezer")
        with st.form("freeze"):
            idea = st.text_area("Distracting Idea?", label_visibility="collapsed")
            if st.form_submit_button("Freeze It"):
                if idea:
                    freeze_idea(idea)
                    st.success("Frozen!")
    
    with c_right:
        st.subheader("❄️ Vault")
        ideas = get_frozen_ideas()
        if ideas:
            for i in ideas:
                st.code(i, language="text")
        else:
            st.caption("No frozen ideas.")

    st.write("---")
    
    # AI Coach Section
    st.subheader("🤖 AI Strategy Coach")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask the coach... (e.g., Should I start a new project?)"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = ask_coach(prompt, active_tasks_count)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})