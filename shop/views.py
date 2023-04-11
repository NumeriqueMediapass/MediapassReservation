from datetime import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.core.mail import send_mail, EmailMultiAlternatives
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .forms import ReservationForm, CategoryForm, StructureForm, ApprovalForm, StructureRegisterForm
from .models import Reservation, Category, Structure
from .forms import ProductForm
from .models import Product


# Produits
def is_staff_or_superuser(user):
    return user.is_staff or user.is_superuser


@user_passes_test(is_staff_or_superuser)
def product_list(request):
    products = Product.objects.all()
    return render(request, 'shop/product_list.html', {'products': products})


def product_list_user(request):
    products = Product.objects.all()
    product_count = products.count()
    return render(request, 'shop/product_list_user.html', {'products': products, 'product_count': product_count})


def product_detail(request, pk):
    product = Product.objects.get(pk=pk)
    reservations = Reservation.objects.filter(product=product)
    structures = Structure.objects.filter(is_registered=True)
    today = datetime.today().strftime('%Y-%m-%d')

    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.product = product
            try:
                reservation.clean()  # Ajout de la validation du formulaire
            except forms.ValidationError as e:
                form.add_error(None, e)
            else:
                if reservation.quantity > product.quantity:
                    form.add_error('quantity', "La quantité demandée n'est pas disponible.")
                elif Reservation.objects.filter(
                        product=product,
                        start_date__lte=reservation.end_date,
                        end_date__gte=reservation.start_date
                ).exists():
                    form.add_error(None, "Le produit est déjà réservé pour les dates demandées.")
                elif (
                        reservation.start_date == reservation.end_date and
                        reservation.pickup_time >= reservation.deposit_time
                ):
                    form.add_error(
                        'deposit_time',
                        "L'heure de récupération doit être postérieure à l'heure de dépôt si "
                        "la réservation commence et se termine le même jour."
                    )
                else:
                    reservation.save()
                    messages.success(request, "La réservation a bien été enregistrée.")

                    subject = 'Nouvelle réservation'
                    from_email = 'numerique.ccsa@gmail.com'
                    to_email = ['j.brechoire@cc-sudavesnois.fr']

                    # Charger le contenu HTML et le texte brut du message à partir de templates
                    html_content = render_to_string('mail/mailresa.html',
                                                    {'product': product, 'reservation': reservation})
                    text_content = strip_tags(html_content)

                    # Créer l'email avec l'en-tête Content-Type défini sur 'text/html'
                    email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
                    email.attach_alternative(html_content, "text/html")

                    # Envoyer l'email
                    email.send()
                    return redirect('home')
    else:
        form = ReservationForm()

    return render(
        request,
        'shop/product_detail.html',
        {
            'product': product,
            'form': form,
            'reservations': reservations,
            'today': today,
            'structures': structures
        }
    )


@login_required
@user_passes_test(is_staff_or_superuser)
def product_create(request):
    categories = Category.objects.all()
    categories_count = categories.count()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Le produit a été créé avec succès.')
            return redirect('product_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProductForm()
    return render(request, 'shop/product_form.html', {'form': form, 'categories_count': categories_count})


@user_passes_test(is_staff_or_superuser)
def product_update(request, pk):
    product = Product.objects.get(pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Le produit a été mis à jour avec succès.')
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'shop/product_form.html', {'form': form})


@user_passes_test(is_staff_or_superuser)
def product_delete(request, pk):
    Product.objects.get(pk=pk).delete()
    messages.success(request, 'Le produit a été supprimé avec succès.')
    return redirect('product_list')


# Réservations
@user_passes_test(is_staff_or_superuser)
def create_reservation(request, product_id):
    product = Product.objects.get(id=product_id)
    reservations = Reservation.objects.filter(product=product)
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.product = product

            # Vérifier si une réservation existe déjà pour la plage de dates sélectionnée
            existing_reservation = Reservation.objects.filter(
                product=product,
                start_date__lte=reservation.end_date,
                end_date__gte=reservation.start_date,
            ).first()

            if existing_reservation:
                messages.error(request, 'Ce produit est déjà réservé pour cette période.')
                return redirect('create_reservation', product_id=product.id)

            reservation.save()
            messages.success(request, 'Réservation créée avec succès.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = ReservationForm()
    return render(request, 'shop/create_reservation.html',
                  {'product': product, 'form': form, 'reservations': reservations})


@user_passes_test(is_staff_or_superuser)
def reservation_details(request, pk):
    reservation = Reservation.objects.get(pk=pk)
    return render(request, 'shop/reservation_details.html', {'reservation': reservation})


@user_passes_test(is_staff_or_superuser)
def reservation_list(request):
    reservations = Reservation.objects.all()
    return render(request, 'shop/reservation_list.html', {'reservations': reservations})


@user_passes_test(is_staff_or_superuser)
def approve_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if reservation.is_approved:
        return redirect('reservation_list')
    if request.method == 'POST':
        form = ApprovalForm(request.POST)
        if form.is_valid():
            reservation.is_approved = True
            reservation.approval_comment = form.cleaned_data['comment']
            reservation.save()
            # Envoyer un email de confirmation
            send_mail(
                f'Réservation approuvée pour {reservation.product.name}',
                f'Votre réservation pour le produit {reservation.product.name} a été approuvée. ',
                'j.brechoire@cc-sudavesnois.fr',
                [reservation.structure.email],
                fail_silently=False,
            )
            messages.success(request, 'Réservation approuvée avec succès.')
            return redirect('reservation_list')
    else:
        form = ApprovalForm()
    return render(request, 'shop/approve_reservation.html', {'reservation': reservation, 'form': form})


@user_passes_test(is_staff_or_superuser)
def disapprove_reservation(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.method == 'POST':
        reservation.is_approved = False
        reservation.approval_comment = ''
        reservation.save()
        send_mail(
            f'Réservation désapprouvée pour {reservation.product.name}',
            f'Votre réservation pour le produit {reservation.product.name} a été désapprouvée.',
            'j.brechoire@cc-sudavesnois.fr',
            [reservation.structure.email],
            fail_silently=False,
        )
        messages.success(request, 'Réservation désapprouvée avec succès.')
        return redirect('reservation_list')
    return render(request, 'shop/disapprove_reservation.html', {'reservation': reservation})


@user_passes_test(is_staff_or_superuser)
def delete_reservation(request, pk):
    Reservation.objects.get(pk=pk).delete()
    messages.success(request, 'La réservation a été supprimée avec succès.')
    return redirect('reservation_list')


# Categories

@user_passes_test(is_staff_or_superuser)
def category_list(request):
    categorys = Category.objects.all()
    return render(request, 'shop/category_list.html', {'categorys': categorys})


def category_detail(request, pk):
    category = Category.objects.get(pk=pk)
    products = category.product_set.all()
    product_count = products.count()
    return render(request, 'shop/category_detail.html', {'category': category,
                                                         'products': products,
                                                         'product_count': product_count})


@user_passes_test(is_staff_or_superuser)
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'La catégorie a été créée avec succès.')
            return redirect('category_list')
    else:
        form = CategoryForm()
    return render(request, 'shop/category_form.html', {'form': form})


@user_passes_test(is_staff_or_superuser)
def category_update(request, pk):
    category = Category.objects.get(pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'shop/category_form.html', {'form': form})


@user_passes_test(is_staff_or_superuser)
def category_delete(request, pk):
    Category.objects.get(pk=pk).delete()
    return redirect('category_list')


# Structures
@user_passes_test(is_staff_or_superuser)
def structure_list(request):
    structures = Structure.objects.all()
    return render(request, 'shop/structure_list.html', {'structures': structures})


@user_passes_test(is_staff_or_superuser)
def structure_detail(request, pk):
    structure = Structure.objects.get(pk=pk)
    reservations = Reservation.objects.filter(structure=structure).order_by('-id')
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.structure = structure
            reservation.save()
            return redirect('reservation_details', pk=reservation.pk)
    else:
        form = ReservationForm()
    return render(request, 'shop/structure_detail.html',
                  {'structure': structure, 'reservations': reservations, 'form': form})


@user_passes_test(is_staff_or_superuser)
def structure_create(request):
    if request.method == 'POST':
        form = StructureForm(request.POST)
        if form.is_valid():
            form = StructureForm(request.POST, request.FILES)
            form.save()
            return redirect('structure_list')
    else:
        form = StructureForm()
    return render(request, 'shop/structure_form.html', {'form': form})


def structure_create_register(request):
    if request.method == 'POST':
        form = StructureRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            structure = form.save(commit=False)
            structure.valid = False
            structure.save()
            messages.success(request, 'Merci pour votre demande d\'inscription.')
            return redirect('home')
    else:
        form = StructureRegisterForm()
    return render(request, 'shop/structure_form_register.html', {'form': form})


@user_passes_test(is_staff_or_superuser)
def structure_update(request, pk):
    structure = Structure.objects.get(pk=pk)
    if request.method == 'POST':
        form = StructureForm(request.POST, request.FILES, instance=structure)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            messages.success(request, 'La structure a été modifiée avec succès.')
            return redirect('structure_list')
    else:
        form = StructureForm(instance=structure)
    return render(request, 'shop/structure_form.html', {'form': form, 'structure': structure})


@user_passes_test(is_staff_or_superuser)
def structure_validate(request, pk):
    structure = Structure.objects.get(pk=pk)
    structure.is_registered = True
    structure.save()

    # Envoi d'un email de confirmation
    subject = 'Validation de votre structure'
    message = 'Bonjour {},\n\nNous vous informons que votre structure {} a été validée.\n\nCordialement,\nL\'équipe ' \
              'du réseau Médi@\'pass'.format(structure.name, structure.name)
    from_email = 'j.brechoire@cc-sudavesnois.fr'
    recipient_list = [structure.email]
    send_mail(subject, message, from_email, recipient_list)

    messages.success(request, 'La structure a été validée avec succès.')
    return redirect('structure_list')


@user_passes_test(is_staff_or_superuser)
def structure_delete(request, pk):
    Structure.objects.get(pk=pk).delete()
    return redirect('structure_list')


def reservation_count(request):
    count = Reservation.objects.filter(is_approved=False).count()
    return {'reservation_count': count}


def count_pending_structures(request):
    count = Structure.objects.filter(valid=False).count()
    return {'pending_count': count}

