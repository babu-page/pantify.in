# Create default SAI PAINTS shop if no shop exists (run after 0001_initial)

from django.db import migrations


def create_default_shop(apps, schema_editor):
    Shop = apps.get_model('invoices', 'Shop')
    if Shop.objects.exists():
        return
    Shop.objects.create(
        name='SAI PAINTS',
        gstin='37PEFPS6526R1Z6',
        address='#17/505-A2, Kasapuram Road, GUNTAKAL-515 801, A.P.',
        cell='8639034294',
        state='A.P.',
        state_code='37',
        invoice_prefix='SP',
        bank_name='STATE BANK OF INDIA',
        bank_account_no='44758266961',
        bank_ifsc='SBIN0013021',
        is_default=True,
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_shop, noop),
    ]
