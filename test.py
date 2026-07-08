# test.py - Updated with tiny model
from transformers import pipeline

# Use the tiny model (14 MB instead of 268 MB)
sentiment = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    model_kwargs={"cache_dir": "./model_cache"}  # Cache locally
)

result = sentiment("I'm excited to build my chatbot!")
print(f"✅ Sentiment test: {result}")

import torch
print(f"✅ PyTorch version: {torch.__version__}")

import transformers
print(f"✅ Transformers version: {transformers.__version__}")# test.py - Updated with tiny model
from transformers import pipeline

# Use the tiny model (14 MB instead of 268 MB)
sentiment = pipeline(
    "sentiment-analysis",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    model_kwargs={"cache_dir": "./model_cache"}  # Cache locally
)

result = sentiment("I'm excited to build my chatbot!")
print(f"✅ Sentiment test: {result}")

import torch
print(f"✅ PyTorch version: {torch.__version__}")

import transformers
print(f"✅ Transformers version: {transformers.__version__}")