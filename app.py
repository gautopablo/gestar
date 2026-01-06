# app.py
# UI principal de GESTAR (Gestión de Solicitudes y Tareas)
# Streamlit app: pantallas de tickets y tareas

import streamlit as st
import db
import models

# Configuración de la página
st.set_page_config(
    page_title="GESTAR - Gestión de Solicitudes", page_icon="🎫", layout="wide"
)

# Inicializar BD
db.init_db()

# --- Sidebar: Simulación de Contexto ---
st.sidebar.title("GESTAR")
st.sidebar.markdown("### 👤 Simulación de Sesión")
current_user = st.sidebar.selectbox("Usuario Actual", models.USERS_PROV)
current_role = st.sidebar.selectbox("Rol", models.ROLES, index=1)  # Default Analista
current_area = st.sidebar.selectbox("Mi Área", models.AREAS, index=1)  # Default IT

st.sidebar.divider()

# --- Funciones de Interfaz ---


def show_create_ticket():
    st.header("📝 Crear Nuevo Ticket")

    with st.form("new_ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            titulo = st.text_input("Título del Ticket*")
            area = st.selectbox("Área Destino", models.AREAS)
            urgencia = st.selectbox("Urgencia Sugerida", models.PRIORIDADES)
            solicitante = st.selectbox(
                "Solicitante*",
                models.USERS_PROV,
                index=models.USERS_PROV.index(current_user)
                if current_user in models.USERS_PROV
                else 0,
            )

        with col2:
            categoria = st.selectbox("Categoría", models.CATEGORIAS)
            sub_options = models.SUBCATEGORIAS.get(categoria, [])
            subcategoria = st.selectbox("Subcategoría", sub_options)
            division = st.selectbox("División", models.DIVISIONES)
            planta = st.selectbox("Planta", models.PLANTAS)
            resp_sugerido = st.selectbox(
                "Responsable Sugerido", ["Sin Sugerir"] + models.USERS_PROV
            )

        descripcion = st.text_area("Descripción detallada*")

        # Hidden Priority (set by system/analyst later)

        submitted = st.form_submit_button("Crear Ticket")

        if submitted:
            if not titulo or not descripcion or not solicitante:
                st.error("Por favor complete los campos obligatorios (*)")
            else:
                data = {
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "area_destino": area,
                    "categoria": categoria,
                    "subcategoria": subcategoria,
                    "division": division,
                    "planta": planta,
                    "urgencia_sugerida": urgencia,  # User input
                    "prioridad": "Media",  # Default for new tickets
                    "responsable_sugerido": resp_sugerido,
                    "solicitante": solicitante,
                    "created_by": current_user,  # Audit
                }
                ticket_id = db.create_ticket(data)
                st.success(f"Ticket creado exitosamente! ID: {ticket_id}")


def show_ticket_tray():
    st.header("📥 Bandeja de Tickets")

    # Tabs para filtro rápido
    tab_cola, tab_asignados, tab_proceso, tab_cerrados, tab_todos = st.tabs(
        [
            "🔴 Cola (Nuevos)",
            "👤 Mis Asignados",
            "🟡 En Proceso",
            "🟢 Cerrados",
            "📋 Todos",
        ]
    )

    # 1. Cola: Tickets NUEVOS de MI Área
    with tab_cola:
        st.caption(f"Tickets Nuevos para el área: {current_area}")
        filters = {
            "estado": "NUEVO",
            "area_destino": current_area if current_role != "Director" else None,
        }
        df_cola = db.get_tickets(filters)
        render_ticket_table(df_cola, key_suffix="cola")

    # 2. Mis Asignados
    with tab_asignados:
        filters = {
            "responsable_asignado": current_user,
            "estado": ["ASIGNADO", "EN PROCESO"],
        }
        df_my = db.get_tickets(filters)
        render_ticket_table(df_my, key_suffix="my")

    # 3. En Proceso (Global o de Area)
    with tab_proceso:
        f_area = st.selectbox("Filtrar Área", ["Todas"] + models.AREAS, key="fp_area")
        filters = {"estado": ["ASIGNADO", "EN PROCESO"]}
        if f_area != "Todas":
            filters["area_destino"] = f_area
        df_proc = db.get_tickets(filters)
        render_ticket_table(df_proc, key_suffix="proc")

    # 4. Cerrados
    with tab_cerrados:
        filters = {"estado": ["RESUELTO", "CERRADO"]}
        df_closed = db.get_tickets(filters)
        render_ticket_table(df_closed, key_suffix="closed")

    # 5. Todos (Busqueda)
    with tab_todos:
        render_ticket_table(db.get_tickets(), show_filters=True, key_suffix="all")


def render_ticket_table(df, show_filters=False, key_suffix=""):
    if df.empty:
        st.info("No hay tickets en esta vista.")
        return

    st.dataframe(
        df[
            [
                "id",
                "titulo",
                "estado",
                "prioridad",
                "area_destino",
                "solicitante",
                "updated_at",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    # Selector para ver detalles
    c1, c2 = st.columns([3, 1])
    with c1:
        ticket_id = st.number_input(
            f"ID Ticket a Consultar {key_suffix}",
            min_value=1,
            step=1,
            key=f"tid_{key_suffix}",
        )
    with c2:
        if st.button(f"Ver Detalle {key_suffix}", key=f"btn_{key_suffix}"):
            st.session_state["current_ticket_id"] = ticket_id
            st.session_state["page"] = "Detalle de Ticket"
            st.rerun()


def show_ticket_detail():
    st.header("🔍 Detalle de Ticket")

    ticket_id = st.session_state.get("current_ticket_id")

    if not ticket_id:
        st.warning("Seleccione un ticket desde la Bandeja.")
        return

    ticket = db.get_ticket_by_id(ticket_id)
    if ticket is None:
        st.error(f"Ticket {ticket_id} no encontrado.")
        return

    # Header con estado y acciones principales
    c_head1, c_head2 = st.columns([3, 1])
    with c_head1:
        st.markdown(f"### #{ticket['id']} - {ticket['titulo']}")
    with c_head2:
        st.metric("Estado", ticket["estado"])

    st.divider()

    # --- LOGICA DE ACCIONES (Autoasignación) ---
    # Si es NUEVO y soy del área (o Director) -> Botón "Tomar Ticket"
    can_take = False
    if ticket["estado"] == "NUEVO":
        if current_role == "Director":
            can_take = True
        elif (
            current_role in ["Analista", "Jefe"]
            and ticket["area_destino"] == current_area
        ):
            can_take = True

    if can_take:
        if st.button("🙋 Tomar Ticket (Autoasignar)"):
            db.update_ticket(
                ticket_id,
                {"responsable_asignado": current_user, "estado": "ASIGNADO"},
                author=current_user,
            )
            st.success("Ticket asignado a ti correctamente.")
            st.rerun()

    # --- EDICION DE CAMPOS ---
    with st.expander("📝 Editar / Gestionar", expanded=True):
        with st.form("edit_ticket"):
            c1, c2, c3 = st.columns(3)
            with c1:
                # Prioridad editable solo por Analista/Jefe/Director
                if current_role in ["Solicitante"]:
                    st.write(f"**Prioridad:** {ticket['prioridad']}")
                    new_prioridad = ticket["prioridad"]
                else:
                    new_prioridad = st.selectbox(
                        "Prioridad",
                        models.PRIORIDADES,
                        index=models.PRIORIDADES.index(ticket["prioridad"])
                        if ticket["prioridad"] in models.PRIORIDADES
                        else 1,
                    )

            with c2:
                new_status = st.selectbox(
                    "Estado",
                    models.ESTADOS_TICKET,
                    index=models.ESTADOS_TICKET.index(ticket["estado"]),
                )

            with c3:
                # Responsable editable solo por Jefe/Director
                can_assign = (current_role == "Director") or (
                    current_role == "Jefe" and ticket["area_destino"] == current_area
                )

                if can_assign:
                    current_resp = ticket["responsable_asignado"]
                    resps_list = ["Sin Asignar"] + models.USERS_PROV
                    try:
                        resp_idx = (
                            resps_list.index(current_resp)
                            if current_resp in resps_list
                            else 0
                        )
                    except:
                        resp_idx = 0

                    new_asignado = st.selectbox(
                        "Responsable Asignado", resps_list, index=resp_idx
                    )
                else:
                    st.write(
                        f"**Responsable:** {ticket['responsable_asignado'] if ticket['responsable_asignado'] else 'Sin Asignar'}"
                    )
                    new_asignado = ticket["responsable_asignado"]

            update_btn = st.form_submit_button("Guardar Cambios")
            if update_btn:
                db.update_ticket(
                    ticket_id,
                    {
                        "prioridad": new_prioridad,
                        "estado": new_status,
                        "responsable_asignado": new_asignado,
                    },
                    author=current_user,
                )
                st.success("Ticket actualizado")
                st.rerun()

    # Detalles de solo lectura
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**Área:** {ticket['area_destino']}")
        st.write(f"**Urgencia Sugerida:** {ticket['urgencia_sugerida']}")
        st.write(f"**Responsable Sugerido:** {ticket['responsable_sugerido']}")
    with c2:
        st.write(f"**Solicitante:** {ticket['solicitante']}")
        st.write(f"**Creado Por:** {ticket['created_by']}")
        st.write(f"**División/Planta:** {ticket['division']} / {ticket['planta']}")
    with c3:
        st.write(f"**Creado:** {ticket['created_at']}")
        st.write(f"**Actualizado:** {ticket['updated_at']}")
        if ticket["closed_at"]:
            st.write(f"**Cerrado:** {ticket['closed_at']}")

    st.write("**Descripción:**")
    st.info(ticket["descripcion"])

    # --- TAREAS ---
    st.divider()
    st.subheader("📋 Tareas")

    tasks = db.get_tasks_for_ticket(ticket_id)
    if not tasks.empty:
        for idx, task in tasks.iterrows():
            col_t1, col_t2, col_t3 = st.columns([4, 2, 2])
            with col_t1:
                st.write(f"- {task['descripcion']}")
                if task["responsable"]:
                    st.caption(f"Resp: {task['responsable']}")
            with col_t2:
                st.caption(f"Est: {task['estado']}")
            with col_t3:
                # Quick action
                if task["estado"] != "COMPLETADA":
                    if st.button("✅", key=f"done_{task['id']}"):
                        db.update_task_status(task["id"], "COMPLETADA")
                        st.rerun()

    with st.form("add_task"):
        c_add1, c_add2 = st.columns([3, 1])
        with c_add1:
            desc = st.text_input("Nueva Tarea")
        with c_add2:
            resp = st.selectbox(
                "Resp.",
                models.USERS_PROV,
                index=models.USERS_PROV.index(current_user)
                if current_user in models.USERS_PROV
                else 0,
            )
        if st.form_submit_button("Agregar"):
            if desc:
                db.create_task(ticket_id, desc, resp)
                st.rerun()

    # --- HISTORIAL / COMENTARIOS ---
    st.divider()
    st.subheader("📜 Historial y Comentarios")

    logs = db.get_ticket_logs(ticket_id)
    if not logs.empty:
        for idx, log in logs.iterrows():
            with st.chat_message(
                "user" if log["event_type"] == "comment" else "assistant"
            ):
                st.write(f"**{log['author']}** ({log['created_at']}):")
                st.write(log["message"])
                if log["event_type"] != "comment" and log["meta_json"]:
                    st.caption(f"Detalles: {log['meta_json']}")

    with st.form("new_comment"):
        comment_text = st.text_area("Agregar Comentario")
        if st.form_submit_button("Enviar Comentario"):
            if comment_text:
                db.add_ticket_log(ticket_id, current_user, "comment", comment_text)
                st.success("Comentario agregado")
                st.rerun()


def show_my_tasks():
    st.header("👤 Mis Tareas")
    # Usa el usuario de la simulacion
    tasks = db.get_tasks_by_user(current_user)
    if tasks.empty:
        st.info(f"No tienes tareas pendientes, {current_user}.")
    else:
        st.dataframe(
            tasks[["id", "ticket_id", "ticket_titulo", "descripcion", "estado"]],
            hide_index=True,
        )


# --- Navegación Principal ---
opciones = ["Crear Ticket", "Bandeja de Tickets", "Detalle de Ticket", "Mis Tareas"]
if "page" not in st.session_state:
    st.session_state["page"] = "Crear Ticket"

selection = st.sidebar.radio(
    "Ir a:",
    opciones,
    index=opciones.index(st.session_state["page"])
    if st.session_state["page"] in opciones
    else 0,
)

if selection != st.session_state["page"]:
    st.session_state["page"] = selection
    st.rerun()

if st.session_state["page"] == "Crear Ticket":
    show_create_ticket()
elif st.session_state["page"] == "Bandeja de Tickets":
    show_ticket_tray()
elif st.session_state["page"] == "Detalle de Ticket":
    show_ticket_detail()
elif st.session_state["page"] == "Mis Tareas":
    show_my_tasks()
