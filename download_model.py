import clip
import torch
from transformers import MarianMTModel, MarianTokenizer

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Downloading CLIP...")
clip.load("ViT-B/32", device=device)

print("Downloading Marian...")
name = "Helsinki-NLP/opus-mt-zh-en"
MarianTokenizer.from_pretrained(name)
MarianMTModel.from_pretrained(name)

print("Done.")