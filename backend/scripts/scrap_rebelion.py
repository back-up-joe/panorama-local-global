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
    Extrae URLs de noticias de las secciones de rebelion.org
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias en rebelion.org...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal
        driver.get("https://www.rebelion.org/")
        time.sleep(3)
        
        # Hacer scroll para cargar contenido dinámico
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Estrategia 1: Buscar en todos los enlaces de artículos basándonos en la estructura HTML proporcionada
        print("\nBuscando enlaces de artículos...")
        
        # En rebelion.org, los artículos están en contenedores con clase específica
        # Buscar en los widgets de "sticky-posts" y otros contenedores de artículos
        selectores_articulos = [
            ".upw-posts .entry-title a",  # Enlaces dentro de widgets
            "article .entry-title a",     # Enlaces dentro de articles
            ".sticky-posts a",            # Posts destacados
            ".lateral .entry-title a",    # Columnas laterales
            "h2.entry-title a",           # Títulos de artículos
            "h1.entry-title a",           # Títulos principales
            ".post .entry-title a",       # Posts individuales
        ]
        
        urls_encontradas = set()  # Usar set para evitar duplicados
        
        for selector in selectores_articulos:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                for elemento in elementos:
                    try:
                        href = elemento.get_attribute("href")
                        if href and "rebelion.org" in href:
                            # Filtrar URLs no deseadas
                            if not any(excluir in href for excluir in ['/category/', '/tag/', '/author/', '?s=', '#']):
                                if href not in urls_encontradas:
                                    # Verificar que sea un artículo individual (no página de lista)
                                    if not re.match(r'https://www\.rebelion\.org/(categoria|tag|author)/', href):
                                        urls_encontradas.add(href)
                    except:
                        continue
            except:
                continue
        
        # Estrategia 2: Buscar específicamente en la estructura principal de la página
        # En la página principal, hay múltiples widgets con artículos
        try:
            # Buscar en los artículos principales (portada)
            articulos_principales = driver.find_elements(By.CSS_SELECTOR, ".portada .upw-posts article")
            for articulo in articulos_principales:
                try:
                    enlaces = articulo.find_elements(By.CSS_SELECTOR, "a")
                    for enlace in enlaces:
                        href = enlace.get_attribute("href")
                        if href and "rebelion.org" in href and '/al-pueblo-de-estados-unidos-le-digo' not in href:
                            if not any(excluir in href for excluir in ['/category/', '/tag/', '/author/', '?s=', '#']):
                                urls_encontradas.add(href)
                except:
                    continue
        except:
            pass
        
        # Buscar en las columnas laterales
        try:
            columnas_laterales = driver.find_elements(By.CSS_SELECTOR, ".lateral .entry-title a")
            for enlace in columnas_laterales:
                try:
                    href = enlace.get_attribute("href")
                    if href and "rebelion.org" in href:
                        if not any(excluir in href for excluir in ['/category/', '/tag/', '/author/', '?s=', '#']):
                            urls_encontradas.add(href)
                except:
                    continue
        except:
            pass
        
        # Convertir set a lista
        urls_noticias = list(urls_encontradas)
        
        print(f"\nTotal de URLs encontradas: {len(urls_noticias)}")
        
        # Mostrar algunas URLs para debug
        if urls_noticias:
            print("\nPrimeras 10 URLs encontradas:")
            for i, url in enumerate(urls_noticias[:10], 1):
                print(f"{i}. {url}")
            if len(urls_noticias) > 10:
                print(f"... y {len(urls_noticias) - 10} más")
        else:
            print("No se encontraron URLs de artículos.")
            
    except Exception as e:
        print(f"Error al buscar enlaces: {e}")
        import traceback
        traceback.print_exc()
    
    return urls_noticias

def extraer_datos_noticia(driver, url):
    """
    Extrae todos los datos de una noticia individual de rebelion.org
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
        datos['titular'] = _extraer_titular_rebelion(driver)
        
        # Extraer bajada
        datos['bajada'] = _extraer_bajada_rebelion(driver)
        
        # Extraer imagen
        datos['imagen'] = _extraer_imagen_rebelion(driver)
        
        # Extraer contenido
        contenido_info = _extraer_contenido_rebelion(driver)
        datos['contenido'] = contenido_info['parrafos']
        
        # Extraer fecha y autor
        fecha_autor = _extraer_fecha_autor_rebelion(driver)
        datos['fecha'] = fecha_autor['fecha']
        datos['autor'] = fecha_autor['autor']
        
        # Extraer categoria
        datos['categoria'] = _extraer_categoria_rebelion(driver)
        
    except Exception as e:
        print(f"Error general al procesar noticia: {e}")
        import traceback
        traceback.print_exc()
    
    return datos

def _extraer_titular_rebelion(driver):
    """Extrae el titular de la noticia en rebelion.org"""
    try:
        # Primero intentar con el selector principal
        return driver.find_element(By.CSS_SELECTOR, "h1.entry-title").text.strip()
    except:
        try:
            # Fallback a otros selectores
            return driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            try:
                return driver.find_element(By.CSS_SELECTOR, ".entry-title").text.strip()
            except:
                return "No encontrado"

def _extraer_bajada_rebelion(driver):
    """Extrae la bajada/entradilla de la noticia en rebelion.org"""
    try:
        # Intentar extraer de la entradilla
        return driver.find_element(By.CSS_SELECTOR, ".entradilla p").text.strip()
    except:
        try:
            # Buscar el primer párrafo del contenido
            contenido = driver.find_element(By.CSS_SELECTOR, ".entry-content")
            primeros_parrafos = contenido.find_elements(By.TAG_NAME, "p")
            for p in primeros_parrafos[:3]:  # Revisar primeros 3 párrafos
                texto = p.text.strip()
                if len(texto) > 50:
                    return texto[:250] + "..." if len(texto) > 250 else texto
        except:
            pass
    
    return "No encontrada"

def _extraer_imagen_rebelion(driver):
    """Extrae la URL de la imagen principal en rebelion.org"""
    try:
        # 1. Buscar imagen destacada
        return driver.find_element(By.CSS_SELECTOR, ".wp-post-image").get_attribute("src")
    except:
        try:
            # 2. Buscar cualquier imagen dentro del contenido
            return driver.find_element(By.CSS_SELECTOR, ".entry-content img").get_attribute("src")
        except:
            try:
                # 3. Buscar imagen en el header del artículo
                return driver.find_element(By.CSS_SELECTOR, ".entry-header img").get_attribute("src")
            except:
                return ""

def _extraer_contenido_rebelion(driver):
    """Extrae el contenido de la noticia en rebelion.org"""
    parrafos = []
    total = 0
    
    try:
        # Buscar el contenido principal
        contenido_div = driver.find_element(By.CSS_SELECTOR, ".entry-content")
        elementos_parrafo = contenido_div.find_elements(By.TAG_NAME, "p")
        total = len(elementos_parrafo)
        
        for p in elementos_parrafo:
            texto = p.text.strip()
            # Filtrar párrafos demasiado cortos o que sean solo fuentes/enlaces
            if texto and len(texto) > 20 and not texto.startswith("Fuente:"):
                parrafos.append(texto)
                
    except Exception as e:
        print(f"Error al extraer contenido: {e}")
        try:
            # Fallback: buscar cualquier contenido de texto
            contenido = driver.find_element(By.CSS_SELECTOR, "#main").text
            if contenido:
                lineas = contenido.split('\n')
                for linea in lineas:
                    if len(linea.strip()) > 50:
                        parrafos.append(linea.strip())
        except:
            pass
    
    return {'parrafos': parrafos, 'total': total}

def _extraer_categoria_rebelion(driver):
    """Extrae la categoria de la noticia en rebelion.org"""
    try:
        # Buscar en los metadatos del artículo
        categorias = driver.find_elements(By.CSS_SELECTOR, ".entry-meta .category a")
        if categorias:
            return ", ".join([cat.text for cat in categorias])
    except:
        try:
            # Buscar en breadcrumbs o navegación
            return driver.find_element(By.CSS_SELECTOR, ".category").text
        except:
            pass
    
    return "No encontrada"

def _extraer_fecha_autor_rebelion(driver):
    """Extrae fecha y autor de la noticia en rebelion.org"""
    fecha = "No encontrada"
    autor = "No encontrado"
    
    try:
        # Buscar en los metadatos del artículo
        entry_meta = driver.find_element(By.CSS_SELECTOR, ".entry-meta")
        
        # Extraer autor
        try:
            autor_element = entry_meta.find_element(By.CSS_SELECTOR, ".author a")
            autor = autor_element.text
        except:
            try:
                autor = entry_meta.find_element(By.CSS_SELECTOR, ".author").text
            except:
                pass
        
        # Extraer fecha
        try:
            fecha_element = entry_meta.find_element(By.CSS_SELECTOR, ".date")
            fecha = fecha_element.text
        except:
            try:
                fecha = entry_meta.find_element(By.CSS_SELECTOR, "time").text
            except:
                pass
        
    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
        # Intentar métodos alternativos
        try:
            # Buscar por itemprop
            autor = driver.find_element(By.CSS_SELECTOR, "[itemprop='author']").text
        except:
            pass
        
        try:
            fecha = driver.find_element(By.CSS_SELECTOR, "time[datetime]").get_attribute("datetime")
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
    """Función principal de scraping para rebelion.org"""
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE REBELION.ORG")
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
            print(f"\n[{i}/{min(max_noticias, len(urls))}] Procesando: {url}")
            
            # Extraer datos
            datos = extraer_datos_noticia(driver, url)
            
            # Mostrar datos extraídos para debug
            print(f"Titular: {datos['titular'][:80]}...")
            print(f"Autor: {datos['autor']}")
            print(f"Fecha: {datos['fecha']}")
            print(f"Párrafos extraídos: {len(datos['contenido'])}")
            
            # Guardar en DB si tiene contenido
            if datos['contenido']:
                if guardar_en_db(datos):
                    articulos_procesados += 1
            else:
                print(f"Sin contenido suficiente: {datos['titular'][:50]}...")
            
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
    from news.models import Article
    total = Article.objects.count()
    print(f"Total en base de datos: {total}")
    print(f"{'='*80}")

if __name__ == "__main__":
    run()