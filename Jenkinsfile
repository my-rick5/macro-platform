pipeline {
    agent any

    stages {
        stage('Build Image') {
            steps {
                // Force a rebuild to ensure the scripts are actually in the image
                sh 'docker compose build --no-cache'
            }
        }

        stage('Full Pipeline') {
            steps {
                withCredentials([string(credentialsId: 'fred-api-key', variable: 'FRED_API_KEY')]) {
                    sh '''
                        # 1. Completely remove everything, including orphan volumes
                        docker compose down -v --remove-orphans || true
                        
                        # 2. Run with --no-deps and relative paths to bypass compose volume logic
                        docker compose run --no-deps \
                          -e FRED_API_KEY=$FRED_API_KEY \
                          -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
                          macro-engine sh -c "
                            echo '--- DIAGNOSTIC: Where am I? ---'
                            pwd
                            echo '--- DIAGNOSTIC: What is in this directory? ---'
                            ls -la
                            echo '--- DIAGNOSTIC: Is there a scripts folder? ---'
                            ls -la scripts || echo 'NO SCRIPTS FOLDER FOUND'
                            
                            python scripts/fred_ingestion.py && \
                            cd dbt_macro && \
                            dbt run --profiles-dir . && \
                            cd .. && \
                            python scripts/bvar_ultra.py
                        "
                    '''
                    sh 'docker compose run macro-engine python scripts/fred_ingestion.py'
                }
            }
        }
    }

    post {
        always {
            // Ensure containers are stopped after the run
            sh 'docker compose down || true'
        }
    }
}