from django.core.management.commands.runserver import Command as RunserverCommand

class Command(RunserverCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.set_defaults(port="8000")  # Buraya app1 için kullanacağın portu yaz