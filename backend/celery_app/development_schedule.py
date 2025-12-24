from celery.schedules import timedelta, crontab

# Schedule de desarrollo (ejecución rápida para pruebas)
development_beat_schedule = {
    # Para pruebas - ejecutar cada 1 minuto
    'scrap-elsiglo-manana-dev': {
        'task': 'news.tasks.scrap_elsiglo',
        'schedule': timedelta(minutes=1),  # Cada minuto
        'args': (2,),  # Menos artículos para desarrollo
    },
    # Para pruebas - ejecutar cada 2 minutos
    'scrap-elsiglo-tarde-dev': {
        'task': 'news.tasks.scrap_elsiglo',
        'schedule': timedelta(minutes=2),
        'args': (1,),
    },
    # Limpieza cada 5 minutos en desarrollo
    'limpiar-articulos-viejos-dev': {
        'task': 'news.tasks.limpiar_articulos_antiguos',
        'schedule': timedelta(minutes=5),
        'args': (7,),  # 7 días en desarrollo
    },
}