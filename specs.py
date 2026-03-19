from groq import Groq
import json

client = Groq(api_key="YOUR_GROQ_API_KEY_HERE")

def get_official_specs(brand, model):
    prompt = f"""
    You are a phone specifications expert.
    Give me the EXACT official specifications for {brand} model number {model}.
    Be very precise — wrong specs will cause false fraud detection.
    Return ONLY a JSON object with exactly these fields, nothing else:
    {{
        "battery_capacity_mah": 4000,
        "storage_type": "UFS 2.1",
        "display_resolution": "1080x2400",
        "display_refresh_rate": "60Hz",
        "chipset": "Helio G95",
        "ram_gb": 8
    }}
    Return only the JSON, no explanation, no markdown, no backticks.
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    text = response.choices[0].message.content.strip()
    
    # Clean response in case AI adds backticks anyway
    text = text.replace('```json', '').replace('```', '').strip()
    
    specs = json.loads(text)
    return specs

# Test it
if __name__ == '__main__':
    specs = get_official_specs('Vivo', 'V2059')
    print(specs)