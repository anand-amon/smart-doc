import importlib, traceback

print(">>> Trying to import llm_processor manually")
try:
    mod = importlib.import_module("backend.pipeline.llm_processor")
    print("✅ Import succeeded. Contents:", dir(mod))
except Exception:
    print("❌ Import failed. Traceback below:")
    traceback.print_exc()