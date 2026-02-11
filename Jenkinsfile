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
                    // Build the image using the local context
                    sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
                    
                    // Start container as a daemon
                    sh "docker run -d --name engine-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 600"
                    
                    try {
                        echo "⚙️ Preprocessing & Running Model..."
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/preprocess.py"
                        sh "docker exec -w /home/spark engine-${env.BUILD_NUMBER} python3 src/engine.py"
                        
                        echo "🧹 Generating Lite Version & Visuals (Inside Docker)..."
                        sh """
                        docker exec -i engine-${env.BUILD_NUMBER} python3 -u - <<-EOF
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

file_path = 'results/calibration_residuals_e.csv'
if os.path.exists(file_path):
    df = pd.read_csv(file_path)
    
    # DEBUG: Show exactly what columns the engine produced
    print(f'🔍 Found columns in results: {df.columns.tolist()[:10]}')
    
    # UPDATED: These match verified Greenbook names from your logs
    targets = ['LUR', 'GRGDP', 'GPGDP', 'GPCPI', 'GNGDP']
    present = [c for c in targets if c in df.columns]

    if present:
        # Create Lite Version (Last 40 quarters)
        lite_df = df[present].dropna(how='all').tail(40)
        lite_df.to_csv('results/lite_residuals.csv', index=False)
        
        # Print Stats to Jenkins Console
        print('\\n' + '='*30 + '\\n📊 LITE STATISTICS\\n' + '='*30)
        print(lite_df.describe())
        sys.stdout.flush()

        # Create Visuals
        plt.figure(figsize=(10, 6))
        lite_df.plot(marker='o')
        plt.title('Key Macro Residuals (Verified Targets)')
        plt.ylabel('Residual Value')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig('results/residual_plot.png')
        print('\\n✅ Visuals and Lite CSV created.')
    else:
        print('⚠️ Warning: No target variables found. Check the DEBUG list above.')
else:
    print('❌ Error: Raw results file not found!')
EOF
                        """
                        
                        // Copy everything back to the host before cleaning up
                        sh "docker cp engine-${env.BUILD_NUMBER}:/home/spark/results/. ./results/"
                        
                    } finally {
                        // Ensure container is always removed
                        sh "docker rm -f engine-${env.BUILD_NUMBER} || true"
                    }
                }
            }
        }
    }

    post {
        always {
            // Archive all results, including the large raw file and the new visual plot
            archiveArtifacts artifacts: 'results/*', allowEmptyArchive: true
        }
    }
}