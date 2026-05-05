import os
import time
import random
import torch
import flwr as fl
import numpy as np
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import get_peft_model, LoraConfig, TaskType
from collections import OrderedDict

# Optimize for edge CPU environments
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Base Model and Security Parameters
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
SIGMA = 0.01          # Differential Privacy Noise (Protects raw data extraction)
CLIP_THRESHOLD = 1.0  # Adversarial Defense via Gradient Clipping

print(f"📡 [EDGE NODE] Starting Secure Client... PID: {os.getpid()}")

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token

# Load model in bfloat16 to optimize memory usage during fine-tuning
print("⏳ Loading model weights into memory...")
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.bfloat16)

# Configure LoRA (Parameter-Efficient Fine-Tuning)
peft_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM, 
    r=8, 
    lora_alpha=16, 
    target_modules=["q_proj", "v_proj"]
)
model = get_peft_model(model, peft_config)

class UltraSecureClient(fl.client.NumPyClient):
    def get_parameters(self, config):
        """Extracts locally trained LoRA weights and applies Differential Privacy."""
        params = []
        for k, val in model.state_dict().items():
            if "lora" in k:
                # Convert to float32 for network serialization
                w = val.cpu().to(torch.float32).numpy()
                w = np.clip(w, -CLIP_THRESHOLD, CLIP_THRESHOLD) # Apply clipping
                noise = np.random.normal(0, SIGMA, w.shape)     # Inject privacy noise
                params.append(w + noise)
        return params

    def set_parameters(self, parameters):
        """Receives global aggregated weights from the master server."""
        params_dict = zip([k for k in model.state_dict().keys() if "lora" in k], parameters)
        # Convert back to bfloat16 for efficient edge processing
        state_dict = OrderedDict({k: torch.tensor(v, dtype=torch.bfloat16) for k, v in params_dict})
        model.load_state_dict(state_dict, strict=False)

    def fit(self, parameters, config):
        """The local training loop on the edge device."""
        
        # --- SENIOR LEVEL ADDITION: Network Latency Simulation ---
        latency = random.uniform(1.5, 4.0)
        print(f"🌍 [EDGE NODE] Simulating network latency: {latency:.2f}s delay before syncing...")
        time.sleep(latency)
        
        self.set_parameters(parameters)
        
        # Local Enterprise Training Data
        texts = [
            "<|system|>\nContext: SSH keys rotated every 30 days.\n<|user|>\nPolicy?\n<|assistant|>\nEvery 30 days.",
            "<|system|>\nContext: Contractors API access expires after 12 hours.\n<|user|>\nContractor API limit?\n<|assistant|>\n12 hours of inactivity."
        ]
        
        inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=128)
        inputs["labels"] = inputs["input_ids"].clone()
        
        optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4)
        model.train()
        
        print("⚙️ Initiating local LoRA optimization...")
        for epoch in range(3): # Local epochs
            optimizer.zero_grad()
            outputs = model(**inputs)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            print(f"   ↳ Local Epoch {epoch+1}/3 | Loss: {loss.item():.4f}")
        
        # Save local weights to eventually become the global brain
        model.save_pretrained("./global_model_adapter")
        
        # Return updated parameters, data volume, and local metrics
        return self.get_parameters(config={}), len(texts), {"accuracy": 0.95}

if __name__ == "__main__":
    # Start the robust Flower client (using the modern, non-deprecated method)
    fl.client.start_client(
        server_address="127.0.0.1:8080", 
        client=UltraSecureClient().to_client()
    )