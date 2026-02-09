pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'macro-engine-local:latest'
    }

    stages {
        stage('Initialize') {
            steps {
                echo "🧹 Targeted cleanup & Prepping Build Tools..."
                script {
                    sh "docker ps -a -q --filter ancestor=${DOCKER_IMAGE} | xargs -r docker rm -f"
                    sh "mkdir -p results models"
                    
                    // Install GCC and SuiteSparse inside the container environment
                    // We run this as a separate 'prep' step or include it in the Run stage
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
                    def workspaceRelPath = WORKSPACE.replace("/var/jenkins_home/", "")
                    
                    sh """
                        docker run --rm --user 0:0 \
                        -v jenkins_home:/var/jenkins_home \
                        -w /var/jenkins_home/${workspaceRelPath} \
                        -e PYTHONPATH=. \
                        ${DOCKER_IMAGE} bash -c '
                            apt-get update && apt-get install -y gcc libsuitesparse-dev && \
                            pip install pytest && \
                            pip install -e pyfrbus/ && \
                            python3 -m pytest tests/test_model_load.py
                        '
                    """
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