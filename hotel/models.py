from django.db import models
from decimal import Decimal, ROUND_HALF_UP
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta, time


def hitung_durasi_menginap(check_in_dt, check_out_dt):
    """
    Menghitung durasi menginap berdasarkan jam 12 siang (noon).
    - Hitung selisih hari kalender antara tanggal check-in dan check-out.
    - Jika jam checkout > 12:00 siang, tambah 1 malam.
    - Minimal 1 malam.
    """
    # Ambil tanggal saja (tanpa jam)
    tanggal_in = check_in_dt.date() if hasattr(check_in_dt, 'date') else check_in_dt
    tanggal_out = check_out_dt.date() if hasattr(check_out_dt, 'date') else check_out_dt
    
    # Hitung selisih hari kalender
    selisih_hari = (tanggal_out - tanggal_in).days
    
    # Cek apakah jam checkout melewati jam 12 siang
    jam_checkout = check_out_dt.time() if hasattr(check_out_dt, 'time') else time(0, 0)
    noon = time(12, 0)
    
    if jam_checkout > noon:
        selisih_hari += 1
    
    # Minimal 1 malam
    return max(selisih_hari, 1)
from django.contrib.auth.models import User
from django.db.models import Sum
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.formats import number_format
from django.contrib.humanize.templatetags.humanize import intcomma


class InventoryItem(models.Model):
    PURCHASE_UNIT_CHOICES = [
        ('item', 'Item'),
        ('pcs', 'Pcs'),
        ('box', 'Box'),
        ('kg', 'Kg'),
    ]

    tanggal_pembelian = models.DateField()  # Tanggal pembelian
    no_po_nota = models.CharField(max_length=100, blank=True, null=True)  # Nomor PO/nota
    nama_supplier = models.CharField(max_length=200, default='Unknown')  # Nama supplier
    nama_barang = models.CharField(max_length=200, default='Unknown')  # Nama barang
    satuan = models.CharField(max_length=10, choices=PURCHASE_UNIT_CHOICES, default='pcs')  # Satuan
    jumlah = models.PositiveIntegerField(default=1)  # Jumlah barang
    harga_satuan = models.DecimalField(max_digits=10, decimal_places=2)  # Harga satuan
    total_harga = models.DecimalField(max_digits=10, decimal_places=2, blank=True)  # Total harga
    stok_awal = models.PositiveIntegerField()  # Stok awal
    stok_tersedia = models.PositiveIntegerField(default=0, editable=False)  # Sisa stok
    keterangan = models.TextField(blank=True, null=True) #keterangannya

    def save(self, *args, **kwargs):
        # Hitung total harga berdasarkan harga_satuan dan jumlah
        self.total_harga = self.harga_satuan * self.jumlah
        self.stok_tersedia = self.stok_awal - self.jumlah  # Misalkan barang yang terjual adalah 'jumlah'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nama_barang

class RoomType(models.Model):
    nama = models.CharField(max_length=100)
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    kapasitas_dewasa = models.IntegerField()
    kapasitas_anak = models.IntegerField()
    keterangan = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nama

class Room(models.Model):
    STATUS_CHOICES = [
        ('Tersedia', 'Tersedia'),
        ('Tidak Tersedia', 'Tidak Tersedia'),
        ('maintenance', 'Dalam Perawatan'),
    ]

    no_kamar = models.CharField(max_length=10)
    tipe_kamar = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Tersedia')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.no_kamar

    @property
    def details(self):
        return f'Tipe: {self.tipe_kamar.nama}, Harga: {self.tipe_kamar.harga}, Kapasitas Dewasa: {self.tipe_kamar.kapasitas_dewasa}, Kapasitas Anak: {self.tipe_kamar.kapasitas_anak}'

    def check_in(self):
        self.status = 'Tidak Tersedia'
        self.save()

    def check_out(self):
        self.status = 'maintenance'
        self.save()

    def selesai_perawatan(self):
        self.status = 'Tersedia'
        self.save()

    @property
    def is_currently_booked(self):
        today = timezone.now().date()
        return CheckIn.objects.filter(
            room=self,
            check_in_date__lte=today,
            checkout__check_out_date__gte=today
        ).exists()


class Hall(models.Model):
    STATUS_CHOICES = [
        ('available', 'Tersedia'),
        ('reserved', 'Dipesan'),
        ('maintenance', 'Dalam Perawatan'),
    ]

    nama = models.CharField(max_length=100)
    kapasitas = models.IntegerField()
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    keterangan = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nama

    def reserve(self):
        self.status = 'reserved'
        self.save()

    def check_out(self):
        self.status = 'maintenance'
        self.save()

    def selesai_perawatan(self):
        self.status = 'available'
        self.save()

    @property
    def is_currently_booked(self):
        today = timezone.now().date()
        return CheckIn.objects.filter(
            hall=self,
            check_in_date__lte=today,
            checkout__check_out_date__gte=today
        ).exists()
        
class KategoriLayanan(models.Model):
    nama = models.CharField(max_length=100)
    keterangan = models.TextField(blank=True)

    def __str__(self):
        return self.nama

class Layanan(models.Model):
    SATUAN_CHOICES = [
        ('satuan', 'Per Satuan'),
        ('porsi', 'Per Porsi'),
        ('pcs', 'Per Pcs'),
        ('pitcher', 'Per Pitcher'),
        ('trip', 'Per Trip'),
        ('jam', 'Per Jam'),
        ('km', 'Per KM'),
        ('hari', 'Per Hari'),
    ]
    
    nama = models.CharField(max_length=100)
    kategori_layanan = models.ForeignKey(KategoriLayanan, on_delete=models.CASCADE)
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    satuan = models.CharField(max_length=10, choices=SATUAN_CHOICES)

    def __str__(self):
        return self.nama
    
    def harga_format(self):
        return f"Rp {intcomma(int(self.harga))}"

class Tamu(models.Model):
    nama = models.CharField(max_length=100)
    warga_negara = models.CharField(max_length=50)
    no_identitas = models.CharField(max_length=50, unique=True)
    no_hp = models.CharField(max_length=15)
    email = models.CharField(max_length=100) # models.EmailField()
    alamat = models.TextField()

    def __str__(self):
        return self.nama

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Dikonfirmasi'),
        ('checked_in', 'Sudah Check-In'),
        ('cancelled', 'Dibatalkan'),
    ]
    GENDER_CHOICES = [
        ('M', 'Laki-laki'),
        ('F', 'Perempuan'),
    ]

    # Data pemesan (diisi saat booking)
    nama_pemesan = models.CharField(max_length=100)
    no_hp_pemesan = models.CharField(max_length=15)

    # Data tamu (diisi saat konfirmasi)
    nama_tamu = models.ForeignKey(Tamu, on_delete=models.CASCADE, null=True, blank=True)
    jenis_kelamin = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, default='')

    kamar = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    aula = models.ForeignKey(Hall, on_delete=models.SET_NULL, null=True, blank=True)
    jumlah_dewasa = models.IntegerField(default=1)
    jumlah_anak = models.IntegerField(default=0)
    tanggal_booking = models.DateTimeField(auto_now_add=True)
    tanggal_check_in = models.DateTimeField()
    tanggal_check_out = models.DateTimeField()
    deposit_booking = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    keterangan = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        target = self.kamar or self.aula
        nama = self.nama_tamu.nama if self.nama_tamu else self.nama_pemesan
        return f"Booking {nama} - {target} [{self.get_status_display()}]"


class CheckIn(models.Model):
    GENDER_CHOICES = [
        ('M', 'Laki-laki'),
        ('F', 'Perempuan'),
    ]

    kamar = models.ForeignKey(Room, on_delete=models.CASCADE, null=True, blank=True)

    aula = models.ForeignKey(Hall, on_delete=models.CASCADE, null=True, blank=True)
    nama_tamu = models.ForeignKey(Tamu, on_delete=models.CASCADE)
    jenis_kelamin = models.CharField(max_length=1, choices=GENDER_CHOICES)
    jumlah_dewasa = models.IntegerField(choices=[(i, str(i)) for i in range(0, 5)])
    jumlah_anak = models.IntegerField(choices=[(i, str(i)) for i in range(0, 5)])
    tanggal_check_in = models.DateTimeField()
    tanggal_check_out = models.DateTimeField()
    deposit = models.DecimalField(max_digits=10, decimal_places=2)

    diskon_persen = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Diskon dalam persen (0–100)"
    )

    total_harga = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    vat = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    status_checkout = models.BooleanField(default=False)
    layanan = models.ManyToManyField(Layanan, blank=True)

    @property
    def total_harga_sebelum_diskon(self):
        if self.tanggal_check_out and self.tanggal_check_in:
            durasi_menginap = hitung_durasi_menginap(self.tanggal_check_in, self.tanggal_check_out)
        else:
            durasi_menginap = 0

        if self.kamar:
            harga_per_malam = self.kamar.tipe_kamar.harga
            return harga_per_malam * durasi_menginap
        elif self.aula:
            return self.aula.harga
        return Decimal('0.00')

    @property
    def diskon_rupiah(self):
        diskon_persen = self.diskon_persen or Decimal('0.00')
        return (self.total_harga_sebelum_diskon * diskon_persen / Decimal('100.00')).quantize(Decimal('0.01'))

    @property
    def total_harga_setelah_diskon(self):
        return max(self.total_harga_sebelum_diskon - self.diskon_rupiah, Decimal('0.00'))

    @property
    def total_harus_dibayar(self):
        return self.total_harga + self.vat - self.deposit

    def save(self, *args, **kwargs):
        # Hitung harga dasar (sebelum diskon)
        harga_dasar = self.total_harga_sebelum_diskon
        # Hitung diskon rupiah berdasarkan persen
        diskon_rupiah = self.diskon_rupiah
        # Total harga setelah diskon
        self.total_harga = max(harga_dasar - diskon_rupiah, Decimal('0.00'))
        # VAT (pajak) bisa diatur sesuai kebutuhan
        self.vat = Decimal('0.00')

        super().save(*args, **kwargs)

    def __str__(self):
        return f'Check-in for {self.nama_tamu.nama} - {self.tanggal_check_in}'
    
# class Checkout(models.Model):
#     check_in = models.ForeignKey('CheckIn', on_delete=models.CASCADE, null=True, blank=True)
#     kamar = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True, blank=True)
#     aula = models.ForeignKey('Hall', on_delete=models.SET_NULL, null=True, blank=True)
#     total_harga = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
#     ppn = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
#     sisa_pembayaran = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
#     status_pembayaran = models.CharField(max_length=20, default='Belum Lunas')
#     tanggal_checkout = models.DateTimeField(auto_now_add=True)

#     def save(self, *args, **kwargs):
#         if self.check_in:
#             if not self.tanggal_checkout:
#                 self.tanggal_checkout = timezone.now()

#             # Hitung harga berdasarkan jenis (kamar atau aula)
#             if self.kamar:
#                 # Harga kamar berdasarkan durasi menginap dalam hari
#                 durasi_menginap = (self.tanggal_checkout - self.check_in.tanggal_check_in).days
#                 harga_sewa = self.kamar.tipe_kamar.harga
#                 total_harga_menginap = harga_sewa * durasi_menginap
#             elif self.aula:
#                 # Harga aula tetap, tanpa durasi
#                 total_harga_menginap = Decimal(self.aula.harga)
#             else:
#                 total_harga_menginap = Decimal(0)

#             # Hitung PPN (11%)
#             self.ppn = total_harga_menginap * Decimal('0.11')

#             # Total harga setelah PPN, dikurangi deposit
#             total_harga_sebelum_deposit = total_harga_menginap + self.ppn
#             self.total_harga = max(total_harga_sebelum_deposit - self.check_in.deposit, Decimal(0))
#             self.sisa_pembayaran = self.total_harga

#             # Status pembayaran
#             self.status_pembayaran = 'Lunas' if self.sisa_pembayaran == 0 else 'Belum Lunas'

#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f'Checkout {self.kamar if self.kamar else self.aula} - {self.total_harga} IDR'

#     def bayar(self, jumlah):
#         """
#         Metode untuk membayar sisa pembayaran.
#         """
#         self.sisa_pembayaran -= Decimal(jumlah)
#         if self.sisa_pembayaran <= 0:
#             self.sisa_pembayaran = Decimal(0)
#             self.status_pembayaran = 'Lunas'
#         self.save()

class Checkout(models.Model):
    check_in = models.ForeignKey('CheckIn', on_delete=models.CASCADE, null=True, blank=True)
    kamar = models.ForeignKey('Room', on_delete=models.SET_NULL, null=True, blank=True)
    aula = models.ForeignKey('Hall', on_delete=models.SET_NULL, null=True, blank=True)
    total_harga = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    ppn = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    sisa_pembayaran = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
    status_pembayaran = models.CharField(max_length=20, default='Belum Lunas')
    tanggal_checkout = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Perhitungan total_harga, ppn, sisa_pembayaran dilakukan di check_out_view
        # agar diskon dan layanan tambahan terhitung dengan benar.
        # Method save() hanya menyimpan data tanpa menimpa nilai yang sudah diset.
        super().save(*args, **kwargs)

    def bayar(self, jumlah):
        """
        Metode untuk membayar sisa pembayaran.
        """
        try:
            jumlah = Decimal(jumlah)  # Pastikan jumlah dalam tipe Decimal
            # Lakukan pengurangan sisa pembayaran
            if jumlah > self.sisa_pembayaran:
                kembalian = jumlah - self.sisa_pembayaran
                self.sisa_pembayaran = Decimal('0.00')
                self.status_pembayaran = 'Lunas'
            else:
                self.sisa_pembayaran -= jumlah
                self.sisa_pembayaran = self.sisa_pembayaran.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                kembalian = Decimal('0.00')
                if self.sisa_pembayaran <= 0:
                    self.status_pembayaran = 'Lunas'

            self.save()  # Simpan perubahan

            return kembalian  # Mengembalikan jumlah kembalian

        except Exception as e:
            raise Exception(f"Error saat melakukan pembayaran: {e}")

    def __str__(self):
        return f"Checkout {self.id} - {self.check_in.nama_tamu} - {self.status_pembayaran}"

class RoomService(models.Model):
    check_in = models.ForeignKey('CheckIn', on_delete=models.CASCADE)
    kategori_layanan = models.ForeignKey(KategoriLayanan, on_delete=models.CASCADE, default=1)  
    layanan = models.ForeignKey(Layanan, on_delete=models.CASCADE)  # Layanan berdasarkan kategori
    harga_layanan = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tanggal_pemesanan = models.DateTimeField(auto_now_add=True)
    deskripsi_layanan = models.TextField()  # Pastikan ini ada

    def save(self, *args, **kwargs):
        # Atur harga layanan dari model Layanan
        if self.layanan:
            self.harga_layanan = self.layanan.harga
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.kategori_layanan.nama} - {self.layanan.nama} untuk {self.check_in}"
    
class CleaningLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    cleaned_room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL)
    cleaned_hall = models.ForeignKey(Hall, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.TextField(blank=True, null=True)  # Catatan pembersihan

    def __str__(self):
        return f"{self.user} cleaned {self.cleaned_room or self.cleaned_hall} on {self.timestamp}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user.username} Profile'

class CatatanTamu(models.Model):
    checkin = models.ForeignKey(CheckIn, on_delete=models.CASCADE, related_name='catatan')
    isi = models.TextField()
    tanggal = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.checkin.nama_tamu.nama} - {self.isi[:20]}"