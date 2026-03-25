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

# Mapeo de meses en español para parseo de fechas
MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}

def configurar_driver():
    """Configurar Selenium WebDriver en modo headless"""
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

def extraer_urls_principales(driver):
    """
    Extrae las URLs de las noticias principales más recientes.
    Prioriza: featured-main (principal) + primeros artículos del archive-list
    Retorna: lista de URLs únicas (máximo 10)
    """
    print("Extrayendo URLs de las noticias principales más recientes...")
    urls_noticias = []
    
    try:
        driver.get("https://www.resumenlatinoamericano.org/")
        time.sleep(3)
        
        # 1. Extraer noticia principal (destacada)
        try:
            main_story = driver.find_element(By.CSS_SELECTOR, "div.main-story a")
            main_url = main_story.get_attribute("href")
            if main_url and main_url.startswith("https://www.resumenlatinoamericano.org/"):
                urls_noticias.append(main_url)
                print(f"  Noticia principal: {main_url[:80]}...")
        except Exception as e:
            print(f"  No se pudo extraer noticia principal: {e}")
        
        # 2. Extraer sub-stories (noticias secundarias destacadas)
        try:
            sub_stories = driver.find_elements(By.CSS_SELECTOR, "div.sub-story a")
            for story in sub_stories:
                url = story.get_attribute("href")
                if url and url.startswith("https://www.resumenlatinoamericano.org/") and url not in urls_noticias:
                    urls_noticias.append(url)
                    print(f"  Sub-story: {url[:80]}...")
                    if len(urls_noticias) >= 10:
                        break
        except Exception as e:
            print(f"  Error extrayendo sub-stories: {e}")
        
        # 3. Si aún faltan URLs, extraer del listado de archivo (archive-list)
        if len(urls_noticias) < 10:
            try:
                archive_items = driver.find_elements(By.CSS_SELECTOR, "ul.archive-list li div.archive-text h2 a")
                for item in archive_items:
                    url = item.get_attribute("href")
                    if url and url.startswith("https://www.resumenlatinoamericano.org/") and url not in urls_noticias:
                        urls_noticias.append(url)
                        print(f"  Archive: {url[:80]}...")
                        if len(urls_noticias) >= 10:
                            break
            except Exception as e:
                print(f"  Error extrayendo archive-list: {e}")
        
        print(f"\nTotal de URLs únicas extraídas: {len(urls_noticias)}")
        
    except Exception as e:
        print(f"Error al extraer URLs: {e}")
    
    return urls_noticias[:10]  # Asegurar máximo 10

def _parsear_fecha(fecha_str: str) -> date | None:
    """Parsea fechas en formatos típicos de Resumen Latinoamericano"""
    if not fecha_str:
        return None
    
    fecha_str = fecha_str.strip().lower()
    
    # Formato ISO: 2026-03-25
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        pass
    
    # Formato: 25 marzo, 2026  o  25 de marzo de 2026
    match = re.search(r"(\d{1,2})\s+(?:de\s+)?([a-záéíóú]+)(?:\s+de)?\s+(\d{4})", fecha_str)
    if match:
        dia, mes, anio = match.groups()
        if mes in MESES_ES:
            return date(int(anio), MESES_ES[mes], int(dia))
    
    # Formato: marzo 25, 2026
    match = re.search(r"([a-záéíóú]+)\s+(\d{1,2}),?\s+(\d{4})", fecha_str)
    if match:
        mes, dia, anio = match.groups()
        if mes in MESES_ES:
            return date(int(anio), MESES_ES[mes], int(dia))
    
    return None

def extraer_datos_noticia(driver, url):
    """Extrae todos los datos de una noticia individual"""
    datos = {
        'url': url,
        'titular': 'No encontrado',
        'bajada': 'No encontrada',
        'imagen': '',
        'contenido': [],
        'fecha': None,
        'autor': 'No encontrado',
        'categoria': 'No encontrada'
    }
    
    try:
        driver.get(url)
        time.sleep(2)
        
        # Titular (h1 principal)
        try:
            datos['titular'] = driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
        except:
            datos['titular'] = "No encontrado"
        
        # Imagen (meta og:image o imagen destacada)
        try:
            datos['imagen'] = driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content")
        except:
            try:
                datos['imagen'] = driver.find_element(By.CSS_SELECTOR, "div.post-image img").get_attribute("src")
            except:
                pass
        
        # Contenido (párrafos dentro de #content-area)
        try:
            content_area = driver.find_element(By.ID, "content-area")
            parrafos = content_area.find_elements(By.TAG_NAME, "p")
            for p in parrafos:
                texto = p.text.strip()
                # Filtrar párrafos vacíos o muy cortos
                if texto and len(texto) > 20:
                    datos['contenido'].append(texto)
        except Exception as e:
            print(f"  Error extrayendo contenido: {e}")
        
        # Bajada = primer párrafo del contenido (si existe)
        if datos['contenido']:
            datos['bajada'] = datos['contenido'][0][:250]  # Primeros 250 caracteres
        
        # Fecha y autor: buscan en el HTML común de RL
        # Ejemplo: "Resumen Latinoamericano, 25 de marzo de 2026." o "Por Tito Ura, Rebelion, 25 de marzo de 2026."
        try:
            # Buscar en el contenido párrafos con información de autor/fecha
            for p in parrafos[:3]:  # Revisar primeros párrafos
                texto = p.text.strip()
                # Buscar patrón de fecha
                fecha_match = _parsear_fecha(texto)
                if fecha_match:
                    datos['fecha'] = fecha_match
                # Buscar autor: "Por Nombre Apellido," o "Por: Nombre Apellido"
                autor_match = re.search(r"Por\s*:?\s*([A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)*)", texto)
                if autor_match and datos['autor'] == "No encontrado":
                    datos['autor'] = autor_match.group(1).strip()
        except:
            pass
        
        # Categoría (se puede obtener de la URL o de la clase post)
        try:
            # Extraer categoría de la clase post-xxx category-nombre
            post_class = driver.find_element(By.CSS_SELECTOR, "article").get_attribute("class")
            cat_match = re.search(r"category-([a-z-]+)", post_class)
            if cat_match:
                datos['categoria'] = cat_match.group(1).replace('-', ' ').title()
        except:
            pass
        
    except Exception as e:
        print(f"  Error general al procesar noticia: {e}")
    
    return datos

def guardar_en_db(datos):
    """Guardar datos en la base de datos (evitando duplicados)"""
    try:
        if Article.objects.filter(url=datos['url']).exists():
            print(f"  Ya existe: {datos['titular'][:50]}...")
            return False
        
        contenido_texto = '\n\n'.join(datos['contenido'])
        
        articulo = Article.objects.create(
            url=datos['url'],
            title=datos['titular'],
            subtitle=datos['bajada'][:500] if datos['bajada'] != 'No encontrada' else '',
            image_url=datos['imagen'],
            content=contenido_texto,
            publication_date=datos['fecha'],
            author=datos['autor'],
            category=datos['categoria']
        )
        
        print(f"  ✓ Guardado: {articulo.title[:60]}...")
        return True
        
    except Exception as e:
        print(f"  Error guardando en DB: {e}")
        return False

def ejecutar_scraping(max_noticias=10):
    """Función principal de scraping para Resumen Latinoamericano"""
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE RESUMEN LATINOAMERICANO.ORG")
        print("="*80)
        
        driver = configurar_driver()
        
        # Extraer URLs de las noticias principales
        urls = extraer_urls_principales(driver)
        
        if not urls:
            print("No se encontraron URLs de noticias")
            return 0
        
        print(f"\nProcesando {min(max_noticias, len(urls))} noticias...")
        
        for i, url in enumerate(urls[:max_noticias], 1):
            print(f"\n[{i}/{min(max_noticias, len(urls))}]")
            print(f"URL: {url[:80]}...")
            
            datos = extraer_datos_noticia(driver, url)
            
            # Mostrar resumen
            print(f"  Título: {datos['titular'][:70]}...")
            print(f"  Fecha: {datos['fecha']}")
            print(f"  Autor: {datos['autor']}")
            print(f"  Párrafos: {len(datos['contenido'])}")
            
            if datos['contenido']:
                if guardar_en_db(datos):
                    articulos_procesados += 1
            else:
                print("  ⚠ Sin contenido, omitiendo...")
            
            if i < max_noticias:
                time.sleep(1.5)  # Pausa para no sobrecargar
        
        return articulos_procesados
        
    except Exception as e:
        print(f"\nError general en scraping: {e}")
        return 0
        
    finally:
        if driver:
            driver.quit()
            print("\nWebDriver cerrado.")

def run():
    """Función principal para ejecutar el scraping"""
    cantidad = ejecutar_scraping(max_noticias=10)
    print(f"\n{'='*80}")
    print(f"SCRAPING COMPLETADO")
    print(f"Artículos nuevos guardados: {cantidad}")
    total = Article.objects.count()
    print(f"Total de artículos en base de datos: {total}")
    print(f"{'='*80}")

if __name__ == "__main__":
    run()