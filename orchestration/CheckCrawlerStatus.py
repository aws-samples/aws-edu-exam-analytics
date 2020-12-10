import boto3

print("Checking catalog")

glue = boto3.client("glue")


def lambda_handler(event, context):
    crawler_name = event["crawler"]

    try:
        crawler = glue.get_crawler(Name=crawler_name)
        if crawler["Crawler"]["State"] != "READY":
            status = 304
        else:
            status = 200
    except Exception as error:
        print(error)
        raise error
    return status
