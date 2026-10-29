import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Carrega a chave salva no arquivo .env
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Chatbot Groq",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Visual
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #0b1020 0%, #111827 55%, #101522 100%);
        color: #f3f4f6;
    }
    [data-testid="stSidebar"] {
        background: #0b1220;
        border-right: 1px solid rgba(148, 163, 184, 0.16);
    }
    .hero {
        padding: 1.4rem 1.6rem;
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 18px;
        background: linear-gradient(120deg, rgba(30, 41, 59, .92), rgba(17, 24, 39, .8));
        margin-bottom: 1.2rem;
    }
    .hero h1 { margin: 0; font-size: 2.1rem; }
    .hero p { color: #aab6ca; margin: .45rem 0 0 0; }
    [data-testid="stChatMessage"] {
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: .65rem;
        background: rgba(15, 23, 42, 0.48);
    }
    div[data-testid="stMetric"] {
        background: rgba(30, 41, 59, .55);
        border: 1px solid rgba(148, 163, 184, .16);
        padding: 12px 15px;
        border-radius: 14px;
    }
    .small-muted { color: #94a3b8; font-size: .88rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Configurações da sessão
if "historico" not in st.session_state:
    st.session_state.historico = []
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = (
        "Você é um assistente útil, claro e educado. "
        "Responda em português brasileiro por padrão e organize respostas longas "
        "com títulos e listas quando isso ajudar."
    )

# Chave da API: primeiro .env, depois secrets do Streamlit
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    try:
        API_KEY = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        API_KEY = ""

# Barra lateral
with st.sidebar:
    st.markdown("## ⚙️ Configurações")
    st.caption("Personalize a conversa")

    modelo = st.selectbox(
        "Modelo da Groq",
        options=["openai/gpt-oss-120b"],
        index=0,
        help="Você pode adicionar outros modelos disponíveis na sua conta da Groq nesta lista.",
    )

    temperatura = st.slider(
        "Criatividade",
        min_value=0.0,
        max_value=1.5,
        value=0.7,
        step=0.1,
        help="Valores menores tendem a gerar respostas mais previsíveis.",
    )

    limite_tokens = st.select_slider(
        "Tamanho máximo da resposta",
        options=[512, 1024, 2048, 4096],
        value=2048,
        format_func=lambda n: f"{n:,} tokens".replace(",", "."),
    )

    st.session_state.system_prompt = st.text_area(
        "Instrução do assistente",
        value=st.session_state.system_prompt,
        height=125,
        help="Define o estilo e as orientações gerais do chatbot.",
    )

    st.divider()
    st.markdown("### 💬 Conversa")
    st.write(f"Mensagens no histórico: **{len(st.session_state.historico)}**")

    if st.button("🗑️ Limpar conversa", use_container_width=True):
        st.session_state.historico = []
        st.rerun()

    if st.session_state.historico:
        exportacao = ["# Histórico do Chatbot Groq", ""]
        for item in st.session_state.historico:
            nome = "Você" if item["role"] == "user" else "Assistente"
            exportacao.extend([f"## {nome}", item["content"], ""])
        st.download_button(
            "⬇️ Exportar conversa (.md)",
            data="\n".join(exportacao),
            file_name=f"conversa_groq_{datetime.now():%Y%m%d_%H%M}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.divider()
    st.markdown(
        '<p class="small-muted">Feito com Python · Streamlit · Groq</p>',
        unsafe_allow_html=True,
    )

# Cabeçalho principal
st.markdown(
    """
    <div class="hero">
        <h1>🤖 Chatbot Groq</h1>
        <p>Seu espaço de conversa com inteligência artificial.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Métricas rápidas
m1, m2, m3 = st.columns(3)
m1.metric("Mensagens enviadas", sum(1 for x in st.session_state.historico if x["role"] == "user"))
m2.metric("Respostas recebidas", sum(1 for x in st.session_state.historico if x["role"] == "assistant"))
m3.metric("Modelo ativo", "GPT OSS 120B")

if not API_KEY:
    st.error(
        "Não encontrei a chave da API da Groq. Crie um arquivo `.env` na mesma pasta "
        "do `app.py` e adicione `GROQ_API_KEY=sua_chave_aqui`."
    )
    st.info("A chave pode ser criada no painel da Groq. Não compartilhe sua chave com ninguém.")
    st.stop()

client = Groq(api_key=API_KEY)

# Exibe as mensagens anteriores
if not st.session_state.historico:
    st.info("👋 Comece digitando uma pergunta abaixo. Seu histórico fica disponível enquanto a sessão estiver ativa.")
else:
    for mensagem in st.session_state.historico:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])

# Campo de entrada
pergunta = st.chat_input("Digite sua mensagem...")

if pergunta:
    st.session_state.historico.append({"role": "user", "content": pergunta})

    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("A IA está preparando uma resposta..."):
            try:
                mensagens_api = [
                    {"role": "system", "content": st.session_state.system_prompt}
                ]
                mensagens_api.extend(st.session_state.historico)

                resposta = client.chat.completions.create(
                    model=modelo,
                    messages=mensagens_api,
                    temperature=temperatura,
                    max_completion_tokens=limite_tokens,
                )

                texto = resposta.choices[0].message.content
                if not texto or not texto.strip():
                    texto = "Não recebi uma resposta em texto. Tente reformular a pergunta."

                st.markdown(texto)
                st.session_state.historico.append(
                    {"role": "assistant", "content": texto}
                )

            except Exception as erro:
                # Remove a mensagem do usuário para evitar enviar uma conversa incompleta
                if st.session_state.historico and st.session_state.historico[-1]["role"] == "user":
                    st.session_state.historico.pop()
                st.error("Não consegui consultar a Groq. Confira sua conexão, a chave da API e o modelo selecionado.")
                with st.expander("Detalhes técnicos do erro"):
                    st.code(str(erro))
