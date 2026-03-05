from decimal import Decimal
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import InventoryItem
from .models import Room, RoomType, Hall
from .models import Layanan, KategoriLayanan, Tamu, CheckIn
from .models import RoomService
from .models import Booking


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['tanggal_pembelian', 'no_po_nota', 'nama_supplier', 'nama_barang', 'stok_awal', 'jumlah', 'satuan', 'harga_satuan', 'keterangan'] 
        
        widgets = {
            'tanggal_pembelian': forms.DateInput(attrs={'type': 'date'}),
            'harga_satuan': forms.NumberInput(attrs={'step': '0.01'}),
            'jumlah': forms.NumberInput()
        }

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['no_kamar', 'tipe_kamar', 'status']

class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['nama', 'harga', 'kapasitas_dewasa', 'kapasitas_anak', 'keterangan']

class HallForm(forms.ModelForm):
    class Meta:
        model = Hall
        fields = ['nama', 'kapasitas', 'harga', 'keterangan', 'status']

class LayananForm(forms.ModelForm):
    class Meta:
        model = Layanan
        fields = ['nama', 'kategori_layanan', 'harga', 'satuan']

class KategoriLayananForm(forms.ModelForm):
    class Meta:
        model = KategoriLayanan
        fields = ['nama', 'keterangan']

class TamuForm(forms.ModelForm):
    class Meta:
        model = Tamu
        fields = ['nama', 'warga_negara', 'no_identitas', 'no_hp', 'email', 'alamat']

class CheckInForm(forms.ModelForm):
    layanan = forms.ModelMultipleChoiceField(
        queryset=Layanan.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Layanan Tambahan (Room Service)"
    )

    class Meta:
        model = CheckIn
        fields = [
            'kamar',
            'aula',
            'nama_tamu',
            'jenis_kelamin',
            'jumlah_dewasa',
            'jumlah_anak',
            'tanggal_check_in',
            'tanggal_check_out',
            'deposit',
            'diskon_persen',  # pakai ini saja
            'layanan',
        ]
        widgets = {
            'tanggal_check_in': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'required': True
            }),
            'tanggal_check_out': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'required': True
            }),
            'jenis_kelamin': forms.Select(choices=CheckIn.GENDER_CHOICES),
            'diskon_persen': forms.NumberInput(attrs={
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'Masukkan diskon dalam %'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.id:
            self.fields['layanan'].initial = Layanan.objects.filter(roomservice__check_in=self.instance)

# class CheckInForm(forms.ModelForm):
#     class Meta:
#         model = CheckIn
#         fields = [
#             'kamar', 
#             'aula', 
#             'nama_tamu', 
#             'jenis_kelamin', 
#             'jumlah_dewasa', 
#             'jumlah_anak', 
#             'tanggal_check_in', 
#             'tanggal_check_out', 
#             'deposit'
#         ]
#         widgets = {
#             'tanggal_check_in': forms.DateTimeInput(attrs={
#                 'type': 'datetime-local',  # Input untuk tanggal dan waktu
#                 'required': True
#             }),
#             'tanggal_check_out': forms.DateTimeInput(attrs={
#                 'type': 'datetime-local',  # Input untuk tanggal dan waktu
#                 'required': True
#             }),
#             'jenis_kelamin': forms.Select(choices=CheckIn.GENDER_CHOICES),  # Dropdown untuk memilih jenis kelamin
#         }

class CheckOutForm(forms.ModelForm):
    class Meta:
        model = CheckIn
        fields = ['tanggal_check_out']
        widgets = {
            'tanggal_check_out': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'required': True
            }),
        }

class PaymentForm(forms.Form):
    checkout_id = forms.IntegerField(widget=forms.HiddenInput())
    payment = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),  # Pembayaran harus lebih dari 0
        widget=forms.NumberInput(attrs={
            'step': '0.01',
            'required': True,
            'placeholder': 'Masukkan pembayaran'
        })
    )

class RoomServiceForm(forms.ModelForm):
    class Meta:
        model = RoomService
        fields = ['check_in', 'kategori_layanan', 'layanan']
        widgets = {
            'check_in': forms.Select(),
            'kategori_layanan': forms.Select(attrs={
                'id': 'kategori_layanan',
                'onchange': 'this.form.submit()'  # Menambahkan form submit saat kategori berubah
            }),
            'layanan': forms.Select(attrs={'id': 'layanan'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter check_in untuk tamu yang belum check-out
        self.fields['check_in'].queryset = CheckIn.objects.filter(status_checkout=False)

        # Ambil kategori layanan jika ada di data form atau instance
        kategori_id = self.data.get('kategori_layanan') or self.instance.kategori_layanan_id

        if kategori_id:
            try:
                kategori_id = int(kategori_id)
                # Filter layanan berdasarkan kategori
                self.fields['layanan'].queryset = Layanan.objects.filter(kategori_layanan_id=kategori_id)
            except (ValueError, TypeError):
                self.fields['layanan'].queryset = Layanan.objects.none()
        else:
            # Kosongkan queryset layanan jika kategori belum dipilih
            self.fields['layanan'].queryset = Layanan.objects.none()


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'nama_pemesan', 'no_hp_pemesan',
            'kamar', 'aula',
            'jumlah_dewasa', 'jumlah_anak',
            'tanggal_check_in', 'tanggal_check_out',
            'deposit_booking', 'keterangan',
        ]
        widgets = {
            'nama_pemesan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama pemesan'}),
            'no_hp_pemesan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No HP pemesan'}),
            'tanggal_check_in': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 'class': 'form-control'
            }),
            'tanggal_check_out': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 'class': 'form-control'
            }),
            'kamar': forms.Select(attrs={'class': 'form-control'}),
            'aula': forms.Select(attrs={'class': 'form-control'}),
            'jumlah_dewasa': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'jumlah_anak': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'deposit_booking': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'keterangan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['kamar'].queryset = Room.objects.filter(status='Tersedia')
        self.fields['aula'].queryset = Hall.objects.filter(status='available')


class KonfirmasiBookingForm(forms.Form):
    GENDER_CHOICES = [
        ('M', 'Laki-laki'),
        ('F', 'Perempuan'),
    ]

    MODE_CHOICES = [
        ('existing', 'Pilih Tamu yang Sudah Terdaftar'),
        ('new', 'Input Tamu Baru'),
    ]

    mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='existing',
    )

    # Pilih tamu existing
    tamu_existing = forms.ModelChoiceField(
        queryset=Tamu.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Pilih Tamu',
    )

    # Input tamu baru
    nama = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama lengkap'}))
    warga_negara = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contoh: Indonesia'}))
    no_identitas = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No KTP/Paspor'}))
    no_hp = forms.CharField(max_length=15, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'No HP tamu'}))
    email = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email tamu'}))
    alamat = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Alamat tamu'}))

    # Jenis kelamin (wajib)
    jenis_kelamin = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('mode')

        if mode == 'existing':
            if not cleaned_data.get('tamu_existing'):
                raise forms.ValidationError('Silakan pilih tamu yang sudah terdaftar.')
        elif mode == 'new':
            required_fields = ['nama', 'warga_negara', 'no_identitas', 'no_hp', 'email', 'alamat']
            missing = [f for f in required_fields if not cleaned_data.get(f)]
            if missing:
                raise forms.ValidationError(f'Data tamu baru belum lengkap: {", ".join(missing)}')

        return cleaned_data
