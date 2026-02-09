pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
    }

    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Targeted cleanup..."
                script {
                    sh "docker ps -a -q --filter ancestor=${DOCKER_IMAGE} | xargs -r docker rm -f"
                    sh "mkdir -p results models"
                }
            }
        }

        stage('Fetch Model Logic') {
            steps {
                echo "🧠 Isolating model.xml..."
                // Based on your tree: pyfrbus/models/model.xml exists
                sh "cp pyfrbus/models/model.xml ./model.xml"
            }
        }

        stage('Run Engine') {
            steps {
                echo "🧪 Running Structural Validation..."
                script {
                    // We use the 'jenkins_home' volume name instead of the path
                    // and point it to the specific workspace sub-folder
                    def workspaceRelPath = WORKSPACE.replace("/var/jenkins_home/", "")
                    
                    sh """
                        docker run --rm --user 0:0 \
                        -v jenkins_home:/var/jenkins_home \
                        -w /var/jenkins_home/${workspaceRelPath} \
                        ${DOCKER_IMAGE} bash -c 'pip install pytest && python3 -m pytest tests/test_model_load.py'
                    """
                    
                    echo "🚀 Running Engine: Solving for Add Factors (e)..."
                    sh """
                        docker run --rm --user 0:0 \
                        --memory='6g' --memory-swap='6g' \
                        -v jenkins_home:/var/jenkins_home \
                        -w /var/jenkins_home/${workspaceRelPath} \
                        ${DOCKER_IMAGE} python3 src/engine.py
                    """
                }
            }
        }
    }

    post {
        always {
            echo "📦 Archiving Build Artifacts..."
            archiveArtifacts artifacts: 'results/*.csv, models/*.xml', allowEmptyArchive: true
        }
    }
}