import json
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model
from datasets import Dataset
import torch

# -----------------------------
# Configuration
# -----------------------------
MODEL_NAME = "Qwen/Qwen3-1.7B-Base"  # smaller Qwen model
PATENT_JSON = "patents.json"
MAX_LENGTH = 512  # reduce memory usage
DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

# -----------------------------
# Load tokenizer and model
# -----------------------------
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)

# Force all layers onto a single device to avoid disk offload errors
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map={i: DEVICE for i in range(1000)},  # force all layers to same device
    trust_remote_code=True
)

# -----------------------------
# LoRA configuration
# -----------------------------
lora_config = LoraConfig(
    r=16,
    lora_alpha=16,
    target_modules=["q_proj","k_proj","v_proj","o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)

# -----------------------------
# Load and prepare dataset
# -----------------------------
with open(PATENT_JSON) as f:
    patents = json.load(f)

sft_data = []
for item in tqdm(patents, desc="Preparing SFT data"):
    inp = f"Title: {item['title']}\nSummary: {item['summary']}"
    tgt = item['description']
    sft_data.append({
        "instruction": "Generate a detailed patent description.",
        "input": inp,
        "output": tgt
    })

ds = Dataset.from_list(sft_data)

def preprocess(examples):
    texts = [
        f"Instruction: {e['instruction']}\nInput: {e['input']}\nOutput: {e['output']}"
        for e in examples
    ]
    return tokenizer(texts, truncation=True, padding="max_length", max_length=MAX_LENGTH)

tok_ds = ds.map(preprocess, batched=True, remove_columns=ds.column_names, desc="Tokenizing dataset")

# -----------------------------
# Training arguments
# -----------------------------
training_args = TrainingArguments(
    output_dir="qwen3_lora_mac",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-5,
    num_train_epochs=5,
    fp16=torch.backends.mps.is_available(),  # use fp16 if MPS is available
    logging_steps=10,
    save_strategy="epoch",
    report_to="none",
    disable_tqdm=False
)

# -----------------------------
# Trainer
# -----------------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tok_ds,
    tokenizer=tokenizer,
)

trainer.train()

# -----------------------------
# Save model
# -----------------------------
model.save_pretrained("qwen3_lora_mac")
tokenizer.save_pretrained("qwen3_lora_mac")
