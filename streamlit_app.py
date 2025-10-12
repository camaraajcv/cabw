import json
from typing import Dict, List, Tuple
from datetime import date, timedelta
import streamlit as st

APP_TITLE = "Checklist de Preparação para Designação – CABW"
PAGES = [
    "Antes da Missão",
    "INSPSAU (Inspeção de Saúde)",
    "Pagamento",
    "RAIRE",
    "Passaporte e Visto",
]

# ----------------------
# Estado e navegação
# ----------------------

def _init_state():
    if "data" not in st.session_state:
        st.session_state.data = {page: [] for page in PAGES}
    if "page" not in st.session_state:
        st.session_state.page = PAGES[0]
    if "nav" not in st.session_state:
        st.session_state.nav = st.session_state.page
    if "auth_date" not in st.session_state:
        st.session_state.auth_date = None


def _page_index() -> int:
    return PAGES.index(st.session_state.page)


def _go_prev_page():
    idx = _page_index()
    new_page = PAGES[max(0, idx - 1)]
    st.session_state.page = new_page
    st.session_state.nav = new_page


def _go_next_page():
    idx = _page_index()
    new_page = PAGES[min(len(PAGES) - 1, idx + 1)]
    st.session_state.page = new_page
    st.session_state.nav = new_page

# ----------------------
# Helpers de tarefas manuais (mantidos para compatibilidade)
# ----------------------

def _get_tasks(page: str) -> List[Dict]:
    return st.session_state.data.setdefault(page, [])


def _toggle_task(page: str, idx: int, value: bool):
    st.session_state.data[page][idx]["done"] = value


def _update_notes(page: str, idx: int, value: str):
    st.session_state.data[page][idx]["notes"] = value


def _delete_task(page: str, idx: int):
    st.session_state.data[page].pop(idx)

# ----------------------
# UI helpers
# ----------------------

def status_badge(is_done: bool):
    color = "#16a34a" if is_done else "#dc2626"  # verde / vermelho
    label = "Feito" if is_done else "Aguardando"
    st.markdown(
        f"<span style='padding:2px 8px; border-radius:999px; background:{color}; color:white; font-size:12px;'>{label}</span>",
        unsafe_allow_html=True,
    )


def deadline_chip(d: date):
    today = date.today()
    delta = (d - today).days
    color = "#16a34a" if delta > 0 else "#dc2626"  # verde futuro / vermelho hoje ou passado
    txt = f"Prazo: {d.strftime('%d/%m/%Y')}"
    if delta < 0:
        txt += f" (Atraso: {abs(delta)}d)"
    elif delta == 0:
        txt += " (HOJE)"
    st.markdown(
        f"<div style='display:inline-block;padding:5px 12px;border-radius:12px;background:{color};color:white;font-weight:bold;font-size:12px;'>{txt}</div>",
        unsafe_allow_html=True,
    )

# ----------------------
# Flags comuns
# ----------------------

def _get_flag(key: str) -> bool:
    return bool(st.session_state.get(f"done-{key}", False))


def _set_flag(key: str, val: bool):
    st.session_state[f"done-{key}"] = val

# ----------------------
# FÉRIAS (datas relativas)
# ----------------------

def _get_ferias_tasks(auth_date: date) -> List[Dict]:
    if not auth_date:
        return []
    return [
        {
            "title": "Solicitar Férias no Portal do Militar",
            "deadline": auth_date - timedelta(days=100),
            "key": "ferias-1",
        },
        {
            "title": "Apresentação no Portal do Militar – INÍCIO de Férias",
            "deadline": auth_date - timedelta(days=30),
            "key": "ferias-2",
        },
        {
            "title": "Apresentação no Portal do Militar – TÉRMINO de Férias",
            "deadline": auth_date - timedelta(days=1),
            "key": "ferias-3",
        },
    ]


def _ferias_progress(auth_date: date):
    tasks = _get_ferias_tasks(auth_date)
    total = len(tasks)
    done = sum(1 for t in tasks if _get_flag(t["key"]))
    return done, total


def render_ferias_section():
    st.subheader("Férias – prazos automáticos")
    if not st.session_state.auth_date:
        st.info("Selecione a **data de autorização de saída do país** na barra lateral para ver os prazos de férias.")
        return 0, 0

    tasks = _get_ferias_tasks(st.session_state.auth_date)
    f_done = 0

    for t in tasks:
        cols = st.columns([0.08, 0.62, 0.15, 0.15])
        with cols[0]:
            checked = st.checkbox("", value=_get_flag(t["key"]), key=f"ui-{t['key']}")
            if checked != _get_flag(t["key"]):
                _set_flag(t["key"], checked)
        with cols[1]:
            st.markdown(f"**{t['title']}**")
            deadline_chip(t["deadline"])
        with cols[2]:
            status_badge(_get_flag(t["key"]))
        with cols[3]:
            st.write("")
        if _get_flag(t["key"]):
            f_done += 1

    return f_done, len(tasks)

# ----------------------
# PASSAPORTE & VISTO (automático + tabela opcional)
# ----------------------
_PASSAPORTE_DEFS: List[Tuple[int, str]] = [
    (180, "Fazer contato com o GAP para verificar possibilidade de passaporte pelo DECEA"),
    (155, "Agendar foto"),
    (150, "Elaborar Ofício de Apoio ao GAP solicitando apoio para emissão de passaporte"),
    (150, "Preencher o Formulário MRE (modelo militar) — 1 (uma) via para cada solicitante."),
    (150, "Preencher o Modelo de Autorização para Menor, caso aplicável."),
    (130, "Ofício de Apoio assinado"),
    (130, "FPP ou Portaria (se houver)"),
    (130, "RG Civil"),
    (130, "RG Militar"),
    (130, "CPF"),
    (130, "Certidão de Casamento ou Nascimento (se for o caso)"),
    (130, "Título de Eleitor"),
    (130, "Comprovante de Quitação Eleitoral"),
    (130, "Passaportes Oficiais anteriores, se tiver"),
    (130, "Fotos 5x7 cm (formato digital)"),
    (130, "Assinaturas digitalizadas (modelo em anexo no e-mail)"),
    (120, "Enviar por e-mail ao GAP (Seção de Passaportes)/DECEA ou EMAER: a) Formulários preenchidos; b) Arquivos digitais das fotos e assinaturas; c) Documentação digitalizada (PDF)"),
    (100, "Aguardar o envio dos Recibos MRE (enviados por e-mail após cadastro no sistema do Itamaraty)"),
    (100, "Envio/Entrega das Fotos, Recibos de Entrega e Passaportes antigos"),
    (100, "Aguardar recebimento das cópias dos Passaportes pelo ITAMARATY"),
    (100, "Preenchimento do Formulário DS-160"),
    (100, "Envio dos formulários em versão preto e branco para o GAP-SJ"),
    (70,  "Receber os passaportes e vistos"),
]

_PASSAPORTE_TABELA = [
    {"Categoria": "Passaporte Titular", "Atividade": "Preencher requerimento eletrônico de passaporte", "Prazo": "Assim que tiver a portaria", "Destino/Envio": "formulário-autoridades.serpro.gov.br"},
    {"Categoria": "", "Atividade": "Imprimir e assinar RER", "Prazo": "Logo após gerar o RER", "Destino/Envio": "Assinar e colar foto"},
    {"Categoria": "", "Atividade": "Incluir Ficha de Controle", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Identidade militar autenticada", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Documento de naturalidade", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Foto 5x7", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Certidão de quitação eleitoral", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Termo de devolução do passaporte anterior", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},

    {"Categoria": "Passaporte Marido/Esposa", "Atividade": "Preencher requerimento eletrônico de passaporte", "Prazo": "Assim que possível", "Destino/Envio": "formulário-autoridades.serpro.gov.br"},
    {"Categoria": "", "Atividade": "Imprimir e assinar RER", "Prazo": "Logo após gerar o RER", "Destino/Envio": "Assinar e colar foto"},
    {"Categoria": "", "Atividade": "Incluir Ficha de Controle", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Identidade civil autenticada (RG ou CNH)", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Documento de naturalidade (Certidão de Nascimento ou Casamento)", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Foto 5x7", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Certidão de quitação eleitoral", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},

    {"Categoria": "Passaporte Filho/Filha", "Atividade": "Preencher requerimento eletrônico de passaporte", "Prazo": "Assim que possível", "Destino/Envio": "formulário-autoridades.serpro.gov.br"},
    {"Categoria": "", "Atividade": "Imprimir e assinar RER (responsável assina)", "Prazo": "Logo após gerar o RER", "Destino/Envio": "Assinar e colar foto (responsável)"},
    {"Categoria": "", "Atividade": "Incluir Ficha de Controle", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Certidão de Nascimento autenticada", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Documento de naturalidade (Certidão de Nascimento)", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Preencher Formulário de Autorização para emissão de passaporte de menor Assinado por ambos os pais, reconhecer firma em cartório", "Prazo": "Assinado por ambos os pais, reconhecer firma em cartório", "Destino/Envio": "Anexar ao processo físico da filha enviado ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Foto 5x7", "Prazo": "Após emissão do RER", "Destino/Envio": "Processo físico enviado ao EMAER"},

    {"Categoria": "Visto A-2 Titular", "Atividade": "Preencher formulário DS-160", "Prazo": "Até 30 dias antes da missão", "Destino/Envio": "ceac.state.gov"},
    {"Categoria": "", "Atividade": "Imprimir confirmação DS-160", "Prazo": "Após preenchimento DS-160", "Destino/Envio": "Juntar ao processo"},
    {"Categoria": "", "Atividade": "Incluir Ficha de Controle Solicitação", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Portaria de Designação", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Passaporte oficial ou diplomático válido", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Cópias das páginas 2 e 3 do passaporte", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},

    {"Categoria": "Visto A-2 Titular", "Atividade": "Incluir Foto 5x7", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},
    {"Categoria": "", "Atividade": "Preencher formulário DS-160", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "ceac.state.gov"},
    {"Categoria": "", "Atividade": "Imprimir confirmação DS-160", "Prazo": "Após preenchimento DS-160", "Destino/Envio": "Juntar ao processo"},
    {"Categoria": "", "Atividade": "Incluir cópia do passaporte oficial", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Cópia das páginas 2 e 3 do passaporte", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Foto 5x7", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},

    {"Categoria": "Visto A-2 Filha", "Atividade": "Preencher formulário DS-160", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "ceac.state.gov"},
    {"Categoria": "", "Atividade": "Imprimir confirmação DS-160", "Prazo": "Após preenchimento DS-160", "Destino/Envio": "Juntar ao processo"},
    {"Categoria": "", "Atividade": "Incluir cópia do passaporte oficial", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Cópia das páginas 2 e 3 do passaporte", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},
    {"Categoria": "", "Atividade": "Incluir Foto 5x7", "Prazo": "Após obtenção do passaporte", "Destino/Envio": "Enviar ao EMAER"},
]


def _get_passaporte_tasks(auth_date: date) -> List[Dict]:
    if not auth_date:
        return []
    tasks = []
    for i, (offset, title) in enumerate(_PASSAPORTE_DEFS, start=1):
        tasks.append({
            "title": title,
            "deadline": auth_date - timedelta(days=offset),
            "key": f"pass-{i:02d}",
        })
    return tasks


def _passaporte_progress(auth_date: date):
    tasks = _get_passaporte_tasks(auth_date)
    total = len(tasks)
    done = sum(1 for t in tasks if _get_flag(t["key"]))
    return done, total


def render_passaporte_reference_table():
    st.markdown("### Tabela de referência – Passaporte e Visto")
    h = st.columns([0.22, 0.44, 0.18, 0.16])
    h[0].markdown("**Categoria**")
    h[1].markdown("**Atividade**")
    h[2].markdown("**Prazo**")
    h[3].markdown("**Destino/Envio**")
    st.divider()

    def _prazo_box(label_date: date, prefix: str = ""):
        today = date.today()
        delta = (label_date - today).days
        color = "#16a34a" if delta > 0 else "#dc2626"
        txt = f"{prefix}{label_date.strftime('%d/%m/%Y')}"
        st.markdown(
            f"<div style='display:inline-block;padding:5px 12px;border-radius:12px;background:{color};color:white;font-weight:bold;font-size:12px;'>{txt}</div>",
            unsafe_allow_html=True,
        )

    for row in _PASSAPORTE_TABELA:
        c = st.columns([0.22, 0.44, 0.18, 0.16])
        c[0].write(row.get("Categoria", ""))
        c[1].write(row.get("Atividade", ""))
        prazo_txt = row.get("Prazo", "").strip()
        if "30 dias antes da missão" in prazo_txt.lower() and st.session_state.auth_date:
            d = st.session_state.auth_date - timedelta(days=30)
            with c[2]:
                _prazo_box(d, prefix="Até 30 dias – ")
        else:
            c[2].write(prazo_txt)
        c[3].write(row.get("Destino/Envio", ""))


def render_passaporte_section():
    st.subheader("Passaporte e Visto – prazos automáticos")
    if not st.session_state.auth_date:
        st.info("Selecione a **data de autorização de saída do país** na barra lateral para ver os prazos de passaporte.")
        return 0, 0

    tasks = _get_passaporte_tasks(st.session_state.auth_date)
    p_done = 0

    for t in tasks:
        cols = st.columns([0.08, 0.62, 0.15, 0.15])
        with cols[0]:
            checked = st.checkbox("", value=_get_flag(t["key"]), key=f"ui-{t['key']}")
            if checked != _get_flag(t["key"]):
                _set_flag(t["key"], checked)
        with cols[1]:
            st.markdown(f"**{t['title']}**")
            deadline_chip(t["deadline"])
        with cols[2]:
            status_badge(_get_flag(t["key"]))
        with cols[3]:
            st.write("")
        if _get_flag(t["key"]):
            p_done += 1

    st.divider()
    if "show_pass_table" not in st.session_state:
        st.session_state.show_pass_table = False

    if st.session_state.show_pass_table:
        if st.button("🔙 Ocultar Tabela", use_container_width=True):
            st.session_state.show_pass_table = False
            st.rerun()
        render_passaporte_reference_table()
    else:
        if st.button("🔍 Visualizar Tabela Completa", use_container_width=True):
            st.session_state.show_pass_table = True
            st.rerun()

    return p_done, len(tasks)

# ----------------------
# INSPSAU (automático + dicas sob demanda)
# ----------------------

_INSPSAU_DEFS: List[Tuple[int, str]] = [
    (180, "Marcar exames Preventivos (MULHER)"),
    (120, "Marcar Inspeção de Saúde (Letra F) para toda família"),
    (30,  "Resultado da INSPSAU publicada em BCA e nas alterações"),
]


def _get_inspsau_tasks(auth_date: date) -> List[Dict]:
    if not auth_date:
        return []
    tasks = []
    for i, (offset, title) in enumerate(_INSPSAU_DEFS, start=1):
        tasks.append({
            "title": title,
            "deadline": auth_date - timedelta(days=offset),
            "key": f"insp-{i:02d}",
        })
    return tasks


def _inspsau_progress(auth_date: date):
    tasks = _get_inspsau_tasks(auth_date)
    total = len(tasks)
    done = sum(1 for t in tasks if _get_flag(t["key"]))
    return done, total

_INSPSAU_TIPS = [
    {"Categoria": "Pré-inspeção", "Item/Exame": "Realizar INSPSAU 120 dias antes do embarque", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Jejum de 10-12h para coleta de exames", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Finalizar tratamentos médicos e odontológicos prévios", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Carteira de vacinação atualizada", "Observações": "Hepatite B, Febre Amarela e Tétano em dia"},
    {"Categoria": "Recomendações gerais", "Item/Exame": "Agendar Teste Ergométrico", "Observações": "Obrigatório a partir de 35 anos"},
    {"Categoria": "", "Item/Exame": "Agendar Radiografia Panorâmica Oral", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Realizar EPF (sangue oculto nas fezes)", "Observações": "> 40 anos obrigatório"},
    {"Categoria": "", "Item/Exame": "Revisão odontológica / finalização de tratamentos", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Atualizar Carteira de Vacinação", "Observações": ""},
    {"Categoria": "Recomendações específicas - Mulheres", "Item/Exame": "Avaliação ginecológica e exames ginecológicos", "Observações": "Obrigatório se vida sexual iniciada. Papanicolau válido por 180 dias"},
    {"Categoria": "Exames clínicos obrigatórios", "Item/Exame": "Exame médico geral (altura, peso, IMC, PA, FC)", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Exame oftalmológico completo", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Otorrino com audiometria tonal aérea", "Observações": "Validade máxima: 180 dias"},
    {"Categoria": "", "Item/Exame": "Exame odontológico com radiografia panorâmica", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Exame psiquiátrico + questionários L e M", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Exame neurológico (EEG se indicado)", "Observações": "EEG às quintas, se indicado"},
    {"Categoria": "", "Item/Exame": "Exame ginecológico", "Observações": ""},
    {"Categoria": "", "Item/Exame": "ECG em repouso (a partir de 12 anos)", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Teste ergométrico (>= 35 anos)", "Observações": "Trazer resultado no dia"},
    {"Categoria": "", "Item/Exame": "Radiografia de tórax (PA e perfil)", "Observações": ""},
    {"Categoria": "Exames laboratoriais - até 35 anos", "Item/Exame": "Hemograma completo", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Glicose, ureia, creatinina", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Grupo sanguíneo e fator Rh", "Observações": ""},
    {"Categoria": "", "Item/Exame": "VDRL (e FTA-ABS se positivo)", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Anti-HIV (com confirmação se positivo)", "Observações": ""},
    {"Categoria": "", "Item/Exame": "EAS (urina tipo 1)", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Beta-HCG (para mulheres)", "Observações": ""},
    {"Categoria": "Exames laboratoriais - mulheres", "Item/Exame": "Colesterol total, HDL, LDL, triglicérides", "Observações": "Válido por 180 dias"},
    {"Categoria": "Exames laboratoriais - acima de 35 anos", "Item/Exame": "Ácido úrico", "Observações": ""},
    {"Categoria": "", "Item/Exame": "PSA total (>= 45 anos)", "Observações": ""},
    {"Categoria": "", "Item/Exame": "PSA livre (se PSA total > 2,5)", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Hemoglobina glicada (se aplicável)", "Observações": ""},
    {"Categoria": "Vacinas obrigatórias", "Item/Exame": "Vacina Febre Amarela", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Vacina Antitetânica", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Vacina Hepatite B", "Observações": ""},
    {"Categoria": "", "Item/Exame": "Vacina COVID-19", "Observações": ""},
    {"Categoria": "Dependentes < 12 anos", "Item/Exame": "Relatório do pediatra", "Observações": "Será feito no dia da inspeção"},
    {"Categoria": "", "Item/Exame": "Carteira de Vacinação da criança", "Observações": "Cópia da caderneta"},
    {"Categoria": "", "Item/Exame": "Exames sob critério clínico", "Observações": ""},
]


def render_inspsau_tips():
    st.markdown("### Dicas sobre a INSPSAU")
    h = st.columns([0.24, 0.46, 0.30])
    h[0].markdown("**Categoria**")
    h[1].markdown("**Item / Exame**")
    h[2].markdown("**Observações**")
    st.divider()
    for row in _INSPSAU_TIPS:
        c = st.columns([0.24, 0.46, 0.30])
        c[0].write(row.get("Categoria", ""))
        c[1].write(row.get("Item/Exame", ""))
        c[2].write(row.get("Observações", ""))


def render_inspsau_section():
    st.subheader("INSPSAU – prazos automáticos")
    if not st.session_state.auth_date:
        st.info("Selecione a **data de autorização de saída do país** na barra lateral para ver os prazos da INSPSAU.")
        return 0, 0

    tasks = _get_inspsau_tasks(st.session_state.auth_date)
    i_done = 0

    for t in tasks:
        cols = st.columns([0.08, 0.62, 0.15, 0.15])
        with cols[0]:
            checked = st.checkbox("", value=_get_flag(t["key"]), key=f"ui-{t['key']}")
            if checked != _get_flag(t["key"]):
                _set_flag(t["key"], checked)
        with cols[1]:
            st.markdown(f"**{t['title']}**")
            deadline_chip(t["deadline"])
        with cols[2]:
            status_badge(_get_flag(t["key"]))
        with cols[3]:
            st.write("")
        if _get_flag(t["key"]):
            i_done += 1

    st.divider()
    if "show_inspsau_tips" not in st.session_state:
        st.session_state.show_inspsau_tips = False

    if st.session_state.show_inspsau_tips:
        if st.button("🔙 Ocultar Dicas", use_container_width=True):
            st.session_state.show_inspsau_tips = False
            st.rerun()
        render_inspsau_tips()
    else:
        if st.button("💡 Dicas sobre a INSPSAU", use_container_width=True):
            st.session_state.show_inspsau_tips = True
            st.rerun()

    return i_done, len(tasks)

# ----------------------
# PAGAMENTO (automático)
# ----------------------

_PAGAMENTO_DEFS: List[Tuple[int, str]] = [
    (90, "Tomar conhecimento das peculiaridades do pagamento no exterior (Módulo 16 do MCA 177-2) e verificar com a UPAG a transcrição da portaria de designação em Boletim Interno."),

    (60, "Preencher dados (portaria, identidade, comprovante de residência) em https://www.bbamericas.com/br/expatriados/ para abertura on-line da conta-corrente no exterior."),
    (60, "Aguardar análise do Banco do Brasil Americas; sanar pendências ou receber confirmação de abertura da conta-corrente por e-mail."),
    (60, "Após abertura da conta e com a data do deslocamento definida, enviar para chefiapp2.dirad@fab.mil.br: Declaração de Embarque (Anexo A), Termo de Ciência (Anexo B) e captura do e-mail do banco com nome e nº da conta."),
    (60, "Enviar a Declaração de Embarque (Anexo A) ao Setor de Pagamento de Pessoal da UPAG."),
    (60, "Receber por e-mail (PP2) a planilha estimativa de retribuição mensal (Anexo C) e, se aplicável, cálculos do FSN (Anexo D) e pensão alimentícia (Anexo E); responder informando a forma de recebimento da Ajuda de Custo de ida."),

    (10, "Se houver obrigação de pensão alimentícia/judicial: preencher a 'Declaração de Pagamento de Pensão Alimentícia durante Missão no Exterior' (Anexo E) e efetuar, até o dia 5 do mês de embarque, o pagamento da 1ª parcela via GRU (valor de 1 mês)."),
    (10, "Se optar por sacar parte da Ajuda de Custo em espécie: informar à PP2 (por e-mail) com, no mínimo, 8 dias úteis de antecedência a agência (do rol enviado), o valor (US$ múltiplos de 100) e a data do saque; janela entre D-30 e 3 dias úteis antes do embarque."),
    (10, "Se não houver interesse no saque em espécie: informar por e-mail à PP2 para pagamento integral da Ajuda de Custo na conta-corrente do banco credenciado."),
    (10, "Ao receber o Ofício de venda de moeda estrangeira (PP2), conferir e solicitar ajustes; no dia do saque levar o Ofício e documento com foto; após o saque, enviar à PP2/SDPP (chefiapp2.dirad@fab.mil.br) cópia do contrato de câmbio emitido pelo Banco do Brasil SA."),

    (5,  "A partir do mês de embarque, regularizar diretamente com as entidades consignatárias os pagamentos devidos durante a missão no exterior."),
]


def _get_pagamento_tasks(auth_date: date) -> List[Dict]:
    if not auth_date:
        return []
    tasks = []
    for i, (offset, title) in enumerate(_PAGAMENTO_DEFS, start=1):
        tasks.append({
            "title": title,
            "deadline": auth_date - timedelta(days=offset),
            "key": f"pay-{i:02d}",
        })
    return tasks


def _pagamento_progress(auth_date: date):
    tasks = _get_pagamento_tasks(auth_date)
    total = len(tasks)
    done = sum(1 for t in tasks if _get_flag(t["key"]))
    return done, total


def render_pagamento_section():
    st.subheader("Pagamento – prazos automáticos")
    if not st.session_state.auth_date:
        st.info("Selecione a **data de autorização de saída do país** na barra lateral para ver os prazos de Pagamento.")
        return 0, 0

    tasks = _get_pagamento_tasks(st.session_state.auth_date)
    pay_done = 0

    for t in tasks:
        cols = st.columns([0.08, 0.62, 0.15, 0.15])
        with cols[0]:
            checked = st.checkbox("", value=_get_flag(t["key"]), key=f"ui-{t['key']}")
            if checked != _get_flag(t["key"]):
                _set_flag(t["key"], checked)
        with cols[1]:
            st.markdown(f"**{t['title']}**")
            deadline_chip(t["deadline"])
        with cols[2]:
            status_badge(_get_flag(t["key"]))
        with cols[3]:
            st.write("")
        if _get_flag(t["key"]):
            pay_done += 1

    return pay_done, len(tasks)

# ----------------------
# RAIRE (automático)
# ----------------------

# Offsets em dias relativos à data de autorização:
# use valores POSITIVOS para D-XX (antes) e NEGATIVOS para D+XX (depois)
_RAIRE_DEFS: List[Tuple[int, str]] = [
    (30,  "Verificar o valor do aluguel em https://raire-pp2-sdpp.streamlit.app/"),  # D-30
    (-10, "Contrato assinado (Locador/Locatário)"),                                   # D+10
    (-15, "Contrato traduzido para Português"),                                      # D+15
    (-20, "Declaração de Pagamento (ANEXO H) assinada pelo Adido/Chefe"),            # D+20
    (-30, "Comprovante de Pagamento (Recibo/NF/Fatura + comprovante bancário)"),     # D+30
]


def _get_raire_tasks(auth_date: date) -> List[Dict]:
    if not auth_date:
        return []
    tasks = []
    for i, (offset, title) in enumerate(_RAIRE_DEFS, start=1):
        # se offset > 0 => D-offset (antes); se offset < 0 => D+abs(offset) (depois)
        deadline = auth_date - timedelta(days=offset)
        tasks.append({
            "title": title,
            "deadline": deadline,
            "key": f"raire-{i:02d}",
        })
    return tasks


def _raire_progress(auth_date: date):
    tasks = _get_raire_tasks(auth_date)
    total = len(tasks)
    done = sum(1 for t in tasks if _get_flag(t["key"]))
    return done, total


def render_raire_section():
    st.subheader("RAIRE – prazos automáticos")
    if not st.session_state.auth_date:
        st.info("Selecione a **data de autorização de saída do país** na barra lateral para ver os prazos da RAIRE.")
        return 0, 0

    tasks = _get_raire_tasks(st.session_state.auth_date)
    r_done = 0

    for t in tasks:
        cols = st.columns([0.08, 0.62, 0.15, 0.15])
        with cols[0]:
            checked = st.checkbox("", value=_get_flag(t["key"]), key=f"ui-{t['key']}")
            if checked != _get_flag(t["key"]):
                _set_flag(t["key"], checked)
        with cols[1]:
            # Link clicável para o primeiro item (aluguel)
            title = t['title']
            if "raire-pp2-sdpp.streamlit.app" in title:
                title = title.replace("https://raire-pp2-sdpp.streamlit.app/", "[raire-pp2-sdpp.streamlit.app](https://raire-pp2-sdpp.streamlit.app/)")
            st.markdown(f"**{title}**")
            deadline_chip(t["deadline"])
        with cols[2]:
            status_badge(_get_flag(t["key"]))
        with cols[3]:
            st.write("")
        if _get_flag(t["key"]):
            r_done += 1

    return r_done, len(tasks)

# ----------------------
# Progresso geral
# ----------------------

def _overall_progress() -> float:
    total = 0
    done = 0
    # listas manuais (se houver)
    for page in PAGES:
        tasks = _get_tasks(page)
        total += len(tasks)
        done += sum(1 for t in tasks if t.get("done"))
    # blocos automáticos
    if st.session_state.auth_date:
        f_done, f_total = _ferias_progress(st.session_state.auth_date)
        p_done, p_total = _passaporte_progress(st.session_state.auth_date)
        i_done, i_total = _inspsau_progress(st.session_state.auth_date)
        pay_done, pay_total = _pagamento_progress(st.session_state.auth_date)
        r_done, r_total = _raire_progress(st.session_state.auth_date)
        total += (f_total + p_total + i_total + pay_total + r_total)
        done  += (f_done + p_done + i_done + pay_done + r_done)
    return (done / total) if total else 0.0

# ----------------------
# Exportar / importar
# ----------------------

def export_json_button():
    extra_state = {k: v for k, v in st.session_state.items() if k.startswith("done-")}
    payload = {
        "lists": st.session_state.data,
        "auth_date": st.session_state.auth_date.isoformat() if st.session_state.auth_date else None,
        "extras": extra_state,
    }
    blob = json.dumps(payload, ensure_ascii=False, indent=2)
    st.download_button(
        label="⬇️ Exportar progresso (JSON)",
        file_name="cabw_checklist.json",
        mime="application/json",
        data=blob,
        use_container_width=True,
    )


def import_json_uploader():
    up = st.file_uploader("Importar progresso (JSON)", type=["json"], accept_multiple_files=False)
    if up is not None:
        try:
            data = json.loads(up.read().decode("utf-8"))
            if isinstance(data, dict):
                lists = data.get("lists", {})
                for page in PAGES:
                    lists.setdefault(page, [])
                st.session_state.data = lists

                ad = data.get("auth_date")
                st.session_state.auth_date = date.fromisoformat(ad) if ad else None

                extras = data.get("extras", {})
                for k, v in extras.items():
                    st.session_state[k] = v

                st.success("Progresso importado com sucesso.")
            else:
                st.error("Arquivo JSON inválido.")
        except Exception as e:
            st.error(f"Falha ao importar: {e}")

# ----------------------
# Render por página
# ----------------------

def render_tasks(page: str):
    st.subheader(page)

    manual_tasks = _get_tasks(page)
    manual_done = sum(1 for t in manual_tasks if t.get("done"))
    manual_total = len(manual_tasks)

    auto_done = 0
    auto_total = 0

    if page == "Férias":
        st.info("As atividades de **Férias** são geradas automaticamente a partir da data selecionada.")
        f_done, f_total = render_ferias_section()
        auto_done += f_done
        auto_total += f_total
        st.divider()
    elif page == "Passaporte e Visto":
        st.info("As atividades de **Passaporte e Visto** são geradas automaticamente a partir da data selecionada.")
        p_done, p_total = render_passaporte_section()
        auto_done += p_done
        auto_total += p_total
        st.divider()
    elif page == "INSPSAU (Inspeção de Saúde)":
        st.info("As atividades da **INSPSAU** são geradas automaticamente a partir da data selecionada.")
        i_done, i_total = render_inspsau_section()
        auto_done += i_done
        auto_total += i_total
        st.divider()
    elif page == "Pagamento":
        st.info("As atividades de **Pagamento** são geradas automaticamente a partir da data selecionada.")
        pay_done, pay_total = render_pagamento_section()
        auto_done += pay_done
        auto_total += pay_total
        st.divider()
    elif page == "RAIRE":
        st.info("As atividades da **RAIRE** são geradas automaticamente a partir da data selecionada.")
        r_done, r_total = render_raire_section()
        auto_done += r_done
        auto_total += r_total
        st.divider()
    elif page == "Pagamento":
        st.info("As atividades de **Pagamento** são geradas automaticamente a partir da data selecionada.")
        pay_done, pay_total = render_pagamento_section()
        auto_done += pay_done
        auto_total += pay_total
        st.divider()

    total = manual_total + auto_total
    done = manual_done + auto_done
    prog = (done / total) if total else 0.0
    st.progress(prog, text=f"Progresso: {int(prog*100)}%")

    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("◀️ Anterior", use_container_width=True, disabled=_page_index() == 0):
            _go_prev_page()
            st.rerun()
    with c2:
        idx = _page_index() + 1
        st.markdown(f"<div style='text-align:center;'>Etapa {idx}/{len(PAGES)}</div>", unsafe_allow_html=True)
    with c3:
        if st.button("Próximo ▶️", use_container_width=True, disabled=_page_index() == len(PAGES)-1):
            _go_next_page()
            st.rerun()

# ----------------------
# App principal
# ----------------------

def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🛫", layout="wide")
    _init_state()

    st.title(APP_TITLE)
    st.caption("Acompanhe o status dos afazeres antes da IDA e nas primeiras etapas na CABW.")

    # Barra superior com Data da Missão e Progresso Geral
    top1, top2 = st.columns([1, 1])
    with top1:
        st.markdown("**Data de autorização de saída do país**")
        st.session_state.auth_date = st.date_input(
            "Selecione a data",
            value=st.session_state.auth_date,
            format="DD/MM/YYYY",
        )
    with top2:
        st.markdown("**Progresso Geral**")
        overall = _overall_progress()
        st.progress(overall, text=f"{int(overall*100)}% concluído")

    st.divider()

    with st.sidebar:
        st.header("Menu")
        nav_index = PAGES.index(st.session_state.page)
        selected = st.radio("Etapas", options=PAGES, index=nav_index)
        st.session_state.page = selected
        st.divider()
        export_json_button()
        import_json_uploader()
        st.caption("Dica: exporte seu progresso antes de trocar de dispositivo.")

    render_tasks(st.session_state.page)

    st.divider()
    st.caption("Versão com prazos automáticos para Férias, Passaporte/Visto e INSPSAU. Tabelas auxiliares sob demanda.")


if __name__ == "__main__":
    main()
