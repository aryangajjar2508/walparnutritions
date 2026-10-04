import os
import json
from pathlib import Path
from typing import Dict, Any

CONFIG_FILE_PATH = Path(__file__).resolve().parent / "data" / "master_config.json"

DEFAULT_MASTER_CONFIG = {
    "liquid": {
        "standard_packaging": {
            "15_60ml": 8.00,
            "60_100ml": 10.00,
            "200ml": 12.00,
            "default": 12.00
        },
        "components": {
            "bottles": {
                "15ml": {"PET": 1.50, "Glass": 2.50, "HDPE": 1.80},
                "30ml": {"PET": 1.80, "Glass": 2.80, "HDPE": 2.00},
                "60ml": {"PET": 2.00, "Glass": 3.00, "HDPE": 2.20},
                "100ml": {"PET": 2.25, "Glass": 3.50, "HDPE": 2.50},
                "150ml": {"PET": 3.00, "Glass": 4.20, "HDPE": 3.20},
                "200ml": {"PET": 4.00, "Glass": 5.00, "HDPE": 4.20},
                "250ml": {"PET": 4.50, "Glass": 5.50, "HDPE": 4.80},
                "300ml": {"PET": 5.20, "Glass": 6.20, "HDPE": 5.50},
                "500ml": {"PET": 6.50, "Glass": 8.00, "HDPE": 7.00}
            },
            "caps": {
                "ROPP Golden": 0.72,
                "ROPP Plain": 0.55,
                "ROPP QAP": 0.60,
                "CRC Cap": 1.20,
                "Plastic Screw Cap": 0.50
            },
            "measuring_cup": {
                "5ml": 0.25,
                "10ml": 0.30,
                "15ml": 0.30,
                "20ml": 0.35,
                "25ml": 0.35,
                "default": 0.30
            },
            "dropper": {
                "Standard Dropper": 1.50,
                "Calibrated Glass Dropper": 2.50
            },
            "labels": {
                "UV Varnish Roll (120x45)": 0.65,
                "Chromo Label": 0.50,
                "Metallic Label": 1.30,
                "Transparent BOPP": 0.85
            },
            "cartons": {
                "Mono Carton UV Drip Off": 3.20,
                "Plain Mono Carton": 2.00,
                "Metallic Foil Board Carton": 3.50,
                "Heavy 350 GSM Carton": 3.80
            },
            "boxes": {
                "60 BOTT Corrugated (5-ply)": 1.00,
                "72 BOTT Corrugated (5-ply)": 1.20,
                "100 BOTT Corrugated (5-ply)": 1.50,
                "7-ply Heavy Duty Box": 1.80
            },
            "insert": {
                "Paper Leaflet / Insert": 0.35
            }
        },
        "manufacturing": {
            "conversion_cost_per_bottle": 1.50,
            "stereo_cost_per_bottle": 0.05,
            "testing_charge_per_bottle": 0.50,
            "margin_per_bottle": 1.00,
            "dm_water_rate_per_L": 0.80,
            "pharma_sugar_rate_per_kg": 70.00,
            "sorbitol_rate_per_kg": 49.00,
            "xanthan_gum_rate_per_kg": 1400.00,
            "glycerin_rate_per_kg": 180.00,
            "tween_80_rate_per_kg": 300.00,
            "sodium_benzoate_rate_per_kg": 250.00,
            "sodium_methyl_parabene_rate_per_kg": 500.00,
            "sodium_propyl_parabene_rate_per_kg": 550.00,
            "default_yield_percent": 100.0
        }
    },
    "tablet": {
        "conversion_cost_per_tablet": 0.25,
        "margin_percent": 20.0,
        "coating_material_rate_per_kg": 150.00,
        "strip_costs": {
            "Alu Alu 1*10": 1.80,
            "Alu Alu 1*15": 2.20,
            "Alu Alu 1*4": 1.00,
            "Blister 1*10": 0.90,
            "Blister 1*15": 1.80,
            "Blister 1*4": 1.25,
            "Pharmafoil 1*10": 1.00
        },
        "carton_costs": {
            "350 GSM 1*10": 3.00,
            "350 GSM 1*15": 3.00,
            "350 GSM 3*10": 4.00,
            "350 GSM 6*10": 5.50,
            "300 GSM 1*10": 2.00,
            "300 GSM 1*15": 2.00
        },
        "jar_costs": {
            "PET 60 Tab": 5.30,
            "HDPE 60 Tab": 5.50,
            "CRC Cap": 3.50,
            "CT Cap": 2.00,
            "Sticker Label": 4.50
        }
    },
    "capsule": {
        "conversion_cost_per_capsule": 0.25,
        "margin_percent": 20.0,
        "shell_costs": {
            "veg_hpmc": 0.48,
            "gelatin": 0.18,
            "size_000_veg": 0.60,
            "size_000_gelatin": 0.30,
            "dr_delayed_release": 0.75
        }
    }
}

class MasterConfigManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.config_path = CONFIG_FILE_PATH
        self.config = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge with default config to ensure all keys exist
                    merged = dict(DEFAULT_MASTER_CONFIG)
                    for section, subdict in data.items():
                        if section in merged and isinstance(subdict, dict):
                            merged[section] = {**merged[section], **subdict}
                        else:
                            merged[section] = subdict
                    return merged
            except Exception as e:
                print(f"[MasterConfig] Error reading {self.config_path}: {e}")
        # Save default config
        self._save(DEFAULT_MASTER_CONFIG)
        return dict(DEFAULT_MASTER_CONFIG)

    def _save(self, config_data: Dict[str, Any]):
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
        except Exception as e:
            print(f"[MasterConfig] Error saving {self.config_path}: {e}")

    def get_config(self) -> Dict[str, Any]:
        return self.config

    def update_config(self, new_data: Dict[str, Any]) -> Dict[str, Any]:
        for k, v in new_data.items():
            if k in self.config and isinstance(v, dict) and isinstance(self.config[k], dict):
                # Deep merge 2 levels
                for sub_k, sub_v in v.items():
                    if isinstance(sub_v, dict) and isinstance(self.config[k].get(sub_k), dict):
                        self.config[k][sub_k].update(sub_v)
                    else:
                        self.config[k][sub_k] = sub_v
            else:
                self.config[k] = v
        self._save(self.config)
        return self.config

master_config_mgr = MasterConfigManager.get_instance()
