import os
import requests

from dotenv import load_dotenv
from pathlib import Path
from random import randrange
from time import sleep


def download_pic(dir, url):
    response = requests.get(url)
    response.raise_for_status()

    with open(dir, 'wb') as file:
        file.write(response.content)


def download_comics(comics_number, dir):
    main_url = f"https://xkcd.com/{comics_number}/info.0.json"
    comics_data = requests.get(main_url).json()
    img_url = comics_data["img"]
    description = comics_data["alt"]
    download_pic(dir, img_url)
    return description


def get_last_comics_num():
    url = "https://xkcd.com/info.0.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["num"]


def publish_photo(token, group_id, api_v, file_path, message):
    url = "https://api.vk.com/method/photos.getWallUploadServer"
    response = requests.get(url, params={"group_id": group_id,
                                         "access_token": token,
                                         "v": api_v})
    response.raise_for_status()
    response = response.json()
    upload_url = response['response']['upload_url']

    with open(file_path, 'rb') as file:
        files = {'photo': file}
        uploading_response = requests.post(upload_url, files=files)
        uploading_response.raise_for_status()
        uploading_response = uploading_response.json()

        server = uploading_response["server"]
        photo = uploading_response["photo"]
        photo_hash = uploading_response["hash"]

        save_photo_url = "https://api.vk.com/method/photos.saveWallPhoto"
        save_photo_response = requests.post(save_photo_url,
                                            params={"group_id": group_id,
                                                    "photo": photo,
                                                    "server": server,
                                                    "hash": photo_hash,
                                                    "access_token": token,
                                                    "v": api_v})
        save_photo_response.raise_for_status()
        save_photo_response = save_photo_response.json()

        media_id = save_photo_response['response'][0]['id']
        owner_id = save_photo_response['response'][0]['owner_id']

        attachment_arg_string = "photo" + str(owner_id) + "_" + str(media_id)
        publish_url = "https://api.vk.com/method/wall.post"
        publish_response = requests.get(publish_url,
                                        params={"owner_id": -group_id,
                                                "from_group": 1,
                                                "message": message,
                                                "attachments": attachment_arg_string,
                                                "access_token": token,
                                                "v": api_v})
        publish_response.raise_for_status()


def main():
    load_dotenv()
    token = os.getenv("VK_API_TOKEN")
    group_id = os.getenv("GROUP_ID")
    delay = int(os.getenv("PUBLISHING_DELAY", default=86400))

    api_v = 5.131

    folder = "files"
    Path(folder).mkdir(parents=True, exist_ok=True)

    while True:
        last_comics_num = get_last_comics_num()
        comics_num = randrange(last_comics_num)

        file_name = str(comics_num) + ".png"
        dir = os.path.join(folder, file_name)

        description = download_comics(comics_num, dir)
        publish_photo(token, int(group_id), api_v, dir, description)

        os.remove(dir)

        sleep(delay)


if __name__ == '__main__':
    main()
