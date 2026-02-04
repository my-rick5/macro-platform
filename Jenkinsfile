pipeline {
    agent any 

    stages {
        stage('Full Pipeline') {
            steps {
                // The opening curly brace starts the 'body'
                withCredentials([string(credentialsId: 'fred-api-key', variable: 'FRED_API_KEY')]) {
                    sh '''
                        docker compose down --remove-orphans || true
                        
                        # Remove the -v $(pwd):/app mount so we use the code baked into the image
                        docker compose run \
                          -e FRED_API_KEY=${FRED_API_KEY} \
                          -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
                          macro-engine sh -c "
                            mkdir -p scripts data/raw notebooks dbt_macro && \
                            python scripts/fred_ingestion.py && \
                            cd dbt_macro && \
                            dbt run --profiles-dir . && \
                            cd .. && \
                            python scripts/bvar_ultra.py
                        "
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker compose down || true'
        }
        failure {
            echo "Pipeline failed. Check FRED API key ID or MLflow connectivity."
        }
    }
}