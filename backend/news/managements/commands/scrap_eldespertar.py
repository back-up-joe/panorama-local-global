from django.core.management.base import BaseCommand
from scripts.scrap_eldespertar import run

class Command(BaseCommand):
    help = "Scrapea El Despertar y puebla la base de datos"

    def handle(self, *args, **kwargs):
        run()

        self.stdout.write(self.style.SUCCESS('Scraping de El Despertar: OK'))