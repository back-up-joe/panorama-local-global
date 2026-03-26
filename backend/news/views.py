from rest_framework.views import APIView
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.db import models
from django.shortcuts import get_object_or_404
from .models import Article, Comment, VisitCounter
from .serializers import (
    ArticleSerializer, 
    ArticleListSerializer, 
    ScrapingTaskSerializer,
    StatsSerializer,
    CommentSerializer,
    CommentCreateSerializer
)
from .tasks import scrap_elsiglo

class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.filter(is_active=True)
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'author']
    search_fields = ['title', 'subtitle', 'content', 'author']
    ordering_fields = ['scraped_at', 'publication_date']
    # ordering = ['-scraped_at']
    ordering = ['-publication_date']
    
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
        """Estadísticas del sistema incluyendo comentarios"""
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

        # Estadísticas de comentarios
        total_comments = Comment.objects.filter(is_approved=True).count()
        pending_comments = Comment.objects.filter(is_approved=False).count()
        comments_last_24h = Comment.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24),
            is_approved=True
        ).count()
        
        data = {
            'total_articles': total,
            'articles_by_category': category_dict,
            'last_scrape': last_scrape.scraped_at if last_scrape else None,
            'articles_last_24h': last_24h,
            'total_comments': total_comments,
            'pending_comments': pending_comments,
            'comments_last_24h': comments_last_24h,
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
    
    # ============= NUEVAS ACCIONES PARA COMENTARIOS =============
    
    @action(detail=True, methods=['get'], url_path='comments')
    def get_comments(self, request, pk=None):
        """Obtener todos los comentarios de un artículo específico"""
        article = self.get_object()
        comments = article.comments.filter(is_approved=True)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='add-comment')
    def add_comment(self, request, pk=None):
        """Agregar un comentario a un artículo específico"""
        article = self.get_object()
        
        # Usar el serializer de creación con el artículo en el contexto
        serializer = CommentCreateSerializer(
            data=request.data,
            context={'article': article}
        )
        
        if serializer.is_valid():
            comment = serializer.save()
            # Retornar el comentario usando el serializer de visualización
            response_serializer = CommentSerializer(comment)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], url_path='comments-count')
    def comments_count(self, request, pk=None):
        """Obtener el número de comentarios de un artículo"""
        article = self.get_object()
        count = article.comments.filter(is_approved=True).count()
        return Response({'comments_count': count})
    
    # ============= ACCIONES ADICIONALES PARA ADMINISTRACIÓN DE COMENTARIOS =============
    
    @action(detail=False, methods=['get'], url_path='comments/pending')
    def pending_comments(self, request):
        """Obtener comentarios pendientes de aprobación (solo para admin)"""
        # Aquí deberías agregar permisos de administrador
        pending = Comment.objects.filter(is_approved=False)
        serializer = CommentSerializer(pending, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], url_path='comments/(?P<comment_id>[^/.]+)/approve')
    def approve_comment(self, request, pk=None, comment_id=None):
        """Aprobar un comentario específico (solo para admin)"""
        # Aquí deberías agregar permisos de administrador
        try:
            comment = Comment.objects.get(pk=comment_id, article_id=pk)
            comment.is_approved = True
            comment.save()
            serializer = CommentSerializer(comment)
            return Response(serializer.data)
        except Comment.DoesNotExist:
            return Response(
                {'error': 'Comentario no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['delete'], url_path='comments/(?P<comment_id>[^/.]+)/delete')
    def delete_comment(self, request, pk=None, comment_id=None):
        """Eliminar un comentario (solo para admin)"""
        # Aquí deberías agregar permisos de administrador
        try:
            comment = Comment.objects.get(pk=comment_id, article_id=pk)
            comment.delete()
            return Response(
                {'message': 'Comentario eliminado exitosamente'}, 
                status=status.HTTP_200_OK
            )
        except Comment.DoesNotExist:
            return Response(
                {'error': 'Comentario no encontrado'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class VisitCounterView(APIView):
    """Vista simple para el contador de visitas"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Obtener el total de visitas"""
        total = VisitCounter.objects.aggregate(
            total=models.Sum('total_visits')
        )['total'] or 0
        
        return Response({'total_visits': total})
    
    def post(self, request):
        """Registrar una nueva visita"""
        # Verificar si ya se contó en esta sesión
        if request.session.get('visit_counted'):
            total = VisitCounter.objects.aggregate(
                total=models.Sum('total_visits')
            )['total'] or 0
            return Response({'total_visits': total, 'status': 'already_counted'})
        
        # Registrar la visita
        today_counter, _ = VisitCounter.objects.get_or_create(
            date=timezone.now().date(),
            defaults={'total_visits': 0}
        )
        today_counter.total_visits += 1
        today_counter.save()
        
        # Marcar en sesión
        request.session['visit_counted'] = True
        
        # Obtener total
        total = VisitCounter.objects.aggregate(
            total=models.Sum('total_visits')
        )['total'] or 0
        
        return Response({'total_visits': total})