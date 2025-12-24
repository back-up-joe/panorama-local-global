from __future__ import absolute_import, unicode_literals
import pytest
from celery import current_app
from django.test import TestCase
from celery_app.celery import app
from datetime import datetime, timedelta

class CeleryConfigTestCase(TestCase):
    """Pruebas para la configuración de Celery"""
    
    def test_celery_app_config(self):
        """Verifica que Celery esté configurado correctamente"""
        self.assertEqual(app.main, 'scraper')
        self.assertEqual(app.conf.task_serializer, 'json')
        self.assertEqual(app.conf.accept_content, ['json'])
        self.assertEqual(app.conf.timezone, 'America/Santiago')
        self.assertTrue(app.conf.enable_utc)

class CeleryBeatScheduleTestCase(TestCase):
    """Pruebas para el beat schedule"""
    
    def test_beat_schedule_exists(self):
        """Verifica que el beat schedule esté configurado"""
        from celery_app.beat_schedule import beat_schedule
        
        self.assertIsNotNone(beat_schedule)
        self.assertIn('scrap-elsiglo-manana', beat_schedule)
        self.assertIn('limpiar-articulos-viejos', beat_schedule)
    
    def test_beat_schedule_for_testing(self):
        """Configura schedule de prueba (ejecución cada 1-2 minutos)"""
        from celery.schedules import crontab
        
        # Schedule para pruebas (ejecutar cada 1 minuto)
        test_schedule = {
            'test-task-every-minute': {
                'task': 'news.tasks.debug_task',
                'schedule': crontab(minute='*/1'),  # Cada minuto
                'args': (),
            },
            'test-task-every-two-minutes': {
                'task': 'news.tasks.debug_task',
                'schedule': crontab(minute='*/2'),  # Cada 2 minutos
                'args': (),
            },
        }
        
        # Configura el schedule de prueba
        app.conf.update(beat_schedule=test_schedule)
        
        self.assertIn('test-task-every-minute', app.conf.beat_schedule)
        self.assertIn('test-task-every-two-minutes', app.conf.beat_schedule)

class CeleryTaskTestCase(TestCase):
    """Pruebas para las tareas de Celery"""
    
    def test_debug_task(self):
        """Prueba la tarea de debug"""
        result = app.tasks['celery_app.celery.debug_task'].apply()
        self.assertIsNone(result.get())  # ignore_result=True
        
    def test_task_registration(self):
        """Verifica que las tareas estén registradas"""
        # Verifica que la tarea de debug esté registrada
        self.assertIn('celery_app.celery.debug_task', app.tasks)
        
        # Verifica que las tareas de la app 'news' estén disponibles
        # (esto requiere que las tareas existan)
        try:
            from news import tasks
            # Si el módulo existe, verifica alguna tarea específica
            # self.assertIn('news.tasks.scrap_elsiglo', app.tasks)
        except ImportError:
            print("Advertencia: Módulo 'news.tasks' no encontrado")

@pytest.fixture(scope='session')
def celery_config():
    """Configuración de Celery para pruebas con pytest"""
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
        'task_always_eager': True,  # Ejecuta tareas sincrónicamente en pruebas
        'task_eager_propagates': True,
    }

@pytest.fixture(scope='session')
def celery_worker_parameters():
    """Parámetros para workers de Celery en pruebas"""
    return {
        'perform_ping_check': False,
        'queues': ('test-queue',),
    }

# Prueba con pytest
def test_celery_beat_schedule_integration():
    """Prueba de integración del beat schedule"""
    from celery_app.beat_schedule import beat_schedule
    
    # Configura schedule de prueba
    app.conf.update(
        beat_schedule=beat_schedule,
        beat_scheduler='celery.beat.PersistentScheduler',
    )
    
    # Verifica que se pueda crear un scheduler
    from celery.beat import ScheduleEntry
    for name, entry in beat_schedule.items():
        schedule_entry = ScheduleEntry(
            name=name,
            task=entry['task'],
            schedule=entry['schedule'],
            args=entry.get('args', ()),
            kwargs=entry.get('kwargs', {}),
            options=entry.get('options', {}),
        )
        assert schedule_entry.name == name
        assert schedule_entry.task == entry['task']