import streamlit as st
import sys
import os
import uuid
import random

from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage
)


# =====================================================
# PROJECT CONFIGURATION
# =====================================================

project_root = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

sys.path.insert(
    0,
    project_root
)

try:
    from Backend.server import (
        workflow,
        get_all_chats,
        create_chat_record,
        rename_chat,
        delete_chat,
        upload_document
    )
except Exception as e:
    st.set_page_config(page_title="AI Assistant", page_icon="◆")
    st.error(
        "The backend failed to start. This usually means a required "
        "environment variable (e.g. GROQ_API_KEY) is missing, or a "
        f"dependency failed to import.\n\nDetails: {e}"
    )
    st.stop()


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="AI Assistant",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# ANIMATED STAR / SNOW BACKGROUND (pure CSS, no JS needed)
# =====================================================

def build_falling_particles(count=55):
    """Generates randomized CSS + HTML for falling stars/snow particles."""
    particles_html = []
    for i in range(count):
        left = random.uniform(0, 100)
        size = random.uniform(2, 4.5)
        duration = random.uniform(9, 24)
        delay = random.uniform(0, 20)
        opacity = random.uniform(0.3, 0.85)
        drift = random.uniform(-50, 50)
        particles_html.append(
            f"""<div class="particle" style="
                left:{left}vw;
                width:{size}px;
                height:{size}px;
                animation-duration:{duration}s;
                animation-delay:-{delay}s;
                opacity:{opacity};
                --drift:{drift}px;
            "></div>"""
        )
    return "".join(particles_html)


PARTICLES_HTML = build_falling_particles(55)


# =====================================================
# PROFESSIONAL COLORFUL UI THEME
# =====================================================

st.markdown(
    f"""
<style>

/* ==========================================
HIDE STREAMLIT CHROME (no header bar / no footer)
but KEEP the sidebar collapse control usable on mobile
========================================== */

#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}
div[data-testid="stToolbar"] {{ visibility: hidden; height: 0; }}
div[data-testid="stDecoration"] {{ display: none; }}
div[data-testid="stStatusWidget"] {{ visibility: hidden; }}

header[data-testid="stHeader"] {{
    background: transparent;
    height: 2.5rem;
}}

header[data-testid="stHeader"] * {{
    visibility: visible;
}}

/* Style the sidebar open/close control so it stays visible + on-theme */
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stBaseButton-headerNoPadding"] {{
    background: linear-gradient(135deg, #6366f1, #ec4899) !important;
    border-radius: 8px !important;
    color: white !important;
}}


/* ==========================================
GLOBAL APPLICATION - PROFESSIONAL GRADIENT THEME
========================================== */

html, body, .stApp {{
    background: radial-gradient(circle at 15% 10%, #1b1140 0%, transparent 45%),
                radial-gradient(circle at 85% 0%, #0d2a4d 0%, transparent 40%),
                radial-gradient(circle at 50% 100%, #14103a 0%, transparent 55%),
                linear-gradient(160deg, #0b0f2b 0%, #0f1638 40%, #1a1042 100%);
    background-attachment: fixed;
    color: #e8ecff;
    overflow-x: hidden;
}}

.block-container {{
    padding-top: 0.5rem;
    padding-bottom: 7rem;
    padding-left: 3rem;
    padding-right: 3rem;
    max-width: 1100px;
    margin: 0 auto;
}}


/* ==========================================
FALLING PARTICLES BACKGROUND (stars / snow)
========================================== */

.particles-container {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    pointer-events: none;
    z-index: 0;
}}

.particle {{
    position: absolute;
    top: -5vh;
    border-radius: 50%;
    background: radial-gradient(circle, #ffffff 0%, #a5b4ff 60%, transparent 100%);
    box-shadow: 0 0 6px 1px rgba(165, 180, 255, 0.75);
    animation-name: fall;
    animation-timing-function: linear;
    animation-iteration-count: infinite;
}}

@keyframes fall {{
    0% {{ transform: translateY(-10vh) translateX(0) scale(1); opacity: 0; }}
    10% {{ opacity: 1; }}
    100% {{ transform: translateY(110vh) translateX(var(--drift)) scale(0.6); opacity: 0.12; }}
}}

.stApp > header, .block-container, section[data-testid="stSidebar"] {{
    position: relative;
    z-index: 1;
}}


/* ==========================================
HERO TITLE BAR
========================================== */

.hero-title {{
    text-align: center;
    padding: 10px 10px 22px 10px;
    border-bottom: 1px solid rgba(167, 139, 250, 0.15);
    margin-bottom: 18px;
}}

.hero-badge {{
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 3px;
    background: linear-gradient(135deg, #6366f1, #ec4899);
    margin-right: 10px;
    vertical-align: middle;
    box-shadow: 0 0 10px rgba(236, 72, 153, 0.6);
}}

.hero-title h1 {{
    font-size: 28px;
    font-weight: 800;
    margin: 0;
    display: inline-block;
    background: linear-gradient(90deg, #7dd3fc, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: 0.3px;
    vertical-align: middle;
}}

.hero-title p {{
    color: #9199c9;
    font-size: 13.5px;
    margin-top: 6px;
    letter-spacing: 0.2px;
}}


/* ==========================================
SIDEBAR - GLASSMORPHISM STYLE
========================================== */

section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, rgba(20, 16, 56, 0.97) 0%, rgba(15, 12, 42, 0.99) 100%);
    border-right: 1px solid rgba(167, 139, 250, 0.2);
    backdrop-filter: blur(12px);
    min-width: 300px !important;
}}

section[data-testid="stSidebar"] * {{
    color: #e5e7ff;
}}

.sidebar-heading {{
    font-size: 12px;
    letter-spacing: 1.2px;
    color: #8b93c9;
    font-weight: 700;
    text-transform: uppercase;
    margin: 4px 0 10px 0;
}}


/* ==========================================
TEXT
========================================== */

p {{ color: #cbd3f7; }}
h1, h2, h3 {{ color: #f5f6ff; }}


/* ==========================================
BUTTONS - COLORFUL GRADIENT
========================================== */

.stButton button {{
    background: linear-gradient(90deg, #6366f1, #8b5cf6, #ec4899);
    background-size: 200% auto;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 9px 16px;
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.2px;
    transition: 0.3s ease;
    box-shadow: 0 4px 14px rgba(139, 92, 246, 0.3);
}}

.stButton button:hover {{
    background-position: right center;
    transform: translateY(-1px);
    box-shadow: 0 6px 18px rgba(236, 72, 153, 0.4);
}}

section[data-testid="stSidebar"] button {{
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(167, 139, 250, 0.3);
    box-shadow: none;
    font-size: 13px;
}}

section[data-testid="stSidebar"] button:hover {{
    background: rgba(139, 92, 246, 0.3);
    transform: none;
}}


/* ==========================================
CHAT AVATARS - clean gradient circles instead of emoji glyphs
========================================== */

div[data-testid="stChatMessageAvatarUser"],
div[data-testid="stChatMessageAvatarAssistant"] {{
    background: linear-gradient(135deg, #6366f1, #ec4899) !important;
}}


/* ==========================================
CHAT AREA - GLASS BUBBLES
========================================== */

div[data-testid="stChatMessage"] {{
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(167, 139, 250, 0.16);
    border-radius: 16px;
    padding: 16px 18px;
    margin-bottom: 14px;
    backdrop-filter: blur(6px);
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.22);
}}

div[data-testid="stChatMessage"] p {{
    color: #f1f3ff;
    font-size: 15.5px;
    line-height: 1.65;
    margin-bottom: 0;
}}

div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {{
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.14), rgba(99, 102, 241, 0.10));
    border: 1px solid rgba(236, 72, 153, 0.28);
}}

div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"]) {{
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.10), rgba(99, 102, 241, 0.12));
    border: 1px solid rgba(56, 189, 248, 0.26);
}}


/* ==========================================
CHAT INPUT - PROFESSIONAL PILL STYLE, PINNED & CENTERED
========================================== */

div[data-testid="stBottom"] > div {{
    background: linear-gradient(180deg, rgba(11, 15, 43, 0) 0%, rgba(11, 15, 43, 0.92) 35%, rgba(11, 15, 43, 0.98) 100%);
    backdrop-filter: blur(6px);
}}

div[data-testid="stChatInput"] {{
    max-width: 1040px;
    margin: 0 auto;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(167, 139, 250, 0.45);
    border-radius: 16px;
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35);
    padding: 2px 4px;
    transition: 0.25s ease;
}}

div[data-testid="stChatInput"]:focus-within {{
    border: 1px solid #a78bfa;
    box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.2), 0 6px 24px rgba(0, 0, 0, 0.35);
}}

div[data-testid="stChatInput"] textarea {{
    background: transparent !important;
    color: #f5f6ff !important;
    border: none !important;
    font-size: 15px !important;
    padding: 12px 10px !important;
}}

div[data-testid="stChatInput"] textarea::placeholder {{
    color: #8890c2 !important;
}}

div[data-testid="stChatInput"] button {{
    background: linear-gradient(135deg, #6366f1, #ec4899) !important;
    border-radius: 12px !important;
    box-shadow: 0 3px 10px rgba(139, 92, 246, 0.4) !important;
}}

div[data-testid="stChatInput"] button svg {{
    fill: white !important;
}}


/* ==========================================
FILE UPLOADER
========================================== */

[data-testid="stFileUploader"] {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px dashed rgba(167, 139, 250, 0.4);
    border-radius: 12px;
    padding: 12px;
}}

[data-testid="stFileUploader"] section {{
    background: transparent;
}}


/* ==========================================
CHAT HISTORY CARD
========================================== */

.chat-card {{
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(167, 139, 250, 0.22);
    padding: 10px 14px;
    border-radius: 10px;
    margin-bottom: 6px;
    color: #dbe0ff;
    font-size: 13px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    transition: 0.25s ease;
}}

.chat-card:hover {{
    background: rgba(139, 92, 246, 0.18);
    border-color: rgba(236, 72, 153, 0.35);
}}


/* ==========================================
STATUS BOXES
========================================== */

div[data-testid="stAlert"] {{
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(167, 139, 250, 0.28);
    font-size: 13px;
}}


/* Scrollbar styling */
::-webkit-scrollbar {{ width: 7px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
    background: linear-gradient(180deg, #6366f1, #ec4899);
    border-radius: 10px;
}}


/* ==========================================
RESPONSIVE DESIGN
========================================== */

@media (max-width: 768px) {{
    .block-container {{
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 8rem;
    }}

    div[data-testid="stChatMessage"] {{
        padding: 12px;
    }}

    div[data-testid="stChatMessage"] p {{
        font-size: 14.5px;
    }}

    .hero-title h1 {{
        font-size: 21px;
    }}

    .hero-title p {{
        font-size: 12px;
    }}

    div[data-testid="stChatInput"] {{
        max-width: 100%;
        border-radius: 14px;
    }}

    section[data-testid="stSidebar"] {{
        min-width: 82vw !important;
    }}
}}

</style>

<div class="particles-container">
    {PARTICLES_HTML}
</div>
""",
    unsafe_allow_html=True
)


# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def generate_thread_id():
    return str(uuid.uuid4())[:8]


def create_new_chat():
    thread_id = generate_thread_id()
    create_chat_record(thread_id)
    st.session_state.thread_ids.append(thread_id)
    st.session_state.chat_names[thread_id] = "New Conversation"
    st.session_state.current_thread_id = thread_id


def get_messages_from_database(thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = workflow.get_state(config)
        if state.values:
            return state.values.get("messages", [])
    except Exception as e:
        print(f"Failed to load state for thread {thread_id}: {e}")
    return []


def extract_text(content) -> str:
    """
    Normalize message content into a plain string.
    Some providers (incl. tool-calling responses) return content as a
    list of content blocks instead of a plain string.
    """

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                # Common shapes: {"type": "text", "text": "..."}
                if "text" in block:
                    parts.append(str(block["text"]))
        return "\n".join(p for p in parts if p)

    return str(content) if content else ""


def format_messages(messages):
    """
    Convert LangGraph message history into chat bubbles for display.

    Only user input and the model's final natural-language answers are
    shown. Intermediate tool calls and raw ToolMessage results are
    intentionally hidden so the user only sees a clean conversation,
    not internal plumbing.
    """

    formatted = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            text = extract_text(msg.content)
            if text:
                formatted.append({"role": "user", "content": text})

        elif isinstance(msg, AIMessage):
            # Skip AI messages that only contain tool calls with no
            # user-facing text (content is empty in that case).
            text = extract_text(msg.content)
            if text:
                formatted.append({"role": "assistant", "content": text})

        # ToolMessage instances are deliberately NOT rendered - they hold
        # raw tool output, not something meant to be shown as chat text.

    return formatted


# =====================================================
# SESSION STATE INITIALIZATION
# =====================================================

if "thread_ids" not in st.session_state:
    chats = get_all_chats()
    st.session_state.thread_ids = [chat[0] for chat in chats]

if "chat_names" not in st.session_state:
    chats = get_all_chats()
    st.session_state.chat_names = {chat[0]: chat[1] for chat in chats}

if "current_thread_id" not in st.session_state:
    if st.session_state.thread_ids:
        st.session_state.current_thread_id = st.session_state.thread_ids[0]
    else:
        create_new_chat()

if "selected_chat" not in st.session_state:
    st.session_state.selected_chat = None

thread_id = st.session_state.current_thread_id

config = {"configurable": {"thread_id": thread_id}}


# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown(
        """
        <h2 style="font-size:21px; font-weight:800; margin-bottom:4px;">
        AI Assistant
        </h2>
        <p style="color:#9199c9; font-size:12.5px; margin-bottom:18px;">
        Upload documents and chat with your knowledge base.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # ==========================================
    # DOCUMENT UPLOAD
    # ==========================================

    st.markdown(
        """<p class="sidebar-heading">Document Upload</p>""",
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader("Select PDF", type=["pdf"], label_visibility="collapsed")

    if uploaded_file:

        upload_folder = os.path.join(project_root, "uploaded_files")
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, uploaded_file.name)

        if not os.path.exists(file_path):
            try:
                with open(file_path, "wb") as file:
                    file.write(uploaded_file.getbuffer())

                with st.spinner("Processing document..."):
                    result = upload_document(file_path)

                if result.get("chunks", 0) > 0:
                    st.success(result["status"])
                else:
                    st.warning(result["status"])

            except Exception as e:
                st.error(f"Failed to process '{uploaded_file.name}': {e}")
        else:
            st.info("Document already indexed")

    st.divider()

    # ==========================================
    # CREATE NEW CHAT
    # ==========================================

    if st.button("New Conversation", use_container_width=True):
        create_new_chat()
        st.rerun()

    st.divider()

    # ==========================================
    # CHAT HISTORY
    # ==========================================

    st.markdown(
        """<p class="sidebar-heading">Conversations</p>""",
        unsafe_allow_html=True
    )

    for tid in reversed(st.session_state.thread_ids):

        st.markdown(
            f"""<div class="chat-card">{st.session_state.chat_names[tid]}</div>""",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("Open", key=f"open_{tid}", use_container_width=True):
                st.session_state.current_thread_id = tid
                st.rerun()

        with col2:
            if st.button("Delete", key=f"delete_{tid}", use_container_width=True):
                delete_chat(tid)

                if tid in st.session_state.thread_ids:
                    st.session_state.thread_ids.remove(tid)

                if tid in st.session_state.chat_names:
                    del st.session_state.chat_names[tid]

                if st.session_state.thread_ids:
                    st.session_state.current_thread_id = st.session_state.thread_ids[0]
                else:
                    create_new_chat()

                st.rerun()


# =====================================================
# HERO TITLE
# =====================================================

st.markdown(
    """
    <div class="hero-title">
        <span class="hero-badge"></span><h1>AI Assistant</h1>
        <p>Your intelligent, document-aware conversation partner</p>
    </div>
    """,
    unsafe_allow_html=True
)


# =====================================================
# MAIN CHAT AREA
# =====================================================

messages = format_messages(get_messages_from_database(thread_id))

# Display Existing Messages
for message in messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# =====================================================
# CHAT INPUT
# =====================================================

user_input = st.chat_input("Type your message...")

if user_input:

    # User Message
    with st.chat_message("user"):
        st.write(user_input)

    # AI Response
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):

            try:
                response = workflow.invoke(
                    {"messages": [HumanMessage(content=user_input)]},
                    config=config
                )
                final_message = response["messages"][-1]
                answer = extract_text(final_message.content)

                if not answer:
                    answer = "I wasn't able to generate a response. Please try rephrasing your question."

            except Exception as e:
                answer = f"Sorry, something went wrong while generating a response: {e}"

            st.write(answer)

    # Auto Rename Chat
    if st.session_state.chat_names[thread_id] == "New Conversation":
        title = user_input[:35]
        rename_chat(thread_id, title)
        st.session_state.chat_names[thread_id] = title

    st.rerun()