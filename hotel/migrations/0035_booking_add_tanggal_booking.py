from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0034_booking'),
    ]

    operations = [
        migrations.RunSQL(
            # Tambah kolom tanggal_booking jika belum ada (SQLite ALTER TABLE ADD COLUMN)
            sql="""
                ALTER TABLE hotel_booking ADD COLUMN tanggal_booking datetime NOT NULL DEFAULT (datetime('now'));
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
