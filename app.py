import streamlit as st
import os
from google import genai
from google.genai import types

# הגדרת תצורת הדף - תמיכה ב-RTL לכותרת הטאב
st.set_page_config(page_title="עוזר טכני ת\"י 466", page_icon="🏗️", layout="centered")

# --- הזרקת CSS מותאם אישית לתמיכה ב-RTL ועיצוב בועות צ'אט ---
st.markdown("""
    <style>
    /* הגדרת כיוון טקסט כללי לימין עבור האפליקציה */
    .main .block-container {
        direction: rtl;
        text-align: right;
    }
    
    /* עיצוב בועות הצ'אט */
    .chat-bubble {
        padding: 14px 18px;
        border-radius: 15px;
        margin-bottom: 10px;
        max-width: 80%;
        word-wrap: break-word;
        display: inline-block;
        line-height: 1.5;
    }
    
    /* בועת משתמש - מיושרת לימין, צבע רקע כחלחל */
    .user-container {
        text-align: right;
    }
    .user-bubble {
        background-color: #007acc;
        color: white;
        border-top-right-radius: 2px;
    }
    
    /* בועת סוכן (AI) - מיושרת לשמאל, אך הטקסט בפנים קריא מימין לשמאל */
    .assistant-container {
        text-align: right; /* נשאר בימין כדי להתאים לקריאה נוחה בעברית */
    }
    .assistant-bubble {
        background-color: #f1f0f0;
        color: #333333;
        border-top-left-radius: 2px;
        direction: rtl;
        text-align: right;
        width: 100%;
    }
    
    /* התאמת כפתורים ורכיבים בסיידבר ל-RTL */
    .stSidebar {
        direction: rtl;
    }
    </style>
""", unsafe_allow_html=True)

# --- סרגל צד (Sidebar) להגדרות ואבטחה ---
with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    
    # הזנת ה-API Key בצורה מאובטחת
# קריאת המפתח ישירות מהכספת המאובטחת של השרת
api_key = st.secrets["AIzaSyB2jrEW37IcOXk4B1SsE66BEt4tAZbR2G8"]
    
    
    # כפתור שיחה חדשה שמנקה את הזיכרון לחלוטין
    if st.button("🔄 שיחה חדשה (איקוס טוקנים)"):
        st.session_state.messages = []
        st.session_state.chat_session = None
        st.rerun()

# --- ניהול מצב השיחה (Session State) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

# כותרת ראשית של האפליקציה
st.title("🏗️ מומחה ת\"י 466 - בטון מזוין")
st.write("מערכת מענה מבוססת חשיבה מעמיקה לחלקים א' וב' של התקן.")

# --- הצגת היסטוריית הצ'אט מעוצבת ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
            <div class="user-container">
                <div class="chat-bubble user-bubble">{msg["content"]}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        # שימוש בתוך קונטיינר רגיל של סטרימליט כדי לאפשר תמיכה מלאה בסימוני Markdown ו-LaTeX
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg["content"])

# --- תיבת קלט למשתמש ותהליך שליחה ---
if prompt := st.chat_input("שאל שאלה על תקן 466..."):
    
    if not api_key_input:
        st.error("⚠️ אנא הכנס Google API Key בסרגל הצד כדי להתחיל בשיחה.")
    else:
        # הצגת הודעת המשתמש באופן מיידי במסך
        st.markdown(f"""
            <div class="user-container">
                <div class="chat-bubble user-bubble">{prompt}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # שמירה בהיסטוריית ההודעות
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # אתחול ה-Client והצ'אט במידה וזהו סיבוב ראשון
        if st.session_state.chat_session is None:
            try:
                # יצירת הלקוח עם ה-API Key שהוזן
                client = genai.Client(api_key=api_key_input)
                
                # הגדרת הקונפיגורציה בדיוק מהקוד שלך (כולל Thinking ו-System Instruction)
                system_instruction_text = (
                    "Role:\n"
                    "You are a highly precise technical assistant specializing in Israeli Standard SI 466 (ת\"י 466), "
                    "focusing on Part 1 and Part 2 (Concrete Structures: Reinforced Concrete). You must treat Part 2 as a "
                    "direct continuation of the requirements in Part 1.\n\n"
                    "Operational Protocol:\n"
                    "Source Integrity: Answer ONLY based on the uploaded files. If information is missing from the files, state: \"המידע אינו מופיע בתקנים שהועלו.\"\n\n"
                    "Mandatory Citation: Every answer MUST start with the exact clause number (סעיף), table number (טבלה), or figure (איור), and clearly state if it is from Part 1 or Part 2.\n\n"
                    "Table Presentation: Whenever the information is found in a table, recreate the table clearly in the chat using Markdown format. Do not just summarize it in text.\n\n"
                    "Terminology: Use the exact technical Hebrew terminology as it appears in the standard.\n\n"
                    "Output Format (Strictly Follow This):\n"
                    "[שם הנושא / הכותרת של הסעיף]\n\n"
                    "מקור: [ת\"י 466 חלק 1/2, סעיף X, עמוד Y]\n\n"
                    "הדרישה: [ציטוט או סיכום טכני מדויק]\n\n"
                    "טבלה רלוונטית: [אם קיימת, הצג אותה כאן בצורה מסודרת]\n\n"
                    "הערות נוספות: [הפניות לסעיפים קשורים או דגשים]\n\n"
                    "Constraint:\n"
                    "Never provide professional engineering advice. Your role is only to locate and retrieve information. "
                    "Treat Part 1 and Part 2 as the combined regulatory basis for reinforced concrete design.\n\n"
                    "Use bullet points for every list.\n"
                    "Use bold text for keywords and section numbers.\n"
                    "Add a horizontal line (---) between different sections of the answer.\n"
                    "When showing formulas, use LaTeX format (e.g., $C = A'_c f_{cd}$) so they stand out."
                )
                
                config = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="HIGH"),
                    system_instruction=[types.Part.from_text(text=system_instruction_text)]
                )
                
                # יצירת סשן צ'אט מתמשך דרך ה-SDK החדש
                st.session_state.chat_session = client.chats.create(
                    model="gemini-3.5-flash",
                    config=config
                )
            except Exception as e:
                st.error(f"שגיאה באתחול המודל: {e}")
                st.stop()

        # שליחת ההודעה וקבלת תגובה (בסטרימינג)
        try:
            with st.chat_message("assistant", avatar="🤖"):
                response_placeholder = st.empty()
                full_response = ""
                
                # ביצוע הסטרים דרך ה-chat_session
                response_stream = st.session_state.chat_session.send_message(prompt,)
                
                for chunk in response_stream:
                    if chunk.text:
                        full_response += chunk.text
                        # עדכון ה-UI בזמן אמת עם תמיכה ב-Markdown ונוסחאות LaTeX שייפלטו מהמודל
                        response_placeholder.markdown(full_response)
                
                # שמירה בהיסטוריית ההודעות בסיום הסטרים
                st.session_state.messages.append({"role": "model", "content": full_response})
                
        except Exception as e:
            st.error(f"שגיאה במהלך הפקת התגובה: {e}")
