pipeline {
    agent any 

    stages {
        stage('Full Pipeline') {
            steps {
                // The opening curly brace starts the 'body'
                withCredentials([string(credentialsId: 'FRED_API_KEY', variable: 'FRED_API_KEY')]) {
                    sh '''
                        docker compose run \
                          -e FRED_API_KEY=${FRED_API_KEY} \
                          -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
                          macro-engine sh -c "
                            mkdir -p /app/data/raw /app/notebooks && \
                            python scripts/fred_ingestion.py && \
                            cd dbt_macro && \
                            dbt run --profiles-dir . && \
                            cd .. && \
                            python scripts/bvar_ultra.py
                        "
                    '''
                } // The closing curly brace ends the 'body'
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