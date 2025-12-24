from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'publication_date', 'scraped_at', 'is_active')
    list_filter = ('category', 'author', 'is_active', 'scraped_at')
    search_fields = ('title', 'subtitle', 'content', 'author', 'category')
    readonly_fields = ('scraped_at', 'paragraphs_count')
    list_per_page = 20
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('url', 'title', 'subtitle', 'category', 'author')
        }),
        ('Contenido', {
            'fields': ('image_url', 'content', 'paragraphs_count')
        }),
        ('Fechas', {
            'fields': ('publication_date', 'scraped_at')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
    )