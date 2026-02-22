import asyncio
import random
import emoji
from io import BytesIO

import torch
import clip
from PIL import Image
from transformers import MarianMTModel, MarianTokenizer
from pyrogram.types import Message
from pyrogram.errors import RPCError

from . import AnswerBotCheckin

# ====== 本地识别模型（参考 recognize.py） ======
_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_CLIP_MODEL = None
_CLIP_PREPROCESS = None
_TRANSLATOR_TOKENIZER = None
_TRANSLATOR_MODEL = None
_TRANSLATOR_MODEL_NAME = "Helsinki-NLP/opus-mt-zh-en"


def _ensure_models():
    global _CLIP_MODEL, _CLIP_PREPROCESS, _TRANSLATOR_TOKENIZER, _TRANSLATOR_MODEL
    if _CLIP_MODEL is None or _CLIP_PREPROCESS is None:
        _CLIP_MODEL, _CLIP_PREPROCESS = clip.load("ViT-B/32", device=_DEVICE)
    if _TRANSLATOR_TOKENIZER is None or _TRANSLATOR_MODEL is None:
        _TRANSLATOR_TOKENIZER = MarianTokenizer.from_pretrained(_TRANSLATOR_MODEL_NAME)
        _TRANSLATOR_MODEL = MarianMTModel.from_pretrained(_TRANSLATOR_MODEL_NAME).to(_DEVICE)


def _translate(text: str) -> str:
    _ensure_models()
    inputs = _TRANSLATOR_TOKENIZER(text, return_tensors="pt").to(_DEVICE)
    outputs = _TRANSLATOR_MODEL.generate(**inputs)
    return _TRANSLATOR_TOKENIZER.decode(outputs[0], skip_special_tokens=True)


def _local_recognize(image_bytes: bytes, chinese_labels: list[str]) -> str | None:
    _ensure_models()
    image = _CLIP_PREPROCESS(Image.open(BytesIO(image_bytes))).unsqueeze(0).to(_DEVICE)
    english_labels = [_translate(label) for label in chinese_labels]
    class_names = [f"a photo of {label}" for label in english_labels]
    text = clip.tokenize(class_names).to(_DEVICE)

    with torch.no_grad():
        image_features = _CLIP_MODEL.encode_image(image)
        text_features = _CLIP_MODEL.encode_text(text)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        similarity = (image_features @ text_features.T) * 100
        probs = similarity.softmax(dim=-1)

    pred_index = probs.argmax().item()
    if pred_index < 0 or pred_index >= len(chinese_labels):
        return None
    return chinese_labels[pred_index]


class TerminusCheckin(AnswerBotCheckin):
    name = "终点站"
    bot_username = "EmbyPublicBot"
    bot_checkin_cmd = ["/cancel", "/checkin"]
    bot_text_ignore = ["会话已取消", "没有活跃的会话"]
    bot_checked_keywords = ["今天已签到"]
    max_retries = 1
    bot_use_history = 3

    async def on_photo(self, message: Message):
        """分析分析传入的验证码图片并返回验证码."""
        if message.reply_markup:
            clean = lambda o: emoji.replace_emoji(o, "").replace(" ", "")
            keys = [k for r in message.reply_markup.inline_keyboard for k in r]
            options = [k.text for k in keys]
            options_cleaned = [clean(o) for o in options]
            if len(options) < 2:
                return
            for i in range(3):
                try:
                    img_io = await self.client.download_media(message.photo.file_id, in_memory=True)
                    img_bytes = img_io.getvalue() if img_io else None
                except Exception:
                    img_bytes = None

                if not img_bytes:
                    self.log.warning(f"本地识别失败: 无法获取图片, 正在重试解析 ({i + 1}/3).")
                    continue

                result = _local_recognize(img_bytes, options_cleaned)
                if result:
                    self.log.debug(f"已通过本地解析答案: {result}.")
                    break
                else:
                    self.log.warning(f"本地解析失败, 正在重试解析 ({i + 1}/3).")
            else:
                self.log.warning(f"签到失败: 验证码识别错误.")
                return await self.fail()
            result = options[options_cleaned.index(result)]
            await asyncio.sleep(random.uniform(0.5, 1.5))
            try:
                await message.click(result)
            except RPCError:
                self.log.warning("按钮点击失败.")
