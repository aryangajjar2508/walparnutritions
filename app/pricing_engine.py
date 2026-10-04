import json
from typing import List, Dict, Any, Optional
from app.config import INGREDIENTS_DB_PATH, DEFAULT_PROFIT_MARGIN_PCT, DEFAULT_GST_PCT

class PricingEngine:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or INGREDIENTS_DB_PATH
        self.ingredients_db = {}
        self.dosage_forms = {}
        self.packaging_options = {}
        self.volume_tiers = []
        self.load_data()

    def load_data(self):
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("ingredients", []):
                    self.ingredients_db[item["id"]] = item
                    self.ingredients_db[item["name"].lower()] = item
                for form in data.get("dosage_forms", []):
                    self.dosage_forms[form["id"]] = form
                for pack in data.get("packaging_options", []):
                    self.packaging_options[pack["id"]] = pack
                self.volume_tiers = data.get("volume_discount_tiers", [])
        except Exception as e:
            print(f"Error loading pricing database: {e}")

    def dose_to_kg_factor(self, unit: str) -> float:
        u = unit.lower()
        if u in ['g', 'gm']:
            return 1e-3
        elif u == 'mcg' or u == 'ug':
            return 1e-9
        elif u == 'iu':
            # Vit D3 standard 1 kg = 40,000,000 IU
            return 2.5e-8
        else: # default mg
            return 1e-6

    def calculate_ingredient_cost(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate cost in INR for a single ingredient in 1 dose unit.
        """
        name = item.get("name", "")
        dosage = float(item.get("dosage", 0))
        unit = item.get("unit", "mg")
        
        # Check custom price override or DB price
        price_per_kg = item.get("price_per_kg_inr")
        if price_per_kg is None or float(price_per_kg) <= 0:
            db_item = self.ingredients_db.get(item.get("id")) or self.ingredients_db.get(name.lower())
            if db_item:
                price_per_kg = float(db_item.get("price_per_kg_inr", 1200))
            else:
                price_per_kg = 1500.0  # default estimated price

        kg_per_unit = dosage * self.dose_to_kg_factor(unit)
        
        # 5% manufacturing stability overage
        overage_multiplier = 1.05
        cost_inr = kg_per_unit * float(price_per_kg) * overage_multiplier

        return {
            "name": name,
            "dosage": dosage,
            "unit": unit,
            "price_per_kg_inr": float(price_per_kg),
            "cost_per_unit_inr": round(cost_inr, 4),
            "overage_pct": 5.0
        }

    def calculate_quote(
        self,
        ingredients: List[Dict[str, Any]],
        dosage_form_id: str = "tablets",
        packaging_id: Optional[str] = None,
        batch_quantity: int = 10000,
        margin_pct: float = DEFAULT_PROFIT_MARGIN_PCT
    ) -> Dict[str, Any]:
        """
        Produce a full quotation breakdown based on active ingredients, excipients,
        manufacturing processing, packaging, volume tiers, and margin.
        """
        # 1. Active Ingredients Cost
        ingredient_breakdown = []
        total_active_cost = 0.0

        for item in ingredients:
            ing_cost = self.calculate_ingredient_cost(item)
            ingredient_breakdown.append(ing_cost)
            total_active_cost += ing_cost["cost_per_unit_inr"]

        # 2. Dosage Form Processing & Excipient Cost
        form_info = self.dosage_forms.get(dosage_form_id, self.dosage_forms.get("tablets", {}))
        processing_cost = float(form_info.get("base_processing_cost_inr", 0.35))
        excipients_cost = float(form_info.get("excipients_cost_inr", 0.25))

        # 3. Packaging Cost
        if not packaging_id:
            # Auto pick suitable packaging
            if dosage_form_id == "effervescent":
                packaging_id = "effervescent_tube_20"
            elif dosage_form_id == "gummies":
                packaging_id = "hdpe_bottle_60"
            elif dosage_form_id == "powder_sachet":
                packaging_id = "sachet_box_30"
            elif dosage_form_id == "liquid_syrup":
                packaging_id = "pet_syrup_bottle"
            else:
                packaging_id = "blister_alu_pvc"

        pack_info = self.packaging_options.get(packaging_id, self.packaging_options.get("blister_alu_pvc", {}))
        unit_pack_size = max(1, int(pack_info.get("unit_pack_size", 10)))
        cost_per_pack = float(pack_info.get("cost_per_pack_inr", 4.50))
        pack_cost_per_unit = cost_per_pack / unit_pack_size

        # 4. Total Direct Cost per Unit
        base_unit_cost = total_active_cost + excipients_cost + processing_cost + pack_cost_per_unit

        # 5. Volume Tier Discount
        discount_pct = 0.0
        tier_label = "Starter MOQ"
        for tier in self.volume_tiers:
            if batch_quantity >= tier["min_quantity"]:
                discount_pct = float(tier["discount_pct"])
                tier_label = tier["label"]

        # Unit cost after volume scale efficiency
        scale_efficiency_factor = (100.0 - discount_pct) / 100.0
        adjusted_unit_cost = base_unit_cost * scale_efficiency_factor

        # 6. Commercial Margin (Manufacturer price)
        unit_selling_price = adjusted_unit_cost * (1.0 + (margin_pct / 100.0))
        price_per_pack = unit_selling_price * unit_pack_size

        # 7. Total Batch Value
        total_batch_units = batch_quantity
        total_packs = total_batch_units // unit_pack_size
        total_batch_ex_factory = unit_selling_price * total_batch_units
        gst_amount = total_batch_ex_factory * (DEFAULT_GST_PCT / 100.0)
        total_with_gst = total_batch_ex_factory + gst_amount

        return {
            "batch_quantity": batch_quantity,
            "dosage_form": form_info.get("name", dosage_form_id),
            "dosage_form_id": dosage_form_id,
            "packaging_name": pack_info.get("name", packaging_id),
            "packaging_id": packaging_id,
            "unit_pack_size": unit_pack_size,
            "total_packs": total_packs,
            "cost_breakdown": {
                "active_ingredients_per_unit_inr": round(total_active_cost, 4),
                "excipients_per_unit_inr": round(excipients_cost, 4),
                "manufacturing_processing_per_unit_inr": round(processing_cost, 4),
                "packaging_per_unit_inr": round(pack_cost_per_unit, 4),
                "base_direct_cost_per_unit_inr": round(base_unit_cost, 4),
                "volume_discount_pct": discount_pct,
                "volume_tier_label": tier_label,
                "adjusted_cost_per_unit_inr": round(adjusted_unit_cost, 4)
            },
            "pricing": {
                "unit_selling_price_inr": round(unit_selling_price, 2),
                "price_per_pack_inr": round(price_per_pack, 2),
                "total_batch_ex_factory_inr": round(total_batch_ex_factory, 2),
                "gst_pct": DEFAULT_GST_PCT,
                "gst_amount_inr": round(gst_amount, 2),
                "total_batch_with_gst_inr": round(total_with_gst, 2)
            },
            "ingredient_breakdown": ingredient_breakdown,
            "lead_time_days": 21 if batch_quantity <= 25000 else 30
        }
