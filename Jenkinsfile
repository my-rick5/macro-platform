pipeline {
    agent any
    
    parameters {
        choice(name: 'BACKTEST_YEAR', 
               choices: ['2004', '2005', '2006', '2007', '2008'], 
               description: 'Select Tealbook Year')
    }

    environment {
        IMAGE_NAME = "macro-engine-local"
    }

    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results data"
                sh "chmod 777 results data"
                // Clean only at start to ensure a fresh run
                sh "rm -f results/* data/*"
            }
        }

        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Fetch & Process Data') {
            steps {
                // Using root to ensure the container can write to host-mounted volumes
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    ${IMAGE_NAME}:latest python3 src/fetch_tealbook.py
                """
            }
        }

        stage('Unit Tests') {
            steps {
                sh """
                    docker run --rm --user 0:0 \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    ${IMAGE_NAME}:latest pytest tests/ --junitxml=results/test-reports.xml
                """
            }
        }
    }

    post {
        success {
            // Archive results while they still exist
            junit testResults: 'results/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'results/*.csv, data/*.txt', allowEmptyArchive: true
            echo "🏁 Build successful! Artifacts archived."
        }
        cleanup {
            // This block runs AFTER success/failure blocks, ensuring files aren't deleted too early
            echo "🧹 Cleaning up workspace directories..."
            sh "rm -rf data/* results/*"
        }
    }
}