from time import timezone

from rest_framework import serializers
from .models import Article, Comment

# ============= SERIALIZER DE COMENTARIOS =============
class CommentSerializer(serializers.ModelSerializer):
    """Serializer para comentarios"""
    formatted_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'name', 'email', 'comment', 'created_at', 'formatted_date', 'is_approved']
        read_only_fields = ['created_at', 'is_approved']
    
    def get_formatted_date(self, obj):
        """Devuelve la fecha formateada en español con hora de Santiago"""
        from django.utils import timezone
    
        # Convertir a zona horaria de Santiago
        santiago_time = timezone.localtime(obj.created_at)
    
        # Diccionario de meses en español
        meses = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
    
        # Formato manual
        dia = santiago_time.day
        mes = meses[santiago_time.month]
        año = santiago_time.year
        hora = santiago_time.strftime("%H:%M")
    
        return f"{dia} de {mes} de {año} - {hora}"
    
    def validate_email(self, value):
        """Validación personalizada para email"""
        if not value or not value.strip():
            raise serializers.ValidationError("El email es obligatorio")
        return value.strip().lower()
    
    def validate_name(self, value):
        """Validación para el nombre"""
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre es obligatorio")
        if len(value.strip()) < 2:
            raise serializers.ValidationError("El nombre debe tener al menos 2 caracteres")
        return value.strip()
    
    def validate_comment(self, value):
        """Validación para el comentario"""
        if not value or not value.strip():
            raise serializers.ValidationError("El comentario no puede estar vacío")
        if len(value.strip()) < 5:
            raise serializers.ValidationError("El comentario debe tener al menos 5 caracteres")
        return value.strip()


# ============= SERIALIZER DE ARTÍCULO CON COMENTARIOS =============
class ArticleSerializer(serializers.ModelSerializer):
    """Serializer detallado de artículo con comentarios incluidos"""
    full_content = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)  # Incluye los comentarios
    comments_count = serializers.SerializerMethodField()     # Cuenta total de comentarios aprobados
    
    class Meta:
        model = Article
        fields = [
            'id', 'url', 'slug', 'title', 'subtitle', 'image_url',
            'content', 'paragraphs_count', 'full_content',
            'publication_date', 'author', 'category',
            'scraped_at', 'is_active', 'published_on_instagram',
            'comments', 'comments_count'
        ]
        read_only_fields = ['scraped_at', 'is_active', 'paragraphs_count', 'slug']
    
    def get_full_content(self, obj):
        return obj.full_content
    
    def get_comments_count(self, obj):
        """Retorna la cantidad de comentarios aprobados"""
        return obj.comments.filter(is_approved=True).count()

# ============= SERIALIZER PARA LISTA DE ARTÍCULOS =============
class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de artículos"""
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'slug', 'url', 'title', 'subtitle', 'image_url',
            'publication_date', 'author', 'category', 'scraped_at',
            'comments_count'
        ]

    def get_comments_count(self, obj):
        """Retorna la cantidad de comentarios aprobados"""
        return obj.comments.filter(is_approved=True).count()
    
# ============= SERIALIZER PARA CREAR COMENTARIOS (SIN ARTÍCULO EN EL BODY) =============
class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para crear comentarios (sin incluir el artículo en la request)"""
    
    class Meta:
        model = Comment
        fields = ['name', 'email', 'comment']
    
    def validate(self, data):
        """Validaciones adicionales combinadas"""
        # Verificar que no haya intentos de spam con emails repetidos muy seguido
        # Esta validación puede ser más compleja según tus necesidades
        return data
    
    def create(self, validated_data):
        """Crear comentario con el artículo asociado"""
        # El artículo se pasa en el contexto, no en los datos validados
        article = self.context.get('article')
        if not article:
            raise serializers.ValidationError("Artículo no especificado")
        
        # Crear el comentario asociado al artículo
        comment = Comment.objects.create(
            article=article,
            **validated_data
        )
        return comment

# ============= SERIALIZER PARA ESTADÍSTICAS =============
class ScrapingTaskSerializer(serializers.Serializer):
    max_articles = serializers.IntegerField(min_value=1, max_value=50, default=15)
    force = serializers.BooleanField(default=False)

class StatsSerializer(serializers.Serializer):
    total_articles = serializers.IntegerField()
    articles_by_category = serializers.DictField()
    last_scrape = serializers.DateTimeField(allow_null=True)
    articles_last_24h = serializers.IntegerField()
    total_comments = serializers.IntegerField(required=False, default=0)
    pending_comments = serializers.IntegerField(required=False, default=0)
    comments_last_24h = serializers.IntegerField(required=False, default=0)



    