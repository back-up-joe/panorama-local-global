from django.contrib import admin
from .models import Article, Comment

# Definir el inline primero
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0  # No muestra filas vacías adicionales
    fields = ('name', 'email', 'comment', 'created_at', 'is_approved')
    readonly_fields = ('created_at',)
    can_delete = True
    show_change_link = True  # Agrega un enlace para editar el comentario
    classes = ('collapse',)  # Opcional: colapsa la sección por defecto
    
    # Personalizar cómo se muestran los campos
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj:  # Si es un artículo existente
            return fields
        return fields
    
    # Agregar estilos personalizados (opcional)
    class Media:
        css = {
            'all': ('admin/css/comments.css',)  # Si quieres estilos personalizados
        }

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'publication_date', 'scraped_at', 'is_active', 'comments_count')
    list_filter = ('category', 'author', 'is_active', 'scraped_at')
    search_fields = ('title', 'subtitle', 'content', 'author', 'category')
    readonly_fields = ('scraped_at', 'paragraphs_count')
    list_per_page = 20

    # Agregar los comentarios como inline
    inlines = [CommentInline]
    
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

    # Método para mostrar cantidad de comentarios en la lista
    def comments_count(self, obj):
        count = obj.comments.filter(is_approved=True).count()
        pending = obj.comments.filter(is_approved=False).count()
        
        if pending > 0:
            return f"{count} (📌 {pending} pendiente{'s' if pending != 1 else ''})"
        return str(count)
    
    comments_count.short_description = "Comentarios"
    comments_count.admin_order_field = 'comments__count'  # Permite ordenar por cantidad

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'article', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at', 'article__category')
    search_fields = ('name', 'email', 'comment', 'article__title')
    readonly_fields = ('created_at',)
    list_per_page = 20
    list_editable = ('is_approved',)  # Permite aprobar/desaprobar directamente desde la lista
    
    fieldsets = (
        ('Información del Comentario', {
            'fields': ('article', 'name', 'email', 'comment')
        }),
        ('Estado', {
            'fields': ('is_approved',)
        }),
        ('Fechas', {
            'fields': ('created_at',)
        }),
    )

    # Enlace al artículo para navegación rápida
    def article_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        
        url = reverse('admin:news_article_change', args=[obj.article.id])
        return format_html('<a href="{}">{}</a>', url, obj.article.title[:50])
    
    article_link.short_description = "Artículo"
    article_link.admin_order_field = 'article__title'
    
    # Acciones personalizadas
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        """Aprobar comentarios seleccionados"""
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} comentarios aprobados.')
    approve_comments.short_description = "Aprobar comentarios seleccionados"
    
    def disapprove_comments(self, request, queryset):
        """Desaprobar comentarios seleccionados"""
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} comentarios desaprobados.')
    disapprove_comments.short_description = "Desaprobar comentarios seleccionados"
