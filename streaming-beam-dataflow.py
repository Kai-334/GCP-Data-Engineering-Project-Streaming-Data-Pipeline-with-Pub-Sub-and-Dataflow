import apache_beam as beam
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.io.gcp.bigquery import WriteToBigQuery
import json
from apache_beam.options.pipeline_options import PipelineOptions

#Define your Dataflow pipeline options
options = PipelineOptions(
    runner='DataflowRunner', 
    project='ultimate-triode-444006-p6',
    region='us-central1',   
    temp_location='gs://bucket-streaming-data/temp',
    staging_location='gs://bucket-streaming-data/staging',
    streaming=True,  #Enable streaming mode
    #Dataflow parameters that are optional
    #job_name='streaming-conversations',  #Set the Dataflow job name here
    #num_workers=10,  #Specify the number of workers
    #max_num_workers=50,  #Specify the maximum number of workers
    #disk_size_gb=100,  #Specify the disk size in GB per worker
    #autoscaling_algorithm='THROUGHPUT_BASED',  #Specify the autoscaling algorithm
    #machine_type='n1-standard-4',  #Specify the machine type for the workers
    #service_account_email='streaming-job@streaming-project-415718.iam.gserviceaccount.com'  #Specify the service account email, add these roles: BigQuery Admin, Dataflow Worker, Pub/Sub Admin, Storage Object Viewer 
)

#Define your Beam pipeline
with beam.Pipeline(options=options) as pipeline:
    #Read the input data from Pub/Sub
    messages = pipeline | ReadFromPubSub(subscription='projects/ultimate-triode-444006-p6/subscriptions/topic-conversations-3-sub')

    # Converts this JSON string into a Python dictionary.
    # Can access individual fields and apply filtering, transformations, or aggregations based on these fields.
    parsed_messages = messages | beam.Map(lambda msg: json.loads(msg))

    # Extract the desired fields for 'conversations' table
    # beam.Map is a PTransform in Apache Beam. It applies a transformation to each element in a PCollection and outputs a new PCollection.
    # Here, beam.Map extracts the desired fields and creates a new dictionary for each input element.
    conversations_data = parsed_messages | beam.Map(lambda data: {
        'senderAppType': data.get('senderAppType', 'N/A'),
        'courierId': data.get('courierId', None),
        'fromId': data.get('fromId', None),
        'toId': data.get('toId', None),
        'chatStartedByMessage': data.get('chatStartedByMessage', False),
        'orderId': data.get('orderId', None),
        'orderStage': data.get('orderStage', 'N/A'),
        'customerId': data.get('customerId', None),
        'messageSentTime': data.get('messageSentTime', None),
        # Only elements with both fields present are processed further in the pipeline
    }) | beam.Filter(lambda data: data['orderId'] is not None and data['customerId'] is not None)

    # Extract the desired fields for 'orders' table
    orders_data = parsed_messages | beam.Map(lambda data: {
        'cityCode': data.get('cityCode', 'N/A'),
        'orderId': data.get('orderId', None),
        # Only elements that satisfy both conditions (non-None 'orderId' and 'cityCode' not equal to 'N/A') will pass through the filter and continue to the subsequent steps in the pipeline.
    }) | beam.Filter(lambda data: data['orderId'] is not None and data['cityCode'] != 'N/A')

    # Define the schema for the 'conversations' table in BigQuery
    conversations_schema = {
        'fields': [
            {'name': 'senderAppType', 'type': 'STRING'},
            {'name': 'courierId', 'type': 'INTEGER'},
            {'name': 'fromId', 'type': 'INTEGER'},
            {'name': 'toId', 'type': 'INTEGER'},
            {'name': 'chatStartedByMessage', 'type': 'BOOLEAN'},
            {'name': 'orderId', 'type': 'INTEGER'},
            {'name': 'orderStage', 'type': 'STRING'},
            {'name': 'customerId', 'type': 'INTEGER'},
            {'name': 'messageSentTime', 'type': 'TIMESTAMP'}
        ]
    }

    # Define the schema for the 'orders' table in Bigquery
    orders_schema = {
        'fields': [
            {'name': 'cityCode', 'type': 'STRING'},
            {'name': 'orderId', 'type': 'INTEGER'}
        ]
    }

    # Write the conversations data to the 'conversations' table in BigQuery
    conversations_data | 'Write conversations to BigQuery' >> WriteToBigQuery(
        table='ultimate-triode-444006-p6:dataset.conversations',
        schema=conversations_schema,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
    )

    # Write the orders data to the 'orders' table in BigQuery
    orders_data | 'Write orders to BigQuery' >> WriteToBigQuery(
        table='ultimate-triode-444006-p6:dataset.orders',
        schema=orders_schema,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
    )