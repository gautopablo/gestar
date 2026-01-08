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
                st.success(f"Ticket #{tid} creado con éxito!")


def render_v2_table(df, key_suffix=""):
    if df.empty:
        st.info("No hay registros en esta vista.")
        return

    # Columnas que vamos a mostrar
    columns_to_show = [
        "id",
        "titulo",
        "estado",
        "prioridad",
        "area_destino",
        "solicitante",
        "updated_at",
    ]
    df_display = df[columns_to_show]

    # Opción 1: Selección Nativa (on_select="rerun")
    selection = st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key=f"v2_grid_{key_suffix}",
    )

    # Procesar selección de fila si existe
    if selection and selection.selection.rows:
        selected_index = selection.selection.rows[0]
        # Obtenemos el ID del ticket de la fila seleccionada
        # Nota: Usamos df_display para asegurar que el índice coincide con el visualizado
        ticket_id = df_display.iloc[selected_index]["id"]

        st.session_state["v2_current_ticket_id"] = int(ticket_id)
        st.session_state["v2_page"] = "DETALLE"
        st.rerun()

    c1, c2 = st.columns([3, 1])
    with c1:
        tid = st.number_input(
            "ID para detalle", min_value=1, step=1, key=f"v2_tid_{key_suffix}"
        )
    with c2:
        if st.button(
            "VER DETALLE", key=f"v2_btn_{key_suffix}", use_container_width=True
        ):
            st.session_state["v2_current_ticket_id"] = tid
            st.session_state["v2_page"] = "DETALLE"
            st.rerun()


def show_ticket_tray(c_area, c_role, c_user):
    st.markdown(
        "### <i class='bi bi-inbox'></i>Bandeja de Gestión",
        unsafe_allow_html=True,
    )
    t_cola, t_asig, t_proc, t_cerr, t_all = st.tabs(
        ["COLA", "MIS TICKETS", "EN PROCESO", "CERRADOS", "BUSCADOR"]
    )

    with t_cola:
        f = {
            "estado": "NUEVO",
            "area_destino": c_area if c_role != "Director" else None,
        }
        render_v2_table(db.get_tickets(f), "cola")

    with t_asig:
        f = {"responsable_asignado": c_user, "estado": ["ASIGNADO", "EN PROCESO"]}
        render_v2_table(db.get_tickets(f), "asig")

    with t_proc:
        f_area = st.selectbox("Área", ["Todas"] + models.AREAS, key="v2_proc_area")
        f = {"estado": ["ASIGNADO", "EN PROCESO"]}
        if f_area != "Todas":
            f["area_destino"] = f_area
        render_v2_table(db.get_tickets(f), "proc")

    with t_cerr:
        f = {"estado": ["RESUELTO", "CERRADO"]}
        render_v2_table(db.get_tickets(f), "cerr")

    with t_all:
        render_v2_table(db.get_tickets(), "all")


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
        for _, t in tasks.iterrows():
            c_t1, c_t2 = st.columns([5, 1])
            c_t1.write(f"**{t['descripcion']}** (Resp: {t['responsable'] or 'N/A'})")
            if t["estado"] != "COMPLETADA":
                if c_t2.button("✅", key=f"v2_tk_{t['id']}"):
                    db.update_task_status(t["id"], "COMPLETADA")
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

        df_all = db.get_users()
        st.data_editor(
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
            state = st.session_state.get("v2_user_ed", {}).get("edited_rows", {})
            for row_idx, updates in state.items():
                uid = df_all.iloc[int(row_idx)]["id"]
                if "activo" in updates:
                    updates["activo"] = 1 if updates["activo"] else 0
                db.update_user(uid, updates)
            st.success("Guardado")
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
        st.dataframe(
            tasks[["id", "ticket_id", "ticket_titulo", "descripcion", "estado"]],
            hide_index=True,
            use_container_width=True,
        )
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
