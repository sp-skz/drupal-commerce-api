from pandas_gbq import to_gbq
from src.drupal_api import get_drupal_commerce_orders
from src.error_report import ErrorReport
import os
from google.cloud import bigquery
from google.auth import default
from google.oauth2 import service_account

try:
    df = get_drupal_commerce_orders()
    
except Exception as e:
        error=ErrorReport()
        error.add_name('Error Downloading Funeflor Orders data')
        error.add_message(f'Error:  {str(e)}')
        error.send()

try: 
        # Determine environment and set up BigQuery client
    try:
        # Running in Google Cloud (Production) - Use default credentials
        credentials, project_id = default()
        
    except:
        # Running locally (Development) - Load service account credentials
        credentials = service_account.Credentials.from_service_account_file("./credentials/memora-224414-3c89b4686c80.json")
        project_id = credentials.project_id
    
    to_gbq(df, os.getenv('GC_TABLE'), project_id=os.getenv('GC_PROJECT'), if_exists='replace', credentials=credentials)

except Exception as e:
        error=ErrorReport()
        error.add_name('MSP Force Manager Synchronization Error!!!!')
        error.add_message(f'Error:  {str(e)}')
        error.send()