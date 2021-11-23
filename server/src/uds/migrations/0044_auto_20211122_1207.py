# Generated by Django 3.2.8 on 2021-11-22 12:07
# Heavily modified by UDS-Team on 2021-11-22 12:07
from django.db import migrations, models
import django.db.models.deletion

from uds.models import Transport, Authenticator

TRANS_ALLOW = Transport.ALLOW
TRANS_DENY = Transport.DENY
TRANS_NOFILTERING = Transport.NO_FILTERING

# Auths
AUTH_ALLOW = Authenticator.ALLOW
AUTH_DENY = Authenticator.DENY
AUTH_NOFILTERING = Authenticator.NO_FILTERING
AUTH_DISABLED = Authenticator.DISABLED
AUTH_VISIBLE = Authenticator.VISIBLE
AUTH_HIDDEN = Authenticator.HIDDEN

def migrate_fwd(apps, schema_editor):
    Transport = apps.get_model('uds', 'Transport')
    for transport in Transport.objects.all():
        value = TRANS_NOFILTERING  # Defaults to "not configured"
        if transport.networks.count() > 0:
            if transport.nets_positive:
                value = TRANS_ALLOW
            else:
                value = TRANS_DENY
        transport.net_filtering = value
        transport.save()

    Authenticator = apps.get_model('uds', 'Authenticator')
    for authenticator in Authenticator.objects.all():
        authenticator.state = AUTH_VISIBLE if authenticator.visible else AUTH_HIDDEN
        authenticator.save()


def migrate_bck(apps, schema_editor):
    Transport = apps.get_model('uds', 'Transport')
    for transport in Transport.objects.all():
        transport.nets_positive = transport.net_filtering == TRANS_ALLOW
        transport.save()

    Authenticator = apps.get_model('uds', 'Authenticator')
    for authenticator in Authenticator.objects.all():
        authenticator.visible = authenticator.state == AUTH_VISIBLE
        authenticator.save()


class Migration(migrations.Migration):

    dependencies = [
        ('uds', '0043_clean_unused_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='network',
            name='authenticators',
            field=models.ManyToManyField(
                db_table='uds_net_auths',
                related_name='networks',
                to='uds.Authenticator',
            ),
        ),
        migrations.AddField(
            model_name='authenticator',
            name='net_filtering',
            field=models.CharField(
                default=AUTH_NOFILTERING,
                max_length=1,
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name='authenticator',
            name='state',
            field=models.CharField(
                default=AUTH_VISIBLE,
                max_length=1,
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name='transport',
            name='net_filtering',
            field=models.CharField(
                default=TRANS_NOFILTERING,
                max_length=1,
                db_index=True,
            ),
        ),
        migrations.AlterField(
            model_name='service',
            name='token',
            field=models.CharField(
                blank=True, default=None, max_length=64, null=True, unique=True
            ),
        ),
        # Indexes

        migrations.CreateModel(
            name='ServiceTokenAlias',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('alias', models.CharField(max_length=64, unique=True)),
                (
                    'service',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='aliases',
                        to='uds.service',
                    ),
                ),
            ],
        ),
        migrations.RunPython(migrate_fwd, migrate_bck),
        migrations.RemoveField(
            model_name='transport',
            name='nets_positive',
        ),
        migrations.RemoveField(
            model_name='authenticator',
            name='visible',
        ),
    ]
