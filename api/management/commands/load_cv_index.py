from django.core.management.base import BaseCommand
from api.models import District, VulnerabilityIndex


class Command(BaseCommand):
    help = "Load Composite Vulnerability Index data into the database"

    DATA = [
        {
            "region": "Mzimba",
            "value": 0.2879,
            "category": "Much less vulnerable",
            "color": "#1A9641"
        },
        {
            "region": "Mzuzu City",
            "value": 0.0919,
            "category": "Much less vulnerable",
            "color": "#1A9641"
        },
        {
            "region": "Neno",
            "value": 0.554,
            "category": "More vulnerable",
            "color": "#FDAE61"
        },
        {
            "region": "Nkhata Bay",
            "value": 0.5313,
            "category": "More vulnerable",
            "color": "#FDAE61"
        },
        {
            "region": "Nkhotakota",
            "value": 0.6601,
            "category": "More vulnerable",
            "color": "#FDAE61"
        },
        {
            "region": "Nsanje",
            "value": 0.7777,
            "category": "Much more vulnerable",
            "color": "#D7191C"
        },
        {
            "region": "Ntcheu",
            "value": 0.4928,
            "category": "Less vulnerable",
            "color": "#A6D96A"
        },
        {
            "region": "Ntchisi",
            "value": 0.4847,
            "category": "Less vulnerable",
            "color": "#A6D96A"
        },
        {
            "region": "Phalombe",
            "value": 0.9742,
            "category": "Much more vulnerable",
            "color": "#D7191C"
        },
        {
            "region": "Rumphi",
            "value": 0.2188,
            "category": "Much less vulnerable",
            "color": "#1A9641"
        },
        {
            "region": "Salima",
            "value": 0.7014,
            "category": "Much more vulnerable",
            "color": "#D7191C"
        },
        {
            "region": "Thyolo",
            "value": 0.5489,
            "category": "More vulnerable",
            "color": "#FDAE61"
        },
        {
            "region": "Zomba City",
            "value": 0.3822,
            "category": "Less vulnerable",
            "color": "#A6D96A"
        },
        {
            "region": "Balaka",
            "value": 0.5578,
            "category": "More vulnerable",
            "color": "#FDAE61"
        },
        {
            "region": "Blantyre City",
            "value": 0.0565,
            "category": "Much less vulnerable",
            "color": "#1A9641"
        },
        {
            "region": "Zomba",
            "value": 1,
            "category": "Much more vulnerable",
            "color": "#D7191C"
        },
        {
            "region": "Blantyre",
            "value": 0.2631,
            "category": "Much less vulnerable",
            "color": "#1A9641"
        },
        {
            "region": "Chikwawa",
            "value": 0.8683,
            "category": "Much more vulnerable",
            "color": "#D7191C"
        },
        {
            "region": "Chiradzulu",
            "value": 0.6714,
            "category": "More vulnerable",
            "color": "#FDAE61"
        },
        {
            "region": "Chitipa",
            "value": 0.0112,
            "category": "Much less vulnerable",
            "color": "#1A9641"
        },
        {
            "region": "Dedza",
            "value": 0.5379,
            "category": "More vulnerable",
            "color": "#FDAE61"
        },
        {
            "region": "Dowa",
            "value": 0.38,
            "category": "Less vulnerable",
            "color": "#A6D96A"
        },
        {
            "region": "Karonga",
            "value": 0.4638,
            "category": "Less vulnerable",
            "color": "#A6D96A"
        },
        {
            "region": "Kasungu",
            "value": 0.4811,
            "category": "Less vulnerable",
            "color": "#A6D96A"
        },
        {
            "region": "Likoma",
            "value": 0.0881,
            "category": "Much less vulnerable",
            "color": "#1A9641"
        },
        {
            "region": "Lilongwe City",
            "value": 0,
            "category": "Much less vulnerable",
            "color": "#1A9641"
        },
        {
            "region": "Lilongwe",
            "value": 0.3522,
            "category": "Less vulnerable",
            "color": "#A6D96A"
        },
        {
            "region": "Machinga",
            "value": 0.9717,
            "category": "Much more vulnerable",
            "color": "#D7191C"
        },
        {
            "region": "Mangochi",
            "value": 0.8293,
            "category": "Much more vulnerable",
            "color": "#D7191C"
        },
        {
            "region": "Mchinji",
            "value": 0.4653,
            "category": "Less vulnerable",
            "color": "#A6D96A"
        },
        {
            "region": "Mulanje",
            "value": 0.6042,
            "category": "More vulnerable",
            "color": "#FDAE61"
        },
        {
            "region": "Mwanza",
            "value": 0.5788,
            "category": "More vulnerable",
            "color": "#FDAE61"
        }
    ]

    def handle(self, *args, **kwargs):
        created_count = 0

        for entry in self.DATA:
            district, _ = District.objects.get_or_create(name=entry["region"])
            created = VulnerabilityIndex.objects.create(
                district=district,
                code="ccv_index",
                name= "Vulnerability to Climate Change Index",
                value= entry["value"],
                category=entry["category"],
                color= entry["color"],
              
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Added CV Index for {district.name}"))
            else:
                self.stdout.write(f"Updated CV Index for {district.name}")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Finished. {created_count} records added/updated."))
