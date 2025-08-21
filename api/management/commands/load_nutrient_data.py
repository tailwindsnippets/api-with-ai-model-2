import os
import pandas as pd
from django.core.management.base import BaseCommand
from api.models import District, NutrientAdequacy


class Command(BaseCommand):
    help = "Load nutrient adequacy data from a CSV file using pandas"

    def handle(self, *args, **options):
        # Locate CSV in fixtures relative to this command file
        command_dir = os.path.dirname(os.path.realpath(__file__))
        csv_file_path = os.path.join(command_dir, "../../fixtures/riboflavin.csv")

        # Load CSV into pandas dataframe
        df = pd.read_csv(csv_file_path)

        created_count = 0
        updated_count = 0

        for _, row in df.iterrows():
            district_name = str(row["district"]).strip()
            nutrient = str(row["nutrient"]).strip()
            value = float(row["value"])

            # Get or create district
            district, _ = District.objects.get_or_create(name=district_name)

            # Insert or update nutrient adequacy
            obj, created = NutrientAdequacy.objects.update_or_create(
                district=district,
                nutrient=nutrient,
                defaults={"value": value}
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"CSV import completed! {created_count} created, {updated_count} updated."
            )
        )
