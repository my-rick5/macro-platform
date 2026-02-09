pipeline {
    agent any
    
    parameters {
        choice(name: 'BACKTEST_YEAR', 
               choices: ['2004', '2005', '2006', '2007', '2008', '2024'], 
               description: 'Select the year for the Tealbook backtest simulation.')
    }

    environment {
        IMAGE_NAME = "macro-engine-local"
    }

        stage('Initialize') {
            steps {
                // Create the directories on the host first
                sh "mkdir -p results data"
                // Grant global write permissions so the Docker user (spark) can create subfolders
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
                echo "Pulling Tealbook data via Docker..."
                sh """
                    docker run --rm \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    ${IMAGE_NAME}:latest python3 src/fetch_tealbook.py
                """
            }
        }

        stage('Unit Tests') {
            steps {
                // Mount results so Jenkins can grab the XML report
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
                sh """
                    docker run --rm \
                    -v ${WORKSPACE}/results:/home/spark/results \
                    -v ${WORKSPACE}/data:/home/spark/data \
                    -e CLOUD_RUN_TASK_INDEX=${Integer.parseInt(params.BACKTEST_YEAR) - 2004} \
                    ${IMAGE_NAME}:latest python3 src/engine.py
                """
            }
        }
    }

    post {
        success {
            // Artifacts are archived BEFORE the workspace is cleaned
            archiveArtifacts artifacts: 'results/*.csv', fingerprint: true, allowEmptyArchive: true
            echo "🏁 Build successful! Results archived."
        }
        always {
            // Clean up the workspace so we don't leak data between runs
            echo "🧹 Cleaning up workspace directories..."
            sh "rm -rf data/* results/*"
        }
    }
}