from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

TYPES = [("sweet", "Sweet breakfast"), ("vegan", "Vegan"), ("vegetarian", "Vegetarian")]


def create_types(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    food_type = apps.get_model("places", "FoodType")
    for slug, name in TYPES:
        food_type.objects.get_or_create(slug=slug, defaults={"name": name})


class Migration(migrations.Migration):
    dependencies = [("places", "0001_initial")]
    operations = [migrations.RunPython(create_types, migrations.RunPython.noop)]
