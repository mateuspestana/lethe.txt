"""
Lethe.TXT - Anonimizador de Documentos
Interface Streamlit
Autor: Matheus C. Pestana
"""

import streamlit as st
from pathlib import Path
import io

from core.document_parser import extract_text, get_supported_extensions
from core.anonymizer import Anonymizer
from core.crypto import encrypt_mapping, decrypt_mapping

# Configuração da página
st.set_page_config(
    page_title="Lethe.TXT",
    page_icon="🔒",
    layout="wide",
)

# Inicializa session_state para persistir resultados
if 'anonymize_result' not in st.session_state:
    st.session_state.anonymize_result = None

if 'reverse_result' not in st.session_state:
    st.session_state.reverse_result = None

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .stats-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Cabeçalho com logo centralizado
_, _, col_logo, _, _= st.columns([3.5, 1, 1, 1, 3.5])
with col_logo:
    st.image("logo.png", width="stretch")

st.markdown('<p class="main-header">🔒 Lethe.TXT / Λήθη.ΤΞΤ </p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Anonimizador de Documentos - Proteja dados sensíveis em seus arquivos</p>', unsafe_allow_html=True)

# Tabs principais
tab_anonymize, tab_reverse = st.tabs(["📝 Anonimizar", "🔓 Reverter"])

with tab_anonymize:
    st.header("Anonimizar Documento")
    
    # Opções de input
    input_method = st.radio(
        "Escolha o método de entrada:",
        ["📁 Upload de arquivo", "✏️ Texto direto"],
        horizontal=True,
    )
    
    text_content = None
    filename = "documento"
    
    if input_method == "📁 Upload de arquivo":
        uploaded_file = st.file_uploader(
            "Selecione um arquivo",
            type=get_supported_extensions(),
            help="Formatos suportados: TXT, DOCX, DOC, PDF"
        )
        
        if uploaded_file:
            filename = Path(uploaded_file.name).stem
            file_type = Path(uploaded_file.name).suffix.lower().lstrip('.')
            
            with st.spinner("Extraindo texto..."):
                try:
                    text_content = extract_text(uploaded_file.read(), file_type)
                    st.success(f"✅ Arquivo carregado: {uploaded_file.name}")
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo: {e}")
    
    else:
        text_content = st.text_area(
            "Cole o texto aqui:",
            height=200,
            placeholder="Cole o texto que deseja anonimizar...",
            key="input_text"
        )
    
    # Configurações
    st.subheader("⚙️ Configurações")
    
    col1, col2 = st.columns(2)
    
    with col1:
        password = st.text_input(
            "🔑 Senha de criptografia",
            type="password",
            help="Esta senha será usada para criptografar o mapeamento. Guarde-a para reverter!",
            key="anon_password"
        )
    
    with col2:
        seed = st.number_input(
            "🎲 Seed (opcional)",
            min_value=0,
            value=0,
            help="Use um seed para resultados reproduzíveis"
        )
    
    # Botão de anonimização
    col_btn, col_clear = st.columns([3, 1])
    
    with col_btn:
        do_anonymize = st.button("🚀 Anonimizar", type="primary", use_container_width=True)
    
    with col_clear:
        if st.button("🗑️ Limpar", use_container_width=True):
            st.session_state.anonymize_result = None
            st.rerun()
    
    # Processa anonimização
    if do_anonymize:
        if not text_content:
            st.warning("⚠️ Por favor, forneça um texto para anonimizar.")
        elif not password:
            st.warning("⚠️ Por favor, defina uma senha para criptografar o mapeamento.")
        else:
            with st.spinner("Processando..."):
                try:
                    # Cria anonimizador
                    anonymizer = Anonymizer(seed=seed if seed > 0 else None)
                    
                    # Anonimiza
                    anonymized_text, mapping = anonymizer.anonymize(text_content)
                    
                    # Criptografa mapeamento
                    encrypted_mapping = encrypt_mapping(mapping, password)
                    
                    # Mostra estatísticas
                    summary = anonymizer.get_summary()
                    
                    # Salva no session_state
                    st.session_state.anonymize_result = {
                        'text_content': text_content,
                        'anonymized_text': anonymized_text,
                        'mapping': mapping,
                        'encrypted_mapping': encrypted_mapping,
                        'summary': summary,
                        'filename': filename,
                    }
                    
                except Exception as e:
                    st.error(f"❌ Erro durante anonimização: {e}")
                    raise e
    
    # Exibe resultados (persistente via session_state)
    if st.session_state.anonymize_result:
        result = st.session_state.anonymize_result
        
        st.success("✅ Documento anonimizado com sucesso!")
        
        # Estatísticas
        st.subheader("📊 Estatísticas")
        cols = st.columns(4)
        cols[0].metric("👤 Nomes", result['summary']['nomes'])
        cols[1].metric("📋 CPFs", result['summary']['cpfs'])
        cols[2].metric("🪪 RGs", result['summary']['rgs'])
        cols[3].metric("📅 Datas", result['summary']['datas'])
        
        # Mostra mapeamento (para conferência)
        with st.expander("🗺️ Ver Mapeamento de Substituições"):
            for entity_type, type_mapping in result['mapping'].items():
                if type_mapping:
                    st.write(f"**{entity_type.upper()}:**")
                    for original, replacement in type_mapping.items():
                        st.write(f"  - `{original}` → `{replacement}`")
        
        # Resultados
        st.subheader("📄 Resultados")
        
        col_orig, col_anon = st.columns(2)
        
        with col_orig:
            st.write("**Texto Original:**")
            st.text_area("Original", result['text_content'], height=300, disabled=True, label_visibility="collapsed", key="orig_display")
        
        with col_anon:
            st.write("**Texto Anonimizado:**")
            st.text_area("Anonimizado", result['anonymized_text'], height=300, disabled=True, label_visibility="collapsed", key="anon_display")
        
        # Downloads
        st.subheader("⬇️ Downloads")
        
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            st.download_button(
                "📥 Baixar Texto Anonimizado",
                data=result['anonymized_text'],
                file_name=f"{result['filename']}_anonimizado.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_anon_text"
            )
        
        with col_dl2:
            st.download_button(
                "🔐 Baixar Mapeamento Criptografado",
                data=result['encrypted_mapping'],
                file_name=f"{result['filename']}_mapping.lethe",
                mime="application/octet-stream",
                use_container_width=True,
                key="dl_mapping"
            )
        
        st.info("💡 **Importante:** Guarde o arquivo de mapeamento (.lethe) e a senha para poder reverter a anonimização!")

with tab_reverse:
    st.header("Reverter Anonimização")
    
    st.info("Use esta aba para restaurar o documento original usando o mapeamento criptografado.")
    
    # Upload do texto anonimizado
    anon_input = st.radio(
        "Texto anonimizado:",
        ["📁 Upload de arquivo", "✏️ Texto direto"],
        horizontal=True,
        key="anon_input"
    )
    
    anon_text = None
    
    if anon_input == "📁 Upload de arquivo":
        anon_file = st.file_uploader(
            "Selecione o arquivo anonimizado",
            type=['txt'],
            key="anon_file"
        )
        if anon_file:
            anon_text = anon_file.read().decode('utf-8')
    else:
        anon_text = st.text_area(
            "Cole o texto anonimizado:",
            height=150,
            key="anon_text_input"
        )
    
    # Upload do mapeamento
    mapping_file = st.file_uploader(
        "📁 Selecione o arquivo de mapeamento (.lethe)",
        type=['lethe'],
        key="mapping_file"
    )
    
    # Senha
    reverse_password = st.text_input(
        "🔑 Senha de descriptografia",
        type="password",
        key="reverse_password"
    )
    
    # Botões
    col_btn_rev, col_clear_rev = st.columns([3, 1])
    
    with col_btn_rev:
        do_reverse = st.button("🔓 Reverter", type="primary", use_container_width=True)
    
    with col_clear_rev:
        if st.button("🗑️ Limpar", use_container_width=True, key="clear_reverse"):
            st.session_state.reverse_result = None
            st.rerun()
    
    # Processa reversão
    if do_reverse:
        if not anon_text:
            st.warning("⚠️ Por favor, forneça o texto anonimizado.")
        elif not mapping_file:
            st.warning("⚠️ Por favor, faça upload do arquivo de mapeamento.")
        elif not reverse_password:
            st.warning("⚠️ Por favor, insira a senha de descriptografia.")
        else:
            with st.spinner("Revertendo..."):
                try:
                    # Descriptografa mapeamento
                    encrypted_data = mapping_file.read()
                    mapping = decrypt_mapping(encrypted_data, reverse_password)
                    
                    # Reverte
                    anonymizer = Anonymizer()
                    original_text = anonymizer.reverse(anon_text, mapping)
                    
                    # Salva no session_state
                    st.session_state.reverse_result = {
                        'original_text': original_text,
                    }
                    
                except ValueError as e:
                    st.error(f"❌ {e}")
                except Exception as e:
                    st.error(f"❌ Erro durante reversão: {e}")
    
    # Exibe resultados (persistente via session_state)
    if st.session_state.reverse_result:
        result = st.session_state.reverse_result
        
        st.success("✅ Documento restaurado com sucesso!")
        
        # Resultado
        st.subheader("📄 Texto Original Restaurado")
        st.text_area("Restaurado", result['original_text'], height=300, disabled=True, label_visibility="collapsed", key="restored_display")
        
        # Download
        st.download_button(
            "📥 Baixar Texto Original",
            data=result['original_text'],
            file_name="documento_restaurado.txt",
            mime="text/plain",
            use_container_width=True,
            key="dl_restored"
        )

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888;'>"
    "Lethe.TXT - Anonimizador de Documentos | "
    "Desenvolvido por Matheus C. Pestana"
    "</p>",
    unsafe_allow_html=True
)
