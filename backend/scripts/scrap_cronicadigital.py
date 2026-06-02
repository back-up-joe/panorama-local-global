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
    Extrae URLs de noticias de las secciones especificadas de Crónica Digital
    Retorna: lista de URLs únicas
    """
    print("Buscando enlaces de noticias en Crónica Digital...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal
        driver.get("https://cronicadigital.cl/")
        time.sleep(3)
        
        # 1. Buscar en el banner principal (sección Portada - slider)
        print("\nBuscando en banner principal (slider de Portada)...")
        try:
            slider_items = driver.find_elements(By.CSS_SELECTOR, ".twp-banner-slider-wrapper .twp-post-style-2 a")
            for enlace in slider_items:
                try:
                    href = enlace.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en slider: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  Error en slider: {e}")
        
        # 2. Buscar en secciones laterales (Internacional, Nacional, etc.)
        print("\nBuscando en secciones laterales...")
        selectores_secciones = [
            ".twp-exclusive-post-list .twp-post-style-1 a",  # Internacional y otras
            ".twp-recent-post-list .twp-post-style-3 a",      # Nacional, etc.
            ".twp-recent-post-list .twp-post-style-4 a",      # Nacional (formato numerado)
            ".twp-post-list .twp-post-style-3 a",             # Posts en el centro
            ".twp-featured-category-post-list .twp-post-style-1 a"  # Categorías destacadas
        ]
        
        for selector in selectores_secciones:
            try:
                enlaces = driver.find_elements(By.CSS_SELECTOR, selector)
                for enlace in enlaces:
                    try:
                        href = enlace.get_attribute("href")
                        if _es_url_noticia_valida(href, urls_noticias):
                            urls_noticias.append(href)
                            print(f"  Encontrado en sección: {href[:60]}...")
                    except:
                        continue
            except:
                continue
        
        # 3. Buscar en el ticker de portada
        print("\nBuscando en ticker de portada...")
        try:
            ticker_items = driver.find_elements(By.CSS_SELECTOR, ".twp-ticket-pin .twp-title-section a")
            for enlace in ticker_items:
                try:
                    href = enlace.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en ticker: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  Error en ticker: {e}")
        
        # Eliminar duplicados manteniendo el orden
        urls_noticias = list(dict.fromkeys(urls_noticias))
        
        print(f"\nTotal de URLs encontradas: {len(urls_noticias)}")
        
        # Mostrar las URLs encontradas
        if urls_noticias:
            print("\nURLs encontradas:")
            for i, url in enumerate(urls_noticias[:15], 1):  # Mostrar solo primeras 15
                print(f"{i}. {url}")
            if len(urls_noticias) > 15:
                print(f"... y {len(urls_noticias) - 15} más")
        
    except Exception as e:
        print(f"Error al buscar enlaces: {e}")
    
    return urls_noticias

def _es_url_noticia_valida(href, urls_existentes):
    """
    Valida si una URL es una noticia válida
    Retorna: True si es válida, False en caso contrario
    """
    if not href:
        return False
    
    condiciones = [
        href.startswith("https://cronicadigital.cl/"),
        not href.endswith((".jpg", ".png", ".gif", ".webp")),
        not "/category/" in href,
        not "/tag/" in href,
        not "/author/" in href,
        not "/page/" in href,
        href != "https://cronicadigital.cl/",
        href not in urls_existentes,
        len(href.split("/")) > 3  # Que tenga al menos una parte después del dominio
    ]
    
    return all(condiciones)

def extraer_datos_noticia(driver, url):
    """
    Extrae todos los datos de una noticia individual de Crónica Digital
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
        
        # Extraer bajada (primer párrafo significativo)
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
        # En Crónica Digital, el título está dentro del article
        titulo = driver.find_element(By.CSS_SELECTOR, "article .entry-title").text.strip()
        if titulo:
            return titulo
    except:
        pass
    
    try:
        return driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        return "No encontrado"

def _extraer_bajada(driver):
    """Extrae la bajada (primer párrafo significativo del contenido)"""
    try:
        # Buscar dentro de entry-content
        entry_content = driver.find_element(By.CLASS_NAME, "entry-content")
        
        # Buscar el primer párrafo que no esté dentro de bloques especiales
        parrafos = entry_content.find_elements(By.TAG_NAME, "p")
        
        for p in parrafos:
            texto = p.text.strip()
            # Ignorar párrafos que parecen ser de videos embebidos o muy cortos
            if texto and len(texto) > 100 and not "iframe" in texto.lower():
                return texto[:500]  # Limitamos la longitud de la bajada
        
        # Si no hay párrafo largo, buscar el primero que tenga más de 50 caracteres
        for p in parrafos:
            texto = p.text.strip()
            if texto and len(texto) > 50:
                return texto[:500]
                
    except Exception as e:
        print(f"Error al extraer bajada: {e}")
    
    # Fallbacks con meta tags
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
                return texto.strip()[:500]
        except:
            continue
    
    return "No encontrada"

def _extraer_imagen(driver):
    """Extrae la URL de la imagen principal"""
    # 1. Buscar en meta og:image
    try:
        return driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content")
    except:
        pass
    
    # 2. Buscar imagen destacada en el article
    try:
        img = driver.find_element(By.CSS_SELECTOR, "article .wp-post-image")
        src = img.get_attribute("src")
        if src:
            return src
    except:
        pass
    
    # 3. Buscar cualquier imagen grande dentro del contenido
    try:
        img = driver.find_element(By.CSS_SELECTOR, ".entry-content img")
        src = img.get_attribute("src")
        if src and "logo" not in src.lower():
            return src
    except:
        pass
    
    return ""

def _extraer_contenido(driver):
    """Extrae el contenido de la noticia"""
    parrafos = []
    
    try:
        contenido_div = driver.find_element(By.CSS_SELECTOR, "div.entry-content")
        elementos_parrafo = contenido_div.find_elements(By.TAG_NAME, "p")
        
        for p in elementos_parrafo:
            texto = p.text.strip()
            # Filtrar párrafos vacíos o muy cortos, y excluir contenido de botones de compartir
            if texto and len(texto) > 20 and not any(skip in texto.lower() for skip in ["compartir en:", "addtoany"]):
                parrafos.append(texto)
                
    except Exception as e:
        print(f"Error al extraer contenido: {e}")
    
    return {'parrafos': parrafos, 'total': len(parrafos)}

def _extraer_categoria(driver):
    """Extrae la categoría de la noticia"""
    try:
        # Buscar en entry-footer o en cat-links
        categoria = driver.find_element(By.CSS_SELECTOR, ".cat-links a").text
        if categoria:
            return categoria
    except:
        pass
    
    try:
        categoria = driver.find_element(By.CSS_SELECTOR, ".entry-footer .cat-links a").text
        return categoria
    except:
        pass
    
    return "."

# Importar funciones de parseo de fechas (reutilizamos las mismas)
from datetime import date

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

def _parsear_fecha(fecha_str: str) -> date | None:
    if not fecha_str:
        return None

    fecha_str = fecha_str.strip().lower()

    # Formatos ISO
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        pass

    # Formato: 1 junio, 2026
    m = re.match(r"(\d{1,2})\s+([a-záéíóú]+),?\s+(\d{4})", fecha_str)
    if m:
        dia, mes, anio = m.groups()
        return date(int(anio), MESES_ES[mes], int(dia))

    # Formato: junio 1, 2026
    m = re.match(r"([a-záéíóú]+)\s+(\d{1,2}),?\s+(\d{4})", fecha_str)
    if m:
        mes, dia, anio = m.groups()
        return date(int(anio), MESES_ES[mes], int(dia))

    return None

def _extraer_fecha_autor(driver):
    """Extrae fecha y autor de la noticia"""
    fecha = None
    autor = "No encontrado"

    # Buscar en el área de metadatos del artículo
    try:
        # Los metadatos pueden estar en diferentes lugares
        metadatos = driver.find_elements(By.CSS_SELECTOR, ".twp-author-desc, .entry-meta")
        
        for meta in metadatos:
            # Buscar fecha
            try:
                fecha_elem = meta.find_element(By.CSS_SELECTOR, ".posts-date, .date a")
                fecha_raw = fecha_elem.text.strip()
                if fecha_raw:
                    fecha = _parsear_fecha(fecha_raw)
            except:
                pass
            
            # Buscar autor
            try:
                autor_elem = meta.find_element(By.CSS_SELECTOR, ".twp-single-post-author .twp-caption, .by-author a")
                autor = autor_elem.text.strip()
                if autor and autor != "No encontrado":
                    break
            except:
                pass
    
    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
        
        # Intentar con selectores directos como fallback
        try:
            fecha_elem = driver.find_element(By.CSS_SELECTOR, ".posts-date")
            fecha_raw = fecha_elem.text.strip()
            fecha = _parsear_fecha(fecha_raw)
        except:
            pass
        
        try:
            autor_elem = driver.find_element(By.CSS_SELECTOR, ".twp-single-post-author .twp-caption")
            autor = autor_elem.text.strip()
        except:
            pass

    return {
        "fecha": fecha,
        "autor": autor if autor != "No encontrado" else "Crónica Digital"
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
        
        print(f"✓ Guardado: {articulo.title[:60]}...")
        return True
        
    except Exception as e:
        print(f"✗ Error guardando en DB: {e}")
        return False

def ejecutar_scraping(max_noticias=10):
    """Función principal de scraping para Crónica Digital"""
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE CRÓNICA DIGITAL")
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
            
            # Mostrar resumen
            print(f"  Título: {datos['titular'][:60]}...")
            print(f"  Autor: {datos['autor']}")
            print(f"  Categoría: {datos['categoria']}")
            print(f"  Párrafos: {len(datos['contenido'])}")
            
            # Guardar en DB si tiene contenido
            if datos['contenido']:
                if guardar_en_db(datos):
                    articulos_procesados += 1
            else:
                print(f"  ✗ Sin contenido significativo")
            
            # Pausa para no sobrecargar
            if i < min(max_noticias, len(urls)):
                time.sleep(2)
        
        return articulos_procesados
        
    except Exception as e:
        print(f"\n✗ Error general en scraping: {e}")
        return 0
        
    finally:
        if driver:
            driver.quit()
            print("\nWebDriver cerrado.")

def run():
    cantidad = ejecutar_scraping(max_noticias=10)
    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETADO")
    print(f"Artículos procesados y guardados: {cantidad}")
    
    # Mostrar estadísticas
    total = Article.objects.count()
    print(f"Total de artículos en base de datos: {total}")
    print(f"{'='*80}")

if __name__ == "__main__":
    run()