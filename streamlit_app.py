import json
from typing import Dict, List, Tuple
from datetime import date, timedelta, datetime
import streamlit as st

APP_TITLE = "Checklist de Preparação para Designação – CABW"
PAGES = [
    "Antes da Missão",
    "Chegada na CABW",
    "INSPSAU (Inspeção de Saúde)",
    "Pagamento",
    "RAIRE",
    "Passaporte e Visto",
]

# ----------------------
# Helpers de estado
# ----------------------

def _init_state():
    if "data" not in st.session_state:
        st.session_state.data = {page: [] for page in PAGES}
    if "page" not in st.session_state:
        st.session_state.page = PAGES[0]
    if "auth_date" not in st.session_state:
        st.session_state.auth_date = None


def _get_tasks(page: str) -> List[Dict]:
    return st.session_state.data.setdefault(page, [])


def _save_task(page: str, title: str):
    tasks = _get_tasks(page)
    tasks.append({
        "title": title.strip(),
        "done": False,
        "notes": "",
    })


def _toggle_task(page: str, idx: int, value: bool):
    st.session_state.data[page][idx]["done"] = value


def _update_notes(page: str, idx: int, value: str):
    st.session_state.data[page][idx]["notes"] = value


def _delete_task(page: str, idx: int):
    st.session_state.data[page].pop(idx)


def _progress(tasks: List[Dict]) -> float:
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks if t.get("done"))
    return done / len(tasks)

# ----------------------
# FERIAS (geradas a partir da data de autorização de saída do país)
# ----------------------

def _get_ferias_tasks(auth_date: date) -> List[Dict]:
    """Retorna as 3 atividades de férias e seus prazos relativos à data selecionada."""
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
            # assumindo que a data de missão = data de saída do país
            "deadline": auth_date - timedelta(days=1),
            "key": "ferias-3",
        },
    ]


def _get_ferias_done(key: str) -> bool:
    return bool(st.session_state.get(f"done-{key}", False))


def _set_ferias_done(key: str, val: bool):
    st.session_state[f"done-{key}"] = val


def _ferias_progress(auth_date: date) -> Tuple[int, int]:
    tasks = _get_ferias_tasks(auth_date)
    total = len(tasks)
    done = sum(1 for t in tasks if _get_ferias_done(t["key"]))
    return done, total


def _overall_progress() -> float:
    # progresso das listas manuais
    total = 0
    done = 0
    for page in PAGES:
        tasks = _get_tasks(page)
        total += len(tasks)
        done += sum(1 for t in tasks if t.get("done"))
    # incluir férias, se houver data
    if st.session_state.auth_date:
        f_done, f_total = _ferias_progress(st.session_state.auth_date)
        total += f_total
        done += f_done
    return (done / total) if total else 0.0


# ----------------------
# Exportar / importar
# ----------------------

def export_json_button():
    # também exportamos os estados de férias
    extra_state = {
        k: v for k, v in st.session_state.items() if k.startswith("done-ferias-")
    }
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
# UI utilitários
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
    if delta > 0:
        txt = f"Prazo: {d.strftime('%d/%m/%Y')} (D-{delta})"
    elif delta == 0:
        txt = f"Prazo: {d.strftime('%d/%m/%Y')} (HOJE)"
    else:
        txt = f"Prazo: {d.strftime('%d/%m/%Y')} (Atraso: {abs(delta)}d)"
    st.caption(txt)


# ----------------------
# UI de tarefas por página
# ----------------------

def render_ferias_section():
    st.subheader("Férias – prazos automáticos")
    if not st.session_state.auth_date:
        st.info("Selecione a **data de autorização de saída do país** no MENU lateral para ver os prazos de todas as atividades.")
        return 0, 0

    tasks = _get_ferias_tasks(st.session_state.auth_date)
    f_done = 0

    for i, t in enumerate(tasks):
        cols = st.columns([0.08, 0.62, 0.15, 0.15])
        with cols[0]:
            checked = st.checkbox("", value=_get_ferias_done(t["key"]), key=f"ui-{t['key']}")
            if checked != _get_ferias_done(t["key"]):
                _set_ferias_done(t["key"], checked)
        with cols[1]:
            st.markdown(f"**{t['title']}**")
            deadline_chip(t["deadline"])
        with cols[2]:
            status_badge(_get_ferias_done(t["key"]))
        with cols[3]:
            st.write("")
        if _get_ferias_done(t["key"]):
            f_done += 1

    return f_done, len(tasks)


def render_tasks(page: str):
    st.subheader(page)

    # progresso da página (lista manual + férias quando aplicável)
    manual_tasks = _get_tasks(page)
    manual_done = sum(1 for t in manual_tasks if t.get("done"))
    manual_total = len(manual_tasks)

    ferias_done = 0
    ferias_total = 0

    # Se for "Antes da Missão", renderizar a seção de férias primeiro
    if page == "Antes da Missão":
        st.info("As atividades de **Férias** são geradas automaticamente a partir da data selecionada.")
        ferias_done, ferias_total = render_ferias_section()
        st.divider()

    total = manual_total + ferias_total
    done = manual_done + ferias_done
    prog = (done / total) if total else 0.0
    st.progress(prog, text=f"Progresso: {int(prog*100)}%")

    # Lista de tarefas manuais (com status em verde/vermelho)
    if manual_tasks:
        for i, task in enumerate(manual_tasks):
            cols = st.columns([0.08, 0.62, 0.15, 0.15])
            with cols[0]:
                checked = st.checkbox("", value=task.get("done", False), key=f"done-{page}-{i}")
                if checked != task.get("done", False):
                    _toggle_task(page, i, checked)
            with cols[1]:
                st.markdown(f"**{task['title']}**")
                note_val = st.text_area("Notas", value=task.get("notes", ""), key=f"notes-{page}-{i}", height=60)
                if note_val != task.get("notes", ""):
                    _update_notes(page, i, note_val)
            with cols[2]:
                status_badge(task.get("done", False))
            with cols[3]:
                if st.button("🗑️ Excluir", key=f"del-{page}-{i}"):
                    _delete_task(page, i)
                    st.experimental_rerun()
    else:
        st.info("Nenhuma tarefa adicionada ainda para esta etapa (listas manuais).")

    st.divider()
    # Form para nova tarefa (enquanto não definirmos todas as listas oficiais)
    with st.form(key=f"new-task-{page}", clear_on_submit=True):
        new_title = st.text_input("Adicionar tarefa (temporário – você poderá me dizer a lista oficial depois)")
        submitted = st.form_submit_button("Adicionar")
        if submitted:
            if new_title.strip():
                _save_task(page, new_title)
                st.success("Tarefa adicionada.")
                st.experimental_rerun()
            else:
                st.warning("Informe um título para a tarefa.")


# ----------------------
# App principal
# ----------------------

def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🛫", layout="wide")
    _init_state()

    st.title(APP_TITLE)
    st.caption("Acompanhe o status dos afazeres antes da IDA e nas primeiras etapas na CABW.")

    with st.sidebar:
        st.header("Menu")
        st.session_state.page = st.radio("Etapas", options=PAGES, index=PAGES.index(st.session_state.page))
        st.divider()
        st.markdown("**Data de autorização de saída do país**")
        st.session_state.auth_date = st.date_input(
            "Selecione a data",
            value=st.session_state.auth_date,
            format="DD/MM/YYYY",
        )
        st.caption("Essa data alimenta os prazos automáticos (ex.: férias).")
        st.divider()
        st.markdown("**Progresso Geral**")
        overall = _overall_progress()
        st.progress(overall, text=f"{int(overall*100)}% concluído")
        export_json_button()
        import_json_uploader()
        st.caption("Dica: exporte seu progresso antes de trocar de dispositivo.")

    # Render da página selecionada
    render_tasks(st.session_state.page)

    # Rodapé
    st.divider()
    st.caption(
        "Protótipo com geração automática da seção 'Férias' com base na data de saída. "
        "Ao definir as demais páginas, incluiremos prazos relativos semelhantes."
    )


if __name__ == "__main__":
    main()
