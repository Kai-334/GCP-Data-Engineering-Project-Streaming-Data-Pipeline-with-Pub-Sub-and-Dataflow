# <img width="40" alt="image" src="https://github.com/janaom/gcp-data-engineering-etl-with-composer-dataflow/assets/83917694/60f8f158-3bdc-4b3d-94ae-27a12441e2a3">  GCP Data Engineering Project: Streaming Data Pipeline with Pub/Sub and Apache Beam/Dataflow 📡

When it comes to streaming data, Kafka and Flink are popular topics of discussion. However, if you are working with Google Cloud Platform (GCP), it is more likely that you will utilize Pub/Sub, Apache Beam, and Dataflow as your primary streaming services. These tools can be used either standalone or in conjunction with other streaming solutions.

[Pub/Sub](https://cloud.google.com/pubsub/docs/overview) is an asynchronous and scalable messaging service that decouples services producing messages from services processing those messages. Pub/Sub is used for streaming analytics and data integration pipelines to load and distribute data. It's equally effective as a messaging-oriented middleware for service integration or as a queue to parallelize tasks.

[Dataflow](https://cloud.google.com/dataflow/docs/overview) is a Google Cloud service that provides unified stream and batch data processing at scale. Use Dataflow to create data pipelines that read from one or more sources, transform the data, and write the data to a destination. Dataflow is built on the open source Apache Beam project. Apache Beam lets you write pipelines using a language-specific SDK. Apache Beam supports Java, Python, and Go SDKs, as well as multi-language pipelines. Dataflow executes Apache Beam pipelines. If you decide later to run your pipeline on a different platform, such as Apache Flink or Apache Spark, you can do so without rewriting the pipeline code.
With prior experience in utilizing Beam for batch projects, I was keen to experiment with its streaming functionality. The following is a challenging task I came across and the corresponding solution I developed.

# Problem Description

![](https://github.com/Kai-334/GCP-Data-Engineering-Project-Streaming-Data-Pipeline-with-Pub-Sub-and-Dataflow/blob/18aeb28d0f53827b656adb75ba62db8a57c73b43/Scenario%20Image.png)

We are tasked with processing simulated **"customer_courier_chat_messages"** data, which records individual chat messages exchanged between customers and couriers through an in-app chat system. Each message contains metadata such as sender type, order information, and timestamp.

In addition to the chat messages, we have access to an **"orders" event**, which maps each unique `orderId` to its corresponding `cityCode`. This **orders event** appears only once per `orderId` and provides important context for the conversation data.

---

## Simulated Data Generation

To simulate this data, a Python script was used to generate **400 conversations**. Here's how the simulation works:

1. **Conversations**:
   - Each conversation starts with a message sent by either the **Customer** or **Courier**.
   - The first message is followed by an **orders event** that includes the `orderId` and `cityCode`.
   - Subsequent messages are exchanged chronologically between the **Customer** and **Courier**.
   - Each conversation contains **2 to 5 messages** in total.

2. **Orders Data**:
   - Each unique `orderId` is paired with a single **orders event** that includes the `cityCode`.
   - This event only appears once per `orderId`, typically as the second message in a conversation.

---

## Sample Simulated Data

A sample of the **`conversations.json` file** is shown below:

```json
{"senderAppType": "Courier Android", "courierId": 17935441, "fromId": 17935441, "toId": 31685802, "chatStartedByMessage": true, "orderId": 82414506, "orderStage": "RETURNED", "customerId": 31685802, "messageSentTime": "2024-02-01T10:00:56Z"}
{"orderId": 82414506, "cityCode": "IST"}
{"senderAppType": "Customer iOS", "customerId": 31685802, "fromId": 31685802, "toId": 17935441, "chatStartedByMessage": false, "orderId": 82414506, "orderStage": "IN_PROGRESS", "courierId": 17935441, "messageSentTime": "2024-02-01T10:01:07Z"}
{"senderAppType": "Customer iOS", "customerId": 85223204, "fromId": 85223204, "toId": 68924298, "chatStartedByMessage": true, "orderId": 13129173, "orderStage": "IN_PROGRESS", "courierId": 68924298, "messageSentTime": "2024-02-01T10:01:53Z"}
{"orderId": 13129173, "cityCode": "IST"}
{"senderAppType": "Courier Android", "courierId": 37614487, "fromId": 37614487, "toId": 56464808, "chatStartedByMessage": true, "orderId": 79545352, "orderStage": "OUT_FOR_DELIVERY", "customerId": 56464808, "messageSentTime": "2024-02-01T10:02:30Z"}
{"orderId": 79545352, "cityCode": "SYD"}
{"senderAppType": "Courier Android", "courierId": 68924298, "fromId": 68924298, "toId": 85223204, "chatStartedByMessage": false, "orderId": 13129173, "orderStage": "AWAITING_PICKUP", "customerId": 85223204, "messageSentTime": "2024-02-01T10:02:43Z"}
{"senderAppType": "Courier Android", "courierId": 56230356, "fromId": 56230356, "toId": 57998724, "chatStartedByMessage": true, "orderId": 44410052, "orderStage": "ACCEPTED", "customerId": 57998724, "messageSentTime": "2024-02-01T10:03:01Z"}
{"orderId": 44410052, "cityCode": "BER"}
...
```

# Task Description

The task is to build a **data pipeline** that processes this streaming data, aggregates messages into meaningful **conversations**, and splits the data into two BigQuery tables:
1. **orders Table**:
   - Contains orderId and cityCode.
   - Used to track order-level metadata.

2. **conversations Table**:
   - Contains individual messages exchanged between couriers and customers.

After the data is stored in these two tables, create a unified **BigQuery view** called **`customer_courier_conversations`**. This view combines data from the `orders` and `conversations` tables and performs **aggregation and grouping** to provide meaningful insights at the conversation level.

---

## Output Schema

The customer_courier_conversations view must include the following fields:

| Field Name                     | Description                                                       |
|--------------------------------|-------------------------------------------------------------------|
| order_id                     | Unique identifier for the order.                                 |
| city_code                    | City where the delivery is scheduled.                            |
| first_courier_message        | Timestamp of the first message sent by the courier.              |
| first_customer_message       | Timestamp of the first message sent by the customer.             |
| num_messages_courier         | Total number of messages sent by the courier in the conversation.|
| num_messages_customer        | Total number of messages sent by the customer in the conversation.|
| first_message_by             | Indicates who sent the first message (courier or customer).      |
| conversation_started_at      | Timestamp of the first message in the conversation.              |
| first_responsetime_delay_seconds | Time elapsed (in seconds) between the first message and the first response. |
| last_message_time            | Timestamp of the last message in the conversation.               |
| last_message_order_stage     | The order stage (orderStage) during the last message.          |

---

# Tech Stack Architecture

![](https://github.com/Kai-334/GCP-Data-Engineering-Project-Streaming-Data-Pipeline-with-Pub-Sub-and-Dataflow/blob/18aeb28d0f53827b656adb75ba62db8a57c73b43/Tech%20Stack%20Architecture.png)

`Google Cloud Storage (GCS)`: Acts as the storage solution for the conversations.json file. GCS provides reliable, scalable object storage, ensuring the data is securely stored and accessible for processing.

`Pub/Sub`: Facilitates the asynchronous publishing of the conversations.json file content to a designated topic. It ensures reliable message delivery and decouples the communication between producers (publishers) and consumers (subscribers).

<img src="https://github.com/Kai-334/GCP-Data-Engineering-Project-Streaming-Data-Pipeline-with-Pub-Sub-and-Dataflow/blob/ecda05ba2e96cf0ef80b59c8ffa94106b9319a99/how%20pub%20sub%20works.png?raw=true" alt="Image" width="600">

`Dataflow`: Built on Apache Beam, Dataflow enables real-time streaming data processing and transformations. It processes the conversations data and organizes it into two tables: conversations and orders.

`BigQuery`: Serves as the storage for the processed data. BigQuery’s scalability and efficient query capabilities allow for rapid analysis and retrieval of the transformed data.

# Google Cloud Storage

The simulated conversation data which resides in the conversation.json file is uploaded to the GCS bucket.

![](https://github.com/Kai-334/GCP-Data-Engineering-Project-Streaming-Data-Pipeline-with-Pub-Sub-and-Dataflow/blob/793b11bc60a5c4187c16d47686035cea8eb2e687/GCS%20bucket.png)

# Pub/Sub: Messaging Bus
Here we utilize the GCP console to manually set up the Topic and Subscription.

Create a Topic named `topic-conversations-3`:
![](https://github.com/Kai-334/GCP-Data-Engineering-Project-Streaming-Data-Pipeline-with-Pub-Sub-and-Dataflow/blob/c748f3787b2efc645a77e8aef378ac40b25319b0/Pub-Sub%20Topic.png)

Create a Subscription named `topic-conversations-3-sub`:
![](https://github.com/Kai-334/GCP-Data-Engineering-Project-Streaming-Data-Pipeline-with-Pub-Sub-and-Dataflow/blob/c748f3787b2efc645a77e8aef378ac40b25319b0/Pub-Sub%20Subscription.png)

# Publishing Data to Pub/Sub

The Python script `send-data-to-pubsub.py` publishes messages from a file to a Pub/Sub topic. It reads each line of a JSON file stored in Google Cloud Storage, encodes the data, and publishes it to a specified Pub/Sub topic at 1-second intervals.

---

### Key Steps:

1. **Initialize Clients**:
   - Use `pubsub_v1.PublisherClient` to interact with Pub/Sub.
   - Use `storage.Client` to access the JSON file stored in a GCS bucket.

2. **Read File**:
   - The script retrieves the specified file (`conversations.json`) from a GCS bucket.

3. **Publish Messages**:
   - Each line in the file is read, encoded to a bytestring, and published to the specified Pub/Sub topic.

4. **Add Delay**:
   - A 1-second delay between publishing each message simulates streaming data.

---

# Streaming Dataflow Pipeline

The Python script `streaming-dataflow-pipeline.py` processes streaming data from Pub/Sub and writes the transformed data into BigQuery tables. The pipeline is built using Apache Beam and deployed using Google Cloud Dataflow, enabling real-time data processing and storage.

---

### Key Steps:

1. **Ingest Data**:
   - The pipeline reads real-time messages from a **Pub/Sub subscription**.

2. **Parse and Transform**:
   - JSON messages are converted into Python dictionaries for processing.
   - Messages are split into two datasets:
     - **Conversations**: Extracts and filters relevant fields for the `conversations` table.
     - **Orders**: Extracts and filters relevant fields for the `orders` table.

3. **Write to BigQuery**:
   - The pipeline writes the processed data to two **BigQuery tables**:
     - `conversations`
     - `orders`
   - Ensures schema compliance and appends new data without overwriting existing records.

---
![](https://github.com/Kai-334/GCP-Data-Engineering-Project-Streaming-Data-Pipeline-with-Pub-Sub-and-Dataflow/blob/a40ce3c9fdf15f37a7c7d05fa2aa54cd71c20a5d/Dataflow%20Graph%20View.png)

Thus, executing the provided code (`python send-data-to-pubsub.py` and `python streaming-beam-dataflow.py`) will trigger a series of actions:
- Publish the messages to the Pub/Sub topic.
- The pipeline reads data from a Pub/Sub subscription using the `ReadFromPubSub` transform.
- The desired fields from the parsed messages are extracted for the "conversations" and "orders" tables using the `beam.Map` transform and lambda functions.
- The processed "conversations" and "orders" data is written to the respective BigQuery tables using the `WriteToBigQuery` transform.

# ⏯️ BigQuery Streaming Buffer
By default, BigQuery stores streaming data in a special storage location called the "streaming buffer." The streaming buffer is a temporary storage area that holds the incoming data for a short period before it is fully committed and becomes part of the permanent table.

![1 g4PjtluUvzrwRtpdpEziEA](https://github.com/janaom/gcp-de-project-streaming-beam-dataflow-pubsub/assets/83917694/0d5b4e86-c01b-485b-b7c5-8a88d07e4f3a)


When you stop streaming data, the data in the streaming buffer is no longer continuously updated. BigQuery then starts the process of flushing the buffered data into the main table storage. The data is also reorganized and compressed for efficient storage. This process ensures data consistency and integrity before fully committing it to the table.

The time it takes for the streamed data to be fully committed and visible in the table depends on various factors, including the size of the buffer, the volume of data, and BigQuery's internal processing capacity. Typically, it takes a few minutes or up to 90 minutes for the streaming buffer to be completely flushed and the data to be visible in the table.

In the provided example, the updated information becomes visible in the "Storage info" section.

![1 NDYjPiI7HAgPbLboYfIVRw](https://github.com/janaom/gcp-de-project-streaming-beam-dataflow-pubsub/assets/83917694/ceb1dcfd-22a2-4073-b237-3021b0e86dc0)


# 🧮 Querying the Final Table
The final step involves creating the "customer_courier_conversations" table. In this case, we will generate a [view](https://cloud.google.com/bigquery/docs/views-intro), which is a virtual table defined by a SQL query. The custom SQL code will help transform the data to meet the specific task requirements.

![1 7SFCGTdJLBsjC1I7am3h7Q](https://github.com/janaom/gcp-de-project-streaming-beam-dataflow-pubsub/assets/83917694/b7b88fdd-0272-401c-ab25-e754c5345a20)


Views are virtual references to a set of data, offering reusable access without physically storing the data. [Materialized views](https://cloud.google.com/bigquery/docs/materialized-views-intro), on the other hand, are defined using SQL like regular views but physically store the data. However, they come with [limitations](https://cloud.google.com/bigquery/docs/materialized-views-intro#comparison) in query support. Due to the substantial size of my query, opting for a regular view was the more suitable choice in this case.

Once the streaming process has been initiated, you can execute the saved view after a brief interval.

```sql
SELECT * FROM `your-project-id.dataset.view`
```

Let's examine the first row from the results by extracting all messages associated with the "orderId" 77656162 from the "conversations.json" file.

![1 G-LpAKxAmGHTShp743ed7A](https://github.com/janaom/gcp-de-project-streaming-beam-dataflow-pubsub/assets/83917694/74e59371-a38f-42ff-a6e6-e80dfa871b1b)


The analysis yielded the following results: a total of 5 messages were identified. The conversation commenced with a Courier message in Rome at 10:04:46. The Customer responded after 42 seconds, at 10:05:28. The final message was received from the Courier at 10:06:35, and the last message order stage was recorded as "FAILED".

```json
{"senderAppType": "Courier Android", "courierId": 45035010, "fromId": 45035010, "toId": 57270753, "chatStartedByMessage": true, "orderId": 77656162, "orderStage": "AWAITING_PICKUP", "customerId": 57270753, "messageSentTime": "2024-02-01T10:04:46Z"}
{"orderId": 77656162, "cityCode": "ROM"}
{"senderAppType": "Customer iOS", "customerId": 57270753, "fromId": 57270753, "toId": 45035010, "chatStartedByMessage": false, "orderId": 77656162, "orderStage": "DELAYED", "courierId": 45035010, "messageSentTime": "2024-02-01T10:05:28Z"}
{"senderAppType": "Courier Android", "courierId": 45035010, "fromId": 45035010, "toId": 57270753, "chatStartedByMessage": false, "orderId": 77656162, "orderStage": "ACCEPTED", "customerId": 57270753, "messageSentTime": "2024-02-01T10:05:31Z"}
{"senderAppType": "Customer iOS", "customerId": 57270753, "fromId": 57270753, "toId": 45035010, "chatStartedByMessage": false, "orderId": 77656162, "orderStage": "DELAYED", "courierId": 45035010, "messageSentTime": "2024-02-01T10:06:16Z"}
{"senderAppType": "Courier Android", "courierId": 45035010, "fromId": 45035010, "toId": 57270753, "chatStartedByMessage": false, "orderId": 77656162, "orderStage": "FAILED", "customerId": 57270753, "messageSentTime": "2024-02-01T10:06:35Z"}
```

Please note that, in my case, the time difference between the first and last messages was only 2 minutes, resulting in a relatively quick analysis. As new data is continuously streaming into the source, the view is automatically updated in real-time to reflect the changes. This means that whenever you query the view, you will get the most up-to-date data that matches the defined criteria.

To gain further insights into the dynamic nature of the streaming process, let's examine additional examples and observe how the results evolve over time.

![1 QRnvMHwBdOKcmfP11bWeXw](https://github.com/janaom/gcp-de-project-streaming-beam-dataflow-pubsub/assets/83917694/bbfdd566-6cb2-49ea-ba0f-110ababd7f60)


In the first example, the conversation associated with "orderId" 66096282 in Tokyo commenced with a Courier message at 10:38:50. At this point, no response from the Customer has been received. The last message order stage is shown as "OUT_FOR_DELIVERY".

To observe any changes, let's execute the view once again and compare the results.

![1 zROM0ndny_c4DQRkz0mTdg](https://github.com/janaom/gcp-de-project-streaming-beam-dataflow-pubsub/assets/83917694/289c77a2-37e4-4650-add1-bd0bfa0f6e13)


A Customer reply was received at 10:39:30. Although the view indicates that the last message was sent at 10:39:45 with the status "PENDING", a closer examination of the JSON file reveals that the actual last message will be sent at 10:41:07, which hasn't been received yet. Additionally, expect the number of messages to be updated shortly.

Let's execute the view one more time.

![1 jV6tijubvOGB6-xjfQLTbQ](https://github.com/janaom/gcp-de-project-streaming-beam-dataflow-pubsub/assets/83917694/205087dc-4963-427d-95a1-be4a552aae1b)

Here we see that all 5 messages have been received, and the last message order stage now is "ACCEPTED". 🥳

```json
{"senderAppType": "Courier Android", "courierId": 64897260, "fromId": 64897260, "toId": 55461000, "chatStartedByMessage": true, "orderId": 66096282, "orderStage": "OUT_FOR_DELIVERY", "customerId": 55461000, "messageSentTime": "2024-02-01T10:38:50Z"}
{"orderId": 66096282, "cityCode": "TOK"}
{"senderAppType": "Customer iOS", "customerId": 55461000, "fromId": 55461000, "toId": 64897260, "chatStartedByMessage": false, "orderId": 66096282, "orderStage": "ACCEPTED", "courierId": 64897260, "messageSentTime": "2024-02-01T10:39:30Z"}
{"senderAppType": "Courier Android", "courierId": 64897260, "fromId": 64897260, "toId": 55461000, "chatStartedByMessage": false, "orderId": 66096282, "orderStage": "PENDING", "customerId": 55461000, "messageSentTime": "2024-02-01T10:39:45Z"}
{"senderAppType": "Customer iOS", "customerId": 55461000, "fromId": 55461000, "toId": 64897260, "chatStartedByMessage": false, "orderId": 66096282, "orderStage": "IN_PROGRESS", "courierId": 64897260, "messageSentTime": "2024-02-01T10:40:37Z"}
{"senderAppType": "Courier Android", "courierId": 64897260, "fromId": 64897260, "toId": 55461000, "chatStartedByMessage": false, "orderId": 66096282, "orderStage": "ACCEPTED", "customerId": 55461000, "messageSentTime": "2024-02-01T10:41:07Z"}
```


To experiment with larger data, you can access the `generate-the-data.py` code on my GitHub repository. This code allows you to generate additional conversations, enabling you to test the project's scalability.🤖

If you have any questions or would like to discuss streaming, feel free to connect with me on [LinkedIn](https://www.linkedin.com/in/jana-polianskaja/)! I'm always open to sharing ideas and engaging in insightful conversations.😊

Throughout this article, I've referred to the following sources for specific details and concepts:

https://cloud.google.com/dataflow/docs/overview

https://cloud.google.com/pubsub/docs/overview

https://beam.apache.org/documentation/runners/dataflow/

https://beam.apache.org/documentation/runners/direct/

https://cloud.google.com/bigquery/docs/views-intro






