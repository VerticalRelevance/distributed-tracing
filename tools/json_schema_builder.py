import json
import sys
from genson import SchemaBuilder

# Ensure a filename is provided
if len(sys.argv) != 2:
    print("Usage: python generate_schema.py <json_file>")
    sys.exit(1)

json_file = sys.argv[1]

# Load JSON data from the file
try:
    with open(json_file, "r") as f:
        json_data = json.load(f)
except Exception as e:
    print(f"Error loading JSON file: {e}")
    sys.exit(1)

# Generate schema
builder = SchemaBuilder()
builder.add_object(json_data)
schema = builder.to_schema()

# Replace property names with a generic structure
if "properties" in schema:
    schema = {
        "type": "object",
        "additionalProperties": {
            "oneOf": list({tuple(p.items()) for p in schema["properties"].values()})
        },
    }

# Print the minimal JSON Schema
print(json.dumps(schema, indent=2))
