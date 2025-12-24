from celery.schedules import crontab

beat_schedule = {
    'scrap-elsiglo-manana': {
        'task': 'news.tasks.scrap_elsiglo',
        'schedule': crontab(hour=8, minute=0),
        'args': (15,),
    },
    'scrap-elsiglo-tarde': {
        'task': 'news.tasks.scrap_elsiglo',
        'schedule': crontab(hour=14, minute=0),
        'args': (10,),
    },
    'scrap-elsiglo-noche': {
        'task': 'news.tasks.scrap_elsiglo',
        'schedule': crontab(hour=20, minute=0),
        'args': (10,),
    },
    'limpiar-articulos-viejos': {
        'task': 'news.tasks.limpiar_articulos_antiguos',
        'schedule': crontab(day_of_week='sunday', hour=3, minute=0),
        'args': (30,),
    },
}