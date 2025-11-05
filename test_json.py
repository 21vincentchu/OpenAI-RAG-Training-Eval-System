import json
from chroma_vector_store import answer_question_json

# Test input
test_input = {"question": "What fumehood are we using?"}

print("Input JSON:")
print(json.dumps(test_input, indent=2))
print()

# Call the function
response = answer_question_json(test_input)

print("Output JSON:")
print(json.dumps(response, indent=2))
print()

# Validate it's proper JSON
try:
    json_str = json.dumps(response)
    parsed = json.loads(json_str)
    print("✓ Valid JSON")
    print(f"Keys: {list(parsed.keys())}")
except Exception as e:
    print(f"✗ Invalid JSON: {e}")
