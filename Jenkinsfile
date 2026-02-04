pipeline {
    agent any 

    stages {
        stage('Full Pipeline') {
            // We use withCredentials inside the stage to ensure it's tightly scoped
            steps {
                withCredentials([string(credentialsId: 'af3b122c380f66ec4808d665e80786a7', variable: 'FRED_API_KEY')])
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
                }
            }
        }
    }

    // Moving post-actions inside the pipeline ensures they have the right context
    post {
        always {
            // This ensures we clean up containers even if the script fails
            sh 'docker compose down || true'
        }
        failure {
            echo "Pipeline failed. Check FRED API key validity or MLflow server status."
        }
    }
}