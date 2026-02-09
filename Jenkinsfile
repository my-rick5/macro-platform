pipeline {
    agent any
    
    parameters {
        choice(name: 'BACKTEST_YEAR', choices: ['2004', '2005', '2006', '2020'], description: 'Tealbook Year')
    }

    environment {
        IMAGE_NAME = "macro-engine-local"
    }

    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results data"
                sh "chmod 777 results data"
                sh "rm -f results/*.csv data/*.txt"
            }
        }

        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Fetch Macro Data') {
            steps {
                // Using root (0:0) to ensure we can write to host-mounted volumes
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/data:/home/spark/data ${IMAGE_NAME}:latest python3 src/fetch_tealbook.py"
            }
        }

        stage('Unit Tests') {
            steps {
                // Fixed: Added --user 0:0 so pytest can write the .xml report
                sh "docker run --rm --user 0:0 -v ${WORKSPACE}/results:/home/spark/results ${IMAGE_NAME}:latest pytest tests/ --junitxml=results/test-reports.xml"
            }
            post {
                always {
                    junit 'results/test-reports.xml'
                }
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
        success {
            archiveArtifacts artifacts: 'results/*.csv, data/*.txt', fingerprint: true
        }
        always {
            sh "rm -rf data/* results/*"
        }
    }
}