pipeline {
    agent any

    stages {
        stage('Build & Clean') {
            steps {
                // Build the image to ensure the latest Python scripts are baked in
                sh 'docker compose build'
            }
        }

        stage('Full Pipeline') {
            steps {
                withCredentials([string(credentialsId: 'fred-api-key', variable: 'FRED_API_KEY')]) {
                    sh '''
                        # 1. CLEANUP OLD CONTAINERS (The Fix for Build #64)
                        # This stops and removes old containers to prevent name conflicts,
                        # but keeps the mlflow_data volume intact.
                        docker compose rm -f -s mlflow macro-engine || true
                        
                        # 2. START MLFLOW SERVER
                        # Starts in background (-d) so it stays alive for viewing
                        docker compose up -d mlflow
                        
                        # 3. RUN THE MACRO ENGINE
                        # We use 'run' to execute the pipeline steps sequentially.
                        # Since volumes were removed from compose, it uses the internal image files.
                        docker compose run \
                          -e FRED_API_KEY=$FRED_API_KEY \
                          -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
                          macro-engine sh -c "
                            mkdir -p notebooks && \
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
            // We only STOP the engine to free up memory.
            // We do NOT use 'down' so that the mlflow_server remains reachable.
            sh 'docker compose stop macro-engine || true'
        }
    }
}