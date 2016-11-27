from django.contrib import admin
from .models import Date, Product, Activity

# Register your models here.


admin.site.register(
    Date,
    list_display=["title", "date"],
    list_display_links=["title", "date"],
)

admin.site.register(
    Product,
    list_display=["title", "notes", "count"],
    list_display_links=["title", "count"],
)

admin.site.register(
    Activity,
    list_display=["id", "date", "product", "member", "count_change"],
    list_display_links=["date", "product", "count_change"],
)
