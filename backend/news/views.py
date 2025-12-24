from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import Article
from .serializers import (
    ArticleSerializer, 
    ArticleListSerializer, 
    ScrapingTaskSerializer,
    StatsSerializer
)
from .tasks import scrap_elsiglo

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.filter(is_active=True)
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author']
    search_fields = ['title', 'subtitle', 'content', 'author']
    ordering_fields = ['scraped_at', 'publication_date']
    ordering = ['-scraped_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        return ArticleSerializer
    
    @action(detail=False, methods=['post'])
    def trigger_scraping(self, request):
        """Ejecutar scraping manualmente"""
        serializer = ScrapingTaskSerializer(data=request.data)
        if serializer.is_valid():
            max_articles = serializer.validated_data['max_articles']
            task = scrap_elsiglo.delay(max_articles)
            
            return Response({
                'status': 'started',
                'task_id': task.id,
                'max_articles': max_articles,
                'message': 'Scraping iniciado en segundo plano'
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas del sistema"""
        total = Article.objects.count()
        
        # Artículos por categoría
        by_category = Article.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        category_dict = {item['category']: item['count'] for item in by_category}
        
        # Artículos últimas 24h
        last_24h = Article.objects.filter(
            scraped_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Último scraping
        last_scrape = Article.objects.order_by('-scraped_at').first()
        
        data = {
            'total_articles': total,
            'articles_by_category': category_dict,
            'last_scrape': last_scrape.scraped_at if last_scrape else None,
            'articles_last_24h': last_24h,
        }
        
        serializer = StatsSerializer(data=data)
        serializer.is_valid()
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Listar categorías disponibles"""
        categories = Article.objects.values_list('category', flat=True).distinct().order_by('category')
        return Response(list(categories))
    
    @action(detail=False, methods=['get'])
    def authors(self, request):
        """Listar autores disponibles"""
        authors = Article.objects.values_list('author', flat=True).distinct().order_by('author')
        return Response(list(authors))
    
    @action(detail=False, methods=['get'], url_path='search')
    def search_articles(self, request):
        """Búsqueda avanzada simplificada"""
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', '')
        author = request.query_params.get('author', '')
        
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filtros básicos que funcionan seguro
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(subtitle__icontains=query) |
                Q(author__icontains=query) |
                Q(category__icontains=query)
            )
        
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        if author:
            queryset = queryset.filter(author__icontains=author)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)