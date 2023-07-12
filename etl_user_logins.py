import boto3
import ast
import psycopg2
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

#Reference for AWS localstack through boto3 https://docs.localstack.cloud/user-guide/integrations/sdks/python/
client = boto3.client('sqs', endpoint_url='http://localhost:4566/000000000000/login-queue')

#Unsecure plain text AES encryption parameters
encryption_key = b'Sixteen byte key'
encryption_iv = b'InitializationVe'


class UserLogins(object):
    '''Encapsulation of data from SQS queue with data masking functions'''
    def __init__(self, sqs_message, user_id, device_type, ip, device_id, locale, app_version, create_date):
        self.sqs_message = sqs_message
        self.data = {
            "user_id": user_id,
            "device_type": device_type,
            "ip": ip,
            "masked_ip": "",
            "device_id": device_id,
            "masked_device_id": "",
            "locale": locale,
            "app_version": app_version,
            "create_date": create_date
        }

    # Function to encrypt data using AES
    def encrypt(self, data:str) -> str:
        '''AES encryption using the encryption_key and initialization vector'''
        cipher = AES.new(encryption_key, AES.MODE_CBC, encryption_iv)
        ciphertext = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
        return ciphertext.hex()

    # Function to decrypt data using AES
    def decrypt(self, ciphertext:str) -> str:
        '''AES deencryption using a encryption_key and initialization vector'''
        cipher = AES.new(encryption_key, AES.MODE_CBC, encryption_iv)
        decrypted_data = unpad(cipher.decrypt(bytes.fromhex(ciphertext)), AES.block_size)
        return decrypted_data.decode('utf-8')
   
    def mask_pii(self):
        '''Reversibly encrypt ip and device_id'''
        self.data['masked_ip'] = self.encrypt(self.data['ip'])
        self.data['masked_device_id'] = self.encrypt(self.data['device_id'])


def get_localstack_sqs(endpoint_url = 'http://localhost:4566/000000000000/login-queue'):
    '''Utilize Boto3 to retrieve and then delete message from stack
    Retrieve message from sqs stack:
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/receive_message.html

    delete from the sqs queue:
    https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_DeleteMessage.html
    '''
    #https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/client/receive_message.html
    sqs_response = client.receive_message(QueueUrl=endpoint_url, MaxNumberOfMessages = 1)
    client.delete_message(QueueUrl = endpoint_url, ReceiptHandle = sqs_response["Messages"][0]['ReceiptHandle'])
    return sqs_response


def parse_data(sqs_message:dict) -> UserLogins:
    '''Parse sqs response into UserLogin class and create encrypted pii'''
    
    #sqs_message["Messages"][0]['Body'] value is dict as string. Ast converts str value to dict
    print(sqs_message["Messages"][0]['Body'])
    print(type(sqs_message["Messages"][0]['Body']))
    data = ast.literal_eval(sqs_message["Messages"][0]['Body'])
    data['create_date'] = sqs_message['ResponseMetadata']['HTTPHeaders']['date']
    encrypted_data = UserLogins(
        sqs_message = sqs_message,
        user_id = data['user_id'],
        device_type = data['device_type'],
        ip = data['ip'],
        device_id = data['device_id'],
        locale = data['locale'],
        app_version = data['app_version'].replace('.', ''), #remove . since table is int
        create_date = data['create_date']
        )
    encrypted_data.mask_pii()
    return encrypted_data


def psycopg2_db_connection() -> tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]:
    '''Return a connection and cursor for the specified database using credentials.'''
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='postgres',
        user='postgres',
        password='postgres',
        )
    return conn, conn.cursor()


def insert_user_logins(login_data: dict) -> int:
    '''Insert data to the user_logins database'''

    conn,cur = psycopg2_db_connection()
    sql = """
        INSERT INTO user_logins (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
    updated_rows = 0
    try:
        cur.execute(sql, (login_data.get("user_id"), login_data.get("device_type"), login_data.get("masked_ip"), login_data.get("masked_device_id"), login_data.get("locale"), login_data.get("app_version"), login_data.get("create_date")))
        updated_rows = cur.rowcount
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    print(f'Inserted {updated_rows} rows')
    return updated_rows


def main():
    '''Serially process SQS stack into user_logins table'''
    while True:
        result = get_localstack_sqs()
        print(result["Messages"][0]['Body'])
        parsed_result = parse_data(result)
        #print(parsed_result.data)
        insert_user_logins(login_data = parsed_result.data)


if __name__ == '__main__':
    main()
