import argparse
import json
from pathlib import Path

import torch
from PIL import Image
from torchvision import models, transforms


def load_model(model_path: Path, labels_path: Path, image_size: int):
    class_names = json.loads(labels_path.read_text(encoding="utf-8"))

    model = models.resnet18(weights=None)
    in_features = model.fc.in_features
    model.fc = torch.nn.Linear(in_features, len(class_names))
    model.load_state_dict(torch.load(model_path, map_location="cpu"))
    model.eval()

    tfms = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    return model, class_names, tfms


def severity_from_confidence(confidence: float):
    if confidence >= 0.85:
        return "high"
    if confidence >= 0.65:
        return "medium"
    return "low"


def recommended_action(label: str, severity: str):
    label_l = label.lower()
    if "pothole" in label_l and severity in {"high", "medium"}:
        return "urgent patching and lane safety review"
    if "crack" in label_l and severity == "high":
        return "priority surface repair within 1 week"
    if severity == "medium":
        return "schedule maintenance cycle and monitor weekly"
    return "monitor condition and re-inspect in 30 days"


def main():
    parser = argparse.ArgumentParser(description="Predict infrastructure damage class from image")
    parser.add_argument("--image", type=str, required=True)
    parser.add_argument("--model", type=str, default="artifacts/baseline_model.pt")
    parser.add_argument("--labels", type=str, default="artifacts/labels.json")
    parser.add_argument("--image_size", type=int, default=224)
    args = parser.parse_args()

    model, class_names, tfms = load_model(Path(args.model), Path(args.labels), args.image_size)

    image = Image.open(args.image).convert("RGB")
    x = tfms(image).unsqueeze(0)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0]
        idx = int(torch.argmax(probs).item())
        confidence = float(probs[idx].item())

    label = class_names[idx]
    severity = severity_from_confidence(confidence)
    action = recommended_action(label, severity)

    print("prediction:", label)
    print("confidence:", round(confidence, 4))
    print("severity:", severity)
    print("recommended_action:", action)


if __name__ == "__main__":
    main()
