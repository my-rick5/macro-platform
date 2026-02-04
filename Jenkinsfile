pipeline {
    agent any

    stages {
        stage('Build & Clean') {
            steps {
                // We keep volumes but clean orphans to ensure named volume persists
                sh 'docker compose build'
            }
        }

        stage('Full Pipeline') {
            steps {
                withCredentials([string(credentialsId: 'fred-api-key', variable: 'FRED_API_KEY')]) {
                    sh '''
                        # 1. THE FIX: Remove any existing containers with these names
                        # This clears the "Conflict" error without deleting the 'mlflow_data' volume
                        docker compose rm -f -s mlflow macro-engine || true
                        
                        # 2. Start MLflow
                        docker compose up -d mlflow
                        
                        # 3. Run the engine
                        docker compose run \
                          -e FRED_API_KEY=$FRED_API_KEY \
                          -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
                          macro-engine sh -c "
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

    post {
        always {
            // STOP the engine to save resources, but do NOT 'down' the whole project.
            // This keeps the mlflow_server container running for you to view.
            sh 'docker compose stop macro-engine || true'
        }
    }
}   