import torch
import clip
from PIL import Image
from transformers import MarianMTModel, MarianTokenizer

# ========= 设备 =========
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

# ========= 加载 CLIP =========
model, preprocess = clip.load("ViT-B/32", device=device)

image = preprocess(Image.open("test.jpg")).unsqueeze(0).to(device)

# ========= 加载翻译模型（中文 -> 英文） =========
model_name = "Helsinki-NLP/opus-mt-zh-en"

translator_tokenizer = MarianTokenizer.from_pretrained(model_name)
translator_model = MarianMTModel.from_pretrained(model_name).to(device)

def translate(text):
    inputs = translator_tokenizer(text, return_tensors="pt").to(device)
    outputs = translator_model.generate(**inputs)
    return translator_tokenizer.decode(outputs[0], skip_special_tokens=True)

# ========= 中文类别 =========
chinese_labels = ["口红", "灯", "口罩", "丝袜"]

# 翻译
english_labels = [translate(label) for label in chinese_labels]

print("翻译结果:", english_labels)

# 给 CLIP 加 prompt（推荐）
class_names = [f"a photo of {label}" for label in english_labels]

text = clip.tokenize(class_names).to(device)

# ========= 推理 =========
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)

    image_features /= image_features.norm(dim=-1, keepdim=True)
    text_features /= text_features.norm(dim=-1, keepdim=True)

    similarity = (image_features @ text_features.T) * 100
    probs = similarity.softmax(dim=-1)

# 输出
for i, name in enumerate(chinese_labels):
    print(f"{name}: {probs[0][i].item():.4f}")

pred_index = probs.argmax().item()
print("\n预测结果:", chinese_labels[pred_index])