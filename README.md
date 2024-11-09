# Bundesliga Football Match Prediction

This project provides weekly predictions of Bundesliga football player performance using the LGBM (LightGBM) algorithm. Predictions are based on match statistics, head-to-head performance, and other relevant factors, with an automated pipeline for data retrieval, transformation, and model training.

## Project Overview

This repository contains a complete solution for building, deploying, and maintaining a Bundesliga football match prediction system. Key components include:

- **Web scraping**: Automated script to collect weekly data from the [FBref](https://fbref.com) website.
- **Containerization**: Dockerized environment with dependencies, pushed to AWS ECS.
- **AWS ECS Integration**: Configuration of ECS tasks, including service and task roles, to handle automated jobs.
- **Batch Job Scheduling**: Batch job scheduling using AWS Lambda and EventBridge to trigger the data pipeline weekly.
- **Data Storage**: Collected data is stored in an S3 bucket for secure and reliable storage.
- **Data Transformation**: AWS Glue processes the data for model training and predictions.
- **Model Training and Deployment**: SageMaker trains and deploys the LGBM model.
- **Email Notifications**: Weekly emails to users with the predicted results.

## Pipeline Flow

1. **Web Scraping**: Python script scrapes player performance data from FBref weekly.
2. **Dockerization**: Script builds and pushes a Docker container with necessary dependencies to AWS ECS.
3. **ECS Task Configuration**: Sets up ECS task and service roles, configuring AWS permissions.
4. **Scheduling with Lambda**: Lambda function triggers weekly batch jobs on a predetermined schedule.
5. **Data Storage**: Raw and processed data stored in Amazon S3.
6. **Data Transformation**: AWS Glue transforms and prepares the data for modeling.
7. **Model Training and Deployment**: LGBM model is trained on SageMaker and deployed to generate predictions.
8. **Weekly Email Notifications**: Predicted results are sent to users via email.

## Architecture Diagram

Below is the architecture diagram illustrating the data flow and AWS services involved in the prediction pipeline:

![AWS Bundesliga Match Prediction Architecture](./AWS%20Bundesliga%20Match%20Prediction%20Diagram.drawio.png)

## Setup and Requirements

### Prerequisites
- **AWS Account**: Access to AWS services, including ECS, Lambda, EventBridge, S3, Glue, and SageMaker.
- **Docker**: For containerizing the web scraping and data processing scripts.
- **Python**: Version 3.x with necessary libraries (listed in `requirements.txt`).

### Improvements
- Expand the model to predict additional metrics.
- Add a front-end dashboard for real-time viewing of predictions.
- Non measurable factors such as player mood, mentality strength are ommitted which could be essential for model accuracy 

1. Clone this repository:
   ```bash
   git clone https://github.com/username/bundesliga-football-prediction.git
   cd bundesliga-football-prediction
