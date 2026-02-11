pipeline {
    agent any

    environment {
        PYTHONPATH = "/home/spark/.local/lib/python3.9/site-packages:/home/spark:/home/spark/src"
    }

    stages {
        stage('Initialize & Search') {
            steps {
                script {
                    echo "🔍 Preparing workspace and aliasing data..."
                    // Create directories
                    sh "mkdir -p results data"
                    
                    // The "Tealbook-to-Library" Alias Fix
                    sh """
                        if [ ! -f data/library.xlsx ]; then
                            echo '📝 library.xlsx not found, aliasing tealbook_raw.xlsx...'
                            cp data/tealbook_raw.xlsx data/library.xlsx
                        fi
                    """
                    
                    // Verify the Model Path
                    sh "ls -R pyfrbus/models || echo '⚠️ Warning: pyfrbus/models not found!'"
                    
                    sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
                }
            }
        }

        stage('Build Image') {
            steps {
                echo "🔨 Building Docker Image..."
                // Using --no-cache once ensures our new path fixes are captured
                sh "docker build -t macro-engine-image:${env.BUILD_NUMBER} ."
            }
        }

        stage('Run Model Pipeline') {
            steps {
                script {
                    sh "docker run -d --name engine-run-${env.BUILD_NUMBER} macro-engine-image:${env.BUILD_NUMBER} sleep 600"
                    try {
                        echo "🚀 Running Engine..."
                        sh "docker exec -w /home/spark -e PYTHONPATH=${env.PYTHONPATH} engine-run-${env.BUILD_NUMBER} python3 src/preprocess.py"
                        sh "docker exec -w /home/spark -e PYTHONPATH=${env.PYTHONPATH} engine-run-${env.BUILD_NUMBER} python3 src/engine.py"
                        
                        echo "📥 Extracting Raw Results..."
                        sh "docker cp engine-run-${env.BUILD_NUMBER}:/home/spark/results/. ./results/"
                    } finally {
                        sh "docker rm -f engine-run-${env.BUILD_NUMBER} || true"
                    }
                }
            }
        }

        stage('Post-Process & Visuals') {
            steps {
                script {
                    echo "🧹 Generating Lite Version and Descriptives..."
                    // This runs a python block to filter data and create a plot
                    sh """
                    python3 -c "
                    import pandas as pd
                    import matplotlib.pyplot as plt
                    import os

                    # Load the 'aids-ridden' file
                    df = pd.read_csv('results/calibration_residuals_e.csv')
                    
                    # Define Lite Variables (Common FRB/US targets)
                    targets = ['LUR', 'XGDP', 'PCE', 'RFF']
                    present = [c for c in targets if c in df.columns]
                    
                    if present:
                        lite_df = df[present].dropna(how='all').tail(40) # Last 10 years (quarterly)
                        lite_df.to_csv('results/lite_residuals.csv', index=False)
                        
                        # Generate Descriptive Statistics
                        print('\\n--- LITE STATISTICS ---')
                        print(lite_df.describe())

                        # Generate Visual Plot
                        plt.figure(figsize=(10, 6))
                        lite_df.plot()
                        plt.title('Macro Residuals (Lite View)')
                        plt.grid(True)
                        plt.savefig('results/residual_plot.png')
                        print('✅ Visuals generated.')
                    else:
                        print('⚠️ No target variables found to plot.')
                    "
                    """
                }
            }
        }
    }

    post {
        always {
            // Archive everything: the big file, the lite file, and the PNG
            archiveArtifacts artifacts: 'results/*', allowEmptyArchive: true
        }
    }
}