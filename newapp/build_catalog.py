import json
import argparse
from pathlib import Path
import time
import sys
import re

# Ensure we can import from src
sys.path.append(str(Path(__file__).parent))
try:
    from src.glm_ocr_json.schema import ProfileSchema
except ImportError:
    print("Warning: Could not import ProfileSchema. Validation disabled.")
    ProfileSchema = None

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut
    HAS_GEO = True
except ImportError:
    HAS_GEO = False

class Geocoder:
    def __init__(self, cache_file="geo_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache = {}
        if self.cache_file.exists():
            try:
                self.cache = json.loads(self.cache_file.read_text())
            except:
                pass
        
        if HAS_GEO:
            self.geolocator = Nominatim(user_agent="patron_catalog_builder")
        self.last_call = 0

    def save(self):
        self.cache_file.write_text(json.dumps(self.cache, indent=2))

    def disambiguate(self, loc_str):
        if not HAS_GEO or not loc_str or len(loc_str) < 3:
            return None

        # Clean string
        clean_loc = loc_str.strip()
        if "Costa Rica" not in clean_loc:
            query = f"{clean_loc}, Costa Rica"
        else:
            query = clean_loc

        if query in self.cache:
            return self.cache[query]

        # Rate limiting (1s per request policy for Nominatim)
        now = time.time()
        if now - self.last_call < 1.1:
            time.sleep(1.1 - (now - self.last_call))
        
        try:
            print(f"Geocoding: {query}...")
            location = self.geolocator.geocode(query, addressdetails=True)
            self.last_call = time.time()
            
            if location:
                # Extract clean parts
                addr = location.raw.get('address', {})
                city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('county')
                state = addr.get('state')
                
                norm_name = clean_loc # fallback
                if city and state:
                    norm_name = f"{city}, {state}"
                elif state:
                    norm_name = state
                elif city:
                    norm_name = city
                    
                result = {
                    "normalized": norm_name,
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "raw": location.address
                }
                self.cache[query] = result
                self.save() 
                return result
        except Exception as e:
            print(f"Geo error for {query}: {e}")
        
        self.cache[query] = None
        self.save()
        return None


AGE_KEYWORDS = ("edad", "age")
AGE_REGEX = re.compile(r"(?:edad|age)\s*[:=]?\s*(\d{1,2})", re.IGNORECASE)
GENERIC_NAME_TOKENS = {
    "perfiles", "perfil", "cortesía", "recientemente", "incorporados",
    "videos", "provincia", "patrón", "patron", "perfiles-", "galeria",
}
PROVINCES = {
    "alajuela", "san jose", "san josé", "heredia", "cartago",
    "guanacaste", "puntarenas", "limon", "limón",
}


def infer_age_from_source(source):
    key_values = source.get("key_values") or []
    for entry in key_values:
        key = (entry.get("key") or "").lower()
        value = entry.get("value") or ""
        if any(word in key for word in AGE_KEYWORDS):
            match = re.search(r"\d{1,2}", value)
            if match:
                try:
                    return int(match.group(0))
                except ValueError:
                    continue

    raw_response = source.get("raw_response") or ""
    match = AGE_REGEX.search(raw_response)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def derive_name_from_metadata(meta):
    for segment in reversed(meta):
        if not segment:
            continue
        cleaned = segment.strip()
        cleaned = re.sub(r"^\d+\s*[-–:]\s*", "", cleaned)
        lowercase = cleaned.lower()
        if not cleaned or lowercase in PROVINCES:
            continue
        if any(token in lowercase for token in GENERIC_NAME_TOKENS):
            continue
        if any(ch.isalpha() for ch in cleaned):
            return cleaned
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--web-dir", type=Path, default=Path("web"))
    args = parser.parse_args()

    geo = Geocoder()
    profiles = {}
    
    # 1. Load processed JSON data
    for json_file in args.output_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text())
            image_value = data.get("image") or data.get("ocr") or ""
            abs_img = Path(image_value) if image_value else Path()
            profile_key = str(abs_img.parent) if image_value else json_file.stem
            
            if profile_key not in profiles:
                profiles[profile_key] = {
                    "images": [],
                    "data_sources": [],
                }
            
            try:
                rel_img = abs_img.relative_to(Path.cwd())
                rel_path = str(rel_img)
            except ValueError:
                rel_path = image_value

            profiles[profile_key]["images"].append(rel_path)
            profiles[profile_key]["data_sources"].append(data)

        except Exception as e:
            print(f"Skipping {json_file}: {e}")

    # 2. Merge data for each profile
    catalog = []
    
    for folder_path_str, profile in profiles.items():
        merged = {
            "name": None, "age": None, "location": None, 
            "prices": [], "services": [], "contact": {}, "attributes": {}, "raw_text": ""
        }
        
        path_metadata = []
        
        for source in profile["data_sources"]:
            struct = source.get("structured_data") or {}
            
            # Simple merge strategy: overwrite if present
            if struct.get("name"): merged["name"] = struct["name"]
            if struct.get("age"): merged["age"] = struct["age"]
            if struct.get("location"): merged["location"] = struct["location"]
            if struct.get("raw_text") and len(struct.get("raw_text", "")) > len(merged["raw_text"]): 
                merged["raw_text"] = struct["raw_text"]

            if not merged["age"]:
                inferred_age = infer_age_from_source(source)
                if inferred_age:
                    merged["age"] = inferred_age
            
            # Append lists
            if struct.get("prices"): merged["prices"] = struct["prices"]
            if struct.get("services"): merged["services"] = list(set(merged["services"] + struct["services"]))
            
            # Merge dictionary
            if struct.get("contact"):
                for k, v in struct["contact"].items():
                    if v: merged["contact"][k] = v
            if struct.get("attributes"):
                for k, v in struct["attributes"].items():
                    if v: merged["attributes"][k] = v

            meta = source.get("path_metadata", [])
            if len(meta) > len(path_metadata):
                path_metadata = meta

        if not merged["name"]:
            fallback_name = derive_name_from_metadata(path_metadata)
            if fallback_name:
                merged["name"] = fallback_name

        # Find ALL images in this folder
        folder_path = Path(folder_path_str)
        if folder_path.exists():
            all_imgs = sorted(list(folder_path.glob("*.jpg")) + list(folder_path.glob("*.png")) + list(folder_path.glob("*.jpeg")))
            profile["images"] = []
            for img in all_imgs:
                try:
                    profile["images"].append(str(img.relative_to(Path.cwd())))
                except: pass
        
        # --- Service Cleaning ---
        cleaned_services = []
        blacklist = ["implante", "labio", "gluteo", "glúteo", "lipo", "transferencia", "estatura", "peso", "height", "weight", "eyes", "hair"]
        for s in merged["services"]:
            if not s: continue
            s_lower = s.lower()
            if len(s) > 35: continue 
            if any(bad in s_lower for bad in blacklist): continue
            cleaned_services.append(s)
        merged["services"] = list(set(cleaned_services))

        # --- VALIDATE AND NORMALIZE WITH SCHEMA ---
        # Pre-clean prices to remove incomplete entries that cause validation failures
        if "prices" in merged and isinstance(merged["prices"], list):
            valid_prices = []
            for p in merged["prices"]:
                if isinstance(p, dict):
                    # Must have an amount
                    if p.get("amount") is None:
                        continue
                    # Ensure currency is present, default to CRC if missing
                    if not p.get("currency"):
                       p["currency"] = "CRC"
                    valid_prices.append(p)
            merged["prices"] = valid_prices

        if ProfileSchema:
            try:
                # Pydantic will coerce types (e.g. age "20" -> 20)
                validated_profile = ProfileSchema(**merged)
                merged = validated_profile.model_dump()
            except Exception as e:
                print(f"Validation warning for {folder_path.name}: {e}")
                # Keep going with raw data if validation fails
                pass

        # --- Geo Disambiguation ---
        loc_candidate = merged["location"]
        if not loc_candidate and len(path_metadata) >= 2:
             candidate_prov = path_metadata[1].title()
             if candidate_prov in ["Alajuela", "Heredia", "San Jose", "Cartago", "Puntarenas", "Guanacaste", "Limon", "San José", "Limón"]:
                 loc_candidate = candidate_prov
        
        if loc_candidate:
            if HAS_GEO:
                geo_info = geo.disambiguate(loc_candidate)
                if geo_info:
                    merged["location"] = geo_info["normalized"]
                    merged["geo"] = geo_info
                elif loc_candidate:
                    merged["location"] = loc_candidate
            else:
                 merged["location"] = loc_candidate

        item = {
            "path_key": folder_path_str,
            "path_metadata": path_metadata,
            "images": profile["images"],
            "structured_data": merged
        }
        catalog.append(item)
    
    out_file = args.web_dir / "catalog.json"
    out_file.write_text(json.dumps(catalog, indent=2))
    print(f"Standardized catalog with {len(catalog)} profiles written to {out_file}")

if __name__ == "__main__":
    main()
