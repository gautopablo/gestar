# Estilo web Taranto - resumen extraido

Fuente de referencia: http://taranto.com.ar/Contacto

Nota: este documento resume estilos y estructura detectados en HTML/CSS del sitio. No incluye contenido ni datos.

## Paleta (colores predominantes en CSS)
- Rojo de marca: #d52e25 (muy usado en fondos, links activos y acentos).
- Azul de marca: #156099 (clase .color-azul, color de seleccion).
- Neutros frecuentes: #fff, #f5f5f5, #eee, #ddd, #e5e5e5, #444, #333, #666, #555, #222.

## Tipografia
- Body: Lato, sans-serif (color #555, line-height 1.5).
- Titulos/menu: Raleway, sans-serif.
- Tipografia secundaria: Crete Round (serif).

## Estructura HTML principal (pagina /Contacto)
- Body class: "stretched device-lg".
- Top bar: <div id="top-bar"> dentro de <div class="header ...">.
- Header principal: <header id="header"> con <div id="header-wrap">.
- Navbar/menu: <nav id="primary-menu"> con <ul><li><a>...
- Hero/page title: <section id="page-title" class="page-title-parallax page-title-dark page-title-center"> dentro de <div id="pageContacto">.

## Top bar (barra superior)
Selector: #top-bar
- height: 45px
- line-height: 44px
- font-size: 13px
- border-bottom: 1px solid #eee

## Header + logo
Selector: #header
- background-color: #fff
- border-bottom: 1px solid #f5f5f5

Altura compartida:
- #header, #header-wrap, #logo img => height: 100px

Selector: #header-wrap
- position: relative
- z-index: 199

## Navbar / menu principal
Selector: #primary-menu ul li > a
- padding: 39px 10px
- line-height: 22px
- font-weight: 700
- font-size: 12px
- letter-spacing: 0.5px
- text-transform: uppercase
- font-family: Raleway, sans-serif
- color: #444

Hover/activo:
- #primary-menu ul li.current > a, #primary-menu ul li:hover > a => color #d52e25

## Page title / hero
Selector: #page-title (base)
- padding: 50px 0
- background-color: #f5f5f5
- border-bottom: 1px solid #eee

Titulo principal:
- #page-title h1 => font-weight 600, letter-spacing 1px, font-size 28px, text-transform uppercase, color #333

Subtitulo:
- #page-title span => margin-top 10px, font-weight 300, font-size 18px, color #777

Parallax:
- #page-title.page-title-parallax => padding 100px 0; border-bottom none; background-attachment fixed; background-position 50% 0
- h1 en parallax => font-size 40px, letter-spacing 2px
- span en parallax => font-size 22px

Dark:
- #page-title.page-title-dark => background-color #333; texto blanco semi-transparente
- h1 color rgba(255,255,255,.9)
- span color rgba(255,255,255,.7)

Center:
- #page-title.page-title-center => text-align center
- span max-width 700px; margin auto

## Overrides en Site.css (especificos de /Contacto)
- #page-title => padding 120px 0
- #pageContacto #page-title => background-image url(../images/parallax/contacto.jpg)

## Acentos / detalles visuales
- .linea => width 40px; border-bottom 2px solid #d52e25
- .color-azul => color #156099 !important
- .fondo-rojo => background-color #d52e25 !important
- .fondo-azul => background-color #156099 !important

## Observaciones utiles para replicar look & feel
- Predomina el rojo #d52e25 en header y estados activos.
- Top bar es una franja baja con borde inferior suave.
- Navbar usa mayusculas, tracking leve y padding vertical alto (39px) para dar altura al header.
- Hero (page title) usa fondo con imagen parallax y modo oscuro.
