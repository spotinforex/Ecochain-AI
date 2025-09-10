from src.data_loader import BigQueryCONN
import logging
from google.cloud import bigquery

logging.basicConfig(level=logging.INFO)

def classify_prompt(user_prompt):
    """
    Function to classify user queries.

    Args:
        user_prompt (str): The raw user query.

    Returns:
        str: One of ML.GENERATE_TEXT, AI.GENERATE, AI.GENERATE_IMAGE, VECTOR_SEARCH, VECTOR_SEARCH_IMAGE
    """
    try:
        logging.info("Classifying Prompt...")

        query = '''
                SELECT
                AI.GENERATE(
                    'AI.GENERATE(if the user wants responses that would be summary, explanation, sustainability report, narrative text, tabular or dataframe formats), VECTOR_SEARCH(if the user wants to find similarities between items, keywords or things relating to this.), ONLY OUTPUT THE KEYWORD WITHOUT EXPLANATION. Prompt: ' || user_query,
                    connection_id => 'us.test_connection',
                    endpoint => 'gemini-2.5-flash'
                ).result AS route
                FROM
                (SELECT @prompt AS user_query);
          '''

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("prompt", "STRING", user_prompt)
            ]
        )

        conn = BigQueryCONN()
        client = conn.bigquery_client()
        logging.info("Connected To BigQuery")

        query_job = client.query(query, job_config=job_config)

        for row in query_job.result():
            logging.info(f"Classifier Response: {row["route"]}")
            prompt_class = row["route"]
            return prompt_class
        else:
            logging.warning("No classification returned")
            return None

    except Exception as e:
        logging.error(f"Failed To Classify Query Error: {e}")
        return None

