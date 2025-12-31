from django.core.management.base import BaseCommand
from scripts.scrap_revistadefrente import run

class Command(BaseCommand):
    help = "Scrapea Revista de Frente y puebla la base de datos"

    def handle(self, *args, **kwargs):
        run()

        self.stdout.write(self.style.SUCCESS('Scraping de Revista de Frente: OK'))