pipeline {
    agent any

    environment {
        // Ensuring the container knows where its own code is
        PYTHONPATH = "/home/spark:/home/spark/src"
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    sh "mkdir -p results data"
                    // Alias Tealbook as Library if needed
                    sh "[ -f data/library.xlsx ] || cp data/tealbook_raw.xlsx data/library.xlsx"
                }
            }
        }

        stage('Build & Run Engine') {
            steps {
                script {
                    sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
                    
                    // Start container as a daemon
                    sh "docker run -d --name engine-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 600"
                    
                    try {
                        echo "⚙️ Preprocessing & Running Model..."
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/preprocess.py"
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/engine.py"
                        
                        echo "🧹 Generating Lite Version & Visuals (Inside Docker)..."
                        sh """
                        docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 -c "
import pandas as pd
import matplotlib.pyplot as plt
import os

# 1. Load the results
file_path = 'results/calibration_residuals_e.csv'
if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    targets = ['LUR', 'XGDP', 'PCE', 'RFF']
    present = [c for c in targets if c in df.columns]

    if present:
        # Create Lite Version
        lite_df = df[present].dropna(how='all').tail(40)
        lite_df.to_csv('results/lite_residuals.csv', index=False)
        
        # Print Stats to Jenkins Console
        print('\\n' + '='*30 + '\\nLITE STATISTICS\\n' + '='*30)
        print(lite_df.describe())
        
        # Create Visuals
        plt.figure(figsize=(10, 6))
        lite_df.plot(marker='o')
        plt.title('Key Macro Residuals (Last 40 Qtrs)')
        plt.ylabel('Residual Value')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig('results/residual_plot.png')
        print('\\n✅ Visuals and Lite CSV created.')
else:
    print('❌ Error: Raw results file not found!')
"
                        """
                        
                        // Copy everything back to the host before cleaning up
                        sh "docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/"
                        
                    } finally {
                        sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
                    }
                }
            }
        }
    }

    post {
        always {
            // This will now find: calibration_residuals_e.csv, lite_residuals.csv, and residual_plot.png
            archiveArtifacts artifacts: 'results/*', allowEmptyArchive: true
        }
    }
}