# Adding a New Model to DeepSafe

DeepSafe is designed to make adding new detection models as simple as possible.

## Automated (recommended)

```bash
make add-model NAME=my_detector MEDIA_TYPE=image PORT=5008
```

This command:
1. Creates `models/image/my_detector/` with scaffold files
2. Registers the model in `config/deepsafe_config.json`
3. Prints next steps

## What you write

Implement the `load()` and `predict()` methods in `models/image/my_detector/detector.py`:

```python
# models/image/my_detector/detector.py
import torch
from PIL import Image

class MyDetectorDetector:
    MODEL_NAME = "my_detector"

    def __init__(self):
        self._loaded = False
        self.model = None

    def load(self):
        """Load model weights."""
        import torchvision.models as models
        self.model = models.resnet50(pretrained=False)
        state = torch.load("weights/model.pth", map_location="cpu")
        self.model.load_state_dict(state)
        self.model.eval()
        self._loaded = True

    def predict(self, image: Image.Image, threshold: float = 0.5) -> dict:
        """Run inference."""
        import torchvision.transforms as T
        transform = T.Compose([
            T.Resize(256),
            T.CenterCrop(224),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        x = transform(image).unsqueeze(0)
        with torch.no_grad():
            logits = self.model(x)
            prob = torch.softmax(logits, dim=1)[0, 1].item()

        label = "fake" if prob >= threshold else "real"
        confidence = abs(prob - threshold) / max(threshold, 1 - threshold)
        return {
            "model_name": self.MODEL_NAME,
            "probability": round(prob, 4),
            "label": label,
            "confidence": round(min(confidence, 1.0), 4),
            "threshold_used": threshold,
            "extra": {},
        }
```

## Deploy and retrain

```bash
# Rebuild and start
make start

# Retrain the ensemble meta-learner to include your new model
make retrain MEDIA_TYPE=image
```

## Supported media types

| Type | Port range | Example |
|------|-----------|---------|
| image | 5001–5099 | NPR, CLIP-based |
| video | 7001–7099 | Cross-Efficient ViT |
| audio | 6001–6099 | Future ASVspoof |

## Model contract

Every model must expose:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Returns `{"status": "ok", "model_loaded": true}` |
| `/predict` | POST | Accepts `{"input_data": "<base64>", "threshold": 0.5}` |

The `/predict` response must include:
```json
{
  "model_name": "my_detector",
  "probability": 0.87,
  "label": "fake",
  "confidence": 0.74,
  "threshold_used": 0.5
}
```
