pipeline {
    agent any

    environment {
        // Automatically detect User ID and Docker Group ID to prevent permission issues
        AIRFLOW_UID = sh(script: 'id -u', returnStdout: true).trim()
        DOCKER_GID  = sh(script: "getent group docker | cut -d: -f3 || echo 999", returnStdout: true).trim()
    }

    stages {
        stage('Cleanup & Build') {
            steps {
                echo "Cleaning up old containers and building the Macro Engine..."
                // Stop containers but keep volumes so MLflow and Airflow DB persist
                sh 'docker compose stop || true'
                sh 'docker compose build macro-engine'
            }
        }

        stage('Initialize Airflow') {
            steps {
                echo "Setting up Airflow environment..."
                sh '''
                    # Create host directories for Airflow persistence
                    mkdir -p dags logs plugins
                    
                    # Ensure Postgres is up before initializing
                    docker compose up -d postgres
                    
                    # Initialize Airflow Metadata Database
                    docker compose run --rm airflow-webserver airflow db init
                    
                    # Create Admin User (admin/admin) - ignore error if user exists
                    docker compose run --rm airflow-webserver \
                        airflow users create \
                        --username admin \
                        --password admin \
                        --firstname Zach \
                        --lastname Myrick \
                        --role Admin \
                        --email zach@example.com || true
                '''
            }
        }

        stage('Deploy Stack') {
            steps {
                echo "Launching Full Stack..."
                sh 'docker compose up -d'
                
                script {
                    echo "========================================================="
                    echo "DEPLOYMENT SUCCESSFUL"
                    echo "Jenkins UI:   http://localhost:8080"
                    echo "Airflow UI:   http://localhost:8085 (User: admin / Pass: admin)"
                    echo "MLflow UI:    http://localhost:5000"
                    echo "========================================================="
                }
            }
        }
    }

    post {
        failure {
            echo "Deployment failed. Run 'docker compose logs' on the server to debug."
        }
    }
}