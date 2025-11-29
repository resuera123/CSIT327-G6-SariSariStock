from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone
from unicodedata import category

# Create your models here.
class Products(models.Model):

    CATEGORY_CHOICES = (
        ('food', 'Food'),
        ('drinks', 'Drinks'),
        ('toiletries', 'Toiletries'),
        ('household', 'Household'),
        ('medicine', 'Medicine'),
        ('toys', 'Toys'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('archive', 'Archive'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    code = models.CharField(max_length=100)
    categories = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    name = models.TextField(max_length=100)
    cost = models.FloatField(default=0)
    price = models.FloatField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    quantity = models.IntegerField(default=0)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code + " - " + self.name
    
class MovementLog(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='movement_logs')
    reference = models.CharField(max_length=100)
    date = models.DateTimeField(default=timezone.now)
    quantity_before = models.IntegerField(default=0)
    change = models.IntegerField()
    quantity_after = models.IntegerField(default=0)
    note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.product.code + " - " + self.reference
    
class Sales(models.Model):
    code = models.CharField(max_length=100)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code
    
class salesItems(models.Model):
    sales_id = models.ForeignKey(Sales, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE)
    price = models.FloatField(default=0)
    qty = models.IntegerField(default=0)
    total = models.FloatField(default=0)