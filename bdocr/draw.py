import cv2
import json
import numpy as np
from glob import glob

def draw(image_path):
    export_data = []
    # Load the image
    image = cv2.imread(image_path)

    # Load the JSON file
    with open(image_path.rsplit('.', 1)[0] + '.json','r', encoding='utf-8') as f:
        data = json.load(f)

    # Iterate over the tables_result
    for table in data['tables_result']:
        # Iterate over the body
        for cell in table['body']:
            export_data.append([content['word'] for content in cell['contents']])
            # Extract the coordinates
            points = np.array([[coord['x'], coord['y']] for coord in cell['cell_location']])
            # Draw the bounding box on the image
            cv2.polylines(image, [points], True, (0, 255, 0), 2)
            for content in cell['contents']:
                # Extract the coordinates
                points = np.array([[coord['x'], coord['y']] for coord in content['poly_location']])
                
                # Draw the bounding box on the image
                cv2.polylines(image, [points], True, (0, 255, 0), 2)

                # Extract the text
                text = content['word']

                # Define the position for the text (top left corner of the bounding box)
                x, y = points[0][0], points[0][1]

                # Add the text to the image
                cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    # Save the image
    cv2.imwrite(image_path.rsplit('.', 1)[0] + '_table.jpg', image)

for file in glob('data/*/png/*.png'):
    if 'table' in file:
        continue
    draw(file)
