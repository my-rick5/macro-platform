pipeline {
    agent any 
    parameters {
        choice(name: 'BACKTEST_YEAR', choices: ['2004', '2005', '2006', '2007', '2008', '2024'], description: 'Main branch only.')
    }
    environment { IMAGE_NAME = "macro-engine-local" }

    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results && rm -f results/*.csv"
            }
        }
        stage('Docker Build') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:latest ."
            }
        }
        stage('Fetch Macro Data') {
            steps {
                echo "Pulling latest Tealbook projections..."
                // Run the fetcher on the Jenkins agent
                sh "python3 src/fetch_tealbook.py"
            }
        }
        stage('Unit Tests') {
            steps {
                sh "docker run --rm ${IMAGE_NAME}:latest pytest tests/ --junitxml=results/test-reports.xml"
            }
            post { always { junit 'results/test-reports.xml' } }
        }
        stage('Production Simulation') {
            when { branch 'main' }
            steps {
                script {
                    def taskIndex = Integer.parseInt(params.BACKTEST_YEAR) - 2004
                    sh "docker run --rm -u \$(id -u):\$(id -g) -v ${WORKSPACE}/results:/home/spark/results -e CLOUD_RUN_TASK_INDEX=${taskIndex} ${IMAGE_NAME}:latest python3 src/engine.py"
                }
            }
        }
    }
    post {
        success {
            script {
                if (env.BRANCH_NAME == 'main') {
                    archiveArtifacts artifacts: 'results/*.csv', allowEmptyArchive: true
                }
            }
        }
        always { sh "docker rmi ${IMAGE_NAME}:latest || true" }
    }
}