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
from bs4 import BeautifulSoup

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
    
    # Formato: "28 marzo, 2026" o "28 de marzo de 2026" o "2 abril, 2026"
    match = re.search(r"(\d{1,2})\s+(?:de\s+)?([a-záéíóú]+)(?:\s+de)?,?\s+(\d{4})", fecha_str)
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
    
    # Formato: 25 de marzo 2026 (sin coma)
    match = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+)\s+(\d{4})", fecha_str)
    if match:
        dia, mes, anio = match.groups()
        if mes in MESES_ES:
            return date(int(anio), MESES_ES[mes], int(dia))
    
    return None

def extraer_autor_fecha_desde_html(soup):
    """
    Extrae autor y fecha del HTML usando BeautifulSoup.
    Prioriza la información del span.post-byline que contiene autor y fecha.
    """
    autor = "No encontrado"
    fecha = None
    
    # === MÉTODO PRINCIPAL: Extraer de post-byline ===
    # Buscar el span con clase 'post-byline'
    post_byline = soup.find('span', class_='post-byline')
    
    if post_byline:
        texto_byline = post_byline.get_text().strip()
        print(f"    Debug - post-byline encontrado: '{texto_byline}'")
        
        # Extraer autor: después de "By " y antes de " on "
        # Formato típico: "By Resumen Latinoamericano on 28 marzo, 2026"
        patron_autor = r"By\s+(.+?)\s+on\s+"
        match_autor = re.search(patron_autor, texto_byline)
        if match_autor:
            autor = match_autor.group(1).strip()
            print(f"    Debug - Autor extraído: '{autor}'")
        
        # Extraer fecha: después de "on " hasta el final
        patron_fecha = r"on\s+(.+?)$"
        match_fecha = re.search(patron_fecha, texto_byline)
        if match_fecha:
            fecha_str = match_fecha.group(1).strip()
            print(f"    Debug - Fecha string: '{fecha_str}'")
            fecha = _parsear_fecha(fecha_str)
            if fecha:
                print(f"    Debug - Fecha parseada: {fecha}")
    
    # === MÉTODO SECUNDARIO: Si no se encontró en post-byline, buscar en otros lugares ===
    if autor == "No encontrado" or not fecha:
        # Buscar en párrafos, listas y divs de metadata
        elementos_a_revisar = []
        
        # Agregar todos los párrafos
        elementos_a_revisar.extend(soup.find_all('p'))
        
        # Agregar todos los items de lista
        elementos_a_revisar.extend(soup.find_all('li'))
        
        # Agregar elementos específicos de metadata
        elementos_a_revisar.extend(soup.find_all('div', class_='post-meta'))
        elementos_a_revisar.extend(soup.find_all('span', class_='author'))
        elementos_a_revisar.extend(soup.find_all('span', class_='date'))
        
        for elemento in elementos_a_revisar[:10]:  # Revisar primeros 10 elementos
            texto = elemento.get_text().strip()
            if not texto:
                continue
            
            # Buscar fecha (solo si no se encontró antes)
            if not fecha:
                fecha_encontrada = _parsear_fecha(texto)
                if fecha_encontrada:
                    fecha = fecha_encontrada
            
            # Buscar autor (solo si no se encontró antes)
            if autor == "No encontrado":
                # Patrones alternativos para autor
                patrones_autor = [
                    r"Por\s*:?\s*([A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)*)",
                    r"Autor:\s*([A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)*)",
                    r"Escrito por\s*([A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)*)",
                    r"^([A-ZÁÉÍÓÚ][a-záéíóú]+(?:\s+[A-ZÁÉÍÓÚ][a-záéíóú]+)*)\s*[,|]"
                ]
                
                for patron in patrones_autor:
                    match = re.search(patron, texto)
                    if match:
                        autor_candidate = match.group(1).strip()
                        # Evitar falsos positivos como fechas o palabras sueltas
                        if len(autor_candidate) > 3 and not re.match(r'^\d+$', autor_candidate):
                            autor = autor_candidate
                            break
    
    return autor, fecha

def extraer_bajada(soup, content_area):
    """
    Extrae la bajada (subtítulo) del artículo.
    La bajada puede ser:
    1. El primer párrafo después de los créditos (evitando textos como "Al Mayadeen TV_Resumen...")
    2. Un elemento h2
    3. El primer párrafo con longitud significativa
    """
    bajada = "No encontrada"
    
    if not content_area:
        return bajada
    
    # Lista de patrones que indican créditos o metadata (que NO son la bajada)
    patrones_creditos = [
        r"^Al Mayadeen TV_",
        r"^teleSUR,",
        r"^Brasil de Facto",
        r"^Resumen Latinoamericano",
        r"^.*\/.*,\s+\d+\s+de\s+\w+",
        r"^\d+\s+de\s+\w+,\s+\d{4}$",
        r"^Editado por:",
    ]
    
    # Buscar elementos que podrían ser la bajada
    elementos_candidatos = []
    
    # 1. Buscar h2 (como en el ejemplo 2)
    h2_elements = content_area.find_all('h2')
    for h2 in h2_elements:
        texto = h2.get_text().strip()
        if texto and len(texto) > 20 and len(texto) < 500:
            elementos_candidatos.append(('h2', texto))
    
    # 2. Buscar párrafos
    parrafos = content_area.find_all('p')
    
    # Saltar créditos iniciales
    for p in parrafos:
        texto = p.get_text().strip()
        if not texto or len(texto) < 20:
            continue
        
        # Verificar si es un texto de créditos
        es_credito = False
        for patron in patrones_creditos:
            if re.search(patron, texto, re.IGNORECASE):
                es_credito = True
                break
        
        # Si no es crédito y tiene buena longitud, es candidato
        if not es_credito and len(texto) > 30:
            elementos_candidatos.append(('p', texto))
            # No rompemos aquí para seguir evaluando si hay h2
    
    # 3. Si encontramos candidatos, elegir el mejor
    if elementos_candidatos:
        # Priorizar h2 sobre p
        for tipo, texto in elementos_candidatos:
            if tipo == 'h2':
                bajada = texto
                print(f"    Debug - Bajada encontrada (h2): '{texto[:100]}...'")
                return bajada
        
        # Si no hay h2, tomar el primer párrafo válido
        for tipo, texto in elementos_candidatos:
            if tipo == 'p':
                bajada = texto
                print(f"    Debug - Bajada encontrada (p): '{texto[:100]}...'")
                return bajada
    
    # 4. Si no encontramos nada específico, usar el primer párrafo del contenido completo
    if not bajada == "No encontrada" and parrafos:
        for p in parrafos:
            texto = p.get_text().strip()
            if len(texto) > 30:
                bajada = texto[:500]
                print(f"    Debug - Bajada (fallback): '{texto[:100]}...'")
                break
    
    return bajada

def extraer_contenido_completo(soup):
    """Extrae el contenido completo del artículo"""
    contenido = []
    
    # Buscar el área de contenido principal
    content_area = None
    
    # Opción 1: Por ID
    content_area = soup.find('div', id='content-area')
    
    # Opción 2: Por clase mvp-cont-in
    if not content_area:
        content_area = soup.find('div', class_='mvp-cont-in')
    
    # Opción 3: Por clase post-area
    if not content_area:
        content_area = soup.find('div', id='post-area')
    
    if content_area:
        # Extraer todos los párrafos
        parrafos = content_area.find_all('p')
        for p in parrafos:
            texto = p.get_text().strip()
            # Filtrar párrafos vacíos o demasiado cortos
            if texto and len(texto) > 20:
                contenido.append(texto)
        
        # Si no hay suficientes párrafos, buscar otros elementos con texto
        if len(contenido) < 3:
            # Buscar divs con clase que contenga texto
            divs_texto = content_area.find_all(['div', 'li'], class_=re.compile(r'content|text|entry'))
            for div in divs_texto:
                texto = div.get_text().strip()
                if texto and len(texto) > 50 and texto not in contenido:
                    contenido.append(texto)
    
    return content_area, contenido

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
        
        # Obtener el HTML completo para BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Título - buscar de forma más específica
        selectores_titulo = [
            "h1.headline",  # Priorizar la clase específica
            "h1.entry-title",
            "h1.post-title",
            "div#title-main h1",
            "div.post-area h1",
            "div#content-area h1",
            "h1"
        ]
        
        for selector in selectores_titulo:
            try:
                titulo = driver.find_element(By.CSS_SELECTOR, selector)
                datos['titular'] = titulo.text.strip()
                if datos['titular'] != "No encontrado":
                    break
            except:
                continue
        
        # Si no se encontró con selectores, usar BeautifulSoup
        if datos['titular'] == "No encontrado":
            h1 = soup.find('h1', class_='headline')
            if not h1:
                h1 = soup.find('h1')
            if h1:
                datos['titular'] = h1.get_text().strip()
        
        # Imagen (meta og:image o imagen destacada)
        try:
            datos['imagen'] = driver.find_element(By.CSS_SELECTOR, "meta[property='og:image']").get_attribute("content")
        except:
            try:
                img = soup.find('div', class_='post-image')
                if img:
                    img_tag = img.find('img')
                    if img_tag:
                        datos['imagen'] = img_tag.get('src', '')
            except:
                pass
        
        # Contenido usando BeautifulSoup (más robusto)
        content_area, contenido = extraer_contenido_completo(soup)
        datos['contenido'] = contenido
        
        # Extraer bajada de manera inteligente
        datos['bajada'] = extraer_bajada(soup, content_area)
        
        # Extraer autor y fecha - USANDO EL NUEVO MÉTODO PRIORIZANDO post-byline
        autor, fecha = extraer_autor_fecha_desde_html(soup)
        datos['autor'] = autor
        datos['fecha'] = fecha
        
        # Si no se encontró fecha, intentar con meta tags
        if not datos['fecha']:
            try:
                meta_fecha = driver.find_element(By.CSS_SELECTOR, "meta[property='article:published_time']")
                fecha_str = meta_fecha.get_attribute("content")
                if fecha_str:
                    datos['fecha'] = datetime.strptime(fecha_str[:10], "%Y-%m-%d").date()
            except:
                pass
        
        # Categoría mejorada - usando breadcrumb si está disponible
        try:
            # Intentar obtener del breadcrumb (más preciso)
            breadcrumb = soup.find('div', class_='breadcrumb')
            if breadcrumb:
                enlaces = breadcrumb.find_all('a')
                if len(enlaces) >= 2:
                    # La categoría suele ser el penúltimo elemento
                    categoria_bread = enlaces[-1].get_text().strip()
                    if categoria_bread:
                        datos['categoria'] = categoria_bread
            
            # Si no se encontró en breadcrumb, buscar en la clase del contenedor
            if datos['categoria'] == 'No encontrada':
                post_area = driver.find_element(By.CSS_SELECTOR, "div#post-area")
                class_name = post_area.get_attribute("class")
                cat_match = re.search(r"category-([a-z-]+)", class_name)
                if cat_match:
                    datos['categoria'] = cat_match.group(1).replace('-', ' ').title()
                else:
                    # Buscar en enlaces de categoría
                    cat_link = driver.find_element(By.CSS_SELECTOR, "a[rel='category tag']")
                    if cat_link:
                        datos['categoria'] = cat_link.text.strip()
        except:
            # Intentar obtener de la URL
            if '/category/' in url:
                cat_from_url = url.split('/category/')[1].split('/')[0]
                datos['categoria'] = cat_from_url.replace('-', ' ').title()
        
        # Depuración: mostrar qué se encontró
        print(f"  Título encontrado: {datos['titular'][:70]}...")
        print(f"  Bajada encontrada: {datos['bajada'][:70]}...")
        print(f"  Autor encontrado: {datos['autor']}")
        print(f"  Fecha encontrada: {datos['fecha']}")
        print(f"  Categoría encontrada: {datos['categoria']}")
        print(f"  Párrafos extraídos: {len(datos['contenido'])}")
        
    except Exception as e:
        print(f"  Error general al procesar noticia: {e}")
        import traceback
        traceback.print_exc()
    
    return datos

def guardar_en_db(datos):
    """Guardar datos en la base de datos (evitando duplicados)"""
    try:
        if Article.objects.filter(url=datos['url']).exists():
            print(f"  Ya existe: {datos['titular'][:50]}...")
            return False
        
        contenido_texto = '\n\n'.join(datos['contenido'])
        
        # Asegurar que la fecha no sea None
        fecha_publicacion = datos['fecha'] if datos['fecha'] else date.today()
        
        articulo = Article.objects.create(
            url=datos['url'],
            title=datos['titular'],
            subtitle=datos['bajada'][:500] if datos['bajada'] != 'No encontrada' else '',
            image_url=datos['imagen'],
            content=contenido_texto,
            publication_date=fecha_publicacion,
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
        print("SCRAPING DE RESUMEN LATINOAMERICANO.ORG (VERSIÓN CORREGIDA - CON BAJADA)")
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
        import traceback
        traceback.print_exc()
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