from django.db import models
from django.db.models import Q


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def is_available_for_dates(self, start_date, end_date):
        reservations = self.reservation_set.filter(
            Q(start_date__range=(start_date, end_date)) | Q(end_date__range=(start_date, end_date)) | Q(
                start_date__lte=start_date, end_date__gte=end_date)
        )

        if reservations.exists():
            return False

        return True

    def reserve(self, reservation_quantity):
        self.quantity -= reservation_quantity
        self.save()

    def cancel_reservation(self, reservation_quantity):
        self.quantity += reservation_quantity
        self.save()


class Structure(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    email = models.EmailField()
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    color = models.CharField(blank=True, max_length=20)
    image = models.ImageField(upload_to='structure_images', null=True, blank=True)
    valid = models.BooleanField(default=True)
    is_registered = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Reservation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    structure = models.ForeignKey(Structure, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    is_approved = models.BooleanField(default=False)
    deposit_time = models.TimeField(null=True)
    pickup_time = models.TimeField(null=True)
    description = models.TextField(blank=False)

    def __str__(self):
        return f"Reservation for {self.product.name} from {self.start_date} to {self.end_date}"

    def approve_reservation(self):
        if self.is_approved:
            return
        self.is_approved = True
        self.save()
        self.product.reserve(self.quantity)

    def cancel_reservation(self):
        if not self.is_approved:
            return
        self.is_approved = False
        self.save()
        self.product.cancel_reservation(self.quantity)
