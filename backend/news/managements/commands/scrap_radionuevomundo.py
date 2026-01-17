from django.core.management.base import BaseCommand
from scripts.scrap_radionuevomundo import run

class Command(BaseCommand):
    help = "Scrapea Radio Nuevo Mundo y puebla la base de datos"

    def handle(self, *args, **kwargs):
        run()

        self.stdout.write(self.style.SUCCESS('Scraping de Radio Nuevo Mundo: OK'))