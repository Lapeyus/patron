import os
import json
import re

def process_file(file_path, output_path):
    with open(file_path, 'r') as f:
        data = json.load(f)

    raw_text = data.get('raw_response', '')
    lines = data.get('lines', [])
    
    # Initialize a new structured_data object
    structured_data = {
        "name": None,
        "age": None,
        "location": None,
        "prices": [],
        "services": [],
        "contact": {
            "whatsapp": None,
            "phone": None,
            "email": None,
            "social": None
        },
        "attributes": {
            "height": None,
            "weight": None,
            "measurements": None,
            "hair_color": None,
            "eye_color": None,
            "implants": None
        },
        "raw_text": None,
        "standard_prices": {
            "one_hour": None,
            "two_hours": None,
            "three_hours": None,
            "overnight": None
        }
    }

    # Use existing structured_data as a base
    if 'structured_data' in data:
        for key, value in data['structured_data'].items():
            if isinstance(value, dict) and structured_data.get(key) is not None:
                structured_data[key].update(value)
            else:
                structured_data[key] = value

    # Regex patterns for extraction
    age_pattern = re.compile(r'(\b\d{2}\b)\s*a[ñn]os', re.IGNORECASE)
    price_pattern = re.compile(r'(?:CRC|USD|\$|¢)?\s?(\d{1,3}(?:[.,]\d{3})*)\s*(?:mil)?\s*(?:(?:por|por la|de)\s+)?(\d+\s*horas?|toda la noche|noche completa|1\s*h|2\s*h|3\s*h|1hr|2hr|3hr|\d+\s*hora\s\d+\s*minutos)?', re.IGNORECASE)
    height_pattern = re.compile(r'(\d[.,]\d{2})\s*(?:mts|m|cm)?', re.IGNORECASE)
    weight_pattern = re.compile(r'(\d{2,3})\s*(?:kg|kilos)', re.IGNORECASE)
    hair_color_pattern = re.compile(r'cabello\s*:\s*([a-z\s]+)', re.IGNORECASE)
    eye_color_pattern = re.compile(r'ojos\s*:\s*([a-z\s]+)', re.IGNORECASE)
    location_pattern = re.compile(r'zona donde vive\s*:\s*(.+)', re.IGNORECASE)
    
    # Simple extraction from raw_text
    age_match = age_pattern.search(raw_text)
    if age_match:
        structured_data['age'] = int(age_match.group(1))

    structured_data['prices'] = [] # Reset prices to avoid duplicates
    for line in lines:
        price_matches = price_pattern.findall(line)
        for amount, duration in price_matches:
            currency = "CRC" if "CRC" in line or "¢" in line else "USD"
            amount_clean = int(re.sub(r'[.,]', '', amount))
            structured_data['prices'].append({"duration": duration.strip() if duration else None, "amount": amount_clean, "currency": currency})

    # More advanced extraction if needed for other fields
    
    # Generate a summary for raw_text
    summary_parts = []
    if structured_data.get('name'):
        summary_parts.append(f"Perfil {structured_data['name']}")
    if structured_data.get('age'):
        summary_parts.append(f"{structured_data['age']} años")
    if structured_data.get('location'):
        summary_parts.append(f"de {structured_data['location']}")
    if structured_data.get('prices'):
        price_info_parts = []
        for p in structured_data['prices']:
            if isinstance(p, dict):
                price_info_parts.append(f"{p.get('duration','')} por {p.get('currency','')}{p.get('amount','')}")
        price_info = ", ".join(price_info_parts)
        summary_parts.append(f"con tarifas: {price_info}")

    structured_data['raw_text'] = ", ".join(summary_parts) + "." if summary_parts else "No summary available."


    # Update standard_prices
    if structured_data.get('prices'):
        for price in structured_data.get('prices'):
            if isinstance(price, dict) and price.get('duration'):
                duration_lower = price['duration'].lower()
                if '1 hora' in duration_lower or '1h' in duration_lower:
                    structured_data['standard_prices']['one_hour'] = price['amount']
                elif '2 horas' in duration_lower or '2h' in duration_lower:
                    structured_data['standard_prices']['two_hours'] = price['amount']
                elif '3 horas' in duration_lower or '3h' in duration_lower:
                    structured_data['standard_prices']['three_hours'] = price['amount']
                elif 'noche' in duration_lower:
                    structured_data['standard_prices']['overnight'] = price['amount']
            
    data['structured_data'] = structured_data

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    output_dir = 'output'
    refined_output_dir = 'output_refined'

    if not os.path.exists(refined_output_dir):
        os.makedirs(refined_output_dir)

    for filename in os.listdir(output_dir):
        if filename.endswith('.table.json'):
            file_path = os.path.join(output_dir, filename)
            output_path = os.path.join(refined_output_dir, filename)
            try:
                process_file(file_path, output_path)
                print(f"Processed {filename}")
            except Exception as e:
                print(f"Could not process {filename}. Error: {e}")

if __name__ == "__main__":
    main()