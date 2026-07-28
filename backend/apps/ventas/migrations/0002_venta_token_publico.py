"""Token público de la nota de venta (el QR que se entrega al cliente).

Se añade en tres pasos porque el campo es ``unique``: si se creara ya único con
un default, todas las filas existentes recibirían el MISMO uuid y la restricción
fallaría. Por eso: crear sin unique → rellenar fila por fila → aplicar unique.
"""

import uuid

from django.db import migrations, models


def rellenar_tokens(apps, schema_editor):
    Venta = apps.get_model("ventas", "Venta")
    for venta in Venta.objects.filter(token_publico__isnull=True).iterator():
        Venta.objects.filter(pk=venta.pk).update(token_publico=uuid.uuid4())


class Migration(migrations.Migration):

    dependencies = [
        ("ventas", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="venta",
            name="token_publico",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, null=True, verbose_name="token público"
            ),
        ),
        migrations.RunPython(rellenar_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="venta",
            name="token_publico",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, unique=True, verbose_name="token público"
            ),
        ),
    ]
