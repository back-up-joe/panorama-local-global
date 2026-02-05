from celery import shared_task
from django.utils import timezone
import sys
import os

@shared_task(bind=True, max_retries=3)
def scrap_elsiglo(self, max_articles=5):
    """
    Tarea principal de scraping
    """
    try:
        print(f"[{timezone.now()}] Iniciando scraping de El Siglo...")

        # Agregar directorio scripts al path
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

        # Importar y ejecutar scraping
        from scripts.scrap_elsiglo import ejecutar_scraping

        procesadas = ejecutar_scraping(max_noticias=max_articles)

        return {
            'status': 'success',
            'task': 'scrap_elsiglo',
            'articles_processed': procesadas,
            'timestamp': timezone.now().isoformat(),
            'message': f'Procesadas {procesadas} noticias'
        }

    except Exception as e:
        print(f"Error en scraping: {e}")
        # Reintentar después de 5 minutos
        raise self.retry(exc=e, countdown=300)
    
@shared_task(bind=True, max_retries=3)
def scrap_revistadefrente(self, max_articles=5):
    """
    Tarea principal de scraping
    """
    try:
        print(f"[{timezone.now()}] Iniciando scraping de Revista de Frente...")

        # Agregar directorio scripts al path
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

        # Importar y ejecutar scraping
        from scripts.scrap_revistadefrente import ejecutar_scraping

        procesadas = ejecutar_scraping(max_noticias=max_articles)

        return {
            'status': 'success',
            'task': 'scrap_revistadefrente',
            'articles_processed': procesadas,
            'timestamp': timezone.now().isoformat(),
            'message': f'Procesadas {procesadas} noticias'
        }

    except Exception as e:
        print(f"Error en scraping: {e}")
        # Reintentar después de 5 minutos
        raise self.retry(exc=e, countdown=300)
    
@shared_task(bind=True, max_retries=3)
def scrap_rebelion(self, max_articles=5):
    """
    Tarea principal de scraping
    """
    try:
        print(f"[{timezone.now()}] Iniciando scraping de Rebelion.org...")

        # Agregar directorio scripts al path
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

        # Importar y ejecutar scraping
        from scripts.scrap_rebelion import ejecutar_scraping

        procesadas = ejecutar_scraping(max_noticias=max_articles)

        return {
            'status': 'success',
            'task': 'scrap_rebelion',
            'articles_processed': procesadas,
            'timestamp': timezone.now().isoformat(),
            'message': f'Procesadas {procesadas} noticias'
        }

    except Exception as e:
        print(f"Error en scraping: {e}")
        # Reintentar después de 5 minutos
        raise self.retry(exc=e, countdown=300)

'''
@shared_task(bind=True, max_retries=3)
def scrap_radiouchile(self, max_articles=5):
    """
    Tarea principal de scraping
    """
    try:
        print(f"[{timezone.now()}] Iniciando scraping de Radio UChile...")

        # Agregar directorio scripts al path
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

        # Importar y ejecutar scraping
        from scripts.scrap_radiouchile import ejecutar_scraping

        procesadas = ejecutar_scraping(max_noticias=max_articles)

        return {
            'status': 'success',
            'task': 'scrap_radiouchile',
            'articles_processed': procesadas,
            'timestamp': timezone.now().isoformat(),
            'message': f'Procesadas {procesadas} noticias'
        }

    except Exception as e:
        print(f"Error en scraping: {e}")
        # Reintentar después de 5 minutos
        raise self.retry(exc=e, countdown=300) '''
    
@shared_task(bind=True, max_retries=3)
def scrap_eldespertar(self, max_articles=5):
    """
    Tarea principal de scraping
    """
    try:
        print(f"[{timezone.now()}] Iniciando scraping de El Despertar...")

        # Agregar directorio scripts al path
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

        # Importar y ejecutar scraping
        from scripts.scrap_eldespertar import ejecutar_scraping

        procesadas = ejecutar_scraping(max_noticias=max_articles)

        return {
            'status': 'success',
            'task': 'scrap_eldespertar',
            'articles_processed': procesadas,
            'timestamp': timezone.now().isoformat(),
            'message': f'Procesadas {procesadas} noticias'
        }

    except Exception as e:
        print(f"Error en scraping: {e}")
        # Reintentar después de 5 minutos
        raise self.retry(exc=e, countdown=300)
    
@shared_task(bind=True, max_retries=3)
def scrap_radionuevomundo(self, max_articles=5):
    """
    Tarea principal de scraping
    """
    try:
        print(f"[{timezone.now()}] Iniciando scraping de Radio Nuevo Mundo...")

        # Agregar directorio scripts al path
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

        # Importar y ejecutar scraping
        from scripts.scrap_radionuevomundo import ejecutar_scraping

        procesadas = ejecutar_scraping(max_noticias=max_articles)

        return {
            'status': 'success',
            'task': 'scrap_radionuevomundo',
            'articles_processed': procesadas,
            'timestamp': timezone.now().isoformat(),
            'message': f'Procesadas {procesadas} noticias'
        }

    except Exception as e:
        print(f"Error en scraping: {e}")
        # Reintentar después de 5 minutos
        raise self.retry(exc=e, countdown=300)

@shared_task(bind=True, max_retries=3)
def scrap_diariored(self, max_articles=5):
    """
    Tarea principal de scraping
    """
    try:
        print(f"[{timezone.now()}] Iniciando scraping de Diario Red...")

        # Agregar directorio scripts al path
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

        # Importar y ejecutar scraping
        from scripts.scrap_diariored import ejecutar_scraping

        procesadas = ejecutar_scraping(max_noticias=max_articles)

        return {
            'status': 'success',
            'task': 'scrap_diariored',
            'articles_processed': procesadas,
            'timestamp': timezone.now().isoformat(),
            'message': f'Procesadas {procesadas} noticias'
        }

    except Exception as e:
        print(f"Error en scraping: {e}")
        # Reintentar después de 5 minutos
        raise self.retry(exc=e, countdown=300)

##################################################################################################3

@shared_task
def limpiar_articulos_antiguos(dias=30):
    """
    Limpia artículos antiguos
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        from .models import Article

        fecha_limite = timezone.now() - timedelta(days=dias)
        count = Article.objects.filter(scraped_at__lt=fecha_limite).count()

        if count > 0:
            Article.objects.filter(scraped_at__lt=fecha_limite).delete()
            print(f"[{timezone.now()}] Eliminados {count} artículos antiguos")

        return {
            'status': 'success',
            'articles_deleted': count,
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        print(f"Error limpiando artículos: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@shared_task
def verificar_estado():
    """
    Verifica estado del sistema
    """
    try:
        from .models import Article

        total = Article.objects.count()
        ultimo = Article.objects.order_by('-scraped_at').first()

        return {
            'status': 'ok',
            'total_articles': total,
            'last_scrape': ultimo.scraped_at if ultimo else None,
            'timestamp': timezone.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }