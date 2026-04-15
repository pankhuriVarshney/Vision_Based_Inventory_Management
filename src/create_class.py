# Save as: create_class_names.py
# Run this on your laptop, then upload to Pi

import json
from pathlib import Path

CLASS_NAMES = {
    0: 'chips_snacks',
    1: 'chocolate',
    2: 'candy',
    3: 'desserts',
    4: 'soft_drink',
    5: 'juice',
    6: 'milk_dairy',
    7: 'dried_food',
    8: 'canned_food',
    9: 'seasoning',
    10: 'tissue_paper',
    11: 'stationary'
}

# Save to file
with open("models/class_names.json", "w") as f:
    json.dump(CLASS_NAMES, f, indent=2)

print("✅ Created models/class_names.json")
print(f"   Classes: {len(CLASS_NAMES)}")