from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class Article(models.Model):
    url = models.URLField(max_length=500, unique=True, verbose_name="URL")
    title = models.CharField(max_length=500, verbose_name="Título")
    slug = models.SlugField(max_length=500, unique=True, blank=True, verbose_name="Slug")
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
    published_on_instagram = models.BooleanField(default=False, verbose_name="Publicado en Instagram")

    class Meta:
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['url']),
            models.Index(fields=['slug']),
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
        """Actualiza automáticamente el conteo de párrafos y genera slug"""
        if isinstance(self.content, list):
            self.paragraphs_count = len(self.content)

        # Generar slug si no existe
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1

            # Asegurar unicidad del slug
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
            
        super().save(*args, **kwargs)

# Comentario para cada artículo
class Comment(models.Model):
    article = models.ForeignKey(
        Article, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name="Artículo"
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre",
        help_text="Mínimo 2 caracteres, máximo 100 caracteres",    
    )
    email = models.EmailField(
        max_length=100,
        verbose_name="Email",
        help_text="Máximo 100 caracteres"
    )
    comment = models.TextField(
        max_length=1000,
        verbose_name="Comentario",
        help_text="Mínimo 5, Máximo 1000 caracteres"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Fecha de comentario")
    is_approved = models.BooleanField(default=True, verbose_name="Aprobado")  # Para moderación
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['article', 'created_at']),
            models.Index(fields=['email']),
        ]
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'
    
    def __str__(self):
        return f"Comentario de {self.name} en {self.article.title[:30]}..."

class VisitCounter(models.Model):
    """Contador simple de visitas del sitio"""
    total_visits = models.PositiveIntegerField(default=0, verbose_name="Visitas totales")
    date = models.DateField(auto_now_add=True, verbose_name="Fecha")
    
    class Meta:
        verbose_name = "Contador de visitas"
        verbose_name_plural = "Contadores de visitas"
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.total_visits} visitas - {self.date}"