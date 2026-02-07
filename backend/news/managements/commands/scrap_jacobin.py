from django.core.management.base import BaseCommand
from scripts.scrap_jacobin import run

class Command(BaseCommand):
    help = "Scrapea JacobinLat y puebla la base de datos"

    def handle(self, *args, **kwargs):
        run()

        self.stdout.write(self.style.SUCCESS('Scraping de JacobinLat: OK'))