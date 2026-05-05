import sys

def test_load(name):
    print(f"⏳ Attempting to load {name}...", end=" ", flush=True)
    try:
        __import__(name)
        print("✅ SUCCESS")
    except Exception as e:
        print(f"❌ FAILED: {e}")

print(f"Python Version: {sys.version}")
print("-" * 30)

test_load("fastapi")
test_load("faiss")
test_load("transformers")
test_load("sentence_transformers")
test_load("torch")

if "torch" in sys.modules:
    import torch
    print(f"CUDA Available: {torch.cuda.is_available()}")