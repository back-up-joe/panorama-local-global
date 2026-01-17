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
    Extrae URLs de noticias de eldespertar.cl
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias en eldespertar.cl...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal
        driver.get("https://www.eldespertar.cl/")
        time.sleep(3)
        
        # Buscar en el grid principal (col-lg-8)
        print("\nBuscando en el grid principal...")
        try:
            # Buscar enlaces en las tarjetas de noticias del grid principal
            tarjetas = driver.find_elements(By.CSS_SELECTOR, ".col-lg-8 .bs-blog-post.grid-card a.link-div")
            
            for tarjeta in tarjetas:
                try:
                    href = tarjeta.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en grid principal: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  Error en grid principal: {e}")
        
        # Buscar en el carrusel de noticias destacadas
        print("\nBuscando en noticias destacadas...")
        try:
            # Buscar en el swiper-wrapper de noticias destacadas
            slides = driver.find_elements(By.CSS_SELECTOR, ".crousel-widget .swiper-slide a.link-div")
            
            for slide in slides:
                try:
                    href = slide.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en destacadas: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  Error en destacadas: {e}")
        
        # Buscar en sección principal (homemain)
        print("\nBuscando en sección principal...")
        try:
            main_slides = driver.find_elements(By.CSS_SELECTOR, ".homemain .swiper-slide a.link-div")
            
            for slide in main_slides:
                try:
                    href = slide.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en sección principal: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  Error en sección principal: {e}")
        
        # Buscar en la lista de últimas noticias
        print("\nBuscando en últimas noticias...")
        try:
            ultimas = driver.find_elements(By.CSS_SELECTOR, ".bs-recent-blog-post.six .small-post h5.title a")
            
            for noticia in ultimas:
                try:
                    href = noticia.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en últimas: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  Error en últimas noticias: {e}")
        
        # Eliminar duplicados manteniendo el orden
        urls_noticias = list(dict.fromkeys(urls_noticias))
        
        print(f"\nTotal de URLs encontradas: {len(urls_noticias)}")
        
        # Mostrar las URLs encontradas
        if urls_noticias:
            print("\nURLs encontradas:")
            for i, url in enumerate(urls_noticias, 1):
                print(f"{i}. {url}")
        
    except Exception as e:
        print(f"Error al buscar enlaces en eldespertar.cl: {e}")
    
    return urls_noticias

def _es_url_noticia_valida(href, urls_existentes):
    """
    Valida si una URL es una noticia valida para eldespertar.cl
    Retorna: True si es valida, False en caso contrario
    """
    if not href:
        return False
    
    # Patrones específicos de eldespertar.cl
    condiciones = [
        href.startswith("https://www.eldespertar.cl/"),
        "/category/" not in href,
        "/tag/" not in href,
        "/author/" not in href,
        "/page/" not in href,
        "/feed/" not in href,
        "/wp-json/" not in href,
        "/wp-admin/" not in href,
        "/?s=" not in href,
        href != "https://www.eldespertar.cl/",
        href not in urls_existentes,
        any(x in href for x in ["/2026/", "/2025/", "/2024/"])  # URLs que contienen año
    ]
    
    return all(condiciones)

def extraer_datos_noticia(driver, url):
    """
    Extrae todos los datos de una noticia individual de eldespertar.cl
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
        datos['titular'] = _extraer_titular_eldespertar(driver)
        
        # Extraer bajada
        datos['bajada'] = _extraer_bajada_eldespertar(driver)
        
        # Extraer imagen
        datos['imagen'] = _extraer_imagen_eldespertar(driver)
        
        # Extraer contenido
        contenido_info = _extraer_contenido_eldespertar(driver)
        datos['contenido'] = contenido_info['parrafos']
        
        # Extraer fecha y autor
        fecha_autor = _extraer_fecha_autor_eldespertar(driver)
        datos['fecha'] = fecha_autor['fecha']
        datos['autor'] = fecha_autor['autor']
        
        # Extraer categoria
        datos['categoria'] = _extraer_categoria_eldespertar(driver)
        
    except Exception as e:
        print(f"Error general al procesar noticia: {e}")
    
    return datos

def _extraer_titular_eldespertar(driver):
    """Extrae el titular de la noticia en eldespertar.cl"""
    try:
        return driver.find_element(By.CSS_SELECTOR, "h1.title").text.strip()
    except:
        try:
            return driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            try:
                return driver.find_element(By.CSS_SELECTOR, ".bs-header .title").text.strip()
            except:
                return "No encontrado"

def _extraer_bajada_eldespertar(driver):
    """Extrae la bajada específicamente para eldespertar.cl"""
    try:
        # Buscar el primer h2 con texto centrado (que suele ser la bajada)
        bajada_elem = driver.find_element(By.CSS_SELECTOR, "h2.wp-block-heading.has-text-align-center")
        return bajada_elem.text.strip()
    except:
        # Fallback: buscar meta descripción
        try:
            return driver.find_element(By.CSS_SELECTOR, "meta[property='og:description']").get_attribute("content")
        except:
            try:
                return driver.find_element(By.CSS_SELECTOR, "meta[name='description']").get_attribute("content")
            except:
                return "No encontrada"

def _extraer_imagen_eldespertar(driver):
    """Extrae la URL de la imagen principal en eldespertar.cl - Versión con debug"""
    try:
        print("=== DEBUG: Buscando imagen ===")
        
        # 1. Ver meta tags
        try:
            metas = driver.find_elements(By.CSS_SELECTOR, "meta[property='og:image'], meta[name='twitter:image']")
            for meta in metas:
                url = meta.get_attribute("content")
                print(f"Meta tag encontrado: {url}")
                if url and url.startswith("http"):
                    return url
        except Exception as e:
            print(f"Error en meta tags: {e}")
        
        # 2. Ver todas las imágenes en bs-blog-thumb
        try:
            thumb_divs = driver.find_elements(By.CSS_SELECTOR, ".bs-blog-thumb, div.bs-blog-thumb")
            print(f"Divs bs-blog-thumb encontrados: {len(thumb_divs)}")
            
            for div in thumb_divs:
                imgs = div.find_elements(By.TAG_NAME, "img")
                print(f"Imágenes en este div: {len(imgs)}")
                for img in imgs:
                    url = img.get_attribute("src")
                    classes = img.get_attribute("class")
                    print(f"  Imagen: {url}, Clases: {classes}")
                    
                    # Verificar diferentes atributos
                    for attr in ['src', 'data-src', 'data-lazy-src']:
                        test_url = img.get_attribute(attr)
                        if test_url and test_url.startswith("http"):
                            print(f"  Encontrado en atributo {attr}: {test_url}")
                            return test_url
                    
                    if url and url.startswith("http"):
                        return url
        except Exception as e:
            print(f"Error en bs-blog-thumb: {e}")
        
        # 3. Ver todas las imágenes con clase wp-post-image
        try:
            imgs = driver.find_elements(By.CSS_SELECTOR, ".wp-post-image, img[class*='wp-post-image']")
            print(f"Imágenes con clase wp-post-image: {len(imgs)}")
            for img in imgs:
                # Verificar múltiples atributos
                for attr in ['src', 'data-src', 'data-lazy-src']:
                    url = img.get_attribute(attr)
                    if url and url.startswith("http"):
                        print(f"  URL en atributo {attr}: {url}")
                        return url
        except Exception as e:
            print(f"Error en wp-post-image: {e}")
        
        # 4. Nueva estrategia: buscar la primera imagen dentro del contenido principal
        try:
            # Buscar en el área de contenido principal
            content_selectors = [
                ".single.content-right .bs-blog-thumb img",
                ".bs-blog-post.single .bs-blog-thumb img",
                "article .bs-blog-thumb img",
                ".content-right .bs-blog-thumb img"
            ]
            
            for selector in content_selectors:
                try:
                    imgs = driver.find_elements(By.CSS_SELECTOR, selector)
                    if imgs:
                        print(f"Imágenes encontradas con selector {selector}: {len(imgs)}")
                        for img in imgs:
                            for attr in ['src', 'data-src', 'data-lazy-src']:
                                url = img.get_attribute(attr)
                                if url and url.startswith("http"):
                                    print(f"  Imagen principal encontrada: {url}")
                                    return url
                except Exception as e:
                    print(f"  Error con selector {selector}: {e}")
        except Exception as e:
            print(f"Error en búsqueda de contenido principal: {e}")
        
        # 5. Último recurso: buscar todas las imágenes en el artículo
        try:
            article_imgs = driver.find_elements(By.CSS_SELECTOR, "article img, .bs-blog-post img")
            print(f"Imágenes en artículo: {len(article_imgs)}")
            
            for img in article_imgs:
                # Filtrar por tamaño (imágenes muy pequeñas probablemente no sean la principal)
                width = img.get_attribute("width")
                height = img.get_attribute("height")
                
                for attr in ['src', 'data-src', 'data-lazy-src']:
                    url = img.get_attribute(attr)
                    if url and url.startswith("http"):
                        print(f"  Imagen candidata: {url} (tamaño: {width}x{height})")
                        
                        # Priorizar imágenes que parezcan ser grandes
                        if width and height:
                            try:
                                w = int(width)
                                h = int(height)
                                if w > 300 and h > 200:  # Tamaño mínimo para imagen principal
                                    return url
                            except:
                                pass
                        
                        # Si no podemos determinar el tamaño, al menos devolver la primera
                        if url and "/wp-content/uploads/" in url:
                            return url
        except Exception as e:
            print(f"Error en búsqueda general de imágenes: {e}")
        
        print("=== DEBUG: No se encontró imagen ===")
        return ""
        
    except Exception as e:
        print(f"Error general: {e}")
        return ""

def _extraer_contenido_eldespertar(driver):
    """Extrae el contenido de la noticia en eldespertar.cl"""
    parrafos = []
    total = 0
    
    try:
        # El contenido está en article.small.single
        contenido_div = driver.find_element(By.CSS_SELECTOR, "article.small.single")
        elementos_parrafo = contenido_div.find_elements(By.TAG_NAME, "p")
        total = len(elementos_parrafo)
        
        for index, p in enumerate(elementos_parrafo):
            texto = p.text.strip()
            if texto and len(texto) > 10:
                parrafos.append(texto)
                
    except Exception as e:
        print(f"Error al extraer contenido: {e}")
    
    return {'parrafos': parrafos, 'total': total}

def _extraer_categoria_eldespertar(driver):
    """Extrae la categoria de la noticia en eldespertar.cl"""
    try:
        # Las categorías están en div.bs-blog-category.one
        categorias_div = driver.find_element(By.CSS_SELECTOR, "div.bs-blog-category.one")
        categorias = categorias_div.find_elements(By.TAG_NAME, "a")
        categorias_texto = [cat.text.strip() for cat in categorias]
        return ", ".join(categorias_texto)
    except:
        try:
            categorias_div = driver.find_element(By.CSS_SELECTOR, ".bs-blog-category")
            categorias = categorias_div.find_elements(By.TAG_NAME, "a")
            categorias_texto = [cat.text.strip() for cat in categorias]
            return ", ".join(categorias_texto)
        except:
            return "."

# Función de parseo de fecha (mantenida del original)
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

    # Formato específico de eldespertar.cl: Ene 16, 2026
    m = re.match(r"([a-z]+)\s+(\d{1,2}),\s+(\d{4})", fecha_str)
    if m:
        mes, dia, anio = m.groups()
        # Traducir mes abreviado a español completo
        meses_abr = {
            'ene': 'enero', 'feb': 'febrero', 'mar': 'marzo', 'abr': 'abril',
            'may': 'mayo', 'jun': 'junio', 'jul': 'julio', 'ago': 'agosto',
            'sep': 'septiembre', 'oct': 'octubre', 'nov': 'noviembre', 'dic': 'diciembre'
        }
        mes_completo = meses_abr.get(mes.lower(), mes)
        if mes_completo in MESES_ES:
            return date(int(anio), MESES_ES[mes_completo], int(dia))

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
def _extraer_fecha_autor_eldespertar(driver):
    """Extrae fecha y autor de la noticia en eldespertar.cl"""
    fecha = None
    autor = "No encontrado"

    try:
        # En eldespertar.cl, la fecha está en .bs-blog-date dentro de .bs-info-author-block
        fecha_raw = driver.find_element(
            By.CSS_SELECTOR, ".bs-info-author-block .bs-blog-date"
        ).text.strip()
        
        # Intentar extraer autor si existe
        try:
            autor_elem = driver.find_element(By.CSS_SELECTOR, ".bs-author")
            autor = autor_elem.text.strip()
        except:
            autor = "No encontrado"
            
    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
        fecha_raw = None

    fecha = _parsear_fecha(fecha_raw)

    return {
        "fecha": fecha,  # datetime.date | None
        "autor": autor
    } '''

def _extraer_fecha_autor_eldespertar(driver):
    """Extrae fecha y autor de la noticia en eldespertar.cl"""
    fecha = None
    autor = "No encontrado"

    try:
        # En eldespertar.cl, la fecha está en .bs-blog-date dentro de .bs-info-author-block
        fecha_raw = driver.find_element(
            By.CSS_SELECTOR, ".bs-info-author-block .bs-blog-date"
        ).text.strip()
        
        # Intentar extraer autor - método más específico
        try:
            # Buscar el primer párrafo después del h2 con texto centrado
            h2_element = driver.find_element(By.CSS_SELECTOR, "h2.wp-block-heading.has-text-align-center")
            # Obtener el siguiente hermano que sea párrafo
            siguiente_elemento = h2_element.find_element(By.XPATH, "following-sibling::p[1]")
            autor = siguiente_elemento.text.strip()
        except:
            # Fallback: buscar cualquier párrafo que contenga "Por" o "Equipo"
            try:
                article_content = driver.find_element(By.CLASS_NAME, "small")
                paragraphs = article_content.find_elements(By.TAG_NAME, "p")
                
                for p in paragraphs:
                    text = p.text.strip().lower()
                    if "por " in text or "equipo" in text:
                        autor = p.text.strip()
                        break
            except:
                autor = "No encontrado"
            
    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
        fecha_raw = None

    fecha = _parsear_fecha(fecha_raw)

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
    """Función principal de scraping para eldespertar.cl"""
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE ELDESPERTAR.CL")
        print("="*80)
        
        # Configurar driver
        driver = configurar_driver()
        
        # Extraer URLs de eldespertar.cl
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
            
            # Mostrar datos extraídos
            print(f"  Titular: {datos['titular'][:80]}...")
            print(f"  Bajada: {datos['bajada'][:80]}...")
            print(f"  Fecha: {datos['fecha']}")
            print(f"  Categoría: {datos['categoria']}")
            print(f"  Párrafos extraídos: {len(datos['contenido'])}")
            
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
    total = Article.objects.count()
    print(f"Total en base de datos: {total}")
    print(f"{'='*80}")

if __name__ == "__main__":
    run()