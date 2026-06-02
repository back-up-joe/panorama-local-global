from django.core.management.base import BaseCommand
from scripts.scrap_cronicadigital import run

class Command(BaseCommand):
    help = "Scrapea Crónica Digital y puebla la base de datos"

    def handle(self, *args, **kwargs):
        run()

        self.stdout.write(self.style.SUCCESS('Scraping de Crónica Digital: OK'))