# Estilos CSS en GESTAR v2

Este documento resume los estilos definidos en el bloque `<style>` de `app_v2.py` y el objetivo de cada grupo.

## Tipografia y color base
- `@import` carga las fuentes Lato y Raleway desde Google Fonts.
- `html, body, [class*="css"]` aplica Lato y color base `#444` a toda la app.
- `h1, h2, h3, .raleway` usa Raleway en titulos y elementos con clase `raleway`.

## Iconos y espaciado global
- `.bi` ajusta la alineacion vertical y margen de iconos Bootstrap.
- `.block-container` reduce el padding superior general.
- `.top-icon` estandariza tamano y color de iconos en la barra superior.

## Barra superior (Top Bar)
- `.taranto-header` define el contenedor de la cabecera: fondo blanco, borde rojo, padding y layout flex.

## Botones
- `div.stButton > button` define estilo base: mayusculas, tracking, tipografia y transicion.
- `div.stButton > button[kind="primary"]` aplica el color rojo Taranto para botones primarios.
- `.active-nav button` resalta el boton activo de navegacion.

## Tabs
- `.stTabs [data-baseweb="tab-list"]` separa tabs con `gap`.
- `.stTabs [data-baseweb="tab"]` define fondo, bordes y padding.
- `.stTabs [aria-selected="true"]` resalta la tab activa en azul.

## Dataframes
- `.stDataFrame` agrega borde redondeado y sombra suave.

## Grilla de Bandeja (filas personalizadas)
- `.v2-row-cell` compacta el alto de cada celda (line-height y sin padding).
- `.v2-row-cell a` mantiene el link compacto dentro de la celda.
- `div[data-testid="stHorizontalBlock"]:has(.v2-row-cell)` controla espaciado y separador de filas:
  - `gap: 0` elimina el espacio horizontal entre columnas.
  - `padding-top: 0px`, `padding-bottom: 18px` controla aire vertical.
  - `border-bottom` agrega la linea separadora de filas.

## Tarjetas
- `.v2-card` define tarjetas con borde suave, sombra y padding.

## Sidebar/Filtros
- `[data-testid="stVerticalBlock"] > div:has(.v2-sidebar-header)` aplica fondo y borde redondeado al bloque de filtros.

## Ocultar header/footer de Streamlit
- `header {visibility: hidden;}` y `footer {visibility: hidden;}` ocultan elementos nativos.

## Badge de usuario
- `.user-badge` define el badge del usuario con fondo claro, borde y layout flex.

## Boton con apariencia de link
- `div[data-testid="column"]:has(.link-style) button` convierte un boton en link:
  - sin fondo ni borde, subrayado, color azul.
  - mantiene el estilo en hover, active y focus.

