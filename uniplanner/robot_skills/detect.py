from PIL import Image
from PIL import ImageDraw


def open_vocabulary_detect(detector, color_image, garget_object, save_result=False):
    color_image_pil = Image.fromarray(color_image)
    predictions = detector(color_image_pil, candidate_labels=[garget_object])
    if save_result:
        draw = ImageDraw.Draw(color_image_pil)
        for prediction in predictions[:1]:
            box = prediction["box"]
            label = prediction["label"]
            score = prediction["score"]
            xmin, ymin, xmax, ymax = box.values()
            draw.rectangle((xmin, ymin, xmax, ymax), outline="red", width=1)
            draw.text((xmin, ymin), f"{label}: {round(score,2)}", fill="white")
        color_image_pil.save("save_images/{}.jpg".format(garget_object))
        
    return str(predictions[0])