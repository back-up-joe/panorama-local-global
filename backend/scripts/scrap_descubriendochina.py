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
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException

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

def extraer_urls_categoria_politica(driver):
    """
    Extrae URLs de las 10 noticias más recientes de la categoría "Politica"
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias en la categoría 'Politica'...")
    urls_noticias = []
    base_url = "https://www.descubriendochina.org/noticias/categories/politica"
    driver.get(base_url)
    time.sleep(5)

    max_noticias = 10
    pagina_actual = 1

    while len(urls_noticias) < max_noticias:
        print(f"  Scrapeando página {pagina_actual}. Encontrados: {len(urls_noticias)}")

        try:
            driver.find_element(By.CSS_SELECTOR, ".gallery-item-container")
        except:
            print("  No se encontraron elementos de galería. Esperando...")
            time.sleep(3)

        items_galeria = driver.find_elements(By.CSS_SELECTOR, ".gallery-item-container a[href*='/post/']")
        
        for item in items_galeria:
            try:
                href = item.get_attribute("href")
                if href and '/post/' in href:
                    href = href.split('?')[0]
                    if href not in urls_noticias:
                        urls_noticias.append(href)
                        print(f"    [{len(urls_noticias)}] {href}")
                        if len(urls_noticias) >= max_noticias:
                            break
            except:
                continue
        
        if len(urls_noticias) >= max_noticias:
            break

        if len(urls_noticias) < max_noticias:
            enlaces_posts = driver.find_elements(By.CSS_SELECTOR, "a[href*='/post/']")
            for enlace in enlaces_posts:
                try:
                    href = enlace.get_attribute("href")
                    if href and '/post/' in href:
                        href = href.split('?')[0]
                        if href not in urls_noticias:
                            urls_noticias.append(href)
                            print(f"    [{len(urls_noticias)}] {href}")
                            if len(urls_noticias) >= max_noticias:
                                break
                except:
                    continue

        if len(urls_noticias) >= max_noticias:
            break

        try:
            boton_siguiente = driver.find_element(By.CSS_SELECTOR, "[data-hook='pagination__next']")
            
            clases = boton_siguiente.get_attribute("class")
            if "disabled" in clases or "blog-button-color" not in clases:
                print("  No hay más páginas disponibles.")
                break
            
            driver.execute_script("arguments[0].scrollIntoView(true);", boton_siguiente)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", boton_siguiente)
            
            time.sleep(4)
            pagina_actual += 1
            
        except NoSuchElementException:
            print("  No se encontró el botón 'Siguiente'. Fin de la paginación.")
            break
        except Exception as e:
            print(f"  Error al navegar a la siguiente página: {e}")
            break

    print(f"\nTotal de URLs encontradas en categoría 'Politica': {len(urls_noticias)}")
    return urls_noticias

def extraer_datos_noticia(driver, url):
    """
    Extrae todos los datos de una noticia individual
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
        
        datos['titular'] = _extraer_titular(driver)
        datos['bajada'] = _extraer_bajada(driver)
        datos['imagen'] = _extraer_imagen(driver)
        datos['contenido'] = _extraer_contenido(driver)
        
        fecha_autor = _extraer_fecha_autor(driver)
        datos['fecha'] = fecha_autor['fecha']
        datos['autor'] = fecha_autor['autor']
        datos['categoria'] = _extraer_categoria(driver)
        
    except Exception as e:
        print(f"Error general al procesar noticia {url}: {e}")
    
    return datos

def _extraer_titular(driver):
    try:
        return driver.find_element(By.CSS_SELECTOR, "h1.H3vOVf").text.strip()
    except:
        try:
            return driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            return "No encontrado"

def _extraer_bajada(driver):
    try:
        em_elements = driver.find_elements(By.CSS_SELECTOR, "div.fTEXDR p em span")
        if em_elements and len(em_elements) > 0:
            return ' '.join([span.text for span in em_elements])
        
        meta_desc = driver.find_element(By.CSS_SELECTOR, "meta[name='description']").get_attribute("content")
        if meta_desc:
            return meta_desc.strip()
    except Exception as e:
        print(f"Error en estrategia de bajada: {e}")
    
    return "No encontrada"

def _extraer_imagen(driver):
    try:
        return driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content")
    except:
        return ""

def _extraer_contenido(driver):
    parrafos = []
    try:
        contenido_div = driver.find_element(By.CSS_SELECTOR, "div.fTEXDR")
        elementos_parrafo = contenido_div.find_elements(By.CSS_SELECTOR, "p")
        
        for p in elementos_parrafo:
            texto = p.text.strip()
            if texto and len(texto) > 10 and "No encontrada" not in texto:
                parrafos.append(texto)
                
    except Exception as e:
        print(f"Error al extraer contenido: {e}")
    
    return parrafos

def _extraer_categoria(driver):
    try:
        categoria_element = driver.find_element(By.CSS_SELECTOR, "ul.pRGtWE li a.Tp7c0d")
        return categoria_element.text
    except:
        return "Politica"

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}

def _parsear_fecha(fecha_str: str, driver=None) -> date | None:
    if not fecha_str:
        return None

    fecha_str = fecha_str.strip().lower()
    
    if "hace" in fecha_str and driver:
        try:
            time_ago = driver.find_element(By.CSS_SELECTOR, "time-ago")
            title = time_ago.get_attribute("title")
            if title:
                fecha_str = title
        except:
            pass
    
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d %B, %Y", "%B %d, %Y"]
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            pass
    
    m = re.match(r"(\d{1,2})\s+([a-záéíóú]+),?\s+(\d{4})", fecha_str)
    if m:
        dia, mes, anio = m.groups()
        if mes in MESES_ES:
            try:
                return date(int(anio), MESES_ES[mes], int(dia))
            except ValueError:
                pass

    m = re.match(r"([a-záéíóú]+)\s+(\d{1,2}),?\s+(\d{4})", fecha_str)
    if m:
        mes, dia, anio = m.groups()
        if mes in MESES_ES:
            try:
                return date(int(anio), MESES_ES[mes], int(dia))
            except ValueError:
                pass

    return None

def _extraer_fecha_autor(driver):
    fecha = None
    autor = "No encontrado"

    try:
        lista_metadata = driver.find_element(By.CSS_SELECTOR, "ul.NtBDdE")
        items = lista_metadata.find_elements(By.TAG_NAME, "li")
        
        for item in items:
            texto = item.text.strip()
            if "hace" in texto or "min" in texto or "días" in texto:
                try:
                    time_element = item.find_element(By.CSS_SELECTOR, "time-ago")
                    title = time_element.get_attribute("title")
                    if title:
                        fecha = _parsear_fecha(title, driver)
                    else:
                        fecha = _parsear_fecha(texto, driver)
                except:
                    fecha = _parsear_fecha(texto, driver)
            else:
                autor = texto
        
        if autor == "No encontrado":
            try:
                autor_element = driver.find_element(By.CSS_SELECTOR, "span.user-name")
                autor = autor_element.text
            except:
                pass

    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
    
    return {'fecha': fecha, 'autor': autor}

def guardar_en_db(datos):
    try:
        if Article.objects.filter(url=datos['url']).exists():
            print(f"Ya existe: {datos['titular'][:50]}...")
            return False
        
        contenido_texto = '\n\n'.join(datos['contenido'])
        
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
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE DESCUBRIENDOCHINA.ORG - CATEGORÍA POLÍTICA")
        print("="*80)
        
        driver = configurar_driver()
        
        urls = extraer_urls_categoria_politica(driver)
        
        if not urls:
            print("No se encontraron URLs de noticias en la categoría 'Politica'.")
            return 0
        
        print(f"\nProcesando {min(max_noticias, len(urls))} noticias...")
        
        for i, url in enumerate(urls[:max_noticias], 1):
            print(f"\n[{i}/{min(max_noticias, len(urls))}]")
            print(f"URL: {url}")
            
            datos = extraer_datos_noticia(driver, url)
            
            if datos['contenido']:
                if guardar_en_db(datos):
                    articulos_procesados += 1
            else:
                print(f"Sin contenido: {datos['titular'][:50]}...")
            
            if i < min(max_noticias, len(urls)):
                time.sleep(2)
        
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
    
    total = Article.objects.count()
    print(f"Total en base de datos: {total}")
    print(f"{'='*80}")

if __name__ == "__main__":
    run()