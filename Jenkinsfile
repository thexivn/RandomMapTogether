pipeline {
    agent any
    stages {
        stage("Run tests in container") {
            agent {
                dockerfile true
            }
            stages {
                stage("Install dependencies") {
                    steps {
                        sh "python -m pip install --user .['test']"
                    }
                }
                stage("Run mypy") {
                    steps {
                        sh "python -m mypy random_maps_together tests --check-untyped-defs"
                    }
                }
                stage("Run pylint") {
                    steps {
                        sh "python -m pylint random_maps_together tests"
                    }
                }
                stage("Run pytest") {
                    steps {
                        sh "python -m pytest tests"
                    }
                }
            }
        }
    }
}
