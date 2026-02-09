pipeline {
    agent any
    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results data && chmod 777 results data"
                sh "rm -f results/* data/*"
            }
        }
        stage('Process Data') {
            steps {
                // Ensure absolute paths for volumes
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/data:/home/spark/data -v ${WORKSPACE}/results:/home/spark/results macro-engine-local:latest python3 src/fetch_tealbook.py"
            }
        }
        stage('Unit Tests') {
            steps {
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/results:/home/spark/results macro-engine-local:latest pytest tests/ --junitxml=results/test-reports.xml"
            }
        }
    }
    post {
        always {
            script {
                // Explicitly archive from the local relative directory
                junit testResults: 'results/test-reports.xml', allowEmptyResults: true
                archiveArtifacts artifacts: 'data/*.csv, results/*.xml', allowEmptyArchive: true
            }
        }
        cleanup {
            // Only nuke the files AFTER archiving is done
            sh "rm -rf data/* results/*"
        }
    }
}