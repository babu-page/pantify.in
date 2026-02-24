# Generated initial migration for GST Invoice app

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
                ('address', models.TextField(blank=True)),
                ('gstin', models.CharField(blank=True, max_length=20)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('state_code', models.CharField(blank=True, max_length=4)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='Shop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('gstin', models.CharField(max_length=20)),
                ('address', models.TextField()),
                ('cell', models.CharField(max_length=20)),
                ('state', models.CharField(max_length=64)),
                ('state_code', models.CharField(max_length=4)),
                ('invoice_prefix', models.CharField(default='SP', max_length=10)),
                ('bank_name', models.CharField(max_length=128)),
                ('bank_account_no', models.CharField(max_length=32)),
                ('bank_ifsc', models.CharField(max_length=20)),
                ('is_default', models.BooleanField(default=True)),
            ],
            options={'ordering': ['-is_default', 'name']},
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_date', models.DateTimeField(auto_now_add=True)),
                ('total_before_tax', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=14)),
                ('cgst_amount', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=14)),
                ('sgst_amount', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=14)),
                ('igst_amount', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=14)),
                ('total_amount', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=14)),
                ('is_inter_state', models.BooleanField(default=False)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='invoices.customer')),
            ],
            options={'ordering': ['-order_date']},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sno', models.PositiveSmallIntegerField()),
                ('description', models.CharField(max_length=256)),
                ('hsn_sac', models.CharField(default='998313', max_length=20)),
                ('quantity', models.DecimalField(decimal_places=2, max_digits=12)),
                ('rate', models.DecimalField(decimal_places=2, max_digits=12)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='invoices.order')),
            ],
            options={'ordering': ['order', 'sno'], 'unique_together': {('order', 'sno')}},
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_no', models.CharField(max_length=32, unique=True)),
                ('invoice_date', models.DateField(auto_now_add=True)),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='invoices/%Y/%m/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='invoice', to='invoices.order')),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
