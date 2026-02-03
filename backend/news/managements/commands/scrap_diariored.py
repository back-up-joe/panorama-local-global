from django.core.management.base import BaseCommand
from scripts.scrap_diariored import run

class Command(BaseCommand):
    help = "Scrapea Diario Red y puebla la base de datos"

    def handle(self, *args, **kwargs):
        run()

        self.stdout.write(self.style.SUCCESS('Scraping de Diario Red: OK'))