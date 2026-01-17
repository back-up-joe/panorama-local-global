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
    Extrae URLs de noticias principales y recientes de rebelion.org
    Retorna: lista de URLs
    """
    print("Buscando enlaces de noticias principales en rebelion.org...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal
        driver.get("https://rebelion.org/")
        time.sleep(3)
        
        # Hacer scroll para cargar contenido
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # Estrategia 1: Buscar en la portada principal (artículos destacados)
        print("\nBuscando en portada principal...")
        try:
            portada_section = driver.find_element(By.CSS_SELECTOR, ".portada")
            enlaces_portada = portada_section.find_elements(By.CSS_SELECTOR, "article a")
            
            for enlace in enlaces_portada:
                try:
                    href = enlace.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado en portada: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  No se pudo acceder a portada: {e}")
        
        # Estrategia 2: Buscar en artículos sticky (destacados)
        print("\nBuscando artículos destacados...")
        try:
            sticky_articles = driver.find_elements(By.CSS_SELECTOR, "article.sticky")
            for articulo in sticky_articles:
                try:
                    enlaces = articulo.find_elements(By.TAG_NAME, "a")
                    for enlace in enlaces:
                        href = enlace.get_attribute("href")
                        if _es_url_noticia_valida(href, urls_noticias):
                            urls_noticias.append(href)
                            print(f"  Encontrado artículo destacado: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  No se pudieron buscar artículos destacados: {e}")
        
        # Estrategia 3: Buscar en títulos de noticias recientes
        print("\nBuscando noticias recientes...")
        try:
            titulos_recientes = driver.find_elements(By.CSS_SELECTOR, "h2.entry-title a, h1.entry-title a")
            for titulo in titulos_recientes:
                try:
                    href = titulo.get_attribute("href")
                    if _es_url_noticia_valida(href, urls_noticias):
                        urls_noticias.append(href)
                        print(f"  Encontrado título reciente: {href[:60]}...")
                except:
                    continue
        except Exception as e:
            print(f"  No se pudieron buscar títulos recientes: {e}")
        
        # Eliminar duplicados manteniendo el orden
        urls_noticias = list(dict.fromkeys(urls_noticias))
        
        print(f"\nTotal de URLs encontradas: {len(urls_noticias)}")
        
        # Mostrar las URLs encontradas
        if urls_noticias:
            print("\nPrimeras 10 URLs encontradas:")
            for i, url in enumerate(urls_noticias[:10], 1):
                print(f"{i}. {url}")
            if len(urls_noticias) > 10:
                print(f"... y {len(urls_noticias) - 10} más")
        
    except Exception as e:
        print(f"Error al buscar enlaces: {e}")
    
    return urls_noticias

def _es_url_noticia_valida(href, urls_existentes):
    """
    Valida si una URL es una noticia válida para rebelion.org
    Retorna: True si es válida, False en caso contrario
    """
    if not href:
        return False
    
    # Debe ser de rebelion.org
    if "rebelion.org" not in href:
        return False
    
    # No debe ser una página de lista o categoría
    exclusiones = [
        '/categoria/', '/category/', '/tag/', '/author/', '/autor/',
        '?s=', '#', '/feed/', '/comments/', '/wp-content/', 
        '/busqueda-avanzada', '/galeria/', '/nosotros', '/terminos-uso'
    ]
    
    for excluir in exclusiones:
        if excluir in href:
            return False
    
    # No debe terminar con extensiones de archivo
    if href.endswith(('.jpg', '.png', '.gif', '.jpeg', '.pdf', '.zip')):
        return False
    
    # No debe ser la página principal
    if href == "https://rebelion.org/" or href == "https://rebelion.org":
        return False
    
    # No debe estar ya en la lista
    if href in urls_existentes:
        return False
    
    # Debe tener una estructura de artículo (al menos una barra después del dominio)
    if href.count('/') < 3:
        return False
    
    return True

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
        
        # Extraer categoria
        datos['categoria'] = _extraer_categoria(driver)
        
    except Exception as e:
        print(f"Error general al procesar noticia: {e}")
    
    return datos

def _extraer_titular(driver):
    """Extrae el titular de la noticia en rebelion.org"""
    try:
        return driver.find_element(By.CSS_SELECTOR, "h1.entry-title").text.strip()
    except:
        try:
            return driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            return "No encontrado"

def _extraer_bajada(driver):
    """Extrae la bajada/entradilla de la noticia en rebelion.org"""
    try:
        # Intentar con la entradilla específica
        return driver.find_element(By.CSS_SELECTOR, ".entradilla p").text.strip()
    except:
        try:
            # Buscar el primer párrafo del contenido
            contenido = driver.find_element(By.CSS_SELECTOR, ".entry-content, #cols")
            primeros_parrafos = contenido.find_elements(By.TAG_NAME, "p")
            for p in primeros_parrafos[:3]:
                texto = p.text.strip()
                if len(texto) > 50:
                    return texto[:250] + "..." if len(texto) > 250 else texto
        except:
            pass
    
    return "No encontrada"

def _extraer_imagen(driver):
    """Extrae la URL de la imagen principal en rebelion.org"""
    try:
        # 1. Buscar imagen destacada
        return driver.find_element(By.CSS_SELECTOR, ".wp-post-image").get_attribute("src")
    except:
        try:
            # 2. Buscar cualquier imagen dentro del contenido
            return driver.find_element(By.CSS_SELECTOR, ".entry-content img, #cols img").get_attribute("src")
        except:
            try:
                # 3. Buscar imagen en el header del artículo
                return driver.find_element(By.CSS_SELECTOR, ".entry-header img").get_attribute("src")
            except:
                return ""

def _extraer_contenido(driver):
    """Extrae el contenido de la noticia en rebelion.org"""
    parrafos = []
    total = 0
    
    try:
        # Buscar el contenido principal
        contenido_div = driver.find_element(By.CSS_SELECTOR, ".entry-content, #cols")
        elementos_parrafo = contenido_div.find_elements(By.TAG_NAME, "p")
        total = len(elementos_parrafo)
        
        for p in elementos_parrafo:
            texto = p.text.strip()
            # Filtrar párrafos significativos
            if texto and len(texto) > 20 and not texto.startswith("Fuente:"):
                parrafos.append(texto)
                
    except Exception as e:
        print(f"Error al extraer contenido: {e}")
    
    return {'parrafos': parrafos, 'total': total}

def _extraer_categoria(driver):
    """Extrae la categoria de la noticia en rebelion.org"""
    try:
        # Buscar en los metadatos del artículo
        categorias = driver.find_elements(By.CSS_SELECTOR, ".entry-meta .category a, .category a")
        if categorias:
            return ", ".join([cat.text for cat in categorias])
    except:
        try:
            # Buscar en el encabezado
            return driver.find_element(By.CSS_SELECTOR, ".category").text
        except:
            pass
    
    return "No encontrada"

'''
def _extraer_fecha_autor(driver):
    """Extrae fecha y autor de la noticia en rebelion.org"""
    fecha = "No encontrada"
    autor = "No encontrado"
    
    try:
        # PATRÓN PRINCIPAL: Buscar en .entry-meta.big (páginas individuales)
        try:
            entry_meta = driver.find_element(By.CSS_SELECTOR, ".entry-meta.big")
            
            # Extraer autor - buscar "Por " en el texto
            texto_meta = entry_meta.text
            if "Por " in texto_meta:
                partes = texto_meta.split("Por ")
                if len(partes) > 1:
                    autor_part = partes[1].split(" | ")[0]
                    autor = autor_part.strip()
            
            # Extraer fecha - buscar patrón dd/mm/aaaa
            import re
            fecha_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', entry_meta.text)
            if fecha_match:
                fecha = fecha_match.group(0)
                
        except:
            # PATRÓN SECUNDARIO: Buscar en .entry-meta (sin .big)
            try:
                entry_meta = driver.find_element(By.CSS_SELECTOR, ".entry-meta")
                
                # Buscar autor
                try:
                    autor_elem = entry_meta.find_element(By.CSS_SELECTOR, ".author a, .author")
                    autor = autor_elem.text.strip()
                except:
                    pass
                
                # Buscar fecha
                try:
                    fecha_elem = entry_meta.find_element(By.CSS_SELECTOR, ".date, time")
                    fecha = fecha_elem.text.strip()
                except:
                    # Buscar patrón de fecha en el texto
                    import re
                    fecha_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', entry_meta.text)
                    if fecha_match:
                        fecha = fecha_match.group(0)
                        
            except:
                # ÚLTIMO RECURSO: Buscar en todo el documento
                try:
                    # Buscar cualquier autor
                    autor_elems = driver.find_elements(By.CSS_SELECTOR, ".author, .author-name, [itemprop='author']")
                    for elem in autor_elems:
                        texto = elem.text.strip()
                        if texto and len(texto) > 2:
                            autor = texto
                            break
                except:
                    pass
                
                try:
                    # Buscar cualquier fecha
                    fecha_elems = driver.find_elements(By.CSS_SELECTOR, "time, .date, .published")
                    for elem in fecha_elems:
                        texto = elem.text.strip()
                        if texto and re.search(r'\d{1,2}/\d{1,2}/\d{4}', texto):
                            fecha = texto
                            break
                except:
                    pass
    
    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")
    
    return {'fecha': fecha, 'autor': autor} '''

#######################################################################################################

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
    """Extrae fecha y autor de la noticia en rebelion.org"""
    fecha = None
    autor = "No encontrado"
    fecha_raw = None

    try:
        # PATRÓN PRINCIPAL
        try:
            entry_meta = driver.find_element(By.CSS_SELECTOR, ".entry-meta.big")
            texto_meta = entry_meta.text

            # Autor
            if "Por " in texto_meta:
                partes = texto_meta.split("Por ")
                if len(partes) > 1:
                    autor = partes[1].split(" | ")[0].strip()

            # Fecha dd/mm/yyyy
            fecha_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', texto_meta)
            if fecha_match:
                fecha_raw = fecha_match.group(0)

        except:
            # PATRÓN SECUNDARIO
            try:
                entry_meta = driver.find_element(By.CSS_SELECTOR, ".entry-meta")

                try:
                    autor_elem = entry_meta.find_element(By.CSS_SELECTOR, ".author a, .author")
                    autor = autor_elem.text.strip()
                except:
                    pass

                try:
                    fecha_elem = entry_meta.find_element(By.CSS_SELECTOR, ".date, time")
                    fecha_raw = fecha_elem.text.strip()
                except:
                    fecha_match = re.search(r'\d{1,2}/\d{1,2}/\d{4}', entry_meta.text)
                    if fecha_match:
                        fecha_raw = fecha_match.group(0)

            except:
                # ÚLTIMO RECURSO
                try:
                    fecha_elems = driver.find_elements(By.CSS_SELECTOR, "time, .date, .published")
                    for elem in fecha_elems:
                        texto = elem.text.strip()
                        if re.search(r'\d{1,2}/\d{1,2}/\d{4}', texto):
                            fecha_raw = texto
                            break
                except:
                    pass

    except Exception as e:
        print(f"Error al extraer fecha/autor: {e}")

    # USAR EL PARSER AQUÍ
    fecha = _parsear_fecha(fecha_raw)

    return {
        'fecha': fecha,   # datetime.date | None
        'autor': autor
    }

#######################################################################################################

def guardar_en_db(datos):
    """Guardar datos en la base de datos"""
    try:
        # Verificar si ya existe
        if Article.objects.filter(url=datos['url']).exists():
            print(f"Ya existe: {datos['titular'][:50]}...")
            return False
        
        # Convertir contenido de lista a string
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
    """Función principal de scraping para rebelion.org"""
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE REBELION.ORG - NOTICIAS PRINCIPALES Y RECIENTES")
        print("="*80)
        
        # Configurar driver
        driver = configurar_driver()
        
        # Extraer URLs de noticias principales
        urls = extraer_urls_secciones(driver)
        
        if not urls:
            print("No se encontraron URLs de noticias")
            return 0
        
        print(f"\nProcesando las primeras {min(max_noticias, len(urls))} noticias...")
        
        # Procesar cada URL
        for i, url in enumerate(urls[:max_noticias], 1):
            print(f"\n[{i}/{min(max_noticias, len(urls))}] Procesando: {url[:60]}...")
            
            # Extraer datos
            datos = extraer_datos_noticia(driver, url)
            
            # Mostrar datos básicos
            print(f"  Titular: {datos['titular'][:60]}...")
            print(f"  Autor: {datos['autor']}, Fecha: {datos['fecha']}")
            print(f"  Párrafos extraídos: {len(datos['contenido'])}")
            
            # Guardar en DB si tiene contenido
            if datos['contenido']:
                if guardar_en_db(datos):
                    articulos_procesados += 1
            else:
                print(f"  ⚠ Sin contenido suficiente: {datos['titular'][:50]}...")
            
            # Pausa para no sobrecargar
            if i < min(max_noticias, len(urls)):
                time.sleep(1)
        
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
    print(f"Artículos procesados: {cantidad}")
    
    # Mostrar estadísticas
    total = Article.objects.count()
    print(f"Total en base de datos: {total}")
    print(f"{'='*80}")

if __name__ == "__main__":
    run()