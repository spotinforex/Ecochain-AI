from src.data_loader import BigQueryCONN
import logging
from google.cloud import bigquery
from src.prompt_classifier import classify_prompt
import re

logging.basicConfig(level=logging.INFO)

class LMMConnectors:
    ''' Class To Handle All Core BigQuery AI Logic '''
    def __init__(self, prompt):
        self.conn = BigQueryCONN()
        self.client = self.conn.bigquery_client()
        self.prompt = prompt

    def AI_Generate(self):
        ''' Function To Connect to BigQuery's AI.Generate
        Returns:
          AI Response
        '''
        try:
            logging.info("Using AI.GENERATE to Answer Prompt")

            query = r"""
                        SELECT
                            AI.GENERATE(
                                CONCAT(
                                    'You Are An EcoFriendly Supplier Recommender Assistant for ECOCHAIN AI. ',
                                    'Here is the supplier dataset in JSON format:\n',
                                    TO_JSON_STRING(ARRAY_AGG(STRUCT(
                                        supplier_id,
                                        supplier_name,
                                        country,
                                        region,
                                        product_category,
                                        sub_category,
                                        total_eco_score,
                                        water_score,
                                        waste_score,
                                        social_score,
                                        certification,
                                        partnership_status,
                                        annual_volume,
                                        cost_premium,
                                        risk_level,
                                        last_audit,
                                        image_url,
                                        audit_summary
                                    ))),
                                    '\n\nUser query: ', @prompt, '.'
                                ),
                                connection_id => 'us.test_connection',
                                endpoint => 'gemini-2.5-flash'
                            ).result AS response
                        FROM `ecochain123.supplychain.suppliers_with_images`;
                    """

            job_config = bigquery.QueryJobConfig(
                        query_parameters=[
                            bigquery.ScalarQueryParameter("prompt", "STRING", self.prompt)
                        ]
                    )

            query_job = self.client.query(query, job_config=job_config)

            for row in query_job.result():
                response = row["response"]
            clean_response = re.sub(r'[*#]+', '', response)

            return clean_response.strip()

        except Exception as e:
            logging.error(f"AI.GENERATE Failed to Generate Output: {e}")
            return None

    def Vector_Search(self):
        ''' Function Uses a Hybrid Approach that ensure better accuracy by using BigQuery Vector Search and feeding its results to AI.Generate
        Returns:
          AI Response
        '''
        try:
            logging.info("Using Vector Search Hybrid Approach to answer prompt")

            query = '''
                    WITH query AS (
                    SELECT
                        ml_generate_embedding_result AS query_embedding
                    FROM
                        ML.GENERATE_EMBEDDING(
                        MODEL `ecochain123.supplychain.embedding_model`,
                        (SELECT @prompt AS content),
                        STRUCT(TRUE AS flatten_json_output, 384 AS output_dimensionality)
                        )
                    ),
                    context AS (
                    SELECT
                        *
                    FROM VECTOR_SEARCH(
                        TABLE `ecochain123.supplychain.suppliers_with_images`,
                        'text_embedding',
                        (SELECT query_embedding FROM query),
                        top_k => 5
                    ) vs
                    )
                    SELECT
                    AI.GENERATE(
                        CONCAT(
                        "Based on these rows - preferably list out the main facts about it first then explanation below it unless prompted otherwise, answer the user:\\n",
                        (SELECT STRING_AGG(TO_JSON_STRING(context), '\\n') FROM context),
                        "\\nPROMPT: ", @prompt
                        ),
                        connection_id => 'us.test_connection',
                        endpoint => 'gemini-2.5-flash'
                    ).result AS response
                    FROM context;
                    '''
            job_config = bigquery.QueryJobConfig(
                                query_parameters=[
                                    bigquery.ScalarQueryParameter("prompt", "STRING", self.prompt)
                                ]
                            )

            query_job = self.client.query(query, job_config=job_config)

            for row in query_job.result():
                        response = row["response"]
                        clean_response = re.sub(r'[*#]+', '', response)

            return clean_response.strip()

        except Exception as e:
                    logging.error(f"Failed to Answer Prompt with Vector Search {e}")

