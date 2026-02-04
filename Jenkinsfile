pipeline {
    agent any 

    stages {
        stage('Build Image') {
            steps {
                // This ensures the image actually contains your latest code
                sh 'docker compose build --no-cache'
            }
        }

        stage('Full Pipeline') {
            steps {
                withCredentials([string(credentialsId: 'fred-api-key', variable: 'FRED_API_KEY')]) {
                    sh '''
                        docker compose down --remove-orphans || true
                        
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
    }

    post {
        always {
            sh 'docker compose down || true'
        }
    }
}