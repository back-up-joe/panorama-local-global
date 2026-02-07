import sys
import os
import time
import django
from datetime import datetime, date
import re
from typing import List, Dict, Optional

# Configurar Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scraper.settings')
django.setup()

from news.models import Article
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def extraer_urls_noticias(driver, max_noticias=20):
    """
    Extrae URLs de noticias de JacobinLat en orden CORRECTO:
    1. Sección principal (#loop-container) - LAS MÁS RECIENTES
    2. Segunda sección (#loop-container2)
    3. Barra lateral (solo si necesitamos más)
    """
    print("Extrayendo URLs de noticias de JacobinLat...")
    
    urls_noticias = []
    
    try:
        # Navegar a la página principal
        driver.get("https://jacobinlat.com/")
        time.sleep(3)
        
        # PRIMERO: Sección PRINCIPAL (#loop-container) - LAS MÁS RECIENTES
        print("\n1. Buscando en SECCIÓN PRINCIPAL (más recientes)...")
        urls_principal = []
        try:
            main_section = driver.find_element(By.ID, "loop-container")
            # Buscar todos los enlaces de artículos
            elementos_articulo = main_section.find_elements(By.CSS_SELECTOR, "article, .post")
            
            for articulo in elementos_articulo:
                try:
                    # Buscar enlaces dentro de cada artículo
                    enlaces = articulo.find_elements(By.CSS_SELECTOR, "a[href*='jacobinlat.com']")
                    for enlace in enlaces:
                        href = enlace.get_attribute("href")
                        if _es_url_noticia_valida(href, urls_principal):
                            urls_principal.append(href)
                            print(f"  ✓ Principal: {href[:70]}...")
                            break  # Solo un enlace por artículo
                except:
                    continue
        except Exception as e:
            print(f"  ✗ Error en sección principal: {e}")
        
        # SEGUNDO: Segunda sección (#loop-container2)
        print("\n2. Buscando en segunda sección...")
        urls_segunda = []
        try:
            second_section = driver.find_element(By.ID, "loop-container2")
            elementos_articulo = second_section.find_elements(By.CSS_SELECTOR, "article, .post")
            
            for articulo in elementos_articulo:
                try:
                    enlaces = articulo.find_elements(By.CSS_SELECTOR, "a[href*='jacobinlat.com']")
                    for enlace in enlaces:
                        href = enlace.get_attribute("href")
                        if _es_url_noticia_valida(href, urls_segunda) and href not in urls_principal:
                            urls_segunda.append(href)
                            print(f"  ✓ Segunda: {href[:70]}...")
                            break
                except:
                    continue
        except Exception as e:
            print(f"  ✗ Error en segunda sección: {e}")
        
        # TERCERO: Barra lateral (solo si necesitamos más noticias)
        print("\n3. Buscando en barra lateral...")
        urls_lateral = []
        try:
            sidebar = driver.find_element(By.CSS_SELECTOR, ".sidebar-left")
            elementos_noticia = sidebar.find_elements(By.CSS_SELECTOR, ".post-item, li")
            
            for item in elementos_noticia:
                try:
                    enlaces = item.find_elements(By.CSS_SELECTOR, "a[href*='jacobinlat.com']")
                    for enlace in enlaces:
                        href = enlace.get_attribute("href")
                        if (_es_url_noticia_valida(href, urls_lateral) and 
                            href not in urls_principal and 
                            href not in urls_segunda):
                            urls_lateral.append(href)
                            print(f"  ✓ Lateral: {href[:70]}...")
                            break
                except:
                    continue
        except Exception as e:
            print(f"  ✗ Error en barra lateral: {e}")
        
        # COMBINAR en el ORDEN CORRECTO: 1. Principal, 2. Segunda, 3. Lateral
        urls_noticias = urls_principal + urls_segunda + urls_lateral
        
        # Eliminar cualquier duplicado que pueda haber
        urls_noticias = list(dict.fromkeys(urls_noticias))
        
        # Tomar solo las más recientes hasta el límite
        urls_noticias = urls_noticias[:max_noticias]
        
        print(f"\n✅ Total de URLs encontradas: {len(urls_noticias)}")
        print(f"   - Principal: {len(urls_principal)}")
        print(f"   - Segunda: {len(urls_segunda)}")
        print(f"   - Lateral: {len(urls_lateral)}")
        
        # Mostrar las URLs encontradas en orden
        if urls_noticias:
            print("\n📰 URLs ENCONTRADAS (ordenadas de más reciente a menos):")
            for i, url in enumerate(urls_noticias, 1):
                # Extraer fecha de la URL para mostrar
                fecha_match = re.search(r'/(\d{4})/(\d{2})/', url)
                if fecha_match:
                    fecha_str = f"{fecha_match.group(2)}/{fecha_match.group(1)}"
                else:
                    fecha_str = "??/????"
                print(f"{i:2d}. [{fecha_str}] {url}")
        
    except Exception as e:
        print(f"❌ Error al buscar enlaces: {e}")
        import traceback
        traceback.print_exc()
    
    return urls_noticias

def _es_url_noticia_valida(href: str, urls_existentes: List[str]) -> bool:
    """
    Valida si una URL es una noticia válida para JacobinLat
    """
    if not href:
        return False
    
    # Patrón para URLs de artículos
    patron_articulo = re.compile(r'https://jacobinlat\.com/\d{4}/\d{2}/[^/]+/$')
    
    condiciones = [
        href.startswith("https://jacobinlat.com/"),
        patron_articulo.match(href) is not None,
        not href.endswith((".jpg", ".png", ".gif", ".webp")),
        not any(x in href for x in ["/category/", "/tag/", "/author/", "/page/", "/revista/", "/suscribirse/"]),
        href != "https://jacobinlat.com/",
        href not in urls_existentes,
        "/2026/" in href or "/2025/" in href  # Artículos de 2025-2026
    ]
    
    return all(condiciones)

def extraer_datos_noticia(driver, url: str) -> Dict:
    """
    Extrae todos los datos de una noticia individual de JacobinLat
    """
    datos = {
        'url': url,
        'titular': 'No encontrado',
        'bajada': 'No encontrada',
        'imagen': 'No encontrada',
        'contenido': [],
        'fecha': None,
        'autor': 'No encontrado',
        'categoria': 'No encontrada',
    }
    
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "article"))
        )
        time.sleep(2)
        
        # Extraer datos según la estructura de JacobinLat
        datos['titular'] = _extraer_titular_jacobin(driver)
        datos['bajada'] = _extraer_bajada_jacobin(driver)
        datos['imagen'] = _extraer_imagen_jacobin(driver)
        
        # Extraer contenido completo
        contenido_info = _extraer_contenido_jacobin(driver)
        datos['contenido'] = contenido_info['parrafos']
        
        # Extraer metadatos
        fecha_autor = _extraer_fecha_autor_jacobin(driver)
        datos['fecha'] = fecha_autor['fecha']
        datos['autor'] = fecha_autor['autor']
        
        # Extraer categorías
        datos['categoria'] = _extraer_categoria_jacobin(driver)
        
        print(f"✅ Extraídos: {len(datos['contenido'])} párrafos, {datos['fecha']}, {datos['autor']}")
        
    except Exception as e:
        print(f"❌ Error general al procesar {url}: {e}")
        import traceback
        traceback.print_exc()
    
    return datos

def _extraer_titular_jacobin(driver) -> str:
    """Extrae el titular de la noticia de JacobinLat"""
    selectores = [
        "h1.post-title",
        "h1.entry-title",
        "article h1",
        "h1"
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

def _extraer_bajada_jacobin(driver) -> str:
    """Extrae la bajada/descripción de la noticia"""
    selectores = [
        "p.post-excerpt",
        ".post-header p",
        "meta[name='description']",
        "meta[property='og:description']"
    ]
    
    for selector in selectores:
        try:
            if selector.startswith("meta"):
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                texto = elemento.get_attribute("content")
            else:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                texto = elemento.text
            
            if texto and len(texto.strip()) > 30:
                return texto.strip()
        except:
            continue
    
    # Si no encontramos bajada, usar los primeros párrafos del contenido
    try:
        contenido = _extraer_contenido_jacobin(driver)
        if contenido['parrafos']:
            # Tomar los primeros 2 párrafos como bajada
            bajada = ' '.join(contenido['parrafos'][:2])
            if len(bajada) > 100:
                return bajada[:300] + "..." if len(bajada) > 300 else bajada
    except:
        pass
    
    return "No encontrada"

def _extraer_imagen_jacobin(driver) -> str:
    """Extrae la URL de la imagen principal"""
    selectores = [
        "meta[property='og:image']",
        "meta[name='twitter:image']",
        ".featured-image img",
        ".bloque-imagen img",
        "article img.size-full",
        "article img:first-of-type"
    ]
    
    for selector in selectores:
        try:
            elemento = driver.find_element(By.CSS_SELECTOR, selector)
            if selector.startswith("meta"):
                src = elemento.get_attribute("content")
            else:
                src = elemento.get_attribute("src") or elemento.get_attribute("data-src-img")
            
            if src and src.startswith("http") and not src.endswith((".gif", "base64")):
                return src
        except:
            continue
    
    return ""

def _extraer_contenido_jacobin(driver) -> Dict:
    """Extrace el contenido completo del artículo"""
    parrafos = []
    
    try:
        # Buscar en múltiples contenedores posibles
        contenedores = [
            ".post-content",
            ".entry-content",
            "article .content",
            "div[class*='content']"
        ]
        
        contenido_div = None
        for selector in contenedores:
            try:
                contenido_div = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        if contenido_div:
            # Extraer todos los párrafos
            elementos_parrafo = contenido_div.find_elements(By.TAG_NAME, "p")
            
            for p in elementos_parrafo:
                texto = p.text.strip()
                # Filtrar párrafos significativos (no vacíos, no demasiado cortos)
                if texto and len(texto) > 30:
                    # Eliminar posible texto de suscripción/pie de página
                    if not any(x in texto.lower() for x in ["suscribirse", "compartir", "facebook", "twitter", "email"]):
                        parrafos.append(texto)
        
        print(f"  📄 Encontrados {len(parrafos)} párrafos de contenido")
        
    except Exception as e:
        print(f"  ❌ Error al extraer contenido: {e}")
    
    return {'parrafos': parrafos, 'total': len(parrafos)}

def _parsear_fecha_jacobin(fecha_str: str) -> Optional[date]:
    """Parsea fechas en formato Jacobin (DD.MM.AA)"""
    if not fecha_str:
        return None
    
    fecha_str = fecha_str.strip()
    
    # Formato: DD.MM.AA
    try:
        partes = fecha_str.split('.')
        if len(partes) == 3:
            dia, mes, anio = partes
            # Añadir 2000 si el año es de 2 dígitos
            if len(anio) == 2:
                anio = "20" + anio
            return date(int(anio), int(mes), int(dia))
    except:
        pass
    
    return None

def _extraer_fecha_autor_jacobin(driver) -> Dict:
    """Extrae fecha y autor del artículo"""
    fecha = None
    autor = "No encontrado"
    
    try:
        # Extraer fecha
        selectores_fecha = [
            ".post-date",
            ".post-byline .post-date",
            "span.post-date",
            "time",
            ".post-byline"
        ]
        
        for selector in selectores_fecha:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                texto = elemento.text.strip()
                
                # Buscar patrón de fecha DD.MM.AA
                patron = re.search(r'(\d{2}\.\d{2}\.\d{2,4})', texto)
                if patron:
                    fecha = _parsear_fecha_jacobin(patron.group(1))
                    if fecha:
                        break
            except:
                continue
        
        # Si no encontramos fecha en los selectores, intentar extraer de la URL
        if fecha is None:
            try:
                url = driver.current_url
                patron_url = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
                if patron_url:
                    anio, mes, dia = patron_url.groups()
                    fecha = date(int(anio), int(mes), int(dia))
            except:
                pass
        
        # Extraer autor
        selectores_autor = [
            ".post-author",
            ".post-byline a[href*='author']",
            ".author a",
            "a.post-author"
        ]
        
        for selector in selectores_autor:
            try:
                elemento = driver.find_element(By.CSS_SELECTOR, selector)
                texto = elemento.text.strip()
                if texto and len(texto) > 2:
                    autor = texto
                    break
            except:
                continue
        
    except Exception as e:
        print(f"  ❌ Error al extraer fecha/autor: {e}")
    
    return {'fecha': fecha, 'autor': autor}

def _extraer_categoria_jacobin(driver):
    """Extrae la categoría del artículo"""
    categoria = "No encontrada"
    
    try:
        # Buscar categorías en múltiples ubicaciones
        selectores_cat = [
            ".post-categories a",
            ".cat-links a",
            ".category a",
            "a[href*='categoria']"
        ]
        
        for selector in selectores_cat:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                if elementos:
                    # Tomar la primera categoría encontrada
                    categoria = elementos[0].text.strip()
                    break
            except:
                continue
        
    except Exception as e:
        print(f"  ❌ Error al extraer categorías: {e}")
    
    return categoria

def guardar_en_db(datos: Dict) -> bool:
    """Guardar datos en la base de datos Django"""
    try:
        # Verificar si ya existe
        if Article.objects.filter(url=datos['url']).exists():
            print(f"  ⚠️  Ya existe: {datos['titular'][:50]}...")
            return False
        
        # Convertir contenido
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
        
        print(f"  💾 Guardado: {articulo.title[:60]}...")
        return True
        
    except Exception as e:
        print(f"  ❌ Error guardando en DB: {e}")
        import traceback
        traceback.print_exc()
        return False

def ejecutar_scraping_jacobin(max_noticias=10):
    """Función principal de scraping para JacobinLat"""
    driver = None
    articulos_procesados = 0
    
    try:
        print("\n" + "="*80)
        print("SCRAPING DE JACOBINLAT.COM - LAS NOTICIAS MÁS RECIENTES")
        print("="*80)
        
        # Configurar driver
        driver = configurar_driver()
        
        # Extraer URLs de noticias EN EL ORDEN CORRECTO
        urls = extraer_urls_noticias(driver, max_noticias)
        
        if not urls:
            print("❌ No se encontraron URLs de noticias")
            return 0
        
        print(f"\n📊 Procesando las {len(urls)} noticias más recientes...")
        
        # Procesar cada URL
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] 📰 {url}")
            
            try:
                # Extraer datos
                datos = extraer_datos_noticia(driver, url)
                
                # Verificar que tenga contenido mínimo
                if (datos['titular'] != 'No encontrado' and 
                    len(datos['contenido']) >= 3 and 
                    datos['fecha'] is not None):
                    
                    if guardar_en_db(datos):
                        articulos_procesados += 1
                else:
                    print(f"  ⚠️  Contenido insuficiente, omitiendo...")
                    print(f"     Titular: {datos['titular'][:50]}")
                    print(f"     Párrafos: {len(datos['contenido'])}")
                    print(f"     Fecha: {datos['fecha']}")
                
                # Pausa para no sobrecargar
                if i < len(urls):
                    time.sleep(1)
                    
            except Exception as e:
                print(f"  ❌ Error procesando URL: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return articulos_procesados
        
    except Exception as e:
        print(f"\n❌ Error general en scraping: {e}")
        import traceback
        traceback.print_exc()
        return 0
        
    finally:
        if driver:
            driver.quit()
            print("\n✅ WebDriver cerrado.")

def run():
    """Función para ejecutar desde Django"""
    cantidad = ejecutar_scraping_jacobin(max_noticias=10)
    
    print(f"\n{'='*80}")
    print("SCRAPING COMPLETADO")
    print(f"✅ Artículos procesados exitosamente: {cantidad}")
    
    # Mostrar estadísticas
    total = Article.objects.count()
    print(f"📊 Total en base de datos: {total}")
    
    # Mostrar los últimos artículos guardados
    print(f"\n📰 ÚLTIMOS ARTÍCULOS GUARDADOS:")
    ultimos = Article.objects.order_by('-id')[:5]
    for i, art in enumerate(ultimos, 1):
        print(f"{i}. [{art.publication_date}] {art.title[:70]}...")
    
    print(f"{'='*80}")
    
    return cantidad

if __name__ == "__main__":
    # Ejecutar desde línea de comandos
    cantidad = ejecutar_scraping_jacobin(max_noticias=10)
    print(f"\n{'='*80}")
    print("SCRAPING COMPLETADO")
    print(f"✅ Artículos procesados exitosamente: {cantidad}")
    print(f"{'='*80}")