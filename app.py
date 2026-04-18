import json
from pathlib import Path

import streamlit as st
import torch
from PIL import Image
from torchvision import models, transforms


@st.cache_resource
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
        return "Urgent patching and lane safety review"
    if "crack" in label_l and severity == "high":
        return "Priority surface repair within 1 week"
    if severity == "medium":
        return "Schedule maintenance cycle and monitor weekly"
    return "Monitor condition and re-inspect in 30 days"


def main():
    st.set_page_config(page_title="Infrastructure Damage Assessment", page_icon="RD")
    st.title("Infrastructure Damage Assessment (MVP)")
    st.write("Upload a road image to get a damage class, severity, and maintenance recommendation.")

    model_path = Path("artifacts/baseline_model.pt")
    labels_path = Path("artifacts/labels.json")
    image_size = 224

    if not model_path.exists() or not labels_path.exists():
        st.warning("Model artifacts not found. Train first with train_baseline.py")
        st.stop()

    model, class_names, tfms = load_model(model_path, labels_path, image_size)

    uploaded = st.file_uploader("Upload road image", type=["jpg", "jpeg", "png"])
    if not uploaded:
        st.info("Upload an image to run prediction.")
        return

    image = Image.open(uploaded).convert("RGB")
    st.image(image, caption="Uploaded image", use_column_width=True)

    x = tfms(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0]
        idx = int(torch.argmax(probs).item())
        confidence = float(probs[idx].item())

    label = class_names[idx]
    severity = severity_from_confidence(confidence)
    action = recommended_action(label, severity)

    st.subheader("Prediction")
    st.write(f"Damage class: **{label}**")
    st.write(f"Confidence: **{confidence:.2%}**")
    st.write(f"Severity: **{severity}**")
    st.write(f"Recommended action: **{action}**")


if __name__ == "__main__":
    main()
