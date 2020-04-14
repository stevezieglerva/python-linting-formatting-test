import boto3
import random
import datetime
import json
import random
import re
import uuid
from io import BytesIO
import PIL
from PIL import Image


origin_bucket = "svz-master-pictures-new"
MAX_LANDSCAPE_COUNT = 10
MAX_PORTRAIT_COUNT = 5
MAX_PHOTOS_TO_RETAIN = 200


def lambda_handler(event, context):
    s3 = boto3.resource("s3")
    print(f"Starting: {datetime.datetime.now()}")

    (this_month, this_month_portraits) = get_pictures_for_this_month()
    total = merge_and_copy_portraits(
        this_month_portraits, len(this_month_portraits) - 2
    )
    print(f"\tGot: {len(this_month)}")

    (random_1, portrait_keys_1) = get_random_pictures_for_month(1)
    (random_2, portrait_keys_2) = get_random_pictures_for_month(2)
    (random_3, portrait_keys_3) = get_random_pictures_for_month(3)
    (random_4, portrait_keys_4) = get_random_pictures_for_month(4)
    (random_5, portrait_keys_5) = get_random_pictures_for_month(5)
    (random_6, portrait_keys_6) = get_random_pictures_for_month(6)
    (random_7, portrait_keys_7) = get_random_pictures_for_month(7)
    (random_8, portrait_keys_8) = get_random_pictures_for_month(8)
    (random_9, portrait_keys_9) = get_random_pictures_for_month(9)
    (random_10, portrait_keys_10) = get_random_pictures_for_month(10)
    (random_11, portrait_keys_11) = get_random_pictures_for_month(11)
    (random_12, portrait_keys_12) = get_random_pictures_for_month(12)

    portrait_keys = []
    # portrait_keys.extend(this_month_portraits)
    portrait_keys.extend(portrait_keys_1)
    portrait_keys.extend(portrait_keys_2)
    portrait_keys.extend(portrait_keys_3)
    portrait_keys.extend(portrait_keys_4)
    portrait_keys.extend(portrait_keys_5)
    portrait_keys.extend(portrait_keys_6)
    portrait_keys.extend(portrait_keys_7)
    portrait_keys.extend(portrait_keys_8)
    portrait_keys.extend(portrait_keys_9)
    portrait_keys.extend(portrait_keys_10)
    portrait_keys.extend(portrait_keys_11)
    portrait_keys.extend(portrait_keys_12)
    random.shuffle(portrait_keys)
    total = total + merge_and_copy_portraits(portrait_keys)

    random_pics = []
    random_pics.extend(random_1)
    random_pics.extend(random_2)
    random_pics.extend(random_3)
    random_pics.extend(random_4)
    random_pics.extend(random_5)
    random_pics.extend(random_6)
    random_pics.extend(random_7)
    random_pics.extend(random_8)
    random_pics.extend(random_9)
    random_pics.extend(random_10)
    random_pics.extend(random_11)
    random_pics.extend(random_12)

    random.shuffle(random_pics)
    random_pics_max_list = random_pics[0:MAX_LANDSCAPE_COUNT]

    total = total + copy_keys(this_month)
    total = total + copy_keys(random_pics_max_list)

    print("\tDeleting old shuffle photos")
    deleted = delete_existing_shuffle_photos(MAX_PHOTOS_TO_RETAIN)
    deleted_count = len(deleted)

    print(f"Copied: {total}")
    results = {
        "total": total,
        "this_month": len(this_month),
        "random": len(random_pics_max_list),
        "portrait": len(portrait_keys),
        "deleted": deleted_count,
    }
    print(json.dumps(results, indent=3))
    print(f"Finished: {datetime.datetime.now()}")

    return results


def copy_keys(keys_list):
    s3 = boto3.resource("s3")
    count = 0
    for key in keys_list:
        orig_key = key.replace("original", "small")
        new_key = key.replace("original", "nixplay")
        new_key = re.sub("nixplay/[0-9][0-9][0-9][0-9]/", "nixplay/", new_key)

        try:
            s3.meta.client.copy(
                {"Bucket": "svz-master-pictures-new", "Key": orig_key},
                "svz-master-pictures-new",
                new_key,
            )
            print(f"\tCopied: {orig_key} to {new_key}")
            count = count + 1
        except:
            print(f"\tWarning: unable to copy {orig_key} to {new_key}")
    return count


def delete_existing_shuffle_photos(max_pictures_in_bucket):
    get_last_modified = lambda obj: obj["LastModified"]

    s3 = boto3.client("s3")
    list = s3.list_objects_v2(Bucket="svz-master-pictures-new", Prefix="nixplay")[
        "Contents"
    ]
    current_count = len(list)
    print(f"\fCurrent folder count: {current_count}")
    sorted_list = sorted(list, key=get_last_modified)

    to_delete_count = current_count - max_pictures_in_bucket
    print(f"\fPictures to delete: {to_delete_count}")
    deleted_list = []
    if to_delete_count > 0:
        to_delete = sorted_list[0:to_delete_count]
        count = 0
        for obj in to_delete:
            count = count + 1
            key = obj["Key"]
            s3.delete_object(Bucket="svz-master-pictures-new", Key=key)
            print(f"\t\tDeleted #{count}: {key}")
            deleted_list.append(key)
    return deleted_list


def get_pictures_for_this_month():
    print("\tGetting recent pictures for this month")
    d = boto3.client("dynamodb")
    year = datetime.datetime.now().year
    month = datetime.datetime.now().month
    db_results = d.query(
        TableName="master-pictures",
        IndexName="gsiYearMonth",
        KeyConditionExpression="#year = :year AND #month = :month",
        ExpressionAttributeNames={"#year": "year", "#month": "month"},
        ExpressionAttributeValues={
            ":year": {"N": str(year)},
            ":month": {"N": str(month)},
        },
    )
    keys = []
    portrait_keys = []
    for i in db_results["Items"]:
        url = i["s3_url"]["S"]
        if i.get("layout", {}).get("S", "") == "landscape":
            keys.append(url)
        else:
            print(f"\t\tSkipping but saving portrait picture: {url}")
            portrait_keys.append(url)
    return (keys, portrait_keys)


def get_pictures_for_last_month():
    print("\tGetting recent pictures for last month")
    d = boto3.client("dynamodb")
    last_month = datetime.datetime.now() - datetime.timedelta(days=31)
    year = last_month.year
    month = last_month.month
    db_results = d.query(
        TableName="master-pictures",
        IndexName="gsiYearMonth",
        KeyConditionExpression="#year = :year AND #month = :month",
        ExpressionAttributeNames={"#year": "year", "#month": "month"},
        ExpressionAttributeValues={
            ":year": {"N": str(year)},
            ":month": {"N": str(month)},
        },
    )
    keys = []
    for i in db_results["Items"]:
        url = i["s3_url"]["S"]
        if i.get("layout", {}).get("S", "") == "landscape":
            keys.append(url)
        else:
            print(f"\t\tSkipping but saving portrait picture: {url}")
    return keys


def get_random_pictures_for_month(month):
    print(f"\tGetting old random for month {month}")
    d = boto3.client("dynamodb")
    rand = random.randint(0, 9)
    db_results = d.query(
        TableName="master-pictures",
        IndexName="gsiMonthRandom",
        KeyConditionExpression="#random = :random AND #month = :month",
        ExpressionAttributeNames={"#month": "month", "#random": "random"},
        ExpressionAttributeValues={
            ":random": {"N": str(rand)},
            ":month": {"N": str(month)},
        },
    )
    keys = []
    portrait_keys = []
    for i in db_results["Items"]:
        url = i["s3_url"]["S"]
        if i.get("layout", {}).get("S", "") == "landscape":
            keys.append(url)
        else:
            print(f"\t\tSkipping but saving portrait picture: {url}")
            portrait_keys.append(url)
    print(f"\t\tGot: {len(keys)}")
    return (keys, portrait_keys)


def get_current_month():
    return datetime.datetime.now().month


def get_previous_month():
    month = datetime.datetime.now().month
    if month == 1:
        month = 13
    return month - 1


def get_next_month():
    month = datetime.datetime.now().month
    if month == 12:
        month = 0
    return month + 1


def search(keywords):
    db = boto3.client("dynamodb")
    db_results = db.query(
        TableName="master-pictures-keyword",
        KeyConditionExpression="keyword = :keyword",
        ExpressionAttributeValues={":keyword": {"S": keywords}},
    )
    file_list = []
    for item in db_results["Items"]:
        file = item["s3_url"]["S"]
        file_list.append(file)
    return file_list


def get_professional_pictures(month):
    match_files = []
    cur_month = month
    prev_month = get_previous_month()
    next_month = get_next_month()

    files = search("danzenbaker")
    for file in files:
        file_parts = file.split("/")
        filename = file_parts[2]
        month = filename[5:7]
        month_int = int(month)
        if month_int in [month, cur_month, prev_month]:
            match_files.append(file)
    return match_files


def merge_and_copy_portraits(portrait_key_list, image_count=MAX_PORTRAIT_COUNT):
    print(f"len of portrait_key_list: {len(portrait_key_list)}")
    print(f"image_count: {image_count}")
    if image_count <= 0:
        return 0
    count = 0
    total_actually_copied = 0
    for i in range(0, image_count):
        print(f"\t{i}")
        count = count + 1
        image_1 = portrait_key_list[i]
        image_2 = portrait_key_list[i + image_count]
        image_1 = image_1.replace("original", "small")
        image_2 = image_2.replace("original", "small")
        copied_count = merge_two_portraits(image_1, image_2, count)
        total_actually_copied = total_actually_copied = copied_count
        print(f"Actually copied #{total_actually_copied}")
    return total_actually_copied


def merge_two_portraits(key_1, key_2, count):
    s3 = boto3.resource("s3")
    try:
        print(f"\tProcessing portrait: {key_1}")
        obj = s3.Object(bucket_name="svz-master-pictures-new", key=key_1)
        obj_body = obj.get()["Body"].read()
        image_1 = img = Image.open(BytesIO(obj_body))
        (image_1_width, image_1_height) = image_1.size

        print(f"\tProcessing portrait: {key_2}")
        obj = s3.Object(bucket_name="svz-master-pictures-new", key=key_2)
        obj_body = obj.get()["Body"].read()
        image_2 = img = Image.open(BytesIO(obj_body))
        (image_2_width, image_2_height) = image_2.size

        new_width = image_1_width + image_2_width
        new_height = max(image_1_height, image_2_height)

        result = Image.new("RGB", (new_width, new_height))
        result.paste(im=image_1, box=(0, 0))
        result.paste(im=image_2, box=(image_1_width, 0))

        buffer = BytesIO()
        result.save(buffer, "JPEG")
        buffer.seek(0)

        tmsp = datetime.datetime.now().isoformat()
        new_key = f"nixplay/portrait_{count}_{tmsp}.jpg"
        obj = s3.Object(bucket_name="svz-master-pictures-new", key=new_key)
        obj.put(Body=buffer)
        print(f"\tCreated new portrait merge: {new_key}")
        return 1
    except:
        print(f"\tWarning: unable to merge {key_1} to {key_2}")
        return 0
