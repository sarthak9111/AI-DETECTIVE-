from transformers import pipeline
from PIL import Image
import sys
import os


MODEL_NAME = "Smogy/SMOGY-Ai-images-detector"


print("Loading AI image detector...")
print("First run may take some time because the model must be downloaded.")

detector = pipeline(
    "image-classification",
    model=MODEL_NAME
)

print("Model loaded successfully!\n")


def detect_image(image_path):

    if not os.path.exists(image_path):
        print("ERROR: Image file not found.")
        return

    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        print("ERROR: Could not open image.")
        print(e)
        return

    results = detector(image)

    print("=" * 50)
    print("        AI IMAGE DETECTOR")
    print("=" * 50)

    for result in results:
        label = result["label"]
        score = result["score"] * 100

        print(f"{label:15} : {score:.2f}%")

    print("=" * 50)

    # Find the highest scoring result
    best = max(results, key=lambda x: x["score"])

    label = best["label"]
    confidence = best["score"] * 100

    # Model labels are normally human/artificial
    if label.lower() in ["artificial", "fake", "ai", "generated"]:
        print(f"\n🤖 RESULT: POSSIBLY AI-GENERATED")
    elif label.lower() in ["human", "real", "authentic"]:
        print(f"\n📷 RESULT: LIKELY REAL")
    else:
        print(f"\nRESULT: {label}")

    print(f"Model confidence: {confidence:.2f}%")

    print("\n⚠️ This is a model prediction, not proof.")
    print("AI detectors can make false positives and false negatives.")


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print("Usage:")
        print("python detector.py image.jpg")

    else:

        image_path = sys.argv[1]

        detect_image(image_path)