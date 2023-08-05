pipeline {
    agent any
    environment {
        TWINE_CREDENTIALS = credentials("nexus")
    }
    stages {
        stage("Clean workspace") {
            steps {
                sh "git clean -xdf"
            }
        }
        stage("Run in container") {
            agent {
                docker {
                    image "python:3.8.15-bullseye"
                    reuseNode true
                }
            }
            environment {
                HOME = "${env.WORKSPACE}"
                USERNAME = "jenkins" // getpass.getuser() fix
            }
            stages {
                stage("Install dependencies") {
                    steps {
                        sh "python -m pip install --user .[test]"
                    }
                }
                stage("Run tests") {
                    stages {
                        stage("Run mypy") {
                            steps {
                                sh "python -m mypy it tests"
                            }
                        }
                        stage("Run pylint") {
                            steps {
                                sh "python -m pylint it tests"
                            }
                        }
                        stage("Run pytest") {
                            steps {
                                sh "python -m pytest tests"
                            }
                        }
                    }
                }
                stage("Build wheel") {
                    steps {
                        sh "python setup.py bdist_wheel"
                    }
                }
                stage("Publish wheel") {
                    when {
                        branch 'main'
                    }
                    steps {
                        sh "python -m pip install --user twine"
                        sh "python -m twine upload --repository-url https://nexus.buddaphest.se/repository/pypi-releases/ --u '${TWINE_CREDENTIALS_USR}' --p '${TWINE_CREDENTIALS_PSW}' dist/*"
                    }
                }
            }
        }
    }
    post {
        always {
            sh "docker system prune -af"
        }
    }
}
