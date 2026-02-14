pipeline {
    agent any

    parameters {
        booleanParam(name: 'REBUILD_BASE', defaultValue: false, description: 'Check this to force a rebuild of the macro-engine-base image.')
    }
    
    environment {
        BASE_IMAGE = "macro-engine-base:latest"
        APP_IMAGE  = "macro-engine-app:${env.BUILD_NUMBER}"
        APP_HOME   = "/home/app"
    }

    stages {
        stage('🛠️ Setup Base Image') {
            steps {
                script {
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
                echo "⚡ Building App Layer..."
                sh "docker build -t ${APP_IMAGE} ."
            }
        }

        stage('🧪 Run Engine') {
            steps {
                // Ensure local workspace directories exist for the 'cp' command later
                sh "mkdir -p results debug_data"
                
                // Run the container
                sh "docker run --name engine-${env.BUILD_NUMBER} ${APP_IMAGE}"
            }
            post {
                always {
                    echo "📥 Extracting Results and Diagnostics..."
                    // Fixed: Copying from container to the local workspace folders we just created
                    sh "docker cp engine-${env.BUILD_NUMBER}:${env.APP_HOME}/results/. ./results/ || echo 'Warning: Results folder not found in container'"
                    sh "docker cp engine-${env.BUILD_NUMBER}:${env.APP_HOME}/external_data/. ./debug_data/ || echo 'Warning: Debug data not found'"
                    
                    // Cleanup the container to keep the agent disk clean
                    sh "docker rm -f engine-${env.BUILD_NUMBER}"
                }
            }
        }
    }

    post {
        success {
            // FIXED SYNTAX: Multiple patterns in a single comma-separated string
            archiveArtifacts artifacts: 'results/*.csv, results/*.png', 
                             allowEmptyArchive: true, 
                             fingerprint: true
                             
            echo "🏁 Calibration Complete. Check Artifacts for residuals."
        }
        failure {
            echo "❌ Build Failed. Check the 'Run Engine' logs for solver errors."
        }
    }
}