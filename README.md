<a name="readme-top"></a>

<h3 align="center">Fetch Data Engineer Assessment</h3>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#Design Outline">Design Outline</a>
      <ul>
        <li><a href="#Install Process">Install Process</a></li>
        <li><a href="#Running the Code">Running the Code</a></li>
        <li><a href="#Future Improvements">Future Improvements</a></li>
        <li><a href="#Assignment Questions">Assignment Questions</a></li>
  </ol>
</details>


<!-- Design Outline -->
## Design Outline

My ETL workflow design utilizes Python's Boto3 AWS module redirected to the LocalStack SQS queue. Boto3 Receive_Message[s] from the SQS stack serially and then deletes the message. The SQS message is parsed into a UserLogins class, extracting the desired ETL data into a dictionary. The "RecieptHandle" from the SQS message is passed to a delete_message call to remove messages already received from the queue preventing the reception of the same message twice. I chose to mask PII data using AES encryption (Cryptodome python module) over K-Anonymization due to the prototype processing data serially, allotted time constraints, and long-term reversibility of the data. We upload the rows serially, admittedly slowly, using psycopg2 in Python.

The sections below detail how to configure your environment for running the etl_user_logins.py file. Altogether, this file reads data from the SQS queue, transforms the data, and then inserts the rows into a user_logins table.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Install Process

1. Install Docker and Docker Containers 
    - Install Guide: https://docs.docker.com/get-docker/
    - Postgres https://hub.docker.com/r/fetchdocker/data-takehome-postgres
    - Localstack https://hub.docker.com/r/fetchdocker/data-takehome-localstack
2. Install Python 3.10.8 https://www.python.org/downloads/release/python-3108/
    * Note, other python versions likely work. Use at your own risk.
3. Install Python Requirements from CMD
    - pip install psycopg2
    - pip install cryptodome
    - pip install boto3 (aws)
    - pip install awscli-local (Local testing only)
4. Install PostGreSQL https://www.postgresql.org/download/
    * Ensure the postgres docker container has a database reachable with the following config:
    ```sh
   hostname: localhost
   database name: postgres
   username: postgres
   password: postgres
   port: 5432
   ```
    * Then, Create a "user_logins" table directly or in psql:
    
    ```sh
   CREATE TABLE IF NOT EXISTS user_logins(
    user_id varchar(128),
    device_type varchar(32),
    masked_ip varchar(256),
    masked_device_id varchar(256),
    locale varchar(32),
    app_version integer,
    create_date date
    );
   ```
5. Start Docker Containers
    * Copy this github repo locally
    * Run this command from the repo root:
    ```docker-compose up```
6. Test local Access

    * Read a message from the queue using awslocal:
    ```awslocal sqs receive-message --queue-url http://localhost:4566/000000000000/login-queue```
    * Connect to the Postgres database, verify the table is created
    ```
    psql -d postgres -U postgres -p 5432 -h localhost -W;
    postgres=# select * from user_logins;
    ```


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- Running the Code -->
## Running the Code

Run the following python script located in this repo to begin transforming data from the SQS queue and upload it into the postgres table.
  ```js
  etl_user_logins.py;
  ```

<!-- Future Improvements -->
## Future Improvements

1. Securing Database Auth and AES Encyryption Key/Initialization Vector.
    -   Storing these keys and credentials in AWS Secrets Manager or similiar password keeper and utilizing account auth to securely pull the required information as needed is preferable over plain text.
    
2. Performance Optimization (Batching)
    -   (Detailed in assignment question #3)

3. Refine Error Handling
    -   The data is likely not perfect. We need the application to be able to handle exceptions gracefully (ignore or fail) on these exceptions as aligned with the business expectations for this process. The current version lacks significant testing and we would want to refine data exceptions before pushing to prod.
    -   Stop when the queue is finished. There is no need for the program to run indefinately if there nothing on the queue. An alert saying the application stopped could be considered.
4. Implement Logging
    - Troubleshooting applications with runtime information only visibile via direct console is a limitation. Adding sigificantly more logging and outputting the logging to a log file or logging application is ideal. Python has dedicated logging objects we can use.
    
    https://docs.python.org/3/library/logging.html

5. Tie to Python PyPi application
    - Creating a Python module supporting core features allows for reiterable implementation of logging, auth, environment handling, api integrations, and much more! The development of ETL workflows is significantly faster when developing scripts from a central repo, similiar to what I have developed at Moxe Health.

<!-- Assignment Questions -->
## Assignment Questions

1. How would you deploy this application in production?
    * Historically, I've designed PyPi package to create a python scripting environment package that can be loaded into Jenkins or GitHub Actions. AWS Codebuild is also an option. From there, we can run the script with all needed dependencies remotely. The queues need to be pointed to production, copies of this script can be kept running in non-prod environments, separately.
    
2.  What other components would you want to add to make this production ready?
    * Minimally, we need to secure the database credentials and encryption keys. The "Future Improvements" section above details other improvements I would make with varying priorities. 
    
3.  How can this application scale with a growing dataset.
    * There are several significant ways to increase the performance of this application: (1) batching data ingestion, (2) batching the insertion of rows into the Postgresql table, and (3) spinning up multiple Python instances of the application. 
    <br><br>
    (1) Batching data ingestion by upping the "MaxNumberOfMessages" from 1 to its maximum of 10. We could also separate and containerize the process of recieving messages from the sqs queue from the transformation and upload process if mass-scale bandwidth is required.
    ```
    sqs_response = client.receive_message(QueueUrl=endpoint_url, MaxNumberOfMessages = 1)
    ```
    (2) Batching the insertion of rows into the Postgresql table over inserting each row serially will significantly address IO bottlenecks. If mass-scale is needed, staging the data as CSV spliced into 1gb segments which are then copied into the table will be performant.
    <br><br>
    (3) Python has built in multiprocessing / multithreading modules we can utilize for spinning up additional workers. We can also run multiple instances of the script as long we ensure the same message does not get pulled off of the SQS queue twice. Due to the risk, we would want to do proper design planning for this step.

4. How can PII be recovered later on?
    * By utilizing the AES Encryption Key and the initialization vector, we can reverse the encryption with the decrypt function (not yet implemented).
    ```
    def decrypt(self, ciphertext:str, key = encryption_key, init_vector = encryption_iv) -> str:
        '''AES deencryption using a encryption_key and initialization vector'''
        cipher = AES.new(key, AES.MODE_CBC, init_vector)
        decrypted_data = unpad(cipher.decrypt(bytes.fromhex(ciphertext)), AES.block_size)
        return decrypted_data.decode('utf-8')
    ```
5. What are the assumptions you made?
    * The "nonstandard" data in the sqs queue needs to be ignored.
    * "app_version" should be transformed to an integer the instructions list the field as "integer".
    * We need to remove messages from the sqs stack after receiving them.
    * Due to time constraints, serial-level performance is sufficient for now.
    * We should stop the application when there are no more messages. For production, this may be different.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

