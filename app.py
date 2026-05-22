import streamlit as st
from agent import TOOLS, run_agent, get_client

# ─── Konfigurasi Halaman ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="DeepSeek AI Assistant",
    page_icon="🐋",
    layout="centered"
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    .main-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #4F8EF7 0%, #235FDB 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .subtitle {
        text-align: center;
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 2rem;
    }
    .tool-badge {
        background: #1e2130;
        border: 1px solid #334;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 0.75rem;
        color: #aab;
        display: inline-block;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown('<h1 class="main-title">🐋 DeepSeek AI Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Powered by DeepSeek-V3 · Dilengkapi AI Agent Tools</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<span class="tool-badge">🕐 Jam & Tanggal</span>', unsafe_allow_html=True)
with col2:
    st.markdown('<span class="tool-badge">🔢 Kalkulator</span>', unsafe_allow_html=True)
with col3:
    st.markdown('<span class="tool-badge">🌤️ Info Cuaca</span>', unsafe_allow_html=True)

st.divider()

# ─── Inisialisasi Session State ───────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []      # History untuk API (termasuk tool messages)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # History untuk ditampilkan di UI

# ─── Sidebar: Pengaturan ─────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Pengaturan")

    model_choice = st.selectbox(
        "Pilih Model",
        options=["deepseek-chat", "deepseek-reasoner"],
        help="deepseek-chat = DeepSeek-V3 (cepat), deepseek-reasoner = DeepSeek-R1 (lebih dalam)"
    )

    system_prompt = st.text_area(
        "System Prompt",
        value="""Kamu adalah asisten AI yang ramah dan helpful bernama DeepSeek.
Kamu bisa berbicara dalam Bahasa Indonesia maupun Inggris.
Gunakan tools yang tersedia ketika diperlukan untuk memberikan informasi yang akurat.
Selalu berikan respons yang jelas, terstruktur, dan mudah dipahami.""",
        height=150
    )

    st.divider()

    if st.button("🗑️ Hapus Riwayat Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.chat_history = []
        st.rerun()

    st.divider()
    st.caption("💡 Tips: Coba tanya 'jam berapa sekarang?' atau 'hitung 25 * 48' atau 'cuaca Jakarta'")

# ─── Tampilkan Riwayat Chat ───────────────────────────────────────────────────

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ─── Input & Proses Pesan ─────────────────────────────────────────────────────

if prompt := st.chat_input("Ketik pesan kamu di sini..."):

    # Tampilkan pesan user
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Siapkan messages dengan system prompt
    if not st.session_state.messages:
        st.session_state.messages = [
            {"role": "system", "content": system_prompt}
        ]
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Proses dengan AI Agent
    with st.chat_message("assistant"):
        with st.spinner("Sedang berpikir..."):
            try:
                client = get_client(st.secrets["DEEPSEEK_API_KEY"])

                response_text, updated_messages = run_agent(
                    client=client,
                    messages=st.session_state.messages,
                    model=model_choice
                )

                st.session_state.messages = updated_messages
                st.markdown(response_text)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text
                })

            except Exception as e:
                if "401" in str(e) or "authentication" in str(e).lower():
                    st.error("❌ API Key tidak valid. Periksa `.streamlit/secrets.toml`")
                elif "429" in str(e):
                    st.error("⚠️ Rate limit tercapai. Tunggu beberapa saat lalu coba lagi.")
                else:
                    st.error(f"❌ Error: {str(e)}")