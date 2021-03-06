from __future__ import print_function

import boto3
from decimal import Decimal
import json
import urllib
import uuid

print('Loading function')

rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ImageTag')
thumbFolderName = "Thumbs"
tags = {"Food", "Plant", "Car", "Room"}

# --------------- Helper Functions to call Rekognition APIs ------------------


def detect_faces(bucket, key):
    if key.startswith(thumbFolderName):
        return null

    response = rekognition.detect_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    return response


def detect_labels(bucket, key):
    if key.startswith(thumbFolderName):
        return null
    response = rekognition.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}})

    # Sample code to write response to DynamoDB table 'MyTable' with 'PK' as Primary Key.
    # Note: role used for executing this Lambda function should have write access to the table.
    #table = boto3.resource('dynamodb').Table('AnalyzedImageResult')
    for label_prediction in response['Labels']:
        if label_prediction['Name'] in tags:
            item = {
                'Id':uuid.uuid4().hex,
                'ImageName': key,
                'Tag': label_prediction['Name'],
                'Confidence': Decimal(label_prediction['Confidence'])
            }
            table.put_item(Item=item)
            break

    if not 'item' in locals():
        if len(response['Labels']) > 0:
            item = {
                'Id':uuid.uuid4().hex,
                'ImageName': key,
                'Tag': response['Labels'][0]['Name'],
                'Confidence': Decimal(response['Labels'][0]['Confidence'])
            }
            table.put_item(Item=item)
        else:
            item = {
                'Id':uuid.uuid4().hex,
                'ImageName': key,
                'Tag': "Unrecognized",
                'Confidence': 0
            }
            table.put_item(Item=item)

    return response


def index_faces(bucket, key):
    # Note: Collection has to be created upfront. Use CreateCollection API to create a collecion.
    #rekognition.create_collection(CollectionId='BLUEPRINT_COLLECTION')
    response = rekognition.index_faces(Image={"S3Object": {"Bucket": bucket, "Name": key}}, CollectionId="BLUEPRINT_COLLECTION")
    return response


# --------------- Main handler ------------------


def lambda_handler(event, context):
    '''Demonstrates S3 trigger that uses
    Rekognition APIs to detect faces, labels and index faces in S3 Object.
    '''
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    try:
        # Calls rekognition DetectFaces API to detect faces in S3 object
        #response = detect_faces(bucket, key)

        # Calls rekognition DetectLabels API to detect labels in S3 object
        response = detect_labels(bucket, key)

        # Calls rekognition IndexFaces API to detect faces in S3 object and index faces into specified collection
        #response = index_faces(bucket, key)

        # Print response to console.
        print(key)
        print(response)

        return response
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e
