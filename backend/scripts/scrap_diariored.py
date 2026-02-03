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
    print("Buscando enlaces de noticias en Diario Red...")
    urls_noticias = []

    try:
        # Visitar la página principal en lugar de la sección específica
        driver.get("https://www.diario-red.com/")
        time.sleep(3)

        # Extraer artículos principales (noticias más recientes)
        articles = driver.find_elements(By.CSS_SELECTOR, "article.onm-new a[href]")
        
        # También buscar enlaces en otros elementos de noticia
        article_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/articulo/']")
        
        # Combinar ambos conjuntos
        all_links = list(articles) + list(article_links)
        
        for a in all_links:
            try:
                href = a.get_attribute("href")
                if href and _es_url_noticia_valida_diario_red(href, urls_noticias):
                    urls_noticias.append(href)
                    print(f"  Encontrada: {href}")
            except:
                continue

        urls_noticias = list(dict.fromkeys(urls_noticias))
        print(f"\nTotal URLs encontradas: {len(urls_noticias)}")

    except Exception as e:
        print(f"Error al extraer URLs: {e}")

    return urls_noticias

def _es_url_noticia_valida_diario_red(href, urls_existentes):
    if not href:
        return False
    
    # Patrones válidos para noticias
    patrones_validos = [
        "/articulo/",
        "/opinion/",
        "/vineta/"
    ]
    
    # Excluir URLs no deseadas
    exclusiones = [
        "/seccion/",
        "/author/",
        "/tag/",
        "/blog/",
        ".jpg", ".png", ".webp", ".gif",
        "facebook.com", "twitter.com", "x.com",
        "whatsapp://"
    ]
    
    # Verificar si es una URL de diario-red.com
    if not href.startswith("https://www.diario-red.com/"):
        return False
    
    # Verificar si contiene algún patrón válido
    es_valido = any(patron in href for patron in patrones_validos)
    
    # Verificar que no contenga exclusiones
    no_excluido = not any(excl in href for excl in exclusiones)
    
    # Verificar que no esté ya en la lista
    no_duplicado = href not in urls_existentes
    
    return es_valido and no_excluido and no_duplicado

def extraer_datos_noticia(driver, url):
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
        time.sleep(3)
        
        # DEPURACIÓN: Ver elementos de fecha
        _debug_elementos_fecha(driver)
        
        # Extraer titular
        datos['titular'] = _extraer_titular_actualizado(driver)
        
        # Extraer bajada/resumen
        datos['bajada'] = _extraer_bajada_actualizada(driver)
        
        # Extraer imagen principal
        datos['imagen'] = _extraer_imagen_actualizada(driver)
        
        # Extraer contenido completo
        contenido_info = _extraer_contenido_actualizado(driver)
        datos['contenido'] = contenido_info['parrafos']
        
        # Extraer fecha y autor
        fecha_autor = _extraer_fecha_autor_actualizado(driver)
        datos['fecha'] = fecha_autor['fecha']
        datos['autor'] = fecha_autor['autor']
        
        # Extraer categoría
        datos['categoria'] = _extraer_categoria_actualizada(driver)
        
        # Si no se encontró fecha, intentar de otros lugares
        if not datos['fecha']:
            datos['fecha'] = _buscar_fecha_alternativa(driver)
        
    except Exception as e:
        print(f"Error general al procesar noticia: {e}")
        import traceback
        traceback.print_exc()
    
    return datos

def _extraer_titular_actualizado(driver):
    try:
        # Buscar en diferentes selectores posibles
        selectores = [
            "h1.title",
            "h1.inner-content-title",
            "h1",
            ".article-header h1",
            ".title"
        ]
        
        for selector in selectores:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                texto = elemento.text.strip()
                if texto and len(texto) > 10:
                    return texto
            except:
                continue
                
        return "No encontrado"
    except Exception as e:
        print(f"Error extrayendo titular: {e}")
        return "No encontrado"

def _extraer_imagen_actualizada(driver):
    try:
        # Buscar imagen principal en diferentes selectores
        selectores = [
            "meta[property='og:image']",
            ".article-media-hero img",
            "figure.article-media-hero img",
            ".article-media img",
            "img[fetchpriority='high']"
        ]
        
        for selector in selectores:
            try:
                if selector.startswith("meta"):
                    elemento = driver.find_element(By.CSS_SELECTOR, selector)
                    return elemento.get_attribute("content")
                else:
                    elemento = driver.find_element(By.CSS_SELECTOR, selector)
                    return elemento.get_attribute("src")
            except:
                continue
                
        return ""
    except:
        return ""

def _extraer_bajada_actualizada(driver):
    try:
        selectores = [
            ".summary.inner-content-summary",
            ".summary",
            ".article-header .summary",
            ".inner-content-summary",
            "div.summary"
        ]
        
        for selector in selectores:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                texto = elemento.text.strip()
                if texto and len(texto) > 20:
                    return texto
            except:
                continue
                
        return "No encontrada"
    except:
        return "No encontrada"

def _extraer_categoria_actualizada(driver):
    try:
        selectores = [
            ".breadcrumb-item:not(:first-child)",
            ".category-name",
            ".pretitle",
            ".content-meta .category",
            ".article-header .category"
        ]
        
        for selector in selectores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                for elemento in elementos:
                    texto = elemento.text.strip()
                    if texto and len(texto) > 2:
                        return texto
            except:
                continue
                
        # Si no encuentra categoría, intentar extraer de la URL
        url = driver.current_url
        if "/articulo/" in url:
            partes = url.split("/")
            for i, parte in enumerate(partes):
                if parte == "articulo" and i + 1 < len(partes):
                    categoria = partes[i + 1]
                    if categoria and categoria not in ["articulo", "opinion"]:
                        return categoria.replace("-", " ").title()
        
        return "General"
    except:
        return "General"
    
def _extraer_contenido_actualizado(driver):
    parrafos = []
    
    try:
        # Buscar el contenido en diferentes secciones
        selectores_contenido = [
            ".content-body",
            ".body",
            ".article-content",
            ".entry-content",
            ".content-data",
            "#body001"
        ]
        
        for selector in selectores_contenido:
            try:
                content = driver.find_element(By.CSS_SELECTOR, selector)
                # Extraer todos los párrafos
                ps = content.find_elements(By.TAG_NAME, "p")
                
                for p in ps:
                    texto = p.text.strip()
                    # Filtrar párrafos vacíos o muy cortos
                    if len(texto) > 30 and not texto.startswith(("Foto:", "Crédito:", "Fuente:")):
                        # Eliminar texto repetitivo (como enlaces de redes sociales)
                        if not any(x in texto.lower() for x in ["compartir en", "síguenos en", "@"]):
                            parrafos.append(texto)
                
                if parrafos:
                    break
                    
            except Exception as e:
                print(f"Error con selector {selector}: {e}")
                continue
                
    except Exception as e:
        print(f"Error extrayendo contenido: {e}")
    
    return {"parrafos": parrafos, "total": len(parrafos)}

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
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}

def _parsear_fecha(fecha_str: str) -> date | None:
    if not fecha_str:
        return None
    
    fecha_str = str(fecha_str).strip().lower()
    
    print(f"  Parseando fecha: '{fecha_str}'")
    
    # Intentar diferentes formatos en orden
    
    # Formato 1: YYYY-MM-DD
    try:
        return datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        pass
    
    # Formato 2: DD/MM/YYYY
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y").date()
    except ValueError:
        pass
    
    # Formato 3: DD/MM/YY (dos dígitos para año)
    try:
        if len(fecha_str) == 8 and fecha_str[2] == '/' and fecha_str[5] == '/':
            dia, mes, anio = fecha_str.split('/')
            if len(anio) == 2:
                anio = "20" + anio
            return datetime.strptime(f"{dia}/{mes}/{anio}", "%d/%m/%Y").date()
    except:
        pass
    
    # Formato 4: YYYYMMDD (de URLs)
    try:
        if len(fecha_str) == 8 and fecha_str.isdigit():
            return datetime.strptime(fecha_str, "%Y%m%d").date()
    except:
        pass
    
    # Formato 5: Fechas en español
    try:
        m = re.match(r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)(?:\s+de\s+(\d{4}))?", fecha_str)
        if m:
            dia, mes_es, anio = m.groups()
            if not anio:
                anio = str(datetime.now().year)
            mes_num = MESES_ES.get(mes_es.lower())
            if mes_num:
                return date(int(anio), mes_num, int(dia))
    except:
        pass
    
    print(f"  No se pudo parsear la fecha: '{fecha_str}'")
    return None

def _extraer_fecha_autor_actualizado(driver):
    fecha = None
    autor = "Redacción"
    
    try:
        # EXTRAER FECHA - Mejorado
        fecha_selectores = [
            ".content-meta-date-created",
            ".content-meta-date",
            "time[datetime]",
            "time",
            ".date",
            ".published",
            ".article-date",
            ".metadata-body-start .content-meta-date"
        ]
        
        for selector in fecha_selectores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                for elemento in elementos:
                    fecha_texto = elemento.text.strip()
                    
                    # Si encontramos texto de fecha
                    if fecha_texto:
                        print(f"  Texto de fecha encontrado: '{fecha_texto}'")
                        
                        # Caso 1: Formato "01/02/26 | 10:00"
                        if "|" in fecha_texto:
                            fecha_texto = fecha_texto.split("|")[0].strip()
                            # Formatear para parsear
                            if "/" in fecha_texto:
                                partes = fecha_texto.split("/")
                                if len(partes) == 3:
                                    dia, mes, anio = partes
                                    if len(anio) == 2:  # "26" → "2026"
                                        anio = "20" + anio
                                    fecha_texto = f"{anio}-{mes}-{dia}"
                        
                        # Caso 2: Atributo datetime en time
                        if not fecha_texto and selector == "time[datetime]":
                            fecha_texto = elemento.get_attribute("datetime")
                        
                        fecha = _parsear_fecha(fecha_texto)
                        if fecha:
                            print(f"  Fecha parseada: {fecha}")
                            break
                            
            except Exception as e:
                print(f"  Error con selector {selector}: {e}")
                continue
                
        # Si no encontramos fecha, intentar extraer de la URL
        if not fecha:
            try:
                url = driver.current_url
                # Buscar patrones de fecha en la URL
                import re
                patron_fecha = re.search(r'/(\d{8})/', url)
                if patron_fecha:
                    fecha_str = patron_fecha.group(1)
                    # Convertir "20260201" a "2026-02-01"
                    fecha = _parsear_fecha(fecha_str[:4] + "-" + fecha_str[4:6] + "-" + fecha_str[6:8])
                    print(f"  Fecha extraída de URL: {fecha}")
            except:
                pass
        
        # EXTRAER AUTOR - Mejorado
        autor_selectores = [
            ".author-name a",
            ".author-profile .author-name a",
            "a[href*='/author/']",
            ".author-data .author-name",
            ".content-meta .author-name",
            ".author-header .author-name",
            ".onm-new-author .author-name"
        ]
        
        for selector in autor_selectores:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                for elemento in elementos:
                    autor_texto = elemento.text.strip()
                    if autor_texto and autor_texto.lower() not in ["redacción", "diario red", "editorial"]:
                        autor = autor_texto
                        print(f"  Autor encontrado: {autor}")
                        break
                if autor != "Redacción":
                    break
            except Exception as e:
                print(f"  Error con selector autor {selector}: {e}")
                continue
                
    except Exception as e:
        print(f"Error extrayendo fecha/autor: {e}")
        import traceback
        traceback.print_exc()
    
    return {"fecha": fecha, "autor": autor}

def _debug_elementos_fecha(driver):
    """Función para depurar elementos de fecha"""
    print("\n=== DEBUG DE FECHAS ===")
    
    # Buscar todos los elementos que podrían contener fechas
    posibles_selectores = [
        ".content-meta-date-created",
        ".content-meta-date",
        "time",
        ".date",
        ".published",
        "[datetime]",
        ".metadata-body"
    ]
    
    for selector in posibles_selectores:
        try:
            elementos = driver.find_elements(By.CSS_SELECTOR, selector)
            if elementos:
                print(f"\nSelector: {selector}")
                for i, elem in enumerate(elementos[:3]):  # Mostrar solo primeros 3
                    try:
                        texto = elem.text.strip()
                        if texto:
                            print(f"  [{i}] Texto: '{texto}'")
                        # Verificar atributos
                        attrs = ["datetime", "content", "title"]
                        for attr in attrs:
                            val = elem.get_attribute(attr)
                            if val:
                                print(f"  [{i}] Atributo {attr}: '{val}'")
                    except:
                        continue
        except:
            pass
    
    print("=== FIN DEBUG ===\n")

def _buscar_fecha_alternativa(driver):
    """Buscar fecha en otros lugares de la página"""
    try:
        # Buscar en breadcrumbs
        try:
            breadcrumbs = driver.find_elements(By.CSS_SELECTOR, ".breadcrumb-item")
            for crumb in breadcrumbs:
                texto = crumb.text.strip()
                if re.match(r'\d{2}/\d{2}/\d{2,4}', texto):
                    return _parsear_fecha(texto)
        except:
            pass
        
        # Buscar en meta tags
        try:
            meta_fecha = driver.find_element(By.CSS_SELECTOR, "meta[property='article:published_time']")
            fecha_str = meta_fecha.get_attribute("content")
            if fecha_str:
                # Extraer solo la parte de la fecha "YYYY-MM-DD"
                if "T" in fecha_str:
                    fecha_str = fecha_str.split("T")[0]
                return _parsear_fecha(fecha_str)
        except:
            pass
        
        # Buscar en URL como último recurso
        url = driver.current_url
        patrones = [
            r'/(\d{4})(\d{2})(\d{2})/',
            r'/(\d{2})-(\d{2})-(\d{4})/',
            r'(\d{4})/(\d{2})/(\d{2})/'
        ]
        
        for patron in patrones:
            match = re.search(patron, url)
            if match:
                grupos = match.groups()
                if len(grupos) == 3:
                    if len(grupos[0]) == 4:  # YYYY-MM-DD
                        fecha_str = f"{grupos[0]}-{grupos[1]}-{grupos[2]}"
                    else:  # DD-MM-YYYY
                        fecha_str = f"{grupos[2]}-{grupos[1]}-{grupos[0]}"
                    return _parsear_fecha(fecha_str)
                    
    except Exception as e:
        print(f"Error en búsqueda alternativa de fecha: {e}")
    
    return None

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

def ejecutar_scraping(max_noticias=15):
    """Función principal de scraping"""
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE DIARIO-RED.COM")
        print("="*80)
        
        # Configurar driver
        driver = configurar_driver()
        
        # Extraer URLs de la página principal
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
            
            # Mostrar información de depuración
            print(f"  Titular: {datos['titular'][:80]}...")
            print(f"  Autor: {datos['autor']}")
            print(f"  Fecha: {datos['fecha']}")
            print(f"  Párrafos extraídos: {len(datos['contenido'])}")
            
            # Guardar en DB si tiene contenido
            if datos['contenido']:
                if guardar_en_db(datos):
                    articulos_procesados += 1
            else:
                print(f"  Sin contenido suficiente: {datos['titular'][:50]}...")
            
            # Pausa para no sobrecargar
            if i < min(max_noticias, len(urls)):
                time.sleep(2)  # Aumentar tiempo de espera
        
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