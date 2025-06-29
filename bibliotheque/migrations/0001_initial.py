# Generated by Django 5.2.3 on 2025-06-23 09:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Categorie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, verbose_name='Nom de la catégorie')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sous_categories', to='bibliotheque.categorie', verbose_name='Catégorie parente')),
            ],
            options={
                'verbose_name': 'Catégorie',
                'verbose_name_plural': 'Catégories',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Fourniture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, verbose_name='Nom de la fourniture')),
                ('unite', models.CharField(max_length=20, verbose_name='Unité de mesure')),
                ('prix_achat_ht', models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Prix d'achat HT")),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('reference', models.CharField(blank=True, max_length=50, null=True, verbose_name='Référence')),
                ('categorie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fournitures', to='bibliotheque.categorie', verbose_name='Catégorie')),
            ],
            options={
                'verbose_name': 'Fourniture',
                'verbose_name_plural': 'Fournitures',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='MainOeuvre',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, verbose_name="Nom du type de main d'œuvre")),
                ('cout_horaire', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Coût horaire')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('categorie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='main_oeuvre', to='bibliotheque.categorie', verbose_name='Catégorie')),
            ],
            options={
                'verbose_name': "Main d'œuvre",
                'verbose_name_plural': "Main d'œuvre",
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='Ouvrage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200, verbose_name="Nom de l'ouvrage")),
                ('unite', models.CharField(max_length=20, verbose_name='Unité de mesure')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('code', models.CharField(blank=True, max_length=50, null=True, verbose_name='Code')),
                ('categorie', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ouvrages', to='bibliotheque.categorie', verbose_name='Catégorie')),
            ],
            options={
                'verbose_name': 'Ouvrage',
                'verbose_name_plural': 'Ouvrages',
                'ordering': ['nom'],
            },
        ),
        migrations.CreateModel(
            name='IngredientOuvrage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('element_id', models.PositiveIntegerField(verbose_name="ID de l'élément")),
                ('quantite', models.DecimalField(decimal_places=3, max_digits=10, verbose_name='Quantité')),
                ('element_type', models.ForeignKey(limit_choices_to={'model__in': ('fourniture', 'mainoeuvre')}, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name="Type d'élément")),
                ('ouvrage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients', to='bibliotheque.ouvrage', verbose_name='Ouvrage')),
            ],
            options={
                'verbose_name': "Ingrédient d'ouvrage",
                'verbose_name_plural': "Ingrédients d'ouvrage",
                'ordering': ['ouvrage', 'element_type', 'element_id'],
                'unique_together': {('ouvrage', 'element_type', 'element_id')},
            },
        ),
    ]
