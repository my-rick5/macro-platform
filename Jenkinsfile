pipeline {
    agent any
    
    environment {
        // Ensuring your API key is available to the shell
        FRED_API_KEY = credentials('fred-api-key')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                // Create a blank .env file so Docker Compose doesn't panic
                sh 'touch .env' 
            }
        }

        stage('Build Image') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Test Data (dbt)') {
            steps {
                // Now we can run standard compose commands
                sh 'docker compose run macro-engine dbt test --project-dir dbt_macro --profiles-dir dbt_macro'
            }
        }
        
        stage('Run Forecast') {
            steps {
                sh 'docker compose run macro-engine sh -c "mkdir -p /app/data && python scripts/bvar_ultra.py"'
            }
        }
    }
}
