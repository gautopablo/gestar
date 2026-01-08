import streamlit as st
import db
import models
import base64

# Configuración de página
st.set_page_config(
    page_title="GESTAR V2 - Taranto",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Inicializar BD
db.init_db()


# --- CACHE DE LECTURA ---
def _normalize_filters(filters):
    if not filters:
        return None
    normalized = []
    for key in sorted(filters.keys()):
        value = filters[key]
        if isinstance(value, list):
            value = tuple(value)
        normalized.append((key, value))
    return tuple(normalized)


@st.cache_data(ttl=30, show_spinner=False)
def cached_get_tickets(filters_key):
    filters = None
    if filters_key:
        filters = {}
        for key, value in filters_key:
            if isinstance(value, tuple):
                value = list(value)
            filters[key] = value
    return db.get_tickets(filters)


# --- LÓGICA DE NAVEGACIÓN POR QUERY PARAMS (Para Links Reales) ---
if "v2_tid" in st.query_params:
    try:
        tid = int(st.query_params["v2_tid"])
        st.session_state["v2_current_ticket_id"] = tid
        st.session_state["v2_page"] = "DETALLE"
        # Limpiar para evitar ciclos
        st.query_params.clear()
        st.rerun()
    except Exception:
        pass


# --- CSS PERSONALIZADO (Look & Feel Taranto 2026) ---
def local_css():
    st.markdown(
        """
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
<style>
        @import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Raleway:wght@600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Lato', sans-serif;
            color: #444;
        }

        h1, h2, h3, .raleway {
            font-family: 'Raleway', sans-serif;
            font-weight: 700;
        }

        .bi {
            vertical-align: -0.125em;
            margin-right: 0.35rem;
        }

        .block-container {
            padding-top: 0.75rem;
        }

        .top-icon {
            font-size: 18px;
            color: #156099;
            padding-top: 6px;
        }

        /* Top Bar Custom */
        .taranto-header {
            background-color: white;
            padding: 0.5rem 1rem;
            border-bottom: 3px solid #d52e25;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        /* Botones de Navegación */
        div.stButton > button {
            border-radius: 4px;
            font-family: 'Raleway', sans-serif;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 700;
            transition: all 0.3s;
            white-space: nowrap;
        }

        /* Botón primario Rojo Taranto */
        div.stButton > button[kind="primary"] {
            background-color: #d52e25;
            border: none;
            color: white;
        }

        /* Tables and Dataframes */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }

        /* Compact rows in custom grid:
           reduce Streamlit's default row gap without overriding all markdown/layout spacing */
        .v2-row-cell {
            line-height: 1.0;
            padding: 0;
            margin: 0;
            display: block;
        }
        .v2-row-cell a {
            line-height: 1.0;
            padding: 0;
            margin: 0;
            display: inline-block;
        }
        /* Apply row spacing/separator directly on the row container */
        div[data-testid="stHorizontalBlock"]:has(.v2-row-cell) {
            gap: 0 !important;
            padding-top: 0px !important;
            padding-bottom: 18px !important;
            border-bottom: 1px solid #e0e0e0;
        }

        /* Cards / Containers */
        .v2-card {
            background-color: white;
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #eee;
            box-shadow: 0 2px 15px rgba(0,0,0,0.04);
            margin-bottom: 1rem;
        }

        /* Sidebar / Filters Column */
        [data-testid="stVerticalBlock"] > div:has(.v2-sidebar-header) {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
        }

        /* Hide default header */
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Ajuste de Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #f1f1f1;
            border-radius: 4px 4px 0 0;
            padding: 10px 20px;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background-color: #156099 !important;
            color: white !important;
        }

        /* User Badge in Top Bar */
        .user-badge {
            background-color: #f8f9fa;
            padding: 5px 15px;
            border-radius: 20px;
            border: 1px solid #ddd;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Active Nav Button */
        .active-nav button {
            background-color: #156099 !important;
            color: white !important;
            border: none;
        }

        /* Botón con apariencia de Link (Selector Robusto) */
        div[data-testid="column"]:has(.link-style) button {
            background-color: transparent !important;
            border: none !important;
            color: #156099 !important;
            text-decoration: underline !important;
            text-align: left !important;
            padding: 0 !important;
            font-weight: 400 !important;
            text-transform: none !important;
            letter-spacing: normal !important;
            height: auto !important;
            min-height: 0 !important;
            box-shadow: none !important;
            display: inline-block !important;
            width: auto !important;
        }
        div[data-testid="column"]:has(.link-style) button:hover {
            color: #d52e25 !important;
            background-color: transparent !important;
            text-decoration: underline !important;
        }
        div[data-testid="column"]:has(.link-style) button:active {
            color: #d52e25 !important;
            background-color: transparent !important;
        }
        div[data-testid="column"]:has(.link-style) button:focus {
            box-shadow: none !important;
            background-color: transparent !important;
            outline: none !important;
        }

        </style>
    """,
        unsafe_allow_html=True,
    )


local_css()


# --- HELPER: Cargar Logo ---
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return ""


logo_base64 = get_base64_image("marca - Isologo Taranto.png")

# --- DATA FETCHING ---
df_users = db.get_users(only_active=True)
user_names = df_users["nombre_completo"].tolist()
if not user_names:
    user_names = ["Invitado"]

# --- FUNCIONES DE INTERFAZ REFACTORIZADAS ---


def show_create_ticket(u_names, c_user):
    st.markdown(
        "### <i class='bi bi-pencil-square'></i>Nueva Solicitud",
        unsafe_allow_html=True,
    )
    with st.form("v2_new_ticket", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título del Ticket*")
            area = st.selectbox("Área Destino", models.AREAS)
            urgencia = st.selectbox("Urgencia Sugerida", models.PRIORIDADES)
            solicitante = st.selectbox(
                "Solicitante*",
                u_names,
                index=u_names.index(c_user) if c_user in u_names else 0,
            )

        with col2:
            categoria = st.selectbox("Categoría", models.CATEGORIAS)
            sub_options = models.SUBCATEGORIAS.get(categoria, [])
            subcategoria = st.selectbox("Subcategoría", sub_options)
            division = st.selectbox("División", models.DIVISIONES)
            planta = st.selectbox("Planta", models.PLANTAS)
            resp_sugerido = st.selectbox(
                "Responsable Sugerido", ["Sin Sugerir"] + u_names
            )

        descripcion = st.text_area("Descripción detallada*")

        if st.form_submit_button("CREAR TICKET GESTAR", type="primary"):
            if not titulo or not descripcion:
                st.error("Campos obligatorios faltantes.")
            else:
                data = {
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "area_destino": area,
                    "categoria": categoria,
                    "subcategoria": subcategoria,
                    "division": division,
                    "planta": planta,
                    "urgencia_sugerida": urgencia,
                    "prioridad": "Media",
                    "responsable_sugerido": resp_sugerido,
                    "solicitante": solicitante,
                    "created_by": c_user,
                }
                tid = db.create_ticket(data)
                cached_get_tickets.clear()
                st.success(f"Ticket #{tid} creado con éxito!")


def show_simple_request(c_user):
    st.markdown(
        "### <i class='bi bi-lightning-charge'></i>Solicitud Sencilla",
        unsafe_allow_html=True,
    )
    with st.form("v2_simple_request", clear_on_submit=True):
        titulo = st.text_input("Título del Ticket*")
        area = st.selectbox("Área Destino", models.AREAS)
        descripcion = st.text_area("Descripción detallada*")

        if st.form_submit_button("CREAR SOLICITUD", type="primary"):
            if not titulo or not descripcion:
                st.error("Campos obligatorios faltantes.")
            else:
                data = {
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "area_destino": area,
                    "categoria": "",
                    "subcategoria": None,
                    "division": "",
                    "planta": "",
                    "urgencia_sugerida": None,
                    "prioridad": "Media",
                    "responsable_sugerido": None,
                    "solicitante": c_user,
                    "created_by": c_user,
                }
                tid = db.create_ticket(data)
                cached_get_tickets.clear()
                st.success(f"Ticket #{tid} creado con éxito!")


def render_v2_table(df, key_suffix=""):
    if df.empty:
        st.info("No hay registros en esta vista.")
        return

    # --- LÓGICA DE PAGINACIÓN ---
    items_per_page = 10
    if f"v2_page_num_{key_suffix}" not in st.session_state:
        st.session_state[f"v2_page_num_{key_suffix}"] = 0

    total_items = len(df)
    total_pages = (total_items - 1) // items_per_page + 1

    # Asegurar que la página actual es válida
    current_page = st.session_state[f"v2_page_num_{key_suffix}"]
    if current_page >= total_pages:
        current_page = 0
        st.session_state[f"v2_page_num_{key_suffix}"] = 0

    start_idx = current_page * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)

    df_page = df.iloc[start_idx:end_idx]

    # --- ENCABEZADOS DE LA GRILLA ---
    st.markdown("<br>", unsafe_allow_html=True)
    h_cols = st.columns([0.8, 3.5, 1.5, 1.2, 2, 1.5])
    h_cols[0].markdown("**ID**")
    h_cols[1].markdown("**Título**")
    h_cols[2].markdown("**Estado**")
    h_cols[3].markdown("**Prioridad**")
    h_cols[4].markdown("**Área Destino**")
    h_cols[5].markdown("**Actualizado**")
    st.markdown(
        "<hr style='margin: 0.5rem 0; border: 0.5px solid #eee;'>",
        unsafe_allow_html=True,
    )

    # --- FILAS DE LA GRILLA ---
    for _, row in df_page.iterrows():
        r_cols = st.columns([0.8, 3.5, 1.5, 1.2, 2, 1.5])

        # ID como texto
        r_cols[0].markdown(
            f"<div class='v2-row-cell'>#{row['id']}</div>",
            unsafe_allow_html=True,
        )

        # TÍTULO COMO LINK REAL
        with r_cols[1]:
            link_html = f'<a href="/?v2_tid={row["id"]}" target="_self" style="color:#156099; text-decoration:underline; font-weight:400; font-family:sans-serif;">{row["titulo"]}</a>'
            st.markdown(
                f"<div class='v2-row-cell'>{link_html}</div>",
                unsafe_allow_html=True,
            )

        r_cols[2].markdown(
            f"<div class='v2-row-cell'>{row['estado']}</div>",
            unsafe_allow_html=True,
        )
        r_cols[3].markdown(
            f"<div class='v2-row-cell'>{row['prioridad']}</div>",
            unsafe_allow_html=True,
        )
        r_cols[4].markdown(
            f"<div class='v2-row-cell'>{row['area_destino']}</div>",
            unsafe_allow_html=True,
        )

        # Fecha corta
        updated_val = row["updated_at"]
        if isinstance(updated_val, str) and len(updated_val) > 10:
            updated_val = updated_val[:10]
        r_cols[5].markdown(
            f"<div class='v2-row-cell'>{updated_val}</div>",
            unsafe_allow_html=True,
        )

        # Separador de fila eliminado para compactar la grilla.

    # --- CONTROLES DE PAGINACIÓN ---
    if total_pages > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        p_c1, p_c2, p_c3 = st.columns([1, 2, 1])

        with p_c1:
            if st.button(
                "⬅️ Anterior",
                key=f"v2_prev_{key_suffix}",
                disabled=(current_page == 0),
                use_container_width=True,
            ):
                st.session_state[f"v2_page_num_{key_suffix}"] -= 1
                st.rerun()

        with p_c2:
            st.markdown(
                f"<p style='text-align:center;'>Página <b>{current_page + 1}</b> de {total_pages}<br><small>{total_items} tickets en total</small></p>",
                unsafe_allow_html=True,
            )

        with p_c3:
            if st.button(
                "Siguiente ➡️",
                key=f"v2_next_{key_suffix}",
                disabled=(current_page >= total_pages - 1),
                use_container_width=True,
            ):
                st.session_state[f"v2_page_num_{key_suffix}"] += 1
                st.rerun()

    # Mantenemos el selector manual por ID al final como expander
    with st.expander("Acceso rápido por ID"):
        c1, c2 = st.columns([3, 1])
        with c1:
            tid = st.number_input(
                "Ingresar ID manualmente",
                min_value=1,
                step=1,
                key=f"v2_tid_manual_{key_suffix}",
            )
        with c2:
            if st.button(
                "IR AL DETALLE",
                key=f"v2_btn_manual_{key_suffix}",
                use_container_width=True,
            ):
                st.session_state["v2_current_ticket_id"] = tid
                st.session_state["v2_page"] = "DETALLE"
                st.rerun()


def show_ticket_tray(c_area, c_role, c_user):
    st.markdown(
        "### <i class='bi bi-inbox'></i>Bandeja de Gestión",
        unsafe_allow_html=True,
    )
    # Reordenado: BUSCADOR primero para que sea la seleccionada por defecto
    t_all, t_cola, t_asig, t_proc, t_cerr = st.tabs(
        ["BUSCADOR", "COLA", "MIS TICKETS", "EN PROCESO", "CERRADOS"]
    )

    with t_all:
        render_v2_table(cached_get_tickets(None), "all")

    with t_cola:
        f = {
            "estado": "NUEVO",
            "area_destino": c_area if c_role != "Director" else None,
        }
        render_v2_table(cached_get_tickets(_normalize_filters(f)), "cola")

    with t_asig:
        f = {"responsable_asignado": c_user, "estado": ["ASIGNADO", "EN PROCESO"]}
        render_v2_table(cached_get_tickets(_normalize_filters(f)), "asig")

    with t_proc:
        f_area = st.selectbox("Área", ["Todas"] + models.AREAS, key="v2_proc_area")
        f = {"estado": ["ASIGNADO", "EN PROCESO"]}
        if f_area != "Todas":
            f["area_destino"] = f_area
        render_v2_table(cached_get_tickets(_normalize_filters(f)), "proc")

    with t_cerr:
        f = {"estado": ["RESUELTO", "CERRADO"]}
        render_v2_table(cached_get_tickets(_normalize_filters(f)), "cerr")


def show_ticket_detail(c_user, c_role, c_area, u_names):
    tid = st.session_state.get("v2_current_ticket_id")
    if not tid:
        st.warning("Seleccione un ticket en la bandeja.")
        if st.button("Volver a Bandeja"):
            st.session_state["v2_page"] = "BANDEJA"
            st.rerun()
        return

    ticket = db.get_ticket_by_id(tid)
    if ticket is None:
        st.error("Ticket no encontrado.")
        return

    st.markdown(f"### Ticket #{ticket['id']} - {ticket['titulo']}")

    # Header Info Card
    with st.container():
        st.markdown(
            f"""
        <div class='v2-card'>
            <div style='display:flex; justify-content:space-between;'>
                <div><b>Estado:</b> {ticket["estado"]} | <b>Prioridad:</b> {ticket["prioridad"]}</div>
                <div style='color:#156099;'><b>Solicitante:</b> {ticket["solicitante"]}</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # Actions
    if ticket["estado"] == "NUEVO":
        can_take = (c_role == "Director") or (
            c_role in ["Analista", "Jefe"] and ticket["area_destino"] == c_area
        )
        if can_take:
            if st.button("🙋 TOMAR TICKET", type="primary"):
                db.update_ticket(
                    tid,
                    {"responsable_asignado": c_user, "estado": "ASIGNADO"},
                    author=c_user,
                )
                cached_get_tickets.clear()
                st.rerun()

    # Management Form
    with st.expander("GESTIÓN Y ASIGNACIÓN", expanded=True):
        with st.form("v2_edit_ticket"):
            col1, col2, col3 = st.columns(3)
            with col1:
                prio = st.selectbox(
                    "Prioridad",
                    models.PRIORIDADES,
                    index=models.PRIORIDADES.index(ticket["prioridad"])
                    if ticket["prioridad"] in models.PRIORIDADES
                    else 1,
                )
            with col2:
                stat = st.selectbox(
                    "Estado",
                    models.ESTADOS_TICKET,
                    index=models.ESTADOS_TICKET.index(ticket["estado"]),
                )
            with col3:
                can_assign = (c_role == "Director") or (
                    c_role == "Jefe" and ticket["area_destino"] == c_area
                )
                if can_assign:
                    rl = ["Sin Asignar"] + u_names
                    curr = (
                        rl.index(ticket["responsable_asignado"])
                        if ticket["responsable_asignado"] in rl
                        else 0
                    )
                    asig = st.selectbox("Responsable", rl, index=curr)
                else:
                    st.text_input(
                        "Responsable",
                        value=ticket["responsable_asignado"] or "Sin Asignar",
                        disabled=True,
                    )
                    asig = ticket["responsable_asignado"]

            if st.form_submit_button("ACTUALIZAR TICKET"):
                db.update_ticket(
                    tid,
                    {"prioridad": prio, "estado": stat, "responsable_asignado": asig},
                    author=c_user,
                )
                cached_get_tickets.clear()
                st.rerun()

    # Information Tabs
    t_desc, t_tasks, t_hist = st.tabs(["DESCRIPCIÓN", "TAREAS", "HISTORIAL"])

    with t_desc:
        st.markdown(
            "#### <i class='bi bi-file-earmark-text'></i>Descripción",
            unsafe_allow_html=True,
        )
        st.info(ticket["descripcion"])
        st.markdown(
            f"**Urgencia:** {ticket['urgencia_sugerida']} | **División:** {ticket['division']} | **Planta:** {ticket['planta']}"
        )

    with t_tasks:
        st.markdown(
            "#### <i class='bi bi-check2-square'></i>Tareas",
            unsafe_allow_html=True,
        )
        tasks = db.get_tasks_for_ticket(tid)
        h_t1, h_t2 = st.columns([5, 1])
        h_t1.markdown("**Tarea**")
        h_t2.markdown("**Completada**")
        for _, t in tasks.iterrows():
            c_t1, c_t2 = st.columns([5, 1])
            c_t1.write(f"**{t['descripcion']}** (Resp: {t['responsable'] or 'N/A'})")
            checked = t["estado"] == "COMPLETADA"
            new_checked = c_t2.checkbox(
                "Completada",
                value=checked,
                key=f"v2_tk_{t['id']}",
                label_visibility="collapsed",
            )
            if new_checked != checked:
                new_status = "COMPLETADA" if new_checked else "PENDIENTE"
                db.update_task_status(t["id"], new_status)
                st.rerun()

        with st.form("v2_add_task"):
            c_a1, c_a2 = st.columns([3, 1])
            d = c_a1.text_input("Nueva Tarea")
            r = c_a2.selectbox("Resp.", u_names)
            if st.form_submit_button("AGREGAR TAREA"):
                if d:
                    db.create_task(tid, d, r)
                    st.rerun()

    with t_hist:
        st.markdown(
            "#### <i class='bi bi-chat-left-text'></i>Historial",
            unsafe_allow_html=True,
        )
        logs = db.get_ticket_logs(tid)
        for _, entry in logs.iterrows():
            with st.chat_message(
                "user" if entry["event_type"] == "comment" else "assistant"
            ):
                st.write(f"**{entry['author']}** - {entry['created_at']}")
                st.write(entry["message"])

        with st.form("v2_comment"):
            msg = st.text_area("Comentario")
            if st.form_submit_button("ENVIAR"):
                if msg:
                    db.add_ticket_log(tid, c_user, "comment", msg)
                    st.rerun()


def show_admin():
    tab_u, tab_a = st.tabs(["USUARIOS", "MAESTRAS"])
    with tab_u:
        with st.expander("NUEVO USUARIO"):
            with st.form("v2_add_user"):
                n = st.text_input("Nombre*")
                e = st.text_input("Email")
                r = st.selectbox("Rol", models.ROLES)
                a = st.selectbox("Área", models.AREAS)
                if st.form_submit_button("GUARDAR"):
                    if n:
                        db.create_user(
                            {"nombre_completo": n, "email": e, "rol": r, "area": a}
                        )
                        st.rerun()

        df_all = db.get_users().reset_index(drop=True)
        df_edit = st.data_editor(
            df_all,
            column_config={
                "id": None,
                "nombre_completo": st.column_config.TextColumn("Nombre", disabled=True),
                "rol": st.column_config.SelectboxColumn("Rol", options=models.ROLES),
                "area": st.column_config.SelectboxColumn("Área", options=models.AREAS),
            },
            hide_index=True,
            use_container_width=True,
            key="v2_user_ed",
        )

        if st.button("CONFIRMAR CAMBIOS USUARIOS", type="primary"):
            if "id" not in df_edit.columns:
                st.error("No se pudo leer el ID de usuarios.")
            else:
                editable_cols = [
                    c for c in ["rol", "area", "email", "activo"] if c in df_all.columns
                ]
                df_all_by_id = df_all.set_index("id")
                df_edit_by_id = df_edit.set_index("id")

                def values_equal(a, b):
                    if a != a and b != b:
                        return True
                    return a == b

                updates_applied = 0
                for uid in df_edit_by_id.index.intersection(df_all_by_id.index):
                    updates = {}
                    for col in editable_cols:
                        if col not in df_edit_by_id.columns:
                            continue
                        old_val = df_all_by_id.at[uid, col]
                        new_val = df_edit_by_id.at[uid, col]
                        if not values_equal(old_val, new_val):
                            if col == "activo":
                                new_val = 1 if bool(new_val) else 0
                            updates[col] = new_val
                    if updates:
                        db.update_user(uid, updates)
                        updates_applied += 1
                if updates_applied:
                    st.success(f"Guardado ({updates_applied})")
                else:
                    st.info("No se detectaron cambios.")
                st.rerun()
    with tab_a:
        st.info("Gestión de tablas maestras en desarrollo.")


# --- SESSION & USER INFO ---

# Initialize session if empty
if "v2_user_name" not in st.session_state:
    st.session_state["v2_user_name"] = user_names[0] if user_names else "Invitado"

# Fetch actual current user info from DB
u_info = db.get_user_by_name(st.session_state["v2_user_name"])
if u_info:
    cur_u, cur_r, cur_a = u_info["nombre_completo"], u_info["rol"], u_info["area"]
else:
    cur_u, cur_r, cur_a = st.session_state["v2_user_name"], "Solicitante", "IT"


# --- TOP HEADER ---

c_head1, c_head2, c_head3 = st.columns([1, 2.5, 1.5], vertical_alignment="center")

with c_head1:
    if logo_base64:
        st.markdown(
            f'<img src="data:image/png;base64,{logo_base64}" width="220">',
            unsafe_allow_html=True,
        )
    else:
        st.markdown("<h1 style='margin:0;'>TARANTO</h1>", unsafe_allow_html=True)

with c_head2:
    st.markdown(
        "<h2 style='margin:0; color:#d52e25; text-align:center; font-size:44px; line-height:1.1;'>GESTAR <span style='font-weight:300; font-size:26px; color:#444;'>| Gestión de Solicitudes</span></h2>",
        unsafe_allow_html=True,
    )

with c_head3:
    # Top Right Icons and Session Popover
    cols_top = st.columns([2, 2, 4])
    with cols_top[0]:
        c_home_i, c_home_b = st.columns([1, 5], gap="small")
        with c_home_i:
            st.markdown(
                "<span class='top-icon'><i class='bi bi-house'></i></span>",
                unsafe_allow_html=True,
            )
        with c_home_b:
            if st.button("Inicio", key="v2_btn_home_top", help="Inicio"):
                st.session_state["v2_page"] = "CREAR TICKET"
                st.rerun()
    with cols_top[1]:
        c_ref_i, c_ref_b = st.columns([1, 5], gap="small")
        with c_ref_i:
            st.markdown(
                "<span class='top-icon'><i class='bi bi-arrow-clockwise'></i></span>",
                unsafe_allow_html=True,
            )
        with c_ref_b:
            if st.button("Refrescar", key="v2_btn_refresh_top", help="Refrescar"):
                st.rerun()
    with cols_top[2]:
        display_name = st.session_state["v2_user_name"].split(",")[0]
        with st.popover(f"{display_name}", use_container_width=True):
            st.markdown(
                "### <i class='bi bi-person-circle'></i>Sesión Actual",
                unsafe_allow_html=True,
            )
            st.write(f"**Usuario:** {st.session_state['v2_user_name']}")
            st.write(f"**Rol:** {cur_r}")
            st.write(f"**Área:** {cur_a}")
            st.divider()
            st.markdown("Seleccione un usuario para simular sesión:")
            new_user = st.selectbox(
                "Cambiar Usuario",
                user_names,
                index=user_names.index(st.session_state["v2_user_name"])
                if st.session_state["v2_user_name"] in user_names
                else 0,
            )
            if new_user != st.session_state["v2_user_name"]:
                st.session_state["v2_user_name"] = new_user
                st.rerun()

st.markdown(
    "<hr style='border: 1px solid #d52e25; margin-top:0px; margin-bottom:1rem;'>",
    unsafe_allow_html=True,
)


# --- NAVIGATION ROW ---
if "v2_page" not in st.session_state:
    st.session_state["v2_page"] = "CREAR TICKET"

c_nav1, c_nav2, c_nav3, c_nav4, c_nav5, _ = st.columns([1, 1, 1, 1, 1, 2], gap="small")

with c_nav1:
    btn_class = "active-nav" if st.session_state["v2_page"] == "CREAR TICKET" else ""
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("CREAR TICKET", use_container_width=True, key="nav_btn_create"):
        st.session_state["v2_page"] = "CREAR TICKET"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with c_nav2:
    btn_class = "active-nav" if st.session_state["v2_page"] == "BANDEJA" else ""
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("BANDEJA", use_container_width=True, key="nav_btn_tray"):
        st.session_state["v2_page"] = "BANDEJA"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with c_nav3:
    btn_class = "active-nav" if st.session_state["v2_page"] == "MIS TAREAS" else ""
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("MIS TAREAS", use_container_width=True, key="nav_btn_tasks"):
        st.session_state["v2_page"] = "MIS TAREAS"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with c_nav4:
    btn_class = (
        "active-nav" if st.session_state["v2_page"] == "SOLICITUD SENCILLA" else ""
    )
    st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
    if st.button("SOLICITUD SENCILLA", use_container_width=True, key="nav_btn_simple"):
        st.session_state["v2_page"] = "SOLICITUD SENCILLA"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with c_nav5:
    if cur_r == "Administrador":
        btn_class = "active-nav" if st.session_state["v2_page"] == "ADMIN" else ""
        st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
        if st.button("ADMIN", use_container_width=True, key="nav_btn_admin"):
            st.session_state["v2_page"] = "ADMIN"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Container
page = st.session_state["v2_page"]

if page == "CREAR TICKET":
    show_create_ticket(user_names, cur_u)
elif page == "BANDEJA":
    show_ticket_tray(cur_a, cur_r, cur_u)
elif page == "MIS TAREAS":
    st.markdown(
        "### <i class='bi bi-check2-square'></i>Mis Tareas Pendientes",
        unsafe_allow_html=True,
    )
    tasks = db.get_tasks_by_user(cur_u)
    if tasks.empty:
        st.info("Sin tareas.")
    else:
        df_tasks = tasks[
            ["id", "ticket_id", "ticket_titulo", "descripcion", "estado"]
        ]
        st.dataframe(
            df_tasks,
            hide_index=True,
            use_container_width=True,
            selection_mode="single-row",
            on_select="rerun",
            key="v2_tasks_grid",
        )
        # Navigate to ticket detail when a row is selected.
        selection = st.session_state.get("v2_tasks_grid", {}).get("selection", {})
        selected_rows = selection.get("rows", [])
        if selected_rows:
            row_idx = selected_rows[0]
            tid = int(df_tasks.iloc[row_idx]["ticket_id"])
            st.session_state["v2_current_ticket_id"] = tid
            st.session_state["v2_page"] = "DETALLE"
            st.rerun()
elif page == "SOLICITUD SENCILLA":
    show_simple_request(cur_u)
elif page == "ADMIN":
    if cur_r == "Administrador":
        show_admin()
    else:
        st.error("Acceso denegado.")
elif page == "DETALLE":
    show_ticket_detail(cur_u, cur_r, cur_a, user_names)
    if st.button("VOLVER A BANDEJA", use_container_width=True, key="v2_detail_back"):
        st.session_state["v2_page"] = "BANDEJA"
        st.rerun()

# --- FOOTER ---
st.markdown("---")
st.caption("Taranto - GESTAR v2.0 - © 2026")
