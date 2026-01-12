import random

def detect_pest(image_name):
    pests = ["Aphids", "Armyworm", "Locust", "No Pest Detected"]
    return random.choice(pests)

if __name__ == "__main__":
    image = "sample_crop_image.jpg"
    result = detect_pest(image)

    print("Image:", image)
    print("Prediction:", result)
