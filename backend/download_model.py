"""Download and cache phi-3.5-mini model using Microsoft Foundry Local SDK."""
import sys
import time
from foundry_local_sdk import FoundryLocalManager, Configuration

print("==================================================")
print("Starting Microsoft Foundry Local model download...")
print("Target model: phi-3.5-mini")
print("==================================================")

try:
    config = Configuration(app_name="soc-copilot")
    mgr = FoundryLocalManager(config)
    
    print("Catalog loaded. Checking model status...")
    model = mgr.catalog.get_model("phi-3.5-mini")
    if not model:
        print("ERROR: Model 'phi-3.5-mini' not found in catalog!")
        sys.exit(1)
        
    print(f"Model ID: {model.id}")
    print(f"Already cached: {model.is_cached}")
    
    if not model.is_cached:
        print("Downloading phi-3.5-mini (approx. 2.4 GB)...")
        print("Please keep your internet connection active.")
        
        last_pct = [-1]
        def progress(p):
            pct = int(p)
            if pct % 5 == 0 and pct != last_pct[0]:
                print(f"Download progress: {pct}%", flush=True)
                last_pct[0] = pct
                
        t0 = time.time()
        model.download(progress_callback=progress)
        elapsed = time.time() - t0
        print(f"Download complete in {elapsed:.1f}s!")
    else:
        print("Model is already cached locally!")
        
    print("Verifying cached model directory...")
    path = model.get_path()
    print(f"Model path: {path}")
    print("SUCCESS: phi-3.5-mini is ready for inference!")

except Exception as e:
    print(f"ERROR: Download failed: {e}")
    sys.exit(1)
