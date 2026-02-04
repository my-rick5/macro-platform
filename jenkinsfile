pipeline {
    agent any // Or 'docker' if your Jenkins node has Docker installed

    environment {
        FRED_API_KEY = credentials('fred-api-key')
        DB_PATH = "${WORKSPACE}/data/macro_warehouse.db"
    }

    stages {
        stage('Checkout') {
            steps {
                sh "git config --global --add safe.directory /app"
        	checkout scm
            }
        }

        stage('Build Image') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Test Data (dbt)') {
            steps {
                // We run dbt tests to ensure FRED didn't send us garbage
                sh 'docker compose run macro-engine sh -c "cd dbt_macro && dbt test"'
            }
        }

        stage('Run Forecast') {
            steps {
                // If tests pass, run the actual model
                sh 'docker compose up macro-engine'
            }
        }

        stage('Archive Results') {
            steps {
                // Save the PNG chart so you can see it in the Jenkins UI
                archiveArtifacts artifacts: 'notebooks/*.png', fingerprint: true
            }
        }
    }
}
