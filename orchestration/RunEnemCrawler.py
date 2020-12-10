import boto3

print("Creating/Updating catalog")

glue = boto3.client("glue")


def create_update_tables(crawler):
    try:
        glue.start_crawler(Name=crawler)
    except Exception as crawler_start_exception:
        raise crawler_start_exception
    return


def lambda_handler(event, context):
    crawler_name = event["crawler"]

    try:
        print("Creating/Updating tables")
        create_update_tables(crawler)

        print("Catalog setted")
        catalog = {
            "status": 200,
        }
    except Exception as error:
        print(error)
        raise error

    return catalog
