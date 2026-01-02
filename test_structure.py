"""
Structure validation test - checks code can be parsed without requiring API keys.
"""
import ast
import os

print("Validating Document Processing Agency Structure...")
print("=" * 60)

def validate_python_file(filepath):
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except Exception as e:
        return False, str(e)

# Test all tool files
tool_files = [
    "document_processor/tools/CrawlAndProcessUrl.py",
    "document_processor/tools/SearchSimilarChunks.py",
    "document_processor/tools/ListCollections.py",
]

print("\nValidating Tool Files:")
print("-" * 60)
for tool_file in tool_files:
    if os.path.exists(tool_file):
        valid, error = validate_python_file(tool_file)
        if valid:
            print(f"[OK] {tool_file}")
        else:
            print(f"[FAIL] {tool_file}: {error}")
    else:
        print(f"[MISSING] {tool_file}")

# Test agent files
agent_files = [
    "document_processor/__init__.py",
    "document_processor/document_processor.py",
    "document_processor/instructions.md",
]

print("\nValidating Agent Files:")
print("-" * 60)
for agent_file in agent_files:
    if os.path.exists(agent_file):
        if agent_file.endswith('.py'):
            valid, error = validate_python_file(agent_file)
            if valid:
                print(f"[OK] {agent_file}")
            else:
                print(f"[FAIL] {agent_file}: {error}")
        else:
            print(f"[OK] {agent_file} (exists)")
    else:
        print(f"[MISSING] {agent_file}")

# Test agency files
agency_files = [
    "agency.py",
    "requirements.txt",
    "shared_instructions.md",
    ".env.example",
    "prd.txt",
]

print("\nValidating Agency Files:")
print("-" * 60)
for agency_file in agency_files:
    if os.path.exists(agency_file):
        if agency_file.endswith('.py'):
            valid, error = validate_python_file(agency_file)
            if valid:
                print(f"[OK] {agency_file}")
            else:
                print(f"[FAIL] {agency_file}: {error}")
        else:
            print(f"[OK] {agency_file} (exists)")
    else:
        print(f"[MISSING] {agency_file}")

print("\n" + "=" * 60)
print("Structure validation completed!")
print("\nTo test with actual execution:")
print("1. Create .env file with your OPENAI_API_KEY")
print("2. Set up PostgreSQL with pgvector extension")
print("3. Run: python agency.py")
