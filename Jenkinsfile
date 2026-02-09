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
                sh "cp pyfrbus/models/model.xml ./model.xml"
            }
        }

        stage('Run Engine') {
            steps {
                echo "🧪 Running Structural Validation..."
                script {
                    def workspaceRelPath = WORKSPACE.replace("/var/jenkins_home/", "")
                    
                    // 1. Install system deps (including SWIG), install pyfrbus, and run tests
                    sh """
                        docker run --rm --user 0:0 \
                        -v jenkins_home:/var/jenkins_home \
                        -w /var/jenkins_home/${workspaceRelPath} \
                        -e PYTHONPATH=. \
                        ${DOCKER_IMAGE} bash -c '
                            apt-get update && \
                            apt-get install -y gcc libsuitesparse-dev swig libblas-dev && \
                            pip install pytest && \
                            pip install -e pyfrbus/ && \
                            python3 -m pytest tests/test_model_load.py
                        '
                    """

                    echo "🚀 Running Engine: Solving for Add Factors (e)..."
                    // 2. Run the actual engine script
                    sh """
                        docker run --rm --user 0:0 \
                        --memory='6g' --memory-swap='6g' \
                        -v jenkins_home:/var/jenkins_home \
                        -w /var/jenkins_home/${workspaceRelPath} \
                        -e PYTHONPATH=. \
                        ${DOCKER_IMAGE} python3 src/engine.py
                    """
                }
            }
        }
    } // End of stages

    post {
        always {
            echo "📦 Archiving Build Artifacts..."
            archiveArtifacts artifacts: 'results/*.csv, models/*.xml', allowEmptyArchive: true
        }
    }
}