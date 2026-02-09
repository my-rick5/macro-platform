pipeline {
    agent any
    parameters {
        choice(name: 'BACKTEST_YEAR', choices: ['2004', '2005', '2006'], description: 'Year')
    }
    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results data && chmod 777 results data"
                sh "rm -f results/* data/*"
            }
        }
        stage('Docker Build') {
            steps { sh "docker build -t macro-engine-local:latest ." }
        }
        stage('Process Data') {
            steps {
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
                // Give the filesystem a moment to sync from the Docker volume
                sh "sleep 2" 
                // Archive using the direct workspace path
                junit testResults: '**/test-reports.xml', allowEmptyResults: true
                archiveArtifacts artifacts: '**/tealbook_unemployment.csv, **/add_factors_*.txt', allowEmptyArchive: true
            }
        }
        cleanup {
            sh "rm -rf data/* results/*"
        }
    }
}