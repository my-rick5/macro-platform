pipeline {
    agent any

    parameters {
        booleanParam(name: 'REBUILD_BASE', defaultValue: false, description: 'Check this to force a rebuild of the macro-engine-base image.')
    }
    
    environment {
        BASE_IMAGE = "macro-engine-base:latest"
        APP_IMAGE  = "macro-engine-app:${env.BUILD_NUMBER}"
        SPARK_HOME = "/home/spark"
    }

    stages {
        stage('🛠️ Setup Base Image') {
            steps {
                script {
                    // Check if image exists locally
                    def baseExists = sh(script: "docker images -q ${BASE_IMAGE}", returnStdout: true).trim()
                    
                    if (params.REBUILD_BASE || baseExists == "") {
                        echo "🚀 Building/Refreshing Base Image (This takes ~3 mins)..."
                        // Ensure Dockerfile.base is in your root directory
                        sh "docker build --no-cache -t ${BASE_IMAGE} -f Dockerfile.base ."
                    } else {
                        echo "✅ Base image found. Skipping heavy install stage."
                    }
                }
            }
        }

        stage('Fetch Tealbook') {
            agent {
                docker { 
                    image 'macro-engine-base:latest' // Use the image from Build #831
                    reuseNode true
                }
            }
            steps {
                // This ensures we use the correct python from our base image
                sh "python3 src/fetch_tealbook.py"
            }
        }

        stage('📦 Build App') {
            steps {
                echo "⚡ Building App Layer (This should take < 10s)..."
                // This builds your local Dockerfile which starts 'FROM macro-engine-base:latest'
                sh "docker build -t ${APP_IMAGE} ."
            }
        }

        stage('🧪 Run Engine') {
            steps {
                // We run the container and give it a name based on the build number for easy cleanup
                sh "docker run --name engine-${env.BUILD_NUMBER} ${APP_IMAGE}"
            }
            post {
                always {
                    echo "📥 Extracting Results and Diagnostics..."
                    sh "docker cp engine-${env.BUILD_NUMBER}:${env.SPARK_HOME}/results/. ./results/ || true"
                    sh "docker cp engine-${env.BUILD_NUMBER}:${env.SPARK_HOME}/external_data/. ./debug_data/ || true"
                    sh "docker rm engine-${env.BUILD_NUMBER}"
                }
            }
        }
    }

    post {
        success {
            archiveArtifacts artifacts: 'results/*.csv, debug_data/*.csv', fingerprint: true
            echo "🏁 Calibration Complete. Check Artifacts for residuals."
        }
        failure {
            echo "❌ Build Failed. Check the 'Run Engine' logs for solver errors."
        }
    }
}