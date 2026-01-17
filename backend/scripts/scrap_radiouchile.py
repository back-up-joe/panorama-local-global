import sys
import os
import time
import django
from datetime import datetime
import json

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraper.settings')
django.setup()

from news.models import Article
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

def configurar_driver():
    """Configurar Selenium WebDriver optimizado"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Configuraciones adicionales para mejor rendimiento
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-extensions")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

'''
def extraer_urls_secciones(driver):
    """
    Extrae URLs de noticias de radio.uchile.cl basado en la estructura HTML proporcionada
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias en radio.uchile.cl...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal
        driver.get("https://radio.uchile.cl/")
        time.sleep(3)
        
        # Esperar a que cargue el contenido
        wait = WebDriverWait(driver, 10)
        
        # Hacer scroll para cargar contenido dinámico
        scroll_pauses = [0.5, 0.8, 1]
        for i, pause in enumerate(scroll_pauses):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/len(scroll_pauses)});")
            time.sleep(pause)
        
        print("\nAnalizando estructura de la página...")
        
        # Estrategia 1: Buscar en la sección principal (#hero)
        print("Buscando en sección hero...")
        try:
            hero_section = driver.find_element(By.ID, "hero")
            enlaces_hero = hero_section.find_elements(By.TAG_NAME, "a")
            
            for enlace in enlaces_hero:
                try:
                    href = enlace.get_attribute("href")
                    if href and "radio.uchile.cl" in href and "/2026/" in href:
                        if href not in urls_noticias:
                            urls_noticias.append(href)
                            print(f"  Encontrado en hero: {href}")
                except:
                    continue
        except Exception as e:
            print(f"Error en sección hero: {e}")
        
        # Estrategia 2: Buscar artículos por clases específicas (basado en HTML)
        print("Buscando por clases de artículos...")
        selectores_articulos = [
            "h2.post-title a",  # Títulos principales
            "h4.title-secondary a",  # Títulos secundarios
            "h5.title-secondary a",  # Títulos terciarios
            ".title-secondary a",  # Clase general para títulos
            ".title-third-line a",  # Línea de títulos terciarios
            ".post.featured-post-lg a",  # Artículos destacados grandes
            ".details.clearfix a",  # Detalles de artículos
            ".thumb.rounded a",  # Miniaturas redondeadas
            ".post-list a",  # Lista de artículos
        ]
        
        for selector in selectores_articulos:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"  Selector '{selector}': {len(elementos)} elementos")
                
                for elemento in elementos:
                    try:
                        href = elemento.get_attribute("href")
                        if href and "radio.uchile.cl" in href:
                            # Filtrar URLs de artículos (no categorías, tags, etc.)
                            if re.search(r'/202\d+/\d{2}/\d{2}/', href):  # Patrón de fecha
                                if not any(excluir in href for excluir in [
                                    '/tag/', '/category/', '/author/', '/temas/',
                                    '?s=', '#', '/programacion', '/programas',
                                    '/senal-en-vivo', '/cartas-al-director/',
                                    '/opiniones/', '/cultura/', '/deportes/',
                                    '/internacional/', '/universidad_radio/'
                                ]):
                                    if href not in urls_noticias:
                                        urls_noticias.append(href)
                    except:
                        continue
            except Exception as e:
                print(f"  Error con selector '{selector}': {e}")
                continue
        
        # Estrategia 3: Buscar por estructura de grid/columnas
        print("Buscando en estructura de columnas...")
        try:
            # Buscar en columnas principales (col-lg-6, col-lg-3)
            columnas = driver.find_elements(By.CSS_SELECTOR, ".col-lg-6, .col-lg-3")
            for columna in columnas:
                try:
                    enlaces = columna.find_elements(By.TAG_NAME, "a")
                    for enlace in enlaces:
                        try:
                            href = enlace.get_attribute("href")
                            if href and "radio.uchile.cl" in href and "/2026/" in href:
                                if href not in urls_noticias:
                                    urls_noticias.append(href)
                        except:
                            continue
                except:
                    continue
        except Exception as e:
            print(f"Error en columnas: {e}")
        
        # Filtrar duplicados y URLs no deseadas
        urls_filtradas = []
        for url in urls_noticias:
            if url and 'radio.uchile.cl' in url:
                # Asegurar que sea un artículo con patrón de fecha
                if re.search(r'/202\d+/\d{2}/\d{2}/', url):
                    # Excluir URLs que no son artículos
                    if not any(excluir in url for excluir in [
                        '/temas/', '/tag/', '/category/', '/author/', 
                        '?s=', '#', '/programacion', '/programas',
                        '/senal-en-vivo', '/cartas-al-director/',
                        '/opiniones/', '/cultura/', '/deportes/',
                        '/internacional/', '/universidad_radio/',
                        '/columnas/', '/buscar', '/sitemap'
                    ]):
                        urls_filtradas.append(url)
        
        urls_noticias = list(set(urls_filtradas))  # Eliminar duplicados
        
        print(f"\nTotal de URLs encontradas: {len(urls_noticias)}")
        
        # Mostrar algunas URLs para debug
        if urls_noticias:
            print("\nPrimeras 10 URLs encontradas:")
            for i, url in enumerate(urls_noticias[:10], 1):
                print(f"{i}. {url}")
            if len(urls_noticias) > 10:
                print(f"... y {len(urls_noticias) - 10} más")
        else:
            print("No se encontraron URLs de artículos.")
            
    except Exception as e:
        print(f"Error al buscar enlaces: {e}")
        import traceback
        traceback.print_exc()
    
    return urls_noticias
''' 

def extraer_urls_secciones(driver):
    """
    Extrae URLs de noticias de radio.uchile.cl basado en la estructura HTML proporcionada
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias en radio.uchile.cl...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal
        driver.get("https://radio.uchile.cl/")
        time.sleep(3)
        
        # Esperar a que cargue el contenido
        wait = WebDriverWait(driver, 10)
        
        # Hacer scroll para cargar contenido dinámico
        scroll_pauses = [0.5, 0.8, 1, 1.2]
        for i, pause in enumerate(scroll_pauses):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/len(scroll_pauses)});")
            time.sleep(pause)
        
        print("\nAnalizando estructura de la página...")
        
        # Estrategia principal: Buscar TODOS los enlaces y filtrar los que sean artículos
        print("Buscando todos los enlaces de artículos...")
        try:
            # Buscar todos los enlaces en la página
            all_links = driver.find_elements(By.TAG_NAME, "a")
            print(f"Total de enlaces encontrados: {len(all_links)}")
            
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    if href and 'radio.uchile.cl' in href:
                        # Patrón más flexible para artículos
                        if re.search(r'/\d{4}/\d{2}/\d{2}/', href):  # Patrón de fecha: /2026/01/15/
                            # Excluir URLs no deseadas
                            if not any(excluir in href for excluir in [
                                '/tag/', '/category/', '/author/', '/temas/',
                                '?s=', '#comment', '/programacion', '/programas',
                                '/senal-en-vivo', '/cartas-al-director/',
                                '/opiniones/', '/cultura/', '/deportes/',
                                '/internacional/', '/universidad_radio/',
                                '/columnas/', '/buscar', '/sitemap',
                                '/feed/', '/wp-admin/', '/wp-content/',
                                '/wp-json/', '/xmlrpc.php'
                            ]):
                                if href not in urls_noticias:
                                    urls_noticias.append(href)
                                    print(f"  Artículo encontrado: {href}")
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error al buscar todos los enlaces: {e}")
        
        # Estrategia específica para la sección hero (noticias principales)
        print("\nBuscando en sección hero...")
        try:
            # Buscar en la sección #hero específicamente
            hero_section = driver.find_elements(By.CSS_SELECTOR, "#hero a")
            for enlace in hero_section:
                try:
                    href = enlace.get_attribute("href")
                    if href and re.search(r'/\d{4}/\d{2}/\d{2}/', href):
                        if href not in urls_noticias:
                            urls_noticias.append(href)
                            print(f"  Encontrado en hero: {href}")
                except:
                    continue
        except Exception as e:
            print(f"Error en sección hero: {e}")
        
        # Estrategia: Buscar en los posts principales
        print("\nBuscando posts principales...")
        selectores_posts = [
            ".post.featured-post-lg a",
            ".post-title a",
            ".title-secondary a",
            "h2 a", "h3 a", "h4 a", "h5 a",
            ".thumb.rounded a"
        ]
        
        for selector in selectores_posts:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"  Selector '{selector}': {len(elementos)} elementos")
                
                for elemento in elementos:
                    try:
                        href = elemento.get_attribute("href")
                        if href and 'radio.uchile.cl' in href:
                            if re.search(r'/\d{4}/\d{2}/\d{2}/', href):
                                if href not in urls_noticias:
                                    urls_noticias.append(href)
                    except:
                        continue
            except Exception as e:
                print(f"  Error con selector '{selector}': {e}")
        
        # Filtrar y ordenar URLs
        urls_filtradas = []
        for url in urls_noticias:
            # Asegurar que sea una URL de artículo
            if re.search(r'/\d{4}/\d{2}/\d{2}/', url):
                # Limpiar parámetros de la URL
                url_limpia = url.split('?')[0] if '?' in url else url
                if url_limpia not in urls_filtradas:
                    urls_filtradas.append(url_limpia)
        
        # Ordenar por fecha (más recientes primero)
        def extraer_fecha_url(url):
            match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
            if match:
                return match.group(1), match.group(2), match.group(3)
            return ('0000', '00', '00')
        
        urls_filtradas.sort(key=extraer_fecha_url, reverse=True)
        
        print(f"\nTotal de URLs de artículos encontradas: {len(urls_filtradas)}")
        
        # Mostrar algunas URLs para debug
        if urls_filtradas:
            print("\nPrimeras 15 URLs encontradas:")
            for i, url in enumerate(urls_filtradas[:15], 1):
                print(f"{i}. {url}")
            if len(urls_filtradas) > 15:
                print(f"... y {len(urls_filtradas) - 15} más")
        else:
            print("No se encontraron URLs de artículos.")
            
    except Exception as e:
        print(f"Error al buscar enlaces: {e}")
        import traceback
        traceback.print_exc()
    
    return urls_filtradas

def extraer_datos_noticia(driver, url):
    """
    Extrae todos los datos de una noticia individual de radio.uchile.cl
    Basado en la estructura HTML proporcionada
    Retorna: diccionario con los datos extraídos
    """
    datos = {
        'url': url,
        'titular': 'No encontrado',
        'bajada': 'No encontrada',
        'imagen': 'No encontrada',
        'contenido': [],
        'fecha': 'No encontrada',
        'autor': 'No encontrado',
        'categoria': 'No encontrada'
    }
    
    try:
        print(f"  Navegando a: {url}")
        driver.get(url)
        time.sleep(2)
        
        # Esperar a que cargue la página
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
        except:
            pass
        
        # Extraer datos basados en la estructura HTML de ejemplo
        datos['titular'] = _extraer_titular_uchile(driver)
        print(f"  Titular: {datos['titular'][:80]}...")
        
        datos['bajada'] = _extraer_bajada_uchile(driver)
        print(f"  Bajada: {datos['bajada'][:100]}...")
        
        datos['imagen'] = _extraer_imagen_uchile(driver)
        print(f"  Imagen: {'Encontrada' if datos['imagen'] else 'No encontrada'}")
        
        contenido_info = _extraer_contenido_uchile(driver)
        datos['contenido'] = contenido_info['parrafos']
        print(f"  Párrafos extraídos: {len(datos['contenido'])}")
        
        fecha_autor = _extraer_fecha_autor_uchile(driver)
        datos['fecha'] = fecha_autor['fecha']
        datos['autor'] = fecha_autor['autor']
        print(f"  Fecha: {datos['fecha']}")
        print(f"  Autor: {datos['autor']}")
        
        datos['categoria'] = _extraer_categoria_uchile(driver)
        print(f"  Categoría: {datos['categoria']}")
        
    except Exception as e:
        print(f"Error general al procesar noticia: {e}")
        import traceback
        traceback.print_exc()
    
    return datos

def _extraer_titular_uchile(driver):
    """Extrae el titular de la noticia en radio.uchile.cl"""
    selectores_titular = [
        "h1.title.mt-0",  # Selector principal según HTML
        "h1.title",  # Alternativo
        ".post-header h1",  # En el header del post
        ".single-cover .cover-content h1",  # En la portada del artículo
        "article h1",  # En el artículo
        "h1"  # Último recurso
    ]
    
    for selector in selectores_titular:
        try:
            elemento = driver.find_element(By.CSS_SELECTOR, selector)
            texto = elemento.text.strip()
            if texto and len(texto) > 10:
                return texto
        except:
            continue
    
    # Si no se encuentra con selectores, buscar en metadata
    try:
        return driver.find_element(By.CSS_SELECTOR, "meta[property='og:title']").get_attribute("content").strip()
    except:
        pass
    
    return "No encontrado"

def _extraer_bajada_uchile(driver):
    """Extrae la bajada/entradilla de la noticia en radio.uchile.cl"""
    # Intentar múltiples estrategias basadas en HTML de ejemplo
    estrategias = [
        # 1. Meta description
        lambda: driver.find_element(By.CSS_SELECTOR, "meta[name='description']").get_attribute("content").strip(),
        # 2. Meta og:description
        lambda: driver.find_element(By.CSS_SELECTOR, "meta[property='og:description']").get_attribute("content").strip(),
        # 3. Texto en la portada para móviles (según HTML)
        lambda: driver.find_element(By.CSS_SELECTOR, ".container-xl.d-block.d-sm-none p.title").text.strip(),
        # 4. Primer párrafo del contenido
        lambda: driver.find_element(By.CSS_SELECTOR, ".post-content.clearfix p").text.strip(),
        # 5. Buscar cualquier párrafo significativo
        lambda: _buscar_primer_parrafo_significativo(driver)
    ]
    
    for estrategia in estrategias:
        try:
            resultado = estrategia()
            if resultado and len(resultado) > 50:
                return resultado[:500]  # Limitar longitud
        except:
            continue
    
    return "No encontrada"

def _buscar_primer_parrafo_significativo(driver):
    """Busca el primer párrafo significativo en el contenido"""
    try:
        parrafos = driver.find_elements(By.CSS_SELECTOR, ".post-content.clearfix p")
        for p in parrafos:
            texto = p.text.strip()
            if texto and len(texto) > 100:  # Párrafo significativo
                return texto
    except:
        pass
    return None

def _extraer_imagen_uchile(driver):
    """Extrae la URL de la imagen principal en radio.uchile.cl"""
    estrategias_imagen = [
        # 1. Meta og:image (más confiable)
        lambda: driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content"),
        # 2. Imagen en la portada del artículo
        lambda: driver.find_element(By.CSS_SELECTOR, ".single-cover").get_attribute("data-bg-image"),
        # 3. Imagen en el contenido
        lambda: driver.find_element(By.CSS_SELECTOR, ".post-content img").get_attribute("src"),
        # 4. Imagen destacada
        lambda: driver.find_element(By.CSS_SELECTOR, ".thumb.rounded img").get_attribute("src"),
        # 5. Buscar cualquier imagen grande
        lambda: _buscar_imagen_principal(driver)
    ]
    
    for estrategia in estrategias_imagen:
        try:
            url = estrategia()
            if url and ('http://' in url or 'https://' in url):
                return url
        except:
            continue
    
    return ""

def _buscar_imagen_principal(driver):
    """Busca la imagen principal entre todas las imágenes"""
    try:
        imagenes = driver.find_elements(By.TAG_NAME, "img")
        for img in imagenes:
            try:
                src = img.get_attribute("src")
                if src and ('uploads' in src or 'wp-content' in src):
                    # Verificar si es una imagen significativa
                    alt = img.get_attribute("alt") or ""
                    if len(alt) > 10:  # Tiene texto alternativo significativo
                        return src
            except:
                continue
    except:
        pass
    return None

def _extraer_contenido_uchile(driver):
    """Extrae el contenido de la noticia en radio.uchile.cl"""
    parrafos = []
    
    try:
        # Buscar el contenido principal según HTML
        contenido_div = driver.find_element(By.CSS_SELECTOR, ".post-content.clearfix")
        elementos_parrafo = contenido_div.find_elements(By.TAG_NAME, "p")
        
        for p in elementos_parrafo:
            texto = p.text.strip()
            # Filtrar párrafos vacíos o demasiado cortos
            if texto and len(texto) > 50:
                # Excluir textos que no son parte del contenido
                excluir_palabras = [
                    'publicidad', 'anuncio', 'widget', 'related posts', 
                    'tags:', 'claves:', 'Síguenos en', 'Compartir',
                    'Te puede interesar', 'Lee también'
                ]
                
                if not any(palabra in texto.lower() for palabra in excluir_palabras):
                    # Limpiar texto (remover espacios múltiples)
                    texto_limpio = ' '.join(texto.split())
                    parrafos.append(texto_limpio)
                
    except Exception as e:
        print(f"  Error al extraer contenido: {e}")
        # Fallback: buscar en el artículo completo
        try:
            contenido = driver.find_element(By.TAG_NAME, "article").text
            if contenido:
                # Dividir en párrafos
                lineas = contenido.split('\n')
                for linea in lineas:
                    if len(linea.strip()) > 100:
                        parrafos.append(linea.strip())
        except:
            pass
    
    return {'parrafos': parrafos, 'total': len(parrafos)}

def _extraer_categoria_uchile(driver):
    """Extrae la categoria de la noticia en radio.uchile.cl"""
    estrategias_categoria = [
        # 1. Tags al final del artículo
        lambda: ', '.join([tag.text for tag in driver.find_elements(By.CSS_SELECTOR, ".post-bottom .tag")]),
        # 2. Categoría en el header
        lambda: driver.find_element(By.CSS_SELECTOR, ".post-header .tag").text,
        # 3. En los metadatos
        lambda: driver.find_element(By.CSS_SELECTOR, "meta[property='article:section']").get_attribute("content"),
        # 4. Buscar en los tags al final del contenido
        lambda: _extraer_tags_contenido(driver)
    ]
    
    for estrategia in estrategias_categoria:
        try:
            resultado = estrategia()
            if resultado and len(resultado) > 0:
                return resultado
        except:
            continue
    
    return "No encontrada"

def _extraer_tags_contenido(driver):
    """Extrae tags del contenido"""
    try:
        tags_section = driver.find_element(By.CSS_SELECTOR, ".tags")
        tags = tags_section.find_elements(By.TAG_NAME, "a")
        if tags:
            return ', '.join([tag.text for tag in tags])
    except:
        pass
    return None

'''
def _extraer_fecha_autor_uchile(driver):
    """Extrae fecha y autor de la noticia en radio.uchile.cl"""
    fecha = "No encontrada"
    autor = "No encontrado"
    
    # Estrategia 1: Extraer del header del artículo (según HTML)
    try:
        meta_info = driver.find_element(By.CSS_SELECTOR, ".post-header ul.meta")
        items = meta_info.find_elements(By.TAG_NAME, "li")
        
        if len(items) >= 2:
            autor = items[0].text.strip()
            fecha = items[1].text.strip()
            
            # Limpiar fecha (remover etiquetas HTML si las hay)
            fecha = re.sub(r'<[^>]+>', '', fecha)
    except:
        pass
    
    # Estrategia 2: Buscar en schema.org/JSON-LD
    if fecha == "No encontrada" or autor == "No encontrado":
        try:
            scripts = driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                script_type = script.get_attribute("type")
                if script_type == "application/ld+json":
                    try:
                        data = json.loads(script.get_attribute("innerHTML"))
                        if isinstance(data, dict):
                            if 'datePublished' in data and fecha == "No encontrada":
                                fecha_raw = data['datePublished']
                                # Convertir a formato legible
                                fecha = fecha_raw.split('T')[0] if 'T' in fecha_raw else fecha_raw
                            if 'author' in data and autor == "No encontrado":
                                if isinstance(data['author'], dict) and 'name' in data['author']:
                                    autor = data['author']['name']
                    except:
                        continue
        except:
            pass
    
    # Estrategia 3: Buscar en meta tags
    if fecha == "No encontrada":
        try:
            fecha = driver.find_element(By.CSS_SELECTOR, "meta[property='article:published_time']").get_attribute("content")
            fecha = fecha.split('T')[0] if 'T' in fecha else fecha
        except:
            pass
    
    # Limpiar y formatear
    fecha = fecha.replace("Publicado:", "").replace("Actualizado:", "").strip()
    
    return {'fecha': fecha, 'autor': autor} '''

######################################################################################################################

from datetime import datetime, date
import re

MESES_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

def _parsear_fecha(fecha_str: str) -> date | None:
    if not fecha_str:
        return None

    fecha_str = fecha_str.strip().lower()

    # Formatos ISO: 2026-01-15
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    # Formato: 16/01/2026
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y").date()
    except ValueError:
        pass

    # Formato: 13 enero, 2026
    m = re.match(r"(\d{1,2})\s+([a-záéíóú]+),?\s+(\d{4})", fecha_str)
    if m:
        dia, mes, anio = m.groups()
        return date(int(anio), MESES_ES[mes], int(dia))

    # Formato: enero 13, 2026
    m = re.match(r"([a-záéíóú]+)\s+(\d{1,2}),?\s+(\d{4})", fecha_str)
    if m:
        mes, dia, anio = m.groups()
        return date(int(anio), MESES_ES[mes], int(dia))

    return None

'''
def _extraer_fecha_autor_uchile(driver):
    """Extrae fecha y autor de la noticia en radio.uchile.cl"""
    fecha = None
    fecha_raw = None
    autor = "No encontrado"

    # Estrategia 1: Header del artículo
    try:
        meta_info = driver.find_element(By.CSS_SELECTOR, ".post-header ul.meta")
        items = meta_info.find_elements(By.TAG_NAME, "li")

        if len(items) >= 2:
            autor = items[0].text.strip()
            fecha_raw = items[1].text.strip()
            fecha_raw = re.sub(r'<[^>]+>', '', fecha_raw)
    except:
        pass

    # Estrategia 2: JSON-LD
    if fecha_raw is None or autor == "No encontrado":
        try:
            scripts = driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                if script.get_attribute("type") == "application/ld+json":
                    try:
                        data = json.loads(script.get_attribute("innerHTML"))
                        if isinstance(data, dict):
                            if 'datePublished' in data and fecha_raw is None:
                                fecha_raw = data['datePublished']
                            if 'author' in data and autor == "No encontrado":
                                if isinstance(data['author'], dict):
                                    autor = data['author'].get('name', autor)
                    except:
                        continue
        except:
            pass

    # Estrategia 3: meta tag
    if fecha_raw is None:
        try:
            fecha_raw = driver.find_element(
                By.CSS_SELECTOR,
                "meta[property='article:published_time']"
            ).get_attribute("content")
        except:
            pass

    # Limpieza final del string
    if fecha_raw:
        fecha_raw = (
            fecha_raw
            .replace("Publicado:", "")
            .replace("Actualizado:", "")
            .strip()
        )

    # PARSEO FINAL (UNA SOLA VEZ)
    fecha = _parsear_fecha(fecha_raw)

    return {
        'fecha': fecha,   # datetime.date | None
        'autor': autor
    }
'''

def _extraer_fecha_autor_uchile(driver):
    """Extrae fecha y autor de la noticia en radio.uchile.cl"""
    fecha_raw = None
    autor = "No encontrado"

    # Estrategia 1: Buscar en el post-header (según HTML de ejemplo)
    try:
        # Buscar el post-header
        post_header = driver.find_element(By.CSS_SELECTOR, ".post-header")
        
        # Buscar elementos li dentro del meta
        meta_items = post_header.find_elements(By.CSS_SELECTOR, "ul.meta li")
        
        if len(meta_items) >= 2:
            # Primer li es autor
            autor_elem = meta_items[0].find_element(By.TAG_NAME, "a")
            if autor_elem:
                autor = autor_elem.text.strip()
                if not autor or autor == "":
                    autor = meta_items[0].text.strip()
            
            # Segundo li es fecha (o buscar fecha en cualquier li)
            for item in meta_items:
                texto = item.text.strip()
                # Buscar patrones de fecha
                if re.search(r'\d{2}-\d{2}-\d{4}', texto) or re.search(r'\d{2}/\d{2}/\d{4}', texto):
                    fecha_raw = texto
                    break
            
            # Si no encontramos fecha en los li, buscar directamente
            if not fecha_raw and len(meta_items) >= 2:
                fecha_raw = meta_items[1].text.strip()
                
    except Exception as e:
        print(f"  Error en post-header: {e}")
        pass

    # Estrategia 2: Buscar fecha en elementos strong dentro del post-header
    if not fecha_raw:
        try:
            strong_elements = driver.find_elements(By.CSS_SELECTOR, ".post-header strong")
            for elem in strong_elements:
                texto = elem.text.strip()
                if re.search(r'\d{2}-\d{2}-\d{4}', texto):
                    fecha_raw = texto
                    break
        except:
            pass

    # Estrategia 3: Buscar en JSON-LD
    if not fecha_raw:
        try:
            scripts = driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                if script.get_attribute("type") == "application/ld+json":
                    try:
                        data = json.loads(script.get_attribute("innerHTML"))
                        if isinstance(data, dict):
                            if 'datePublished' in data:
                                fecha_raw = data['datePublished']
                                # Convertir formato ISO a legible
                                if 'T' in fecha_raw:
                                    fecha_raw = fecha_raw.split('T')[0]
                            if 'author' in data and autor == "No encontrado":
                                if isinstance(data['author'], dict):
                                    autor = data['author'].get('name', autor)
                    except:
                        continue
        except:
            pass

    # Estrategia 4: Buscar en meta tags
    if not fecha_raw:
        try:
            fecha_raw = driver.find_element(
                By.CSS_SELECTOR,
                "meta[property='article:published_time']"
            ).get_attribute("content")
            if 'T' in fecha_raw:
                fecha_raw = fecha_raw.split('T')[0]
        except:
            pass
    
    # Estrategia 5: Buscar cualquier elemento con patrón de fecha
    if not fecha_raw:
        try:
            # Buscar en todo el body
            body_text = driver.find_element(By.TAG_NAME, "body").text
            # Buscar patrones de fecha comunes
            fecha_patterns = [
                r'\d{2}-\d{2}-\d{4}',  # 17-01-2026
                r'\d{2}/\d{2}/\d{4}',   # 17/01/2026
                r'\d{4}-\d{2}-\d{2}',   # 2026-01-17
            ]
            for pattern in fecha_patterns:
                match = re.search(pattern, body_text)
                if match:
                    fecha_raw = match.group(0)
                    break
        except:
            pass

    # Limpieza del string de fecha
    if fecha_raw:
        fecha_raw = (
            fecha_raw
            .replace("Publicado:", "")
            .replace("Actualizado:", "")
            .replace("Publicado", "")
            .replace("Actualizado", "")
            .strip()
        )
    
    # Parsear fecha
    fecha = _parsear_fecha(fecha_raw) if fecha_raw else None

    # Si no se encontró autor, usar valor por defecto
    if autor == "No encontrado" or not autor:
        autor = "Diario UCHILE"

    return {
        'fecha': fecha,   # datetime.date | None
        'autor': autor
    }

######################################################################################################################

def guardar_en_db(datos):
    """Guardar datos en la base de datos"""
    try:
        # Verificar si ya existe
        if Article.objects.filter(url=datos['url']).exists():
            print(f"  Ya existe en DB: {datos['titular'][:50]}...")
            return False
        
        # Validar datos mínimos
        if not datos['titular'] or datos['titular'] == 'No encontrado':
            print(f"  Error: Sin titular para {datos['url']}")
            return False
        
        if len(datos['contenido']) < 1:
            print(f"  Error: Sin contenido para {datos['titular'][:50]}...")
            return False
        
        # Convertir contenido de lista a string
        contenido_texto = '\n\n'.join(datos['contenido'])
        
        # Procesar fecha
        fecha_publicacion = datos['fecha']
        try:
            # Intentar parsear diferentes formatos de fecha
            if 'T' in fecha_publicacion:
                fecha_publicacion = fecha_publicacion.split('T')[0]
            
            # Convertir a objeto date
            fecha_obj = datetime.strptime(fecha_publicacion[:10], '%Y-%m-%d').date()
        except:
            # Usar fecha actual si no se puede parsear
            fecha_obj = datetime.now().date()
        
        # Crear nuevo artículo
        articulo = Article.objects.create(
            url=datos['url'],
            title=datos['titular'],
            subtitle=datos['bajada'][:500] if datos['bajada'] else '',
            image_url=datos['imagen'][:500] if datos['imagen'] else '',
            content=contenido_texto[:10000],  # Limitar tamaño
            publication_date=fecha_obj,
            author=datos['autor'][:100] if datos['autor'] else '',
            category=datos['categoria'][:200] if datos['categoria'] else ''
        )
        
        print(f"Guardado: {articulo.title[:60]}...")
        return True
        
    except Exception as e:
        print(f"Error guardando en DB: {e}")
        return False

def ejecutar_scraping(max_noticias=10):
    """Función principal de scraping para radio.uchile.cl"""
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE RADIO.UCHILE.CL - VERSIÓN MEJORADA")
        print("="*80)
        
        # Configurar driver
        print("Configurando WebDriver...")
        driver = configurar_driver()
        
        # Extraer URLs
        print("\nExtrayendo URLs de artículos...")
        urls = extraer_urls_secciones(driver)
        
        if not urls:
            print("No se encontraron URLs de noticias")
            return 0
        
        print(f"\nProcesando las primeras {min(max_noticias, len(urls))} noticias...")
        
        # Procesar cada URL
        for i, url in enumerate(urls[:max_noticias], 1):
            print(f"\n[Artículo {i}/{min(max_noticias, len(urls))}]")
            
            # Extraer datos
            datos = extraer_datos_noticia(driver, url)
            
            # Guardar en DB si tiene contenido suficiente
            if datos['contenido'] and len(datos['contenido']) >= 1:
                if guardar_en_db(datos):
                    articulos_procesados += 1
            else:
                print(f"Sin contenido suficiente: {datos['titular'][:50]}...")
            
            # Pausa para no sobrecargar el servidor
            if i < min(max_noticias, len(urls)):
                time.sleep(1.5)  # Pausa un poco más larga
        
        return articulos_procesados
        
    except Exception as e:
        print(f"\nError general en scraping: {e}")
        import traceback
        traceback.print_exc()
        return 0
        
    finally:
        if driver:
            driver.quit()
            print("\nWebDriver cerrado.")

def run():
    cantidad = ejecutar_scraping(max_noticias=10)
    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETADO")
    print(f"Artículos procesados: {cantidad}")
    
    # Mostrar estadísticas
    from news.models import Article
    total = Article.objects.count()
    print(f"Total en base de datos: {total}")
    
    # Mostrar los últimos artículos agregados
    if cantidad > 0:
        print("\nÚltimos artículos agregados:")
        nuevos = Article.objects.order_by('-id')[:min(3, cantidad)]
        for art in nuevos:
            print(f"  • {art.title[:70]}...")
    
    print(f"{'='*80}")

if __name__ == "__main__":
    run()