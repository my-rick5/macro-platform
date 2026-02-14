pipeline {
    agent any

    parameters {
        booleanParam(name: 'REBUILD_BASE', defaultValue: false, description: 'Check this to force a rebuild of the macro-engine-base image.')
    }
    
    environment {
        BASE_IMAGE = "macro-engine-base:latest"
        APP_IMAGE  = "macro-engine-app:${env.BUILD_NUMBER}"
        // Updated home directory to match your new Dockerfile structure
        APP_HOME   = "/home/app"
    }

    stages {

        stage('Clean') {
            steps {
                cleanWs()
            }
        }
        
        stage('🛠️ Setup Base Image') {
            steps {
                script {
                    // Check if image exists locally
                    def baseExists = sh(script: "docker images -q ${BASE_IMAGE}", returnStdout: true).trim()
                    
                    if (params.REBUILD_BASE || baseExists == "") {
                        echo "🚀 Building/Refreshing Base Image (This takes ~3 mins)..."
                        sh "docker build --no-cache -t ${BASE_IMAGE} -f Dockerfile.base ."
                    } else {
                        echo "✅ Base image found. Skipping heavy install stage."
                    }
                }
            }
        }

        stage('📦 Build App') {
            steps {
                echo "⚡ Building App Layer (This should take < 10s)..."
                sh "docker build -t ${APP_IMAGE} ."
            }
        }

        stage('🧪 Run Engine') {
            steps {
                // Run the container using the build number as a unique identifier
                sh "docker run --name engine-${env.BUILD_NUMBER} ${APP_IMAGE}"
            }
            post {
                always {
                    echo "📥 Extracting Results and Diagnostics..."
                    // Updated paths from /home/spark to /home/app (via ${APP_HOME})
                    sh "docker run --entrypoint /bin/sh ${APP_IMAGE} -c 'ls -R /home/app'"
                    sh "docker cp engine-${env.BUILD_NUMBER}:${env.APP_HOME}/results/. ./results/ || true"
                    sh "docker cp engine-${env.BUILD_NUMBER}:${env.APP_HOME}/external_data/. ./debug_data/ || true"
                    sh "docker rm engine-${env.BUILD_NUMBER}"
                }
            }
        }
    }

    post {
        success {
            // Updated to ensure it looks in the workspace directories we just copied into
            archiveArtifacts artifacts: 'results/*.csv, debug_data/*.csv', allowEmptyArchive: true, fingerprint: true
            echo "🏁 Calibration Complete. Check Artifacts for residuals."
        }
        failure {
            echo "❌ Build Failed. Check the 'Run Engine' logs for solver errors."
        }
    }
}