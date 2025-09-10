from google.cloud import bigquery
import logging
from src.data_loader import BigQueryCONN
from io import BytesIO
from PIL import Image
import numpy as np

logging.basicConfig(level = logging.INFO)


class Update:
    ''' Class to handle all Updates to BigQuery '''
    def __init__(self,new_supplier_info):
        self.conn = BigQueryCONN()
        self.client = self.conn.bigquery_client()
        self.bucket = self.conn.gcs_client()
        self.new_supplier = new_supplier_info

    def upload_supplier_images(self, uploaded_images, supplier_id):
        """
        Uploads supplier images to GCS and returns public URLs.
        """
        bucket = self.bucket
        image_urls = []

        for idx, img_file in enumerate(uploaded_images):
            img = Image.open(img_file)

            # Generate filename (supplier_id + index)
            file_ext = img_file.name.split(".")[-1].lower()
            blob_name = f"{supplier_id}_{idx+1}.{file_ext}"

            # Save image to buffer for upload
            buffer = BytesIO()
            img.save(buffer, format=img.format if img.format else "JPEG")
            buffer.seek(0)

            # Upload to GCS
            blob = bucket.blob(blob_name)
            blob.upload_from_file(buffer, content_type=f"image/{file_ext}")
            blob.make_public()

            image_urls.append(blob.public_url)

        return image_urls

    def supplier_update(self):
        ''' Insert new supplier, handle images dynamically '''
        try:
            logging.info('Adding New Supplier...')

            # Get next supplier_id
            query_id = """
                SELECT
                  CONCAT('SUP', CAST(
                    IFNULL(MAX(CAST(REGEXP_EXTRACT(supplier_id, r'SUP(\\d+)') AS INT64)), 0) + 1 AS STRING)
                  ) AS new_supplier_id
                FROM `ecochain123.supplychain.suppliers_with_images`
            """
            query_job = self.client.query(query_id).result()
            new_supplier_id = [row["new_supplier_id"] for row in query_job][0]

            # --- Handle Images if available ---
            uploaded_images = self.new_supplier.get("uploaded_images", [])
            if uploaded_images:
                image_urls = self.upload_supplier_images(uploaded_images, new_supplier_id)
                image_urls_str = ",".join(image_urls)  # store as comma-separated string
            else:
                image_urls_str = None  # no images

            # --- Insert Supplier ---
            query = f"""
                INSERT INTO `ecochain123.supplychain.suppliers_with_images` (
                    supplier_id,
                    supplier_name,
                    country,
                    region,
                    product_category,
                    sub_category,
                    certification,
                    partnership_status,
                    annual_volume,
                    cost_premium,
                    risk_level,
                    last_audit,
                    audit_summary,
                    image_url
                )
                VALUES (
                    @supplier_id, @supplier_name, @country, @region,
                    @product_category, @sub_category, @certification,
                    @partnership_status, @annual_volume, @cost_premium,
                    @risk_level, @last_audit, @audit_summary, @image_url
                )
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("supplier_id", "STRING", new_supplier_id),
                    bigquery.ScalarQueryParameter("supplier_name", "STRING", self.new_supplier["supplier_name"]),
                    bigquery.ScalarQueryParameter("country", "STRING", self.new_supplier["country"]),
                    bigquery.ScalarQueryParameter("region", "STRING", self.new_supplier["region"]),
                    bigquery.ScalarQueryParameter("product_category", "STRING", self.new_supplier["product_category"]),
                    bigquery.ScalarQueryParameter("sub_category", "STRING", self.new_supplier["sub_category"]),
                    bigquery.ScalarQueryParameter("certification", "STRING", self.new_supplier["certification"]),
                    bigquery.ScalarQueryParameter("partnership_status", "STRING", self.new_supplier["partnership_status"]),
                    bigquery.ScalarQueryParameter("annual_volume", "INT64", self.new_supplier["annual_volume"]),
                    bigquery.ScalarQueryParameter("cost_premium", "FLOAT64", self.new_supplier["cost_premium"]),
                    bigquery.ScalarQueryParameter("risk_level", "STRING", self.new_supplier["risk_level"]),
                    bigquery.ScalarQueryParameter("last_audit", "STRING", self.new_supplier["last_audit"]),
                    bigquery.ScalarQueryParameter("audit_summary", "STRING", self.new_supplier["audit_summary"]),
                    bigquery.ScalarQueryParameter("image_url", "STRING", image_urls_str)
                ]
            )

            insert_job = self.client.query(query, job_config=job_config)
            insert_job.result()

            logging.info(f"✅ Supplier {new_supplier_id} added successfully.")
            return new_supplier_id

        except Exception as e:
            logging.error(f'❌ Failed to add new supplier: {e}')
            return None


    def embed_supplier(self, supplier_id):
        ''' Function to Create embeddings for new supplier'''
        try:
            logging.info('Embedding New Supplier In Progress...')
            logging.info(f'Embedding New Supplier {supplier_id} In Progress...')

            query_1 = f'''
                CREATE OR REPLACE TABLE `ecochain123.supplychain.suppliers_embeddings` AS
                SELECT
                    supplier_id,
                    ml_generate_embedding_result AS text_embedding
                FROM ML.GENERATE_EMBEDDING(
                    MODEL `ecochain123.supplychain.embedding_model`,
                    (
                        SELECT
                            supplier_id,
                            CONCAT(
                                "Category: ", product_category, "; ",
                                "Sub-category: ", sub_category, "; ",
                                "Certification: ", certification, "; ",
                                "Audit: ", audit_summary
                            ) AS content
                        FROM `ecochain123.supplychain.suppliers_with_images`
                        WHERE supplier_id = @supplier_id
                    ),
                    STRUCT(TRUE AS flatten_json_output, 384 AS output_dimensionality)
                );
                '''
            query_2 = '''
                UPDATE `ecochain123.supplychain.suppliers_with_images` AS t
                SET text_embedding = s.text_embedding
                FROM `ecochain123.supplychain.suppliers_embeddings` AS s
                WHERE t.supplier_id = s.supplier_id
                AND t.supplier_id = @supplier_id
                '''
            job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("supplier_id", "STRING", supplier_id),
                    ]
                )

            query_job_1 = self.client.query(query_1, job_config=job_config)
            query_job_1.result()
            logging.info('Created embedding successfully, Adding to database')

            query_job_2 = self.client.query(query_2, job_config=job_config)
            query_job_2.result()
            logging.info('Embeddings Successfully Added')

        except Exception as e:
                logging.error(f'Failed to Add text embedding of supplier {supplier_id} - {e}')
                raise

    def update_ecoscores(self, ecoscores_list):
        """
        Update ecoscores in BigQuery for multiple suppliers.
        ecoscores_list: list of dicts, each dict contains predicted scores + supplier_id
        """
        if not ecoscores_list:
            logging.info("No ecoscores to update.")
            return

        try:
            logging.info("Updating ecoscores in BigQuery...")
            for record in ecoscores_list:
                query = """
                    UPDATE `ecochain123.supplychain.suppliers_with_images`
                    SET
                        carbon_score = @carbon_score,
                        water_score = @water_score,
                        waste_score = @waste_score,
                        social_score = @social_score,
                        total_eco_score = @ecoscore
                    WHERE supplier_id = @supplier_id
                """
                job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("carbon_score", "FLOAT64", float(record["carbon_score"])),
                        bigquery.ScalarQueryParameter("water_score", "FLOAT64", float(record["water_score"])),
                        bigquery.ScalarQueryParameter("waste_score", "FLOAT64", float(record["waste_score"])),
                        bigquery.ScalarQueryParameter("social_score", "FLOAT64", float(record["social_score"])),
                        bigquery.ScalarQueryParameter("ecoscore", "FLOAT64", float(record["ecoscore"])),
                        bigquery.ScalarQueryParameter("supplier_id", "STRING", str(record["supplier_id"]))
                    ]
                )
                query_job = self.client.query(query, job_config=job_config)
                query_job.result()
                logging.info(f"Updated supplier successfully: {record['supplier_id']}")

        except Exception as e:
            logging.error(f"Failed to update ecoscores: {e}")
            raise


    def update_recommendations(self,supplier_id):
        '''Function to add recommendations for new suppliers '''
        try:
            query_1 = '''
                    CREATE OR REPLACE TABLE `ecochain123.supplychain.recommendation` AS
                            SELECT
                            supplier_id,
                            total_eco_score,
                            recommendation
                            FROM
                            AI.GENERATE_TABLE(
                                MODEL `ecochain123.supplychain.gemini_model`,
                                (
                                SELECT
                                    supplier_id,
                                    total_eco_score,
                                    CONCAT(
                                    "Using the following keywords (Preferred, Neutral, or Avoid) categorise this score. ",
                                    "If above 80, it is Preferred; ",
                                    "If between 50 and 80, it is Neutral; ",
                                    "If below 50, it is Avoid. ",
                                    "Score: ", CAST(total_eco_score AS STRING)
                                    ) AS prompt
                                FROM
                                    `ecochain123.supplychain.suppliers_with_images`
                                WHERE supplier_id = @supplier_id AND recommendation IS NULL
                                ),
                                STRUCT("recommendation STRING" AS output_schema)
                            );
                            '''
            query_2 = '''
                    UPDATE `ecochain123.supplychain.suppliers_with_images` t
                    SET t.recommendation = s.recommendation
                    FROM `ecochain123.supplychain.recommendation` s
                    WHERE t.supplier_id = s.supplier_id;
                                '''
            job_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("supplier_id", "STRING", supplier_id),
                    ]
                )
            query_job_1 = self.client.query(query_1, job_config = job_config)
            query_job_1.result()
            logging.info('Created Recommendation successfully, Adding to database')
            query_job_2 = self.client.query(query_2)
            query_job_2.result()
            logging.info('recommendation Successfully Added')

        except Exception as e:
                logging.error(f'Failed to Add Recommendation of new supplier {e}')
                raise




