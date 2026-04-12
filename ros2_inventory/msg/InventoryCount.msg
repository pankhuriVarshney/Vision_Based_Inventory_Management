# Inventory count message
int32 total_objects
string[] class_names
int32[] class_counts
float32 density_score
float32 shelf_capacity_percent
builtin_interfaces/Time timestamp
string status  # "normal", "low_stock", "out_of_stock"
