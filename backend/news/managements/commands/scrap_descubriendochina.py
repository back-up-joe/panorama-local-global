from django.core.management.base import BaseCommand
from scripts.scrap_descubriendochina import run

class Command(BaseCommand):
    help = "Scrapea Descubriendo China y puebla la base de datos"

    def handle(self, *args, **kwargs):
        run()

        self.stdout.write(self.style.SUCCESS('Scraping de Descubriendo China: OK'))