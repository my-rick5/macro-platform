pipeline {
    agent any

    environment {
        // Load the FRED API Key from Jenkins Credentials
        FRED_API_KEY = credentials('FRED_API_KEY')
        // Internal Docker network URI for MLflow
        MLFLOW_TRACKING_URI = "http://mlflow:5000"
    }

    stages {
        stage('Initialize') {
            steps {
                // Ensure environment file exists for Docker Compose
                sh 'touch .env'
            }
        }

        stage('Build Image') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Run Full Pipeline') {
            steps {
                sh '''
                    docker compose run \
                      -e FRED_API_KEY=${FRED_API_KEY} \
                      -e MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI} \
                      macro-engine sh -c "
                        # 1. Create necessary output directories
                        mkdir -p /app/data/raw /app/notebooks && \
                        
                        # 2. Ingest raw data from FRED
                        python scripts/fred_ingestion.py && \
                        
                        # 3. Transform data with dbt
                        cd dbt_macro && \
                        dbt run --profiles-dir . && \
                        cd .. && \
                        
                        # 4. Execute BVAR model and log to MLflow
                        python scripts/bvar_ultra.py
                    "
                '''
            }
        }
    }

    post {
        always {
            // Optional: Spin down containers to free up resources
            sh 'docker compose down'
        }
        failure {
            echo "Pipeline failed. Check the MLflow connection or FRED API quotas."
        }
    }
}