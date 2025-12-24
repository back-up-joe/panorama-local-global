from rest_framework import serializers
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    full_content = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'url', 'title', 'subtitle', 'image_url',
            'content', 'paragraphs_count', 'full_content',
            'publication_date', 'author', 'category',
            'scraped_at', 'is_active'
        ]
        read_only_fields = ['scraped_at', 'is_active', 'paragraphs_count']
    
    def get_full_content(self, obj):
        return obj.full_content

class ArticleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            'id', 'url', 'title', 'subtitle', 'image_url',
            'publication_date', 'author', 'category', 'scraped_at'
        ]

class ScrapingTaskSerializer(serializers.Serializer):
    max_articles = serializers.IntegerField(min_value=1, max_value=50, default=15)
    force = serializers.BooleanField(default=False)

class StatsSerializer(serializers.Serializer):
    total_articles = serializers.IntegerField()
    articles_by_category = serializers.DictField()
    last_scrape = serializers.DateTimeField(allow_null=True)
    articles_last_24h = serializers.IntegerField()