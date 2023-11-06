import json
import requests
import base64
from glob import glob
from key import API_KEY, SECRET_KEY

def ocr(image_path):
    access_token = get_access_token()
    if access_token is None:
        print("Failed to get access token.")
        return

    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/table?access_token=" + access_token

    with open(image_path, 'rb') as f:
        img = f.read()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }

    # Encode image file to base64
    img = base64.b64encode(img)

    payload = {
        'image': img,
        'detect_direction': 'false',
        'probability': 'false',
        "cell_contents": "true",
        "return_excel": "true"
    }

    response = requests.post(url, headers=headers, data=payload)

    response_json = response.json()
    with open(image_path.rsplit('.', 1)[0] + '.json', 'w', encoding='utf-8') as f:
        json.dump(response_json, f, ensure_ascii=False, indent=4)

def get_access_token():
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    response = requests.post(url, params=params).json()
    return response.get("access_token")


if __name__ == '__main__':
    for file in glob('data/*/*.jpg'):
        if 'table' in file:
            continue
        ocr(file)
