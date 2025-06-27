import json
import hashlib
import logging
from rallytools import settings
from .models import *
from lib import battlenet, market

logger = logging.getLogger('__name__')

class AuctionHouseImportError(Exception):
    """
    Base exception class for jobs related to Auction House/Commodities Data Imports
    """
    pass

class AuctionHouseImporter(object):
    def __init__(self):
        self.battlenet_client = battlenet.BattleNetAPI(settings.BATTLENET_CLIENT_ID, settings.BATTLENET_CLIENT_SECRET)

    def import_commodities(self):
        num_added = 0
        num_skipped = 0
        
        origin_hash = hashlib.sha256()

        try:
            response = self.battlenet_client.get_commodities()

            # Generate an origin; helps prevent duplicates

            origin_hash.update(json.dumps(response, sort_keys=True).encode('utf-8'))
            origin = origin_hash.hexdigest()

            # Check for existing matches
            existing_commodities = Commodity.objects.filter(origin=origin).values_list('item__id', flat=True)
            existing_items = Item.objects.all().values_list('id', flat=True)

            # Run market analysis
            market_data = market.analyze_market_data(response['auctions'])
            
            for item_id in market_data:
                if item_id in existing_commodities:
                    num_skipped += 1
                    logging.info(f"DEBUG: Skipping {item_id}.  It exists with origin {origin}")
                    continue

                if item_id not in existing_items:
                    # Need to create this item
                    logging.info(f"INFO: Creating entry for item {item_id}")

                    # First get the item data
                    try:
                        item_response = self.battlenet_client.get_item(item_id)
                    except battlenet.BattleNetAPINotFoundError as e:
                        logger.warning(f"WARNING: item id {item_id} has an existing listing but is not found in the Battle.net API.  It's likely a junk item")
                        continue



                    # Then handle the media
                    item_media_response = self.battlenet_client.get_item_media(item_id)
                    icon = item_media_response['assets'][0]['value']

                    item, created = Item.objects.get_or_create(
                        id=item_id,
                        name=item_response['name'],
                        item_class=item_response['item_class']['name'],
                        item_subclass=item_response['item_subclass']['name'],
                        icon=icon
                    )
                else:
                    item = Item.objects.get(id=item_id)
                    logging.debug(f"DEBUG: Using existing item {item}")

                commodity = Commodity.objects.create(
                    item=item,
                    quantity=market_data[item_id]['total_quantity'],
                    market_price=market_data[item_id]['market_price'],
                    origin=origin
                )
                commodity.save()
                num_added += 1
                logging.debug(f"DEBUG: saved commodity for {item_id} with origin: {origin}")

                num_added += 1

        except Exception as e:
            logger.error(f"ERROR: Failed to import auction house commodity data: {e}")
            raise AuctionHouseImportError(f"Failed to import auction house commodity data: {e}")

        return {"num_added": num_added, "num_skipped": num_skipped} 
