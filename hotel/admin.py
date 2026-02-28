from django.contrib import admin
from .models import InventoryItem
from .models import Tamu
from .models import CheckIn
from .models import Checkout, Room, Hall
from .models import Layanan, KategoriLayanan, CleaningLog

admin.site.register(Tamu)

class CheckoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'check_in', 'kamar', 'aula', 'total_harga', 'status_pembayaran', 'tanggal_checkout')

admin.site.register(Checkout, CheckoutAdmin)

class CheckInAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'nama_tamu', 'jenis_kelamin', 'jumlah_dewasa', 'jumlah_anak', 
        'tanggal_check_in', 'tanggal_check_out', 'deposit', 'total_harga', 
        'vat', 'total_harus_dibayar', 'kamar', 'aula', 'status_checkout'
    )
    list_filter = ('tanggal_check_in', 'tanggal_check_out', 'status_checkout', 'kamar', 'aula')
    search_fields = ('nama_tamu__nama', 'id')
    ordering = ('-tanggal_check_in',)
    readonly_fields = ('total_harga', 'vat', 'total_harus_dibayar')  # Agar field ini hanya bisa dilihat, tidak bisa diubah
    
    fieldsets = (
        (None, {
            'fields': ('nama_tamu', 'jenis_kelamin', 'jumlah_dewasa', 'jumlah_anak', 'deposit')
        }),
        ('Tanggal Check-In/Out', {
            'fields': ('tanggal_check_in', 'tanggal_check_out')
        }),
        ('Kamar atau Aula', {
            'fields': ('kamar', 'aula')
        }),
        ('Informasi Harga', {
            'fields': ('total_harga', 'vat', 'total_harus_dibayar')
        }),
        ('Status', {
            'fields': ('status_checkout',)
        }),
        ('Layanan Tambahan', {
            'fields': ('layanan',)
        })
    )

    # Menambahkan fungsi untuk menampilkan total_harus_dibayar secara dinamis di list display
    def total_harus_dibayar(self, obj):
        return obj.total_harus_dibayar
    total_harus_dibayar.short_description = 'Total Harus Dibayar'

admin.site.register(CheckIn, CheckInAdmin)

class RoomAdmin(admin.ModelAdmin):
    list_display = ('no_kamar', 'tipe_kamar', 'status')  # Sesuaikan field yang ingin ditampilkan
    search_fields = ('no_kamar', 'tipe_kamar__nama')  # Jika ada field terkait di tipe_kamar

admin.site.register(Room, RoomAdmin)

class HallAdmin(admin.ModelAdmin):
    list_display = ('nama', 'kapasitas', 'status')
    search_fields = ('nama',)

admin.site.register(Hall, HallAdmin)

# Register your models here.
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'tanggal_pembelian',
        'no_po_nota',
        'nama_supplier',
        'nama_barang',
        'satuan',
        'harga_satuan',
        'jumlah',
        'total_harga',
        'keterangan',
        
    )
    search_fields = ('nama_barang', 'no_po_nota', 'nama_supplier')
    list_filter = ('tanggal_pembelian', 'satuan')
    ordering = ('-tanggal_pembelian',)
    list_per_page = 20

admin.site.register(InventoryItem, InventoryItemAdmin)

@admin.register(Layanan)
class LayananAdmin(admin.ModelAdmin):
    list_display = ('nama', 'kategori_layanan', 'harga', 'satuan')  # Kolom yang ingin ditampilkan di daftar
    search_fields = ('nama',)  # Memungkinkan pencarian berdasarkan nama layanan

@admin.register(KategoriLayanan)  # Jika Anda juga ingin mendaftarkan kategori layanan
class KategoriLayananAdmin(admin.ModelAdmin):
    list_display = ('nama',)

class CleaningLogAdmin(admin.ModelAdmin):
    # Kolom yang akan ditampilkan di daftar admin
    list_display = ('user', 'cleaned_room', 'cleaned_hall', 'timestamp', 'note')
    
    # Kolom yang bisa dicari di admin
    search_fields = ('user__username', 'cleaned_room__no_kamar', 'cleaned_hall__nama', 'note')
    
    # Filter berdasarkan tanggal atau status
    list_filter = ('timestamp',)
    
    # Fitur pengurutan berdasarkan timestamp
    ordering = ('-timestamp',)
    
    # Menambahkan opsi untuk menghapus banyak item sekaligus
    actions = ['delete_selected']

# Daftarkan model CleaningLog ke admin
admin.site.register(CleaningLog, CleaningLogAdmin)