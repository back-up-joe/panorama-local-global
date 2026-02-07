import sys
import os
import time
import django
from datetime import datetime, date
import re

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraper.settings')
django.setup()

from news.models import Article
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

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
    Extrae URLs de noticias de las secciones de elciudadano.com
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias en elciudadano.com...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal de Chile
        driver.get("https://www.elciudadano.com/chile/")
        time.sleep(3)
        
        # Buscar en la sección principal (front-main)
        print("\nBuscando en la sección principal...")
        try:
            front_main = driver.find_element(By.ID, "front-main")
            enlaces = front_main.find_elements(By.TAG_NAME, "a")
            
            for enlace in enlaces:
                try:
                    href = enlace.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en sección principal: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  No se pudo acceder a front-main: {e}")
        
        # Buscar en las noticias anteriores (front-last)
        print("\nBuscando en noticias anteriores...")
        try:
            front_last = driver.find_element(By.ID, "front-last")
            enlaces = front_last.find_elements(By.TAG_NAME, "a")
            
            for enlace in enlaces:
                try:
                    href = enlace.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en noticias anteriores: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  No se pudo acceder a front-last: {e}")
        
        # Buscar en destacados (front-specials)
        print("\nBuscando en destacados...")
        try:
            front_specials = driver.find_element(By.ID, "front-specials")
            enlaces = front_specials.find_elements(By.TAG_NAME, "a")
            
            for enlace in enlaces:
                try:
                    href = enlace.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en destacados: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  No se pudo acceder a front-specials: {e}")
        
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
    Valida si una URL es una noticia válida para elciudadano.com
    Retorna: True si es válida, False en caso contrario
    """
    if not href:
        return False
    
    # Patrón específico para noticias de elciudadano.com
    patron_noticia = r'https://www\.elciudadano\.com/[^/]+/[^/]+/[0-9]{2}/[0-9]{2}/'
    
    condiciones = [
        href.startswith("https://www.elciudadano.com/"),
        bool(re.match(patron_noticia, href)),
        not href.endswith((".jpg", ".png", ".gif", ".jpeg")),
        not "category" in href,
        not "tag" in href,
        not "author" in href,
        not "page" in href,
        not "search" in href,
        href != "https://www.elciudadano.com/",
        href not in urls_existentes
    ]
    
    return all(condiciones)

def extraer_datos_noticia(driver, url):
    """
    Extrae todos los datos de una noticia individual
    Retorna: diccionario con los datos extraídos
    """
    datos = {
        'url': url,
        'titular': 'No encontrado',
        'bajada': 'No encontrada',
        'imagen': 'No encontrada',
        'contenido': [],
        'fecha': None,
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
        
        # Extraer imagen (función mejorada)
        datos['imagen'] = _extraer_imagen_mejorada(driver)
        
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
        # Intentar con el selector específico de elciudadano
        return driver.find_element(By.CSS_SELECTOR, "h1.mb-4").text.strip()
    except:
        try:
            return driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            return "No encontrado"

def _extraer_bajada(driver):
    """Extrae la bajada/resumen de la noticia"""
    try:
        # Buscar el excerpt del título del artículo
        return driver.find_element(By.CSS_SELECTOR, "p.article-title-excerpt").text.strip()
    except:
        try:
            # Buscar meta description
            return driver.find_element(By.CSS_SELECTOR, "meta[name='description']").get_attribute("content").strip()
        except:
            try:
                # Buscar el primer párrafo del contenido
                primer_parrafo = driver.find_element(By.CSS_SELECTOR, ".content-body p").text.strip()
                if primer_parrafo and len(primer_parrafo) > 30:
                    return primer_parrafo
            except:
                return "No encontrada"
    
    return "No encontrada"

def _extraer_imagen_mejorada(driver):
    """Extrae la URL de la imagen principal - VERSIÓN MEJORADA"""
    try:
        # ESTRATEGIA 1: Buscar imágenes con srcset (elciudadano.com usa esto)
        imagenes = driver.find_elements(By.CSS_SELECTOR, "img[srcset]")
        for img in imagenes:
            try:
                srcset = img.get_attribute("srcset")
                if srcset:
                    # Tomar la primera imagen del srcset (generalmente la más grande)
                    urls = [url.strip() for url in srcset.split(',')]
                    for url_item in urls:
                        # Separar URL y tamaño (ej: "https://... 640w")
                        parts = url_item.strip().split()
                        if len(parts) >= 1:
                            img_url = parts[0]
                            # Verificar que sea una URL de imagen válida
                            if img_url and img_url.startswith('http'):
                                # Preferir imágenes más grandes (que contengan '1024w' o '800w')
                                if len(parts) > 1 and any(size in parts[1] for size in ['1024w', '800w', '640w']):
                                    print(f"  Imagen encontrada en srcset: {img_url[:80]}...")
                                    return img_url
                                elif len(parts) == 1:
                                    # Si no tiene tamaño especificado, usar igualmente
                                    print(f"  Imagen encontrada en srcset (sin tamaño): {img_url[:80]}...")
                                    return img_url
            except:
                continue
        
        # ESTRATEGIA 2: Buscar en el div de imagen del artículo
        try:
            img_div = driver.find_element(By.ID, "article-picture")
            img = img_div.find_element(By.TAG_NAME, "img")
            srcset = img.get_attribute("srcset")
            if srcset:
                urls = [url.strip() for url in srcset.split(',')]
                if urls:
                    parts = urls[0].strip().split()
                    if parts:
                        img_url = parts[0]
                        print(f"  Imagen del artículo: {img_url[:80]}...")
                        return img_url
            # Si tiene src normal
            src = img.get_attribute("src")
            if src and src.startswith('http'):
                print(f"  Imagen del artículo (src): {src[:80]}...")
                return src
        except:
            pass
        
        # ESTRATEGIA 3: Buscar og:image
        try:
            og_image = driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content")
            if og_image and og_image.startswith('http'):
                print(f"  OG Image: {og_image[:80]}...")
                return og_image
        except:
            pass
        
        # ESTRATEGIA 4: Buscar cualquier imagen con clase wp-post-image
        try:
            imgs = driver.find_elements(By.CSS_SELECTOR, ".wp-post-image")
            for img in imgs:
                srcset = img.get_attribute("srcset")
                if srcset:
                    urls = [url.strip() for url in srcset.split(',')]
                    if urls:
                        parts = urls[0].strip().split()
                        if parts:
                            img_url = parts[0]
                            print(f"  wp-post-image: {img_url[:80]}...")
                            return img_url
                src = img.get_attribute("src")
                if src and src.startswith('http'):
                    print(f"  wp-post-image (src): {src[:80]}...")
                    return src
        except:
            pass
        
        # ESTRATEGIA 5: Buscar la primera imagen en el contenido
        try:
            img = driver.find_element(By.CSS_SELECTOR, ".content-body img")
            srcset = img.get_attribute("srcset")
            if srcset:
                urls = [url.strip() for url in srcset.split(',')]
                if urls:
                    parts = urls[0].strip().split()
                    if parts:
                        img_url = parts[0]
                        print(f"  Imagen en contenido: {img_url[:80]}...")
                        return img_url
            src = img.get_attribute("src")
            if src and src.startswith('http'):
                print(f"  Imagen en contenido (src): {src[:80]}...")
                return src
        except:
            pass
        
        # ESTRATEGIA 6: Buscar cualquier imagen
        try:
            imgs = driver.find_elements(By.TAG_NAME, "img")
            for img in imgs:
                srcset = img.get_attribute("srcset")
                if srcset:
                    # Buscar la imagen más grande
                    urls = [url.strip() for url in srcset.split(',')]
                    for url_item in urls:
                        parts = url_item.strip().split()
                        if len(parts) >= 1:
                            img_url = parts[0]
                            if img_url and img_url.startswith('http') and 'elciudadano.com' in img_url:
                                print(f"  Imagen genérica: {img_url[:80]}...")
                                return img_url
                src = img.get_attribute("src")
                if src and src.startswith('http') and 'elciudadano.com' in src:
                    print(f"  Imagen genérica (src): {src[:80]}...")
                    return src
        except:
            pass
        
        print("  No se encontró imagen válida")
        return ""
        
    except Exception as e:
        print(f"Error al extraer imagen: {e}")
        return ""

def _extraer_contenido(driver):
    """Extrae el contenido de la noticia"""
    parrafos = []
    total = 0
    
    try:
        # Buscar el contenido del artículo
        contenido_div = driver.find_element(By.CSS_SELECTOR, "div.content-body")
        elementos_parrafo = contenido_div.find_elements(By.TAG_NAME, "p")
        total = len(elementos_parrafo)
        
        for index, p in enumerate(elementos_parrafo):
            texto = p.text.strip()
            # Filtrar párrafos significativos
            if texto and len(texto) > 10 and not texto.startswith(("Comparte esto:", "Enviar un enlace")):
                parrafos.append(texto)
                
    except Exception as e:
        print(f"Error al extraer contenido: {e}")
    
    return {'parrafos': parrafos, 'total': total}

def _extraer_categoria(driver):
    """Extrae la categoría de la noticia"""
    try:
        # Buscar en la lista de categorías del artículo
        categorias = driver.find_elements(By.CSS_SELECTOR, "#article-categories-list a")
        if categorias:
            # Tomar la primera categoría (generalmente la principal)
            return categorias[0].text.strip()
    except:
        pass
    
    return "."

# Diccionario de meses en español
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

def _parsear_fecha(fecha_str):
    """Convierte una fecha en string a objeto date"""
    if not fecha_str:
        return None
    
    fecha_str = fecha_str.strip().lower()
    
    # Formato: 05/02/2026 1:17pm
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})', fecha_str)
    if match:
        try:
            dia, mes, anio = map(int, match.groups())
            return date(anio, mes, dia)
        except ValueError:
            pass
    
    # Formato: febrero 5, 2026
    for mes_nombre, mes_num in MESES_ES.items():
        if mes_nombre in fecha_str:
            match = re.search(r'(\d{1,2}),\s*(\d{4})', fecha_str)
            if match:
                try:
                    dia, anio = map(int, match.groups())
                    return date(anio, mes_num, dia)
                except ValueError:
                    pass
    
    return None

def _extraer_fecha_autor(driver):
    """Extrae fecha y autor de la noticia"""
    fecha = None
    autor = "No encontrado"
    
    try:
        # Buscar en el meta del artículo
        meta_div = driver.find_element(By.ID, "article-meta-author")
        
        # Extraer autor
        try:
            autor_element = meta_div.find_element(By.CSS_SELECTOR, "a[itemprop='autor']")
            autor = autor_element.text.strip()
        except:
            try:
                autor_element = meta_div.find_element(By.TAG_NAME, "strong")
                autor = autor_element.text.strip()
            except:
                pass
        
        # Extraer fecha
        try:
            time_element = meta_div.find_element(By.TAG_NAME, "time")
            fecha_raw = time_element.text.strip()
            fecha = _parsear_fecha(fecha_raw)
        except:
            try:
                # Intentar extraer del atributo datetime
                time_element = meta_div.find_element(By.TAG_NAME, "time")
                fecha_raw = time_element.get_attribute("datetime")
                if fecha_raw:
                    # Formato: 2026-02-05T13:17:56-03:00
                    try:
                        fecha_obj = datetime.fromisoformat(fecha_raw.replace('Z', '+00:00'))
                        fecha = fecha_obj.date()
                    except:
                        fecha = _parsear_fecha(fecha_raw)
            except:
                pass
                
    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
        
        # Intentar alternativas
        try:
            # Buscar en los meta tags
            fecha_raw = driver.find_element(By.CSS_SELECTOR, "meta[property='article:published_time']").get_attribute("content")
            if fecha_raw:
                try:
                    fecha_obj = datetime.fromisoformat(fecha_raw.replace('Z', '+00:00'))
                    fecha = fecha_obj.date()
                except:
                    fecha = _parsear_fecha(fecha_raw)
        except:
            pass
        
        try:
            autor = driver.find_element(By.CSS_SELECTOR, "meta[name='author']").get_attribute("content")
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
        print(f"  Imagen URL: {datos['imagen'][:80]}...")
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
        print("SCRAPING DE ELCIUDADANO.COM")
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
            print(f"\n[{i}/{min(max_noticias, len(urls))}] Procesando: {url[:80]}...")
            
            # Extraer datos
            datos = extraer_datos_noticia(driver, url)
            
            # Mostrar información extraída
            print(f"  Titular: {datos['titular'][:70]}...")
            print(f"  Bajada: {datos['bajada'][:70]}...")
            print(f"  Autor: {datos['autor']}")
            print(f"  Fecha: {datos['fecha']}")
            print(f"  Categoría: {datos['categoria']}")
            print(f"  Párrafos: {len(datos['contenido'])}")
            
            # Guardar en DB si tiene contenido
            if datos['contenido']:
                if guardar_en_db(datos):
                    articulos_procesados += 1
            else:
                print(f"  Sin contenido suficiente")
            
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
    """Función principal para ejecutar desde Django"""
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
    cantidad = ejecutar_scraping(max_noticias=10)
    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETADO")
    print(f"Artículos procesados: {cantidad}")
    
    # Mostrar estadísticas
    total = Article.objects.count()
    print(f"Total en base de datos: {total}")
    print(f"{'='*80}")