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

# Fetch users from DB
df_users = db.get_users(only_active=True)
user_names = df_users["nombre_completo"].tolist()

if not user_names:
    st.sidebar.error("No hay usuarios activos en la DB.")
    st.stop()

# User Selection
selected_name = st.sidebar.selectbox("Usuario Actual", user_names)
user_info = db.get_user_by_name(selected_name)

if user_info:
    current_user = user_info["nombre_completo"]
    current_role = user_info["rol"]
    current_area = user_info["area"]
else:
    current_user = selected_name
    current_role = "Solicitante"
    current_area = "IT"

st.sidebar.text_input("Rol", value=current_role, disabled=True)
st.sidebar.text_input("Área", value=current_area, disabled=True)

st.sidebar.markdown("---")
# Navigation moved down to dispatcher section
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
                user_names,
                index=user_names.index(current_user)
                if current_user in user_names
                else 0,
            )

        with col2:
            categoria = st.selectbox("Categoría", models.CATEGORIAS)
            sub_options = models.SUBCATEGORIAS.get(categoria, [])
            subcategoria = st.selectbox("Subcategoría", sub_options)
            division = st.selectbox("División", models.DIVISIONES)
            planta = st.selectbox("Planta", models.PLANTAS)
            resp_sugerido = st.selectbox(
                "Responsable Sugerido", ["Sin Sugerir"] + user_names
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
                    resps_list = ["Sin Asignar"] + user_names
                    try:
                        resp_idx = (
                            resps_list.index(current_resp)
                            if current_resp in resps_list
                            else 0
                        )
                    except Exception:
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
                user_names,
                index=user_names.index(current_user)
                if current_user in user_names
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


# --- PANEL ADMINISTRACION ---


def show_admin():
    st.header("⚙️ Panel de Administración")

    tab_users, tab_aux = st.tabs(["👥 Usuarios", "📋 Tablas Auxiliares"])

    with tab_users:
        st.subheader("Gestión de Usuarios")

        # Form to add user
        with st.expander("➕ Agregar Nuevo Usuario"):
            with st.form("add_user_form"):
                new_name = st.text_input("Nombre Completo*")
                new_email = st.text_input("Email")
                new_role = st.selectbox("Rol", models.ROLES)
                new_area = st.selectbox("Área", models.AREAS)

                if st.form_submit_button("Guardar Usuario"):
                    if new_name:
                        db.create_user(
                            {
                                "nombre_completo": new_name,
                                "email": new_email,
                                "rol": new_role,
                                "area": new_area,
                                "activo": 1,
                            }
                        )
                        st.success(f"Usuario {new_name} creado.")
                        st.rerun()
                    else:
                        st.error("El nombre es obligatorio.")

        # Grid Editable
        df_all_users = db.get_users()

        edited_df = st.data_editor(
            df_all_users,
            column_config={
                "id": None,
                "nombre_completo": st.column_config.TextColumn(
                    "Nombre Completo", disabled=True
                ),
                "email": st.column_config.TextColumn("Email"),
                "rol": st.column_config.SelectboxColumn(
                    "Rol", options=models.ROLES, required=True
                ),
                "area": st.column_config.SelectboxColumn(
                    "Área", options=models.AREAS, required=True
                ),
                "activo": st.column_config.CheckboxColumn("Activo"),
            },
            hide_index=True,
            use_container_width=True,
            key="user_editor",
        )

        c1, c2, _ = st.columns([1, 1, 4])
        if c1.button("Confirmar Cambios", type="primary"):
            state = st.session_state.get("user_editor", {})
            edited = state.get("edited_rows", {})

            if edited:
                for row_idx, updates in edited.items():
                    idx = int(row_idx)
                    user_id = int(df_all_users.iloc[idx]["id"])

                    # Convert bool to int for SQLite
                    if "activo" in updates:
                        updates["activo"] = 1 if updates["activo"] else 0

                    db.update_user(user_id, updates)

                st.success("Cambios guardados.")
                st.rerun()
            else:
                st.info("No se detectaron cambios.")

        if c2.button("Cancelar"):
            st.rerun()

    with tab_aux:
        st.info("Próximamente: Gestión de Áreas, Divisiones y Plantas.")


# --- Navegación Principal ---
opciones = ["Crear Ticket", "Bandeja de Tickets", "Detalle de Ticket", "Mis Tareas"]
if current_role == "Administrador":
    opciones.append("Administración")

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

# --- MAIN DISPATCHER ---
if selection == "Crear Ticket":
    show_create_ticket()
elif selection == "Bandeja de Tickets":
    show_ticket_tray()
elif selection == "Detalle de Ticket":
    show_ticket_detail()
elif selection == "Mis Tareas":
    show_my_tasks()
elif selection == "Administración":
    show_admin()
