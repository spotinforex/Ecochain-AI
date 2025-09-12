from google.cloud import bigquery
import os
import logging
import src.config
from google.cloud import storage

logging.basicConfig(level = logging.INFO)

class BigQueryCONN:
    ''' Class To Handle All BigQuery Connections '''
    def __init__(self):
        try:
            logging.info(" Connecting To BigQuery")
            # Authenticate with service account
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = src.config.file_path

            # Initialize client
            self.client = bigquery.Client(project = src.config.project_id)

        except Exception as e:
            print(f"Failed to Connect To BigQuery: {e}")


    def bigquery_loader(self):
        ''' Function For Connnecting to BigQuery
        Returns:
            df: dataframe
        '''
        try:
            logging.info(" Retrieving Dataset From BigQuery")
            query = '''
            SELECT * FROM `ecochain123.supplychain.suppliers_with_images`
            '''
            df = self.client.query(query).to_dataframe()
            logging.info(" Dataset Retrieved Successfully")

            return df

        except Exception as e:
            print(f"Failed to Connect To The Dataset: {e}")

    def bigquery_client(self):
        ''' Function To Return BigQuery Connection '''
        return self.client

    def gcs_client(self):
        '''Function to connect to Google Cloud Storage
        returns: GCS Connection
        '''
        try:
            gcs_client = storage.Client()
            BUCKET_NAME = "ecochain-product-images"
            bucket = gcs_client.bucket(BUCKET_NAME)
            return bucket
        except Exception as e:
            logging.error(f'An Error Occurred while connecting to GCS {e}')
