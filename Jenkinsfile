pipeline {
    agent any
    
    parameters {
        choice(name: 'BACKTEST_YEAR', 
               choices: ['2004', '2005', '2006', '2007', '2008'], 
               description: 'Select the year for the Tealbook backtest.')
    }

    environment {
        IMAGE_NAME = "macro-engine-local"
    }

    stages {
        stage('Initialize') {
            steps {
                // Ensure directories exist and are fresh
                sh "mkdir -p results data"
                sh "chmod 777 results data"
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
                echo "Running Data Fetch for ${params.BACKTEST_YEAR}..."
                // --user 0:0 ensures root-level write access to the host-mounted volume
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
                // Generates the XML report that Jenkins needs for the UI
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
            // Archive while the files are guaranteed to still be in the workspace
            junit testResults: 'results/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'results/*.csv, data/*.txt', allowEmptyArchive: true
            echo "🏁 Build successful! Artifacts and test reports have been recorded."
        }
        
        failure {
            echo "❌ Build failed. Checking logs for permission or data errors."
        }

        cleanup {
            // This runs LAST. It safely wipes the workspace AFTER archiving is finished.
            echo "🧹 Cleaning up workspace directories..."
            sh "rm -rf data/* results/*"
        }
    }
}