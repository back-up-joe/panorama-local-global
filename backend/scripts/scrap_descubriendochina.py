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
from selenium.common.exceptions import NoSuchElementException

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
    Extrae URLs de noticias de las páginas de noticias de descubriendochina.org.
    Va a la primera página y hace clic en "Siguiente" para obtener las más recientes.
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias en descubriendochina.org...")
    urls_noticias = []
    base_url = "https://www.descubriendochina.org/noticias"
    driver.get(base_url)
    time.sleep(3)

    max_noticias = 10

    while len(urls_noticias) < max_noticias:
        print(f"  Scrapeando página actual. Encontrados: {len(urls_noticias)}")

        # Buscar todos los enlaces a posts en la página actual
        enlaces_posts = driver.find_elements(By.CSS_SELECTOR, "a[href*='https://www.descubriendochina.org/post/']")
        
        for enlace in enlaces_posts:
            try:
                href = enlace.get_attribute("href")
                # Evitar duplicados y asegurar que es un enlace de post válido
                if href and href not in urls_noticias:
                    urls_noticias.append(href)
                    print(f"    Encontrado: {href}")
                    if len(urls_noticias) >= max_noticias:
                        break
            except:
                continue
        
        if len(urls_noticias) >= max_noticias:
            break

        # Intentar ir a la siguiente página
        try:
            # Buscar el botón "Siguiente" (pagination__next)
            boton_siguiente = driver.find_element(By.CSS_SELECTOR, "[data-hook='pagination__next']")
            # Verificar si el botón está deshabilitado
            if "disabled" in boton_siguiente.get_attribute("class"):
                print("  No hay más páginas.")
                break
            
            # Hacer clic en el botón "Siguiente"
            driver.execute_script("arguments[0].click();", boton_siguiente)
            time.sleep(3)  # Esperar a que cargue la nueva página
        except NoSuchElementException:
            print("  No se encontró el botón 'Siguiente'. Fin de la paginación.")
            break

    print(f"\nTotal de URLs encontradas: {len(urls_noticias)}")
    return urls_noticias

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
        
        # Extraer imagen
        datos['imagen'] = _extraer_imagen(driver)
        
        # Extraer contenido
        datos['contenido'] = _extraer_contenido(driver)
        
        # Extraer fecha y autor
        fecha_autor = _extraer_fecha_autor(driver)
        datos['fecha'] = fecha_autor['fecha']
        datos['autor'] = fecha_autor['autor']
        
        # Extraer categoria (si está disponible)
        datos['categoria'] = _extraer_categoria(driver)
        
    except Exception as e:
        print(f"Error general al procesar noticia {url}: {e}")
    
    return datos

def _extraer_titular(driver):
    """Extrae el titular de la noticia"""
    try:
        # Selector para el título en Wix
        return driver.find_element(By.CSS_SELECTOR, "h1.H3vOVf").text.strip()
    except:
        return "No encontrado"

def _extraer_bajada(driver):
    """Extrae la bajada de la noticia en Wix"""
    try:
        # Buscar el primer párrafo en cursiva, que suele ser la bajada
        em_elements = driver.find_elements(By.CSS_SELECTOR, "div.fTEXDR p em span")
        if em_elements and len(em_elements) > 0:
            # El primer elemento em suele ser la bajada
            texto = em_elements[0].text.strip()
            # El texto puede estar dividido en varios spans, obtener el texto completo
            return ' '.join([span.text for span in em_elements])
        
        # Fallback: buscar en meta description
        meta_desc = driver.find_element(By.CSS_SELECTOR, "meta[name='description']").get_attribute("content")
        if meta_desc:
            return meta_desc.strip()
    except Exception as e:
        print(f"Error en estrategia de bajada: {e}")
    
    return "No encontrada"

def _extraer_imagen(driver):
    """Extrae la URL de la imagen principal de Wix"""
    try:
        return driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content")
    except:
        return ""

def _extraer_contenido(driver):
    """Extrae el contenido de la noticia"""
    parrafos = []
    try:
        # El contenido principal está dentro de un div con clase 'fTEXDR'
        contenido_div = driver.find_element(By.CSS_SELECTOR, "div.fTEXDR")
        # Dentro de este div, buscar todos los párrafos
        elementos_parrafo = contenido_div.find_elements(By.CSS_SELECTOR, "p")
        
        for p in elementos_parrafo:
            texto = p.text.strip()
            # Filtrar párrafos vacíos o demasiado cortos (como líneas en blanco)
            if texto and len(texto) > 10:
                # Asegurarse de no incluir la bajada como contenido
                if "No encontrada" not in texto:
                    parrafos.append(texto)
                
    except Exception as e:
        print(f"Error al extraer contenido: {e}")
    
    return parrafos

def _extraer_categoria(driver):
    """Extrae la categoría de la noticia"""
    try:
        # Buscar el enlace de la categoría en el footer del post
        categoria_element = driver.find_element(By.CSS_SELECTOR, "ul.pRGtWE li a.Tp7c0d")
        return categoria_element.text
    except:
        return "No encontrada"

MESES_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
    "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
}

def _parsear_fecha(fecha_str: str) -> date | None:
    if not fecha_str:
        return None

    fecha_str = fecha_str.strip().lower()
    # Wix muestra la fecha como "hace X minutos" o "hace X días".
    # Para este script, vamos a intentar obtener la fecha exacta.
    # Pero si no se puede, se guardará como None.
    # Intentar parsear formatos comunes
    formatos = ["%Y-%m-%d", "%d/%m/%Y", "%d %B, %Y", "%B %d, %Y"]
    for fmt in formatos:
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except ValueError:
            pass
    
    # Formato con meses en español
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
    """Extrae fecha y autor de la noticia en Wix"""
    fecha = None
    autor = "No encontrado"

    try:
        # Buscar el elemento que contiene la fecha y el autor
        # En Wix, está dentro de un ul con clase NtBDdE
        lista_metadata = driver.find_element(By.CSS_SELECTOR, "ul.NtBDdE")
        items = lista_metadata.find_elements(By.TAG_NAME, "li")
        
        for item in items:
            texto = item.text.strip()
            # Si contiene "hace", es probable que sea la fecha
            if "hace" in texto or "min" in texto or "días" in texto:
                # Intentar parsear
                fecha = _parsear_fecha(texto)
                if fecha:
                    # Si se pudo parsear, es una fecha exacta
                    break
                else:
                    # Si no se pudo parsear, intentar buscar el atributo title
                    try:
                        time_element = item.find_element(By.CSS_SELECTOR, "time-ago")
                        title = time_element.get_attribute("title")
                        if title:
                            fecha = _parsear_fecha(title)
                            if fecha:
                                break
                    except:
                        pass
            # Si no es fecha, es el autor
            else:
                autor = texto
        
        # Si el autor no se encontró en el bucle, intentar con un selector más específico
        if autor == "No encontrado":
            autor_element = driver.find_element(By.CSS_SELECTOR, "span.user-name")
            autor = autor_element.text

    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
    
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
        print("SCRAPING DE DESCUBRIENDOCHINA.ORG")
        print("="*80)
        
        # Configurar driver
        driver = configurar_driver()
        
        # Extraer URLs de las páginas de noticias
        urls = extraer_urls_secciones(driver)
        
        if not urls:
            print("No se encontraron URLs de noticias.")
            return 0
        
        print(f"\nProcesando las primeras {min(max_noticias, len(urls))} noticias...")
        
        # Procesar cada URL
        for i, url in enumerate(urls[:max_noticias], 1):
            print(f"\n[{i}/{min(max_noticias, len(urls))}]")
            print(f"URL: {url}")
            
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
    run()
    