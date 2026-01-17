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
    Extrae URLs de noticias de radionuevomundo.cl
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias en radionuevomundo.cl...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal
        driver.get("https://radionuevomundo.cl/")
        time.sleep(3)
        
        # Estrategia 1: Buscar enlaces en módulos de noticias (td_module_wrap)
        print("\nBuscando en módulos de noticias...")
        try:
            modulos = driver.find_elements(By.CSS_SELECTOR, "div.td_module_wrap")
            for modulo in modulos:
                try:
                    enlace = modulo.find_element(By.CSS_SELECTOR, "h3.entry-title a")
                    href = enlace.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  No se pudo acceder a módulos de noticias: {e}")
        
        # Estrategia 2: Buscar enlaces en sección de noticias principales
        print("\nBuscando en sección de noticias principales...")
        try:
            noticias_principales = driver.find_elements(By.CSS_SELECTOR, "div.td-module-container a.td-image-wrap")
            for noticia in noticias_principales:
                try:
                    href = noticia.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en principal: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  No se pudo acceder a noticias principales: {e}")
        
        # Estrategia 3: Buscar enlaces en el bloque de contenido
        print("\nBuscando en bloque de contenido...")
        try:
            enlaces_noticias = driver.find_elements(By.CSS_SELECTOR, "a[href*='https://radionuevomundo.cl/']")
            for enlace in enlaces_noticias:
                try:
                    href = enlace.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                except:
                    continue
        except Exception as e:
            print(f"  Error en búsqueda general: {e}")
        
        # Eliminar duplicados manteniendo el orden
        urls_noticias = list(dict.fromkeys(urls_noticias))
        
        print(f"\nTotal de URLs encontradas: {len(urls_noticias)}")
        
        # Mostrar las URLs encontradas
        if urls_noticias:
            print("\nURLs encontradas:")
            for i, url in enumerate(urls_noticias, 1):
                print(f"{i}. {url}")
        
    except Exception as e:
        print(f"Error al buscar enlaces: {e}")
    
    return urls_noticias

def _es_url_noticia_valida(href, urls_existentes):
    """
    Valida si una URL es una noticia válida para radionuevomundo.cl
    Retorna: True si es válida, False en caso contrario
    """
    if not href:
        return False
    
    # Filtros específicos para radionuevomundo.cl
    condiciones = [
        href.startswith("https://radionuevomundo.cl/"),
        not href.endswith((".jpg", ".png", ".gif", ".webp")),
        not "category" in href,
        not "categoria" in href,
        not "tag" in href,
        not "author" in href,
        not "page" in href,
        not "wp-admin" in href,
        not "wp-content" in href,
        not "wp-json" in href,
        not "xmlrpc.php" in href,
        not "feed" in href,
        not "comments" in href,
        href != "https://radionuevomundo.cl/",
        href != "https://radionuevomundo.cl/#",
        href not in urls_existentes,
        "/202" in href,  # Asegura que sea una noticia con fecha (ej: /2026/01/)
    ]
    
    return all(condiciones)

def extraer_datos_noticia(driver, url):
    """
    Extrae todos los datos de una noticia individual de radionuevomundo.cl
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
        driver.get(url)
        time.sleep(2)
        
        # Extraer titular
        datos['titular'] = _extraer_titular(driver)
        
        # Extraer bajada
        datos['bajada'] = _extraer_bajada(driver)
        
        # Extraer imagen
        datos['imagen'] = _extraer_imagen(driver)
        
        # Extraer contenido
        contenido_info = _extraer_contenido(driver)
        datos['contenido'] = contenido_info['parrafos']
        
        # Extraer fecha y autor
        fecha_autor = _extraer_fecha_autor(driver)
        datos['fecha'] = fecha_autor['fecha']
        datos['autor'] = fecha_autor['autor']
        
        # Extraer categoría
        datos['categoria'] = _extraer_categoria(driver)
        
    except Exception as e:
        print(f"Error general al procesar noticia: {e}")
    
    return datos

def _extraer_titular(driver):
    """Extrae el titular de la noticia"""
    try:
        return driver.find_element(By.CSS_SELECTOR, "h1.tdb-title-text").text.strip()
    except:
        try:
            return driver.find_element(By.CSS_SELECTOR, "h1.entry-title").text.strip()
        except:
            try:
                return driver.find_element(By.TAG_NAME, "h1").text.strip()
            except:
                return "No encontrado"

def _extraer_bajada(driver):
    """Extrae la bajada de radionuevomundo.cl"""
    try:
        # Buscar en meta description
        fallbacks = [
            ("meta[name='description']", "content"),
            ("meta[property='og:description']", "content"),
            ("meta[name='twitter:description']", "content")
        ]
        
        for selector, attr in fallbacks:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, selector)
                texto = elem.get_attribute(attr)
                if texto and len(texto.strip()) > 20:
                    return texto.strip()
            except:
                continue
    except Exception as e:
        print(f"Error en estrategia principal de bajada: {e}")
    
    return "No encontrada"

def _extraer_imagen(driver):
    """Extrae la URL de la imagen principal"""
    try:
        return driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content")
    except:
        try:
            return driver.find_element(By.CSS_SELECTOR, "img.tdb-featured-image").get_attribute("src")
        except:
            try:
                return driver.find_element(By.CSS_SELECTOR, "img.wp-post-image").get_attribute("src")
            except:
                try:
                    return driver.find_element(By.CSS_SELECTOR, "img.size-full").get_attribute("src")
                except:
                    try:
                        return driver.find_element(By.CSS_SELECTOR, "article img").get_attribute("src")
                    except:
                        return ""

def _extraer_contenido(driver):
    """Extrae el contenido de la noticia"""
    parrafos = []
    total = 0
    
    try:
        # Buscar contenido en diferentes selectores posibles
        selectores_contenido = [
            "div.tdb-block-inner",
            "div.td-post-content",
            "div.entry-content",
            "article"
        ]
        
        for selector in selectores_contenido:
            try:
                contenido_div = driver.find_element(By.CSS_SELECTOR, selector)
                elementos_parrafo = contenido_div.find_elements(By.TAG_NAME, "p")
                total = len(elementos_parrafo)
                
                if total > 0:
                    for index, p in enumerate(elementos_parrafo):
                        texto = p.text.strip()
                        if texto and len(texto) > 10:
                            parrafos.append(texto)
                    break
            except:
                continue
                
    except Exception as e:
        print(f"Error al extraer contenido: {e}")
    
    return {'parrafos': parrafos, 'total': total}

def _extraer_categoria(driver):
    """Extrae la categoría de la noticia"""
    try:
        return driver.find_element(By.CSS_SELECTOR, "span.td-post-category").text
    except:
        try:
            return driver.find_element(By.CSS_SELECTOR, "a.td-post-category").text
        except:
            return "."

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

    # 1. Primero intentar formato ISO (nuevo)
    # Ejemplo: "2026-01-17T17:27:02-03:00" o "2026-01-17"
    try:
        # Asegurarnos de que Z sea reemplazado por +00:00 para compatibilidad
        fecha_iso = fecha_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(fecha_iso)
        return dt.date()
    except ValueError:
        pass

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
def _extraer_fecha_autor(driver):
    """Extrae fecha y autor de la noticia para radionuevomundo.cl"""
    fecha = None
    autor = "Radio Nuevo Mundo"

    try:
        # Buscar fecha en el atributo datetime del elemento time
        try:
            fecha_raw = driver.find_element(
                By.CSS_SELECTOR, "time.entry-date.updated.td-module-date"
            ).get_attribute("datetime")
        except:
            fecha_raw = None

        # Buscar autor
        '''
'''
        try:
            autor = driver.find_element(
                By.CSS_SELECTOR, "span.td-post-author-name a"
            ).text
        except:
            try:
                autor = driver.find_element(
                    By.CSS_SELECTOR, "div.td-post-author-name a"
                ).text
            except:
                autor = "No encontrado" '''
'''
    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")

    fecha = _parsear_fecha(fecha_raw)

    return {
        "fecha": fecha,  # datetime.date | None
        "autor": autor
    }'''

def _extraer_fecha_autor(driver):
    """Extrae fecha y autor de la noticia para radionuevomundo.cl"""
    fecha = None
    autor = "Radio Nuevo Mundo"

    try:
        # Buscar fecha en el meta tag article:published_time
        try:
            fecha_raw = driver.find_element(
                By.CSS_SELECTOR, "meta[property='article:published_time']"
            ).get_attribute("content")
        except:
            fecha_raw = None

        # Si no funciona, intentar con article:modified_time
        if not fecha_raw:
            try:
                fecha_raw = driver.find_element(
                    By.CSS_SELECTOR, "meta[property='article:modified_time']"
                ).get_attribute("content")
            except:
                fecha_raw = None

        '''
        # Buscar autor (manteniendo tu lógica original, pero sin comentarios)
        try:
            autor = driver.find_element(
                By.CSS_SELECTOR, "span.td-post-author-name a"
            ).text
        except:
            try:
                autor = driver.find_element(
                    By.CSS_SELECTOR, "div.td-post-author-name a"
                ).text
            except:
                autor = "Radio Nuevo Mundo" '''

    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")

    fecha = _parsear_fecha(fecha_raw) if fecha_raw else None

    return {
        "fecha": fecha,  # datetime.date | None
        "autor": autor
    }

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
    """Función principal de scraping para radionuevomundo.cl"""
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE RADIONUEVOMUNDO.CL")
        print("="*80)
        
        # Configurar driver
        driver = configurar_driver()
        
        # Extraer URLs
        urls = extraer_urls_secciones(driver)
        
        if not urls:
            print("No se encontraron URLs de noticias")
            return 0
        
        print(f"\nProcesando las primeras {min(max_noticias, len(urls))} noticias...")
        
        # Procesar cada URL
        for i, url in enumerate(urls[:max_noticias], 1):
            print(f"\n[{i}/{min(max_noticias, len(urls))}] Procesando: {url[:70]}...")
            
            # Extraer datos
            datos = extraer_datos_noticia(driver, url)
            
            # Mostrar datos extraídos
            print(f"  Titular: {datos['titular'][:50]}...")
            print(f"  Contenido: {len(datos['contenido'])} párrafos")
            
            # Guardar en DB si tiene contenido
            if datos['contenido']:
                if guardar_en_db(datos):
                    articulos_procesados += 1
            else:
                print(f"  Sin contenido: {datos['titular'][:50]}...")
            
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
    """Función para ejecutar desde Django"""
    cantidad = ejecutar_scraping(max_noticias=10)
    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETADO")
    print(f"Artículos procesados: {cantidad}")
    
    # Mostrar estadísticas
    total = Article.objects.count()
    print(f"Total en base de datos: {total}")
    print(f"{'='*80}")

if __name__ == "__main__":
    # Ejecutar desde línea de comandos
    run()