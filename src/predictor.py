import joblib
from src.data_loader import BigQueryCONN
import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(level = logging.INFO)

def Prediction():
    ''' Function To Predict Subscores and Ecoscore
    Returns: Predictions
    '''
    try:
            logging.info('Prediction For Scores In Progress')
            conn = BigQueryCONN()
            client = conn.bigquery_client()


            query = f"""
                SELECT *
                FROM `ecochain123.supplychain.suppliers_with_images`
                WHERE total_eco_score IS NULL
                ORDER BY supplier_id DESC
                LIMIT 1
            """
            df = client.query(query).to_dataframe()
            logging.info(f"Data retrieved: {df.shape}")

            if df.empty:
                logging.info("No new suppliers to predict.")
                return []

            supplier_ids = df['supplier_id'].tolist()
            supplier = df.drop(columns=[
                'supplier_id','supplier_name','audit_summary','image_url',
                'certification','sub_category','product_category',
                'recommendation','carbon_score','water_score','waste_score','social_score',
                'total_eco_score'
            ])

            # Load encoder
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            PROJECT_ROOT = os.path.dirname(BASE_DIR)
            encoder_path = os.path.join(PROJECT_ROOT, 'models', 'Encoder_V1.pkl')
            encoder = joblib.load(encoder_path)
            supplier[['country','region','partnership_status','risk_level']] = encoder.transform(
                supplier[['country','region','partnership_status','risk_level']]
            )
            logging.info("Data encoded successfully")


            logging.info('Preprocessing In Progress')
            # Preprocessing
            supplier['last_audit'] = supplier['last_audit'].str.replace("-", "", regex=False)
            supplier['last_audit'] = pd.to_numeric(supplier['last_audit'], errors='coerce')
            supplier['text_embedding'] = supplier['text_embedding'].apply(lambda e: list(map(float, e)))
            embeddings = np.vstack(supplier['text_embedding'].values).astype(np.float32)
            supplier_num = supplier.drop(columns=['text_embedding']).reset_index(drop=True)
            X_final = np.hstack([supplier_num.values, embeddings])


            logging.info('Predicting Subscores')
            subscores_model = joblib.load(os.path.join(PROJECT_ROOT, 'models', 'SubScores_V1.pkl'))
            subscores = subscores_model.predict(X_final)
            subscores_df = pd.DataFrame(subscores, columns=['carbon_score','water_score','waste_score','social_score'])
            logging.info('Subscores Predicted Successfully')

            logging.info('Predicting EcoScore in Progress')
            # Predict ecoscore
            ecoscore_model = joblib.load(os.path.join(PROJECT_ROOT, 'models', 'Ecoscore_V1.pkl'))
            ecoscores = ecoscore_model.predict(subscores_df)
            subscores_df['ecoscore'] = ecoscores
            subscores_df['supplier_id'] = supplier_ids
            logging.info(f"EcoScores predicted:\n{subscores_df.head()}")
            return subscores_df.to_dict(orient='records')

    except Exception as e:
            logging.error(f"Failed to predict ecoscores: {e}")
            raise





