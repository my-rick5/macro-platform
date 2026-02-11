pipeline {
    agent any

    environment {
        PYTHONPATH = "/opt/macro_platform:/home/spark/.local/lib/python3.9/site-packages"
    }

    stages {
        stage('Initialize') {
            steps {
                sh "mkdir -p results models data"
                // || true prevents failure if the container doesn't exist yet
                sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
            }
        }

        stage('Build Image') {
            steps {
                // Ensure your .dockerignore no longer blocks .csv files
                sh "docker build -t macro-engine-image ."
            }
        }

        stage('Debug File System') {
            steps {
                echo "--- Host View (Jenkins Workspace) ---"
                sh "ls -R"
                
                // Spin up container in detached mode to allow exec
                sh "docker run -d --name engine-run-${env.BUILD_NUMBER} -v \$(pwd):/home/spark macro-engine-image sleep 100"
                
                echo "--- Container View ---"
                // Correctly references the current build's container
                sh "docker exec engine-run-${env.BUILD_NUMBER} ls -R /home/spark"
            }
        }

        stage('Run Engine') {
            steps {
                echo "🚀 Running Model Calibration..."
                sh "docker exec -w /home/spark -e PYTHONPATH=${env.PYTHONPATH} engine-run-${env.BUILD_NUMBER} python3 /home/spark/src/engine.py"
            }
        }
    }

    post {
        always {
            script {
                echo "🧹 Cleaning up container..."
                sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
            }
            echo "📦 Archiving Results..."
            archiveArtifacts artifacts: 'results/*.csv', allowEmptyArchive: true
        }
        success {
            echo "🟢 Calibration Successful!"
        }
        failure {
            echo "🔴 Pipeline Failed. Check the Debug output above for missing files or path issues."
        }
    }
}