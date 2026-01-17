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
    Extrae URLs de noticias de las secciones especificadas (igual que el script original)
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias en las secciones especificadas...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal
        driver.get("https://elsiglo.cl/")
        time.sleep(3)
        
        # Buscar en featured-section
        print("\nBuscando en 'featured-section'...")
        try:
            featured_section = driver.find_element(By.CSS_SELECTOR, "section.featured-section")
            enlaces_featured = featured_section.find_elements(By.CSS_SELECTOR, "a[href*='https://elsiglo.cl/']")
            
            for enlace in enlaces_featured:
                try:
                    href = enlace.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en featured-section: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  No se pudo acceder a featured-section: {e}")
        
        # Buscar en site-content pt-0
        print("\nBuscando en 'site-content pt-0'...")
        try:
            site_content = driver.find_element(By.CSS_SELECTOR, "div.site-content.pt-0")
            enlaces_content = site_content.find_elements(By.CSS_SELECTOR, "a[href*='https://elsiglo.cl/']")
            
            for enlace in enlaces_content:
                try:
                    href = enlace.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"Encontrado en site-content: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"No se pudo acceder a site-content pt-0: {e}")
        
        # Eliminar duplicados manteniendo el orden
        urls_noticias = list(dict.fromkeys(urls_noticias))
        
        print(f"\nTotal de URLs encontradas en las secciones especificas: {len(urls_noticias)}")
        
        # Mostrar las URLs encontradas
        if urls_noticias:
            print("\nURLs encontradas:")
            for i, url in enumerate(urls_noticias, 1):
                print(f"{i}. {url}")
        
    except Exception as e:
        print(f"Error al buscar enlaces en secciones especificas: {e}")
    
    return urls_noticias

def _es_url_noticia_valida(href, urls_existentes):
    """
    Valida si una URL es una noticia valida (igual que el script original)
    Retorna: True si es valida, False en caso contrario
    """
    if not href:
        return False
    
    condiciones = [
        href.startswith("https://elsiglo.cl/"),
        not href.endswith((".jpg", ".png", ".gif")),
        not "category" in href,
        not "tag" in href,
        not "author" in href,
        not "page" in href,
        href != "https://elsiglo.cl/",
        href not in urls_existentes
    ]
    
    return all(condiciones)

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
        return driver.find_element(By.CSS_SELECTOR, "h1.entry-title").text.strip()
    except:
        try:
            return driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            return "No encontrado"

def _extraer_bajada_original(driver):
    """Extrae la bajada específicamente para elsiglo.cl (igual que el script original)"""
    try:
        # Buscar el primer <p> dentro de un <blockquote> dentro de entry-content
        entry_content = driver.find_element(By.CLASS_NAME, "entry-content")
        
        # Estrategia 1: Buscar blockquote que contiene la bajada
        blockquotes = entry_content.find_elements(By.TAG_NAME, "blockquote")
        
        for blockquote in blockquotes:
            # Buscar párrafos dentro del blockquote
            parrafos = blockquote.find_elements(By.TAG_NAME, "p")
            for p in parrafos:
                texto = p.text.strip()
                # Filtrar texto significativo
                if len(texto) > 100:
                    return texto
        
        # Estrategia 2: Si no hay blockquote, buscar el primer párrafo después de los divs sociales
        divs_sociales = entry_content.find_elements(By.CSS_SELECTOR, "div.heateor_sss_sharing_container, div.social-share")
        
        if divs_sociales:
            # Encontrar el primer elemento después del último div social
            all_elements = entry_content.find_elements(By.XPATH, "./*")
            last_social_index = -1
            
            for i, elem in enumerate(all_elements):
                if any(cls in elem.get_attribute("class") for cls in ["heateor", "social"]):
                    last_social_index = i
            
            if last_social_index != -1 and last_social_index + 1 < len(all_elements):
                # Buscar el primer párrafo después del div social
                for i in range(last_social_index + 1, len(all_elements)):
                    elem = all_elements[i]
                    if elem.tag_name == "p":
                        texto = elem.text.strip()
                        if len(texto) > 30:
                            return texto
    
    except Exception as e:
        print(f"Error en estrategia principal de bajada: {e}")
    
    # Fallbacks
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
    
    return "No encontrada"

def _extraer_imagen(driver):
    """Extrae la URL de la imagen principal"""
    try:
        return driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content")
    except:
        try:
            return driver.find_element(By.CSS_SELECTOR, ".wp-post-image").get_attribute("src")
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
        contenido_div = driver.find_element(By.CSS_SELECTOR, "div.entry-content")
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
        return driver.find_element(By.CSS_SELECTOR, ".cat-links a").text
    except:
        return "."

'''
def _extraer_fecha_autor(driver):
    """Extrae fecha y autor de la noticia"""
    fecha = "No encontrada"
    autor = "No encontrado"
    
    try:
        # Selectores más específicos para evitar conflictos
        fecha = driver.find_element(By.CSS_SELECTOR, "header.entry-header .date a").text
        autor = driver.find_element(By.CSS_SELECTOR, "header.entry-header .by-author a").text
    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
        # Intentar otros selectores si los principales fallan
        try:
            fecha = driver.find_element(By.CSS_SELECTOR, ".entry-meta .date a").text
        except:
            pass
        
        try:
            autor = driver.find_element(By.CSS_SELECTOR, ".entry-meta .by-author a").text
        except:
            pass
    
    return {'fecha': fecha, 'autor': autor} '''

###################################################################################################################################

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

def _extraer_fecha_autor(driver):
    """Extrae fecha y autor de la noticia"""
    fecha = None
    autor = "No encontrado"

    try:
        fecha_raw = driver.find_element(
            By.CSS_SELECTOR, "header.entry-header .date a"
        ).text
        autor = driver.find_element(
            By.CSS_SELECTOR, "header.entry-header .by-author a"
        ).text
    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
        try:
            fecha_raw = driver.find_element(
                By.CSS_SELECTOR, ".entry-meta .date a"
            ).text
        except:
            fecha_raw = None

        try:
            autor = driver.find_element(
                By.CSS_SELECTOR, ".entry-meta .by-author a"
            ).text
        except:
            pass

    fecha = _parsear_fecha(fecha_raw)

    return {
        "fecha": fecha,  # datetime.date | None
        "autor": autor
    }


##################################################################################################################################

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
        print("SCRAPING DE ELSIGLO.CL")
        print("="*80)
        
        # Configurar driver
        driver = configurar_driver()
        
        # Extraer URLs DE LAS MISMAS SECCIONES QUE EL SCRIPT ORIGINAL
        urls = extraer_urls_secciones(driver)
        
        if not urls:
            print("No se encontraron URLs de noticias en las secciones especificadas")
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