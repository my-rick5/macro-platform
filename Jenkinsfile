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
                        
                        # We use ${WORKSPACE} to be absolutely certain of the host path
                        docker compose run \
                          -v ${WORKSPACE}:/app \
                          -e FRED_API_KEY=${FRED_API_KEY} \
                          -e MLFLOW_TRACKING_URI=http://mlflow:5000 \
                          macro-engine sh -c "
                            # Verify pathing before running
                            if [ -d \\"/app/scripts\\" ]; then
                                echo 'Found scripts directory';
                            else
                                echo 'ERROR: scripts directory not found at /app/scripts';
                                ls -la /app;
                                exit 1;
                            fi
                            
                            python /app/scripts/fred_ingestion.py && \
                            cd /app/dbt_macro && \
                            dbt run --profiles-dir . && \
                            cd /app && \
                            python /app/scripts/bvar_ultra.py
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