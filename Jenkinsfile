pipeline {
    agent any
    
    parameters {
        choice(name: 'BACKTEST_YEAR', 
               choices: ['2004', '2005', '2006', '2007', '2008', '2020'], 
               description: 'Select the year for the Tealbook backtest simulation.')
    }

    environment {
        IMAGE_NAME = "macro-engine-local"
    }

    stages {
        stage('Initialize') {
            steps {
                // Fix: Create directories and grant write access so the Docker 'spark' user 
                // doesn't hit a Permission Denied error when creating subfolders.
                sh "mkdir -p results data"
                sh "chmod 777 results data"
                sh "rm -f results/*.csv"
            }
        }

        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Fetch Macro Data') {
            steps {
                echo "Pulling Tealbook data and Narrative PDFs for ${params.BACKTEST_YEAR}..."
                sh """
                    docker run --rm \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    ${IMAGE_NAME}:latest python3 src/fetch_tealbook.py
                """
            }
        }

        stage('Unit Tests') {
            steps {
                sh """
                    docker run --rm \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    ${IMAGE_NAME}:latest pytest tests/ --junitxml=results/test-reports.xml
                """
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
                echo "Running simulation for year: ${params.BACKTEST_YEAR}"
                script {
                    // Calculate task index (2004 = 0, 2005 = 1, etc.)
                    def taskIndex = params.BACKTEST_YEAR.toInteger() - 2004
                    sh """
                        docker run --rm \
                        -v ${WORKSPACE}/results:/home/spark/results \
                        -v ${WORKSPACE}/data:/home/spark/data \
                        -e CLOUD_RUN_TASK_INDEX=${taskIndex} \
                        ${IMAGE_NAME}:latest python3 src/engine.py
                    """
                }
            }
        }
    }

    post {
        success {
            // Archive the CSV results and the scraped Add-Factor text files
            archiveArtifacts artifacts: 'results/*.csv, data/*.txt', fingerprint: true, allowEmptyArchive: true
            echo "🏁 Build successful! Results and Add-Factors archived."
        }
        always {
            // Cleanup to save disk space, but only AFTER archiving
            echo "🧹 Cleaning up workspace directories..."
            sh "rm -rf data/* results/*"
        }
    }
}