from django.db import models
from django.utils import timezone

class Article(models.Model):
    url = models.URLField(max_length=500, unique=True, verbose_name="URL")
    title = models.CharField(max_length=500, verbose_name="Título")
    subtitle = models.TextField(verbose_name="Bajada/Subtítulo")
    image_url = models.URLField(max_length=500, verbose_name="URL Imagen")
    content = models.JSONField(default=list, verbose_name="Contenido")
    paragraphs_count = models.IntegerField(default=0, verbose_name="Nº Párrafos")
    
    # publication_date = models.CharField(max_length=100, verbose_name="Fecha Publicación")
    publication_date = models.DateField(null=True, blank=True, verbose_name="Fecha Publicación")

    author = models.CharField(max_length=200, verbose_name="Autor")
    category = models.CharField(max_length=200, verbose_name="Categoría")
    scraped_at = models.DateTimeField(default=timezone.now, verbose_name="Fecha Extracción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['scraped_at']),
            models.Index(fields=['category']),
            models.Index(fields=['author']),
        ]
        verbose_name = 'Artículo'
        verbose_name_plural = 'Artículos'
    
    def __str__(self):
        return f"{self.title[:50]}..."
    
    @property
    def full_content(self):
        """Devuelve el contenido completo como texto"""
        return ' '.join(self.content) if isinstance(self.content, list) else ''
    
    def save(self, *args, **kwargs):
        """Actualiza automáticamente el conteo de párrafos"""
        if isinstance(self.content, list):
            self.paragraphs_count = len(self.content)
        super().save(*args, **kwargs)
