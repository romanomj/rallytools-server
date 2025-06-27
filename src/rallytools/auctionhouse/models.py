from django.db import models
from gamedata.models import Item


class Commodity(models.Model):
    id = models.AutoField(primary_key=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, db_index=True)
    quantity = models.IntegerField(help_text="Quantity of item on Auction House at a given timestamp")
    market_price = models.BigIntegerField(help_text="Price in copper")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Automatically set a timestamp")
    origin = models.CharField(max_length=64, db_index=True, help_text="SHA256 value to prevent duplicates")
    
    class Meta:
        verbose_name_plural = "Commodities"
        unique_together = [['item', 'origin']]

    def __str__(self):
        return f"{self.item.name}({self.item.id}) - {self.timestamp}"

