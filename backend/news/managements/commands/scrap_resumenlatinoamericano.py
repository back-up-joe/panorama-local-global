from django.core.management.base import BaseCommand
from scripts.scrap_resumenlatinoamericano import run

class Command(BaseCommand):
    help = "Scrapea Resumen Latinoamericano y puebla la base de datos"

    def handle(self, *args, **kwargs):
        run()

        self.stdout.write(self.style.SUCCESS('Scraping de Resumen Latinoamericano: OK'))