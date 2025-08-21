from django.core.management.base import BaseCommand
from api.models import District

class Command(BaseCommand):
    help = "Load Malawi districts into the database"

    DISTRICTS = [
        "Mzimba",
        "Mzuzu City",
        "Neno",
        "Nkhata Bay",
        "Nkhotakota",
        "Nsanje",
        "Ntcheu",
        "Ntchisi",
        "Phalombe",
        "Rumphi",
        "Salima",
        "Thyolo",
        "Zomba City",
        "Balaka",
        "Blantyre City",
        "Zomba",
        "Blantyre",
        "Chikwawa",
        "Chiradzulu",
        "Chitipa",
        "Dedza",
        "Dowa",
        "Karonga",
        "Kasungu",
        "Likoma",
        "Lilongwe City",
        "Lilongwe",
        "Machinga",
        "Mangochi",
        "Mchinji",
        "Mulanje",
        "Mwanza",
    ]

    def handle(self, *args, **kwargs):
        created_count = 0
        for name in self.DISTRICTS:
            obj, created = District.objects.get_or_create(name=name)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Added: {name}"))
            else:
                self.stdout.write(f"Skipped (already exists): {name}")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Finished. {created_count} districts added."))
