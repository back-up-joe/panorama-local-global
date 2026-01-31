'''
from django.core.management.base import BaseCommand
from scripts.scrap_radiouchile import run

class Command(BaseCommand):
    help = "Scrapea Radio UChile y puebla la base de datos"

    def handle(self, *args, **kwargs):
        run()

        self.stdout.write(self.style.SUCCESS('Scraping de Radio UChile: OK'))
        '''