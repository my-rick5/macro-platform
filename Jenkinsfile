pipeline {
    agent any
    
    parameters {
        choice(name: 'BACKTEST_YEAR', 
               choices: ['2004', '2005', '2006', '2007', '2008'], 
               description: 'Tealbook Year for Simulation')
    }

    environment {
        IMAGE_NAME = "macro-engine-local"
    }

    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results data"
                sh "chmod 777 results data"
                sh "rm -f results/*.csv data/*.txt results/*.xml"
            }
        }

        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Fetch Macro Data') {
            steps {
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/data:/home/spark/data ${IMAGE_NAME}:latest python3 src/fetch_tealbook.py"
            }
        }

        stage('Unit Tests') {
            steps {
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/results:/home/spark/results ${IMAGE_NAME}:latest pytest tests/ --junitxml=results/test-reports.xml"
            }
        }

        stage('Production Simulation') {
            when { branch 'main' }
            steps {
                script {
                    def taskIndex = params.BACKTEST_YEAR.toInteger() - 2004
                    sh "docker run --rm --user 0:0 -v ${WORKSPACE}/results:/home/spark/results -v ${WORKSPACE}/data:/home/spark/data -e CLOUD_RUN_TASK_INDEX=${taskIndex} ${IMAGE_NAME}:latest python3 src/engine.py"
                }
            }
        }
    }

    post {
        always {
            // Fix: Changed allowEmptyResults to allowEmptyArchive for artifacts
            junit testResults: 'results/*.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'results/*.csv, data/*.txt', allowEmptyArchive: true
            
            echo "🧹 Cleaning up workspace..."
            sh "rm -f results/* data/*"
        }
    }
}