from datetime import date
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Reservation
from .models import Product
from .models import Category
from .models import Structure


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nom de la catégorie',
        }


class StructureForm(forms.ModelForm):
    class Meta:
        model = Structure
        fields = ['name', 'email', 'address', 'city', 'zip_code', 'color', 'image', 'valid']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'valid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'Nom de la structure',
            'email': 'Email de la structure pour validation de réservation',
            'address': 'Adresse',
            'city': 'Ville',
            'zip_code': 'Code Postal',
            'color': 'Couleur personnalisé pour le calendrier',
            'image': 'Logo de la structure',
            'valid': 'Valider la structure',
        }


class StructureRegisterForm(forms.ModelForm):
    class Meta:
        model = Structure
        fields = ['name', 'email', 'address', 'city', 'zip_code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Nom de la structure',
            'email': 'Email de la structure pour validation de réservation',
            'address': 'Adresse',
            'city': 'Ville',
            'zip_code': 'Code Postal',
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'quantity', 'category', 'description', 'image', 'price', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

        labels = {
            'name': 'Nom du produit',
            'quantity': 'Quantité',
            'category': 'Catégorie',
            'description': 'Description',
            'image': 'Image',
            'price': 'Prix',
            'status': 'Actif',
        }


class ApprovalForm(forms.Form):
    comment = forms.CharField(label='Commentaire',
                              widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}))


class ReservationForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': timezone.localdate().strftime('%Y-%m-%d'),
                                      'class': 'form-control'}),
        label='Date de début'
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': timezone.localdate().strftime('%Y-%m-%d'),
                                      'class': 'form-control'}),
        label='Date de fin'
    )
    structure = forms.ModelChoiceField(
        queryset=Structure.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Structure'
    )
    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label='Quantité'
    )
    pickup_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label='Heure de récupération'
    )
    deposit_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        label='Heure de dépôt'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        label='Description'
    )

    class Meta:
        model = Reservation
        fields = ['start_date', 'end_date', 'structure', 'quantity', 'pickup_time', 'deposit_time', 'description']

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        product = getattr(self.instance, 'product', None)
        pickup_time = cleaned_data.get('pickup_time')
        deposit_time = cleaned_data.get('deposit_time')

        if start_date == end_date and pickup_time and deposit_time and pickup_time >= deposit_time:
            raise ValidationError("L'heure de récupération doit être postérieure à l'heure de dépôt si la "
                                  "réservation commence et se termine le même jour.")

        if start_date and end_date and start_date > end_date:
            raise ValidationError("La date de départ doit être antérieure à la date de retour.")

        if start_date and start_date < date.today():
            raise ValidationError("La date de départ ne peut pas être antérieure à la date d'aujourd'hui.")

        if product is not None:
            if Reservation.objects.filter(product=product, start_date__lte=end_date, end_date__gte=start_date).exists():
                raise ValidationError("Aucune réservation pour ces dates ne peuvent être fait.")
            if not product.is_available_for_dates(start_date, end_date):
                raise ValidationError("Ce produit n'est pas disponible pour les dates sélectionnées.")

        return cleaned_data
