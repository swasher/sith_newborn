from django.apps import AppConfig


class InventoryConfig(AppConfig):
    name = 'inventory'
    verbose_name = 'Inventory'

    def ready(self):
        import inventory.signals