# GCP Data Engineering Project: Streaming Data Pipeline with Pub/Sub and Dataflow 

Having prior experience with Apache Beam for batch processing projects, I was eager to explore its streaming capabilities. On Google Cloud Platform (GCP), streaming solutions often revolve around Pub/Sub, Apache Beam, and Dataflow, which are powerful tools for building real-time data pipelines. These tools can be used independently or integrated with other platforms to address diverse streaming requirements.

Pub/Sub is a scalable, asynchronous messaging service that decouples producers and consumers. It is widely used for tasks like streaming analytics, data integration, and distributing data across pipelines. It also functions effectively as middleware for service integration or as a task-parallelising queue.

Dataflow is a fully managed GCP service for unified batch and stream data processing. Built on the open-source Apache Beam framework, Dataflow enables developers to build pipelines that ingest, transform, and output data. Apache Beam’s multi-language support (e.g., Java, Python, and Go) and portability across platforms like Apache Flink or Spark make it highly versatile for diverse data processing needs.

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

The task is to build a **data pipeline** that processes streaming data and organises it into two separate BigQuery tables:

1. **Orders Table**:
   - Stores `orderId` and `cityCode`.
   - Tracks metadata related to each order.

2. **Conversations Table**:
   - Stores individual messages exchanged between couriers and customers.

After storing the data, create a **BigQuery view** called **`customer_courier_conversations`**. This view combines data from the two tables, grouping it to provide insights at the conversation level.

---

## Output Schema

The `customer_courier_conversations` view must include the following fields:

| Field Name                     | Description                                                       |
|--------------------------------|-------------------------------------------------------------------|
| order_id                       | Unique identifier for the order.                                 |
| city_code                      | City where the delivery is scheduled.                            |
| first_courier_message          | Timestamp of the first message sent by the courier.              |
| first_customer_message         | Timestamp of the first message sent by the customer.             |
| num_messages_courier           | Total number of messages sent by the courier.                    |
| num_messages_customer          | Total number of messages sent by the customer.                   |
| first_message_by               | Indicates who sent the first message (courier or customer).      |
| conversation_started_at        | Timestamp of the first message in the conversation.              |
| first_responsetime_delay_seconds | Time (in seconds) between the first message and the first response. |
| last_message_time              | Timestamp of the last message in the conversation.               |
| last_message_order_stage       | The order stage (`orderStage`) during the last message.          |

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

# BigQuery Streaming Buffer
By default, BigQuery stores streaming data temporarily in a "streaming buffer." This buffer holds incoming data for a short time before it is fully committed to the main table.

When streaming stops, BigQuery begins flushing the buffered data into the table’s permanent storage. During this process, the data is reorganised and compressed to ensure it is stored efficiently and accurately.

The time for data to fully move from the streaming buffer to the table can vary, typically taking a few minutes to up to 90 minutes, depending on factors like data volume and BigQuery's processing capacity.

![](https://github.com/Kai-334/GCP-Data-Engineering-Project-Streaming-Data-Pipeline-with-Pub-Sub-and-Dataflow/blob/11cd9022f48ec6266f29b43e384df3e1948b72c4/BigQuery%20Streaming%20Buffer.png)


# Querying the Final Table
The SQL view `customer_courier_conversations_view` transforms raw data from the `orders` and `conversations` tables into a **conversation-level summary table**. This summary provides key insights about each conversation between customers and couriers, including details such as the first message, response times, and message counts.

![](https://github.com/Kai-334/GCP-Data-Engineering-Project-Streaming-Data-Pipeline-with-Pub-Sub-and-Dataflow/blob/9c6aa07bb645eac2dfe40705c55f15efcbd4ecea/final%20table.png)
---

## Purpose of the View

The view consolidates data from the `orders` and `conversations` tables to produce the following outputs:

### 1. **Conversation Metadata**
- **`order_id`**: Links the conversation to its associated order.
- **`city_code`**: Indicates the delivery location for the order.

### 2. **First Messages**
- **`first_courier_message`**: Timestamp of the first message sent by the courier.
- **`first_customer_message`**: Timestamp of the first message sent by the customer.
- **`first_message_by`**: Identifies whether the courier or customer initiated the conversation.

### 3. **Message Counts**
- **`num_messages_courier`**: Total number of messages sent by the courier.
- **`num_messages_customer`**: Total number of messages sent by the customer.

### 4. **Timings**
- **`conversation_started_at`**: Timestamp of the first message in the conversation.
- **`first_responsetime_delay_seconds`**: Time difference (in seconds) between the first message and the first response.

### 5. **Last Message Information**
- **`last_message_time`**: Timestamp of the last message in the conversation.
- **`last_message_order_stage`**: The `orderStage` associated with the last message.

---

## What the View Outputs

The resulting view is a **conversation-level summary** with one row per `order_id`. It combines information about the order and all related messages, making it ready for analytics or further processing.

### Example Use Cases:
1. **Response Time Insights**: Measure and compare response times across different city locations or order stages to identify areas requiring improved communication efficiency.
2. **Conversation Flow Analysis**: Analyse how communication dynamics (e.g., who sends the first message and frequency of follow-ups) vary across order stages such as "In Progress" or "Delivered."
3. **Delivery Process Monitoring**: Track the progression of conversations through order stages to identify patterns in communication during critical stages like "Out for Delivery" or "Awaiting Pickup."

# Credits

This project was inspired by [Original Repository Name](https://github.com/janaom/gcp-de-project-streaming-pubsub-beam-dataflow/tree/main).





