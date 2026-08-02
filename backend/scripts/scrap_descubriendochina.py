import sys
import os
import time
import django
from datetime import datetime, date, timedelta
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
        'fecha': None,  # Esto debe ser un objeto date
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
        datos['fecha'] = fecha_autor['fecha']  # Esto debe ser un objeto date o None
        datos['autor'] = fecha_autor['autor']
        datos['categoria'] = _extraer_categoria(driver)
        
        # Verificar que la fecha sea un objeto date o None
        if datos['fecha'] and not isinstance(datos['fecha'], date):
            print(f"  ERROR: La fecha no es un objeto date: {datos['fecha']} (tipo: {type(datos['fecha'])})")
            datos['fecha'] = None
        
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

def _parsear_fecha_relativa(texto_fecha: str, fecha_referencia: date) -> date | None:
    """
    Convierte una fecha relativa como "hace 2 días" a una fecha absoluta
    """
    if not texto_fecha:
        return None
    
    texto_fecha = texto_fecha.lower().strip()
    print(f"  Parseando fecha relativa: '{texto_fecha}'")
    
    # Patrones para fechas relativas
    patrones = [
        (r'hace\s+(\d+)\s+días?', 'dias'),
        (r'hace\s+(\d+)\s+horas?', 'horas'),
        (r'hace\s+(\d+)\s+minutos?', 'minutos'),
        (r'hace\s+(\d+)\s+semanas?', 'semanas'),
        (r'hace\s+(\d+)\s+meses?', 'meses'),
        (r'hace\s+(\d+)\s+años?', 'años'),
        (r'ayer', 'ayer'),
        (r'hoy', 'hoy'),
        (r'(\d+)\s+días?', 'dias'),
        (r'(\d+)\s+horas?', 'horas'),
    ]
    
    for patron, tipo in patrones:
        match = re.search(patron, texto_fecha)
        if match:
            if tipo == 'ayer':
                return fecha_referencia - timedelta(days=1)
            elif tipo == 'hoy':
                return fecha_referencia
            else:
                cantidad = int(match.group(1))
                if tipo == 'dias':
                    return fecha_referencia - timedelta(days=cantidad)
                elif tipo == 'horas':
                    return fecha_referencia
                elif tipo == 'minutos':
                    return fecha_referencia
                elif tipo == 'semanas':
                    return fecha_referencia - timedelta(weeks=cantidad)
                elif tipo == 'meses':
                    return fecha_referencia - timedelta(days=cantidad * 30)
                elif tipo == 'años':
                    return fecha_referencia - timedelta(days=cantidad * 365)
    
    return None

def _parsear_fecha_absoluta(fecha_str: str) -> date | None:
    """
    Parsea una fecha absoluta en diferentes formatos
    """
    if not fecha_str:
        return None

    fecha_str = fecha_str.strip()
    fecha_str = fecha_str.replace('"', '').replace("'", '')
    
    # Formato ISO: 2026-07-29
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        pass
    
    # Formato: 29/07/2026
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y").date()
    except ValueError:
        pass
    
    meses_es = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    
    # Formato: 29 julio, 2026
    m = re.match(r"(\d{1,2})\s+([a-záéíóú]+),?\s+(\d{4})", fecha_str.lower())
    if m:
        dia, mes, anio = m.groups()
        if mes in meses_es:
            try:
                return date(int(anio), meses_es[mes], int(dia))
            except ValueError:
                pass

    # Formato: julio 29, 2026
    m = re.match(r"([a-záéíóú]+)\s+(\d{1,2}),?\s+(\d{4})", fecha_str.lower())
    if m:
        mes, dia, anio = m.groups()
        if mes in meses_es:
            try:
                return date(int(anio), meses_es[mes], int(dia))
            except ValueError:
                pass

    return None

def _extraer_fecha_autor(driver):
    """
    Extrae fecha y autor de la noticia en Wix
    """
    fecha = None
    autor = "No encontrado"
    
    fecha_referencia = date.today()

    try:
        lista_metadata = driver.find_element(By.CSS_SELECTOR, "ul.NtBDdE")
        items = lista_metadata.find_elements(By.TAG_NAME, "li")
        
        print(f"  Encontrados {len(items)} items de metadata")
        
        for idx, item in enumerate(items):
            texto = item.text.strip()
            print(f"    Item {idx}: '{texto}'")
            
            # Buscar el elemento time-ago (contiene la fecha relativa)
            try:
                time_element = item.find_element(By.CSS_SELECTOR, "time-ago")
                title = time_element.get_attribute("title")
                if title:
                    print(f"      Título time-ago: '{title}'")
                    fecha = _parsear_fecha_absoluta(title)
                    if not fecha:
                        fecha = _parsear_fecha_relativa(texto, fecha_referencia)
                    if fecha:
                        print(f"      Fecha parseada del título: {fecha}")
                        continue
            except:
                pass
            
            # Si no se encontró el time-ago, intentar parsear el texto directamente
            if "hace" in texto or "ayer" in texto or "hoy" in texto:
                fecha = _parsear_fecha_relativa(texto, fecha_referencia)
                if fecha:
                    print(f"      Fecha parseada del texto: {fecha}")
                    continue
            
            # Si no es fecha, probablemente es el autor
            if "hace" not in texto and "min" not in texto and "días" not in texto and "lectura" not in texto:
                if texto and len(texto) > 2:
                    autor = texto
                    print(f"      Autor encontrado: '{autor}'")
        
        # Si no se encontró el autor, buscar directamente
        if autor == "No encontrado":
            try:
                autor_element = driver.find_element(By.CSS_SELECTOR, "span.user-name")
                autor = autor_element.text
                print(f"  Autor (fallback): '{autor}'")
            except:
                pass

    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
    
    print(f"  Fecha final: {fecha} (tipo: {type(fecha)}), Autor: {autor}")
    return {'fecha': fecha, 'autor': autor}

def guardar_en_db(datos):
    try:
        if Article.objects.filter(url=datos['url']).exists():
            print(f"Ya existe: {datos['titular'][:50]}...")
            return False
        
        contenido_texto = '\n\n'.join(datos['contenido'])
        
        print(f"  Guardando fecha: {datos['fecha']} (tipo: {type(datos['fecha'])})")
        
        # Verificar que la fecha sea un objeto date o None
        fecha_guardar = datos['fecha']
        if fecha_guardar and not isinstance(fecha_guardar, date):
            print(f"  ERROR: La fecha no es un objeto date: {fecha_guardar}")
            fecha_guardar = None
        
        articulo = Article.objects.create(
            url=datos['url'],
            title=datos['titular'],
            subtitle=datos['bajada'],
            image_url=datos['imagen'],
            content=contenido_texto,
            publication_date=fecha_guardar,  # Este es el campo correcto
            author=datos['autor'],
            category=datos['categoria']
        )
        
        print(f"Guardado: {articulo.title[:60]}...")
        print(f"  Fecha guardada en DB: {articulo.publication_date}")
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
        print(f"Fecha de referencia para fechas relativas: {date.today()}")
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