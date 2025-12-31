import sys
import os
import time
import django
from datetime import datetime

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraper.settings')
django.setup()

from news.models import Article
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re

def configurar_driver():
    """Configurar Selenium WebDriver"""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def extraer_urls_secciones(driver):
    """
    Extrae URLs de noticias de las secciones especificadas
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias en las secciones especificadas...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal
        driver.get("https://www.revistadefrente.cl/")
        time.sleep(3)
        
        # Hacer scroll para cargar contenido dinámico
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Estrategia 1: Buscar en todos los enlaces de artículos
        print("\nBuscando enlaces de artículos...")
        
        # Primero, obtener TODOS los enlaces de la página
        todos_enlaces = driver.find_elements(By.TAG_NAME, "a")
        print(f"Total de enlaces en la página: {len(todos_enlaces)}")
        
        for enlace in todos_enlaces:
            try:
                href = enlace.get_attribute("href")
                if href and "revistadefrente.cl" in href:
                    # Verificar si es un artículo (no página de categoría, tag, etc.)
                    if (href not in urls_noticias and 
                        not href.endswith('/') and  # Excluir páginas principales
                        '#' not in href and  # Excluir anclas
                        '?' not in href and  # Excluir URLs con parámetros
                        '/category/' not in href and
                        '/tag/' not in href and
                        '/author/' not in href and
                        'feed' not in href and
                        'rss' not in href and
                        '.xml' not in href and
                        '.json' not in href and
                        href != "https://www.revistadefrente.cl/" and
                        href != "https://www.revistadefrente.cl/nacional/" and
                        href != "https://www.revistadefrente.cl/internacional/" and
                        href != "https://www.revistadefrente.cl/entrevistas/" and
                        href != "https://www.revistadefrente.cl/memoria-popular/" and
                        href != "https://www.revistadefrente.cl/cultura/" and
                        'category/opinion-de-frente' not in href):
                        
                        # Verificar que tenga un patrón de fecha o sea un artículo
                        import re
                        # Patrones que indican que es un artículo
                        patrones_articulo = [
                            r'/\d{4}/\d{2}/',  # /2025/12/
                            r'-\d+$',  # termina con número
                            r'\.html$',  # termina con .html
                        ]
                        
                        es_articulo = False
                        for patron in patrones_articulo:
                            if re.search(patron, href):
                                es_articulo = True
                                break
                        
                        # Si no tiene patrón claro, verificar por el texto del enlace
                        if not es_articulo:
                            texto = enlace.text.strip()
                            # Si el texto del enlace es largo (más de 10 caracteres), probablemente sea un artículo
                            if len(texto) > 10:
                                es_articulo = True
                        
                        if es_articulo:
                            urls_noticias.append(href)
            except:
                continue
        
        # Estrategia 2: Buscar específicamente en contenedores de noticias
        print("\nBuscando en contenedores de noticias...")
        
        contenedores = [
            ".edgtf-news-item",
            ".edgtf-layout1-item",
            ".edgtf-layout3-item", 
            ".edgtf-layout7-item",
            ".edgtf-layout8-item",
            ".edgtf-post-carousel1 .edgtf-news-item",
            ".edgtf-post-carousel3 .edgtf-news-item",
            ".edgtf-post-carousel6 .edgtf-news-item",
        ]
        
        for contenedor in contenedores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, contenedor)
                for elemento in elementos:
                    try:
                        # Buscar enlaces dentro del elemento
                        enlaces = elemento.find_elements(By.TAG_NAME, "a")
                        for enlace in enlaces:
                            try:
                                href = enlace.get_attribute("href")
                                if href and "revistadefrente.cl" in href and href not in urls_noticias:
                                    # Filtro más simple
                                    if ('/category/' not in href and 
                                        '/tag/' not in href and 
                                        '/author/' not in href and
                                        '#' not in href and
                                        '?' not in href):
                                        urls_noticias.append(href)
                            except:
                                continue
                    except:
                        continue
            except:
                continue
        
        # Eliminar duplicados
        urls_noticias = list(dict.fromkeys(urls_noticias))
        
        print(f"\nURLs encontradas antes de filtrar: {len(urls_noticias)}")
        
        # Filtrar URLs para quedarnos solo con artículos
        urls_filtradas = []
        for url in urls_noticias:
            try:
                # Excluir URLs no deseadas
                excluir = False
                
                # URLs específicas a excluir
                urls_excluir = [
                    "https://www.revistadefrente.cl/",
                    "https://www.revistadefrente.cl/nacional/",
                    "https://www.revistadefrente.cl/internacional/",
                    "https://www.revistadefrente.cl/entrevistas/",
                    "https://www.revistadefrente.cl/memoria-popular/",
                    "https://www.revistadefrente.cl/cultura/",
                    "https://www.revistadefrente.cl/category/opinion-de-frente/",
                    "https://www.revistadefrente.cl/category/nacional/",
                    "https://www.revistadefrente.cl/category/internacional/",
                    "https://www.revistadefrente.cl/feed/",
                    "https://www.revistadefrente.cl/comments/feed/",
                    "https://www.revistadefrente.cl/wp-json/",
                ]
                
                if url in urls_excluir:
                    excluir = True
                
                # Patrones a excluir
                patrones_excluir = [
                    '/category/',
                    '/tag/',
                    '/author/',
                    '/feed',
                    '/rss',
                    '/wp-',
                    '.xml',
                    '.json',
                    '#',
                    '?s=',
                    'search=',
                    '/page/',
                    '/pagina/',
                    '/archivo/',
                    '/archive/',
                ]
                
                if not excluir:
                    for patron in patrones_excluir:
                        if patron in url:
                            excluir = True
                            break
                
                # Incluir solo si no está excluida
                if not excluir:
                    # Verificar que parezca un artículo (no solo una página de mes)
                    import re
                    # Excluir páginas que son solo mes (como /2025/12/)
                    if re.match(r'https://www\.revistadefrente\.cl/\d{4}/\d{2}/$', url):
                        excluir = True
                    
                    # Incluir si tiene más segmentos después de la fecha
                    if not excluir and re.match(r'https://www\.revistadefrente\.cl/\d{4}/\d{2}/.+', url):
                        urls_filtradas.append(url)
                    # O si tiene un formato de título (con guiones)
                    elif not excluir and '-' in url and url.count('-') >= 2:
                        urls_filtradas.append(url)
                    # O si termina con número (ID de post)
                    elif not excluir and re.search(r'/\d+$', url):
                        urls_filtradas.append(url)
            
            except Exception as e:
                print(f"Error procesando URL {url}: {e}")
                continue
        
        urls_noticias = urls_filtradas
        
        print(f"\nTotal de URLs encontradas después de filtrar: {len(urls_noticias)}")
        
        # Mostrar las URLs encontradas
        if urls_noticias:
            print("\nPrimeras 20 URLs encontradas:")
            for i, url in enumerate(urls_noticias[:20], 1):
                print(f"{i}. {url}")
            if len(urls_noticias) > 20:
                print(f"... y {len(urls_noticias) - 20} más")
        else:
            print("No se encontraron URLs de artículos.")
            
            # Para debug
            print("\n--- DEBUG: Mostrando algunas URLs encontradas antes de filtrar ---")
            temp_urls = list(dict.fromkeys(urls_noticias))[:10]
            for i, url in enumerate(temp_urls, 1):
                print(f"{i}. {url}")
        
    except Exception as e:
        print(f"Error al buscar enlaces: {e}")
        import traceback
        traceback.print_exc()
    
    return urls_noticias

def _es_url_noticia_valida(url, lista_existente):
    """
    Verifica si una URL es válida para una noticia (versión simplificada)
    """
    if not url or url in lista_existente:
        return False
    
    if not url.startswith("https://www.revistadefrente.cl/"):
        return False
    
    # Excluir URLs que no son artículos
    excluir = [
        '/category/',
        '/tag/',
        '/author/',
        '?s=',
        '#',
        'feed',
        'rss',
        '.xml',
        '.json',
        '/wp-',
        '/page/',
        '/pagina/',
    ]
    
    for patron in excluir:
        if patron in url:
            return False
    
    # URLs específicas a excluir
    urls_excluir = [
        "https://www.revistadefrente.cl/",
        "https://www.revistadefrente.cl/nacional/",
        "https://www.revistadefrente.cl/internacional/",
        "https://www.revistadefrente.cl/entrevistas/",
        "https://www.revistadefrente.cl/memoria-popular/",
        "https://www.revistadefrente.cl/cultura/",
        "https://www.revistadefrente.cl/category/opinion-de-frente/",
    ]
    
    if url in urls_excluir:
        return False
    
    # Verificar que sea un artículo (tiene fecha en la URL o formato de título)
    import re
    
    # Excluir páginas que son solo mes (como /2025/12/)
    if re.match(r'https://www\.revistadefrente\.cl/\d{4}/\d{2}/$', url):
        return False
    
    # Incluir si tiene formato de artículo
    if (re.match(r'https://www\.revistadefrente\.cl/\d{4}/\d{2}/.+', url) or
        ('-' in url and url.count('-') >= 2) or
        re.search(r'/\d+$', url)):
        return True
    
    return False

def extraer_datos_noticia(driver, url):
    """
    Extrae todos los datos de una noticia individual
    Retorna: diccionario con los datos extraidos
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
                
        driver.get(url)
        time.sleep(2)
        
        # Extraer titular
        datos['titular'] = _extraer_titular(driver)

        # Extraer bajada (método mejorado del script original)
        datos['bajada'] = _extraer_bajada_original(driver)
        
        # Extraer imagen
        datos['imagen'] = _extraer_imagen(driver)
        
        # Extraer contenido
        contenido_info = _extraer_contenido(driver)
        datos['contenido'] = contenido_info['parrafos']
        
        # Extraer fecha y autor
        fecha_autor = _extraer_fecha_autor(driver)
        datos['fecha'] = fecha_autor['fecha']
        datos['autor'] = fecha_autor['autor']
        
        # Extraer categoria
        datos['categoria'] = _extraer_categoria(driver)
        
    except Exception as e:
        print(f"Error general al procesar noticia: {e}")
    
    return datos

def _extraer_titular(driver):
    """Extrae el titular de la noticia"""
    try:
        return driver.find_element(By.CSS_SELECTOR, "h2.entry-title").text.strip()
    except:
        try:
            return driver.find_element(By.TAG_NAME, "h2").text.strip()
        except:
            return "No encontrado"

def _extraer_bajada_original(driver):
    """Extrae la bajada específicamente para revistadefrente.cl - Extrae primer párrafo significativo del contenido"""
    
    # Primero intentar extraer el contenido completo
    try:
        contenido_info = _extraer_contenido(driver)
        parrafos = contenido_info['parrafos']
        
        # Buscar el primer párrafo significativo del contenido
        for parrafo in parrafos:
            texto = parrafo.strip()
            # Filtrar párrafos significativos (no demasiado cortos)
            if len(texto) > 50:  # Ajustar este valor según sea necesario
                return texto[:200] + "..." if len(texto) > 200 else texto
        
    except Exception as e:
        print(f"Error al extraer bajada del contenido: {e}")
    
    # Si no se encuentra en el contenido, intentar métodos alternativos
    try:
        # Intentar extraer el primer párrafo después del título principal
        elementos = driver.find_elements(By.XPATH, "//div[contains(@class, 'edgtf-post-text-main')]//p")
        
        for p in elementos:
            texto = p.text.strip()
            if len(texto) > 50:
                return texto[:200] + "..." if len(texto) > 200 else texto
                
    except Exception as e:
        print(f"Error en método alternativo de bajada: {e}")
    
    # Fallbacks adicionales
    fallbacks = [
        ("meta[property='og:description']", "content"),
        ("meta[name='description']", "content"),
        ("meta[name='twitter:description']", "content")
    ]
    
    for selector, attr in fallbacks:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            texto = elem.get_attribute(attr)
            if texto and len(texto.strip()) > 20:
                return texto.strip()[:200] + "..." if len(texto.strip()) > 200 else texto.strip()
        except:
            continue
    
    return "No encontrada"
                
def _extraer_imagen(driver):
    """Extrae la URL de la imagen principal"""
    try:
        # 1. Primera prioridad: meta tag og:image (Open Graph)
        return driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content")
    except:
        try:
            # 2. Segunda prioridad: wp-post-image (clase específica de WordPress)
            return driver.find_element(By.CSS_SELECTOR, ".wp-post-image").get_attribute("src")
        except:
            try:
                # 3. Tercera prioridad: img dentro del contenedor principal del post
                return driver.find_element(By.CSS_SELECTOR, ".edgtf-post-content .edgtf-post-image img").get_attribute("src")
            except:
                try:
                    # 4. Cuarta prioridad: imagen con clase size-full
                    return driver.find_element(By.CSS_SELECTOR, "img.size-full").get_attribute("src")
                except:
                    try:
                        # 5. Quinta prioridad: cualquier imagen dentro de article
                        return driver.find_element(By.CSS_SELECTOR, "article img").get_attribute("src")
                    except:
                        return ""

def _extraer_contenido(driver):
    """Extrae el contenido de la noticia"""
    parrafos = []
    total = 0
    
    try:
        contenido_div = driver.find_element(By.CSS_SELECTOR, "div.edgtf-post-text-main")
        elementos_parrafo = contenido_div.find_elements(By.TAG_NAME, "p")
        total = len(elementos_parrafo)
        
        for index, p in enumerate(elementos_parrafo):
            texto = p.text.strip()
            if texto and len(texto) > 10:
                parrafos.append(texto)
                
    except Exception as e:
        print(f"Error al extraer contenido: {e}")
    
    return {'parrafos': parrafos, 'total': total}

def _extraer_categoria(driver):
    """Extrae la categoria de la noticia"""
    try:
        return driver.find_element(By.CSS_SELECTOR, ".edgtf-post-info-category a").text
    except:
        return "."

def _extraer_fecha_autor(driver):
    """Extrae fecha y autor de la noticia"""
    fecha = "No encontrada"
    autor = "No encontrado"
    
    try:
        # Para este sitio específico, primero intentamos los selectores del tema Journo
        # 1. Autor: dentro de .edgtf-post-info-author
        autor_element = driver.find_element(By.CSS_SELECTOR, ".edgtf-post-info-author")
        # Extraemos solo el texto del enlace (nombre del autor)
        autor_link = autor_element.find_element(By.CSS_SELECTOR, "a")
        autor = autor_link.text
        
        # 2. Fecha: dentro de .edgtf-post-info-date
        fecha_element = driver.find_element(By.CSS_SELECTOR, ".edgtf-post-info-date")
        # Extraemos el texto del enlace de fecha
        fecha_link = fecha_element.find_element(By.CSS_SELECTOR, "a")
        fecha = fecha_link.text
        
    except Exception as e:
        print(f"Error al extraer fecha/autor con selectores principales: {e}")
        
        # Intentar métodos alternativos
        try:
            # Método 1: Buscar por itemprop
            autor = driver.find_element(By.CSS_SELECTOR, "[itemprop='author'] a").text
        except:
            try:
                # Método 2: Buscar por texto "Por"
                autor = driver.find_element(By.XPATH, "//div[contains(@class, 'edgtf-post-info-author')]//a").text
            except:
                pass
        
        try:
            # Método 1 para fecha: buscar por itemprop='dateCreated'
            fecha = driver.find_element(By.CSS_SELECTOR, "[itemprop='dateCreated'] a").text
        except:
            try:
                # Método 2: Buscar por clase que contenga 'date'
                fecha = driver.find_element(By.XPATH, "//div[contains(@class, 'edgtf-post-info-date')]//a").text
            except:
                try:
                    # Método 3: Buscar en meta tags
                    fecha = driver.find_element(By.CSS_SELECTOR, "meta[property='article:published_time']").get_attribute("content")
                except:
                    pass
    
    return {'fecha': fecha, 'autor': autor}

def guardar_en_db(datos):
    """Guardar datos en la base de datos"""
    try:
        # Verificar si ya existe
        if Article.objects.filter(url=datos['url']).exists():
            print(f"Ya existe: {datos['titular'][:50]}...")
            return False
        
        # Convertir contenido de lista a string separado por doble salto de línea
        contenido_texto = '\n\n'.join(datos['contenido'])
        
        # Crear nuevo artículo
        articulo = Article.objects.create(
            url=datos['url'],
            title=datos['titular'],
            subtitle=datos['bajada'],
            image_url=datos['imagen'],
            content=contenido_texto,
            publication_date=datos['fecha'],
            author=datos['autor'],
            category=datos['categoria']
        )
        
        print(f"Guardado: {articulo.title[:60]}...")
        return True
        
    except Exception as e:
        print(f"Error guardando en DB: {e}")
        return False

def ejecutar_scraping(max_noticias=10):
    """Función principal de scraping"""
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE REVISTADEFRENTE.CL")
        print("="*80)
        
        # Configurar driver
        driver = configurar_driver()
        
        # Extraer URLs DE LAS MISMAS SECCIONES QUE EL SCRIPT ORIGINAL
        urls = extraer_urls_secciones(driver)
        
        if not urls:
            print("No se encontraron URLs de noticias")
            return 0
        
        print(f"\nProcesando las primeras {min(max_noticias, len(urls))} noticias...")
        
        # Procesar cada URL
        for i, url in enumerate(urls[:max_noticias], 1):
            print(f"\n[{i}/{min(max_noticias, len(urls))}]")
            
            # Extraer datos
            datos = extraer_datos_noticia(driver, url)
            
            # Guardar en DB si tiene contenido
            if datos['contenido']:
                if guardar_en_db(datos):
                    articulos_procesados += 1
            else:
                print(f"Sin contenido: {datos['titular'][:50]}...")
            
            # Pausa para no sobrecargar
            if i < min(max_noticias, len(urls)):
                time.sleep(1)
        
        return articulos_procesados
        
    except Exception as e:
        print(f"\nError general en scraping: {e}")
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
    print(f"{'='*80}")

if __name__ == "__main__":
    # Ejecutar desde línea de comandos
    '''
    cantidad = ejecutar_scraping(max_noticias=10)
    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETADO")
    print(f"Artículos procesados: {cantidad}")
    
    # Mostrar estadísticas
    from news.models import Article
    total = Article.objects.count()
    print(f"Total en base de datos: {total}")
    print(f"{'='*80}")
    '''
    run()